"""商品検索（FR-02・FR-04・FR-06）。キーワード・カテゴリー・シーン・関係性・予算帯を組み合わせて探す。

選んだ条件は、すべて満たす商品（AND）を返す。
  ・シーンも関係性も選んでいない：条件に合う商品を、直近1年の販売数の多い順に並べる（2週目と同じ）
  ・シーンか関係性を選んだ：要件定義書 6.2 のとおり
      候補：直近1年の注文のうち、選んだシーン・関係性に一致する注文に含まれる商品
            シーンと関係性の両方を選んで候補が3件未満なら、シーンだけ一致する注文で補う（補った商品は下に並べる）
      順位：① 買った人数 → ② 相手の反応の平均（3件以上のとき） → ③ レビューの平均星 → ④ 販売数
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import ColumnElement, Select, case, distinct, func, literal, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GiftFeedback, Order, OrderItem, Product
from app.schemas.search import SearchItem, SearchResponse
from app.services.schema_status import SchemaStatus, get_schema_status


@dataclass(frozen=True)
class ProductSearchQuery:
    q: str = ""
    category: str | None = None
    scene: str | None = None
    relationship: str | None = None
    price_min: int | None = None
    price_max: int | None = None
    limit: int = 20

    @property
    def uses_purchase_history(self) -> bool:
        return self.scene is not None or self.relationship is not None


# (商品, 買った人数, 相手の反応の平均, 相手の反応の件数)
Row = tuple[Product, int | None, float | None, int]


def recent_period(base_date: date) -> tuple[datetime, datetime]:
    """基準日を含む直近1年（365日）。[start, end) の半開区間で返す"""
    end = datetime.combine(base_date + timedelta(days=1), datetime.min.time())
    return end - timedelta(days=365), end


def _product_conditions(query: ProductSearchQuery) -> list[ColumnElement[bool]]:
    """商品そのものの条件：在庫・キーワード・カテゴリー・予算帯"""
    conditions: list[ColumnElement[bool]] = [Product.stock > 0]
    for word in query.q.split():
        pattern = f"%{word}%"
        conditions.append(
            or_(
                Product.product_name.like(pattern),
                Product.brand.like(pattern),
                Product.description.like(pattern),
            )
        )
    if query.category:
        conditions.append(Product.category == query.category)
    if query.price_min is not None:
        conditions.append(Product.price >= query.price_min)
    if query.price_max is not None:
        conditions.append(Product.price <= query.price_max)
    return conditions


def _order_conditions(scene: str | None, relationship: str | None, base_date: date) -> list[ColumnElement[bool]]:
    """注文の条件：直近1年・シーン・関係性"""
    start, end = recent_period(base_date)
    conditions = [Order.ordered_at >= start, Order.ordered_at < end]
    if scene is not None:
        conditions.append(Order.estimated_scene == scene)
    if relationship is not None:
        conditions.append(Order.relationship == relationship)
    return conditions


def _fetch_by_sales(db: Session, query: ProductSearchQuery) -> list[Row]:
    """シーン・関係性を選んでいないとき：販売数の多い順（2週目と同じ）"""
    stmt = (
        select(Product)
        .where(*_product_conditions(query))
        .order_by(Product.sales_count.desc(), Product.product_id)
        .limit(query.limit)
    )
    return [(p, None, None, 0) for p in db.scalars(stmt).all()]


def _fetch_by_history(
    db: Session,
    query: ProductSearchQuery,
    order_conditions: list[ColumnElement[bool]],
    status: SchemaStatus,
    exclude_ids: list[str],
    limit: int,
) -> list[Row]:
    """選んだシーン・関係性の購入実績で候補を集計し、6.2 の順位で上位 limit 件を返す"""
    buyers = (
        select(OrderItem.product_id, func.count(distinct(Order.user_id)).label("buyer_count"))
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(*order_conditions)
        .group_by(OrderItem.product_id)
        .subquery()
    )
    stmt: Select = select(Product, buyers.c.buyer_count)

    if status.has_feedback:
        reactions = (
            select(
                OrderItem.product_id,
                func.avg(GiftFeedback.reaction).label("reaction_avg"),
                func.count(GiftFeedback.feedback_id).label("reaction_count"),
            )
            .join(Order, Order.order_id == OrderItem.order_id)
            .join(GiftFeedback, GiftFeedback.order_id == Order.order_id)
            .where(*order_conditions)
            .group_by(OrderItem.product_id)
            .subquery()
        )
        # 表示する値と並び順のキーをそろえる（6.3）：件数が足りない反応は、表示も並び順も使わない
        reaction_key = case(
            (reactions.c.reaction_count >= settings.min_reactions_to_show, reactions.c.reaction_avg),
            else_=None,
        )
        reaction_count = func.coalesce(reactions.c.reaction_count, 0)
        stmt = stmt.add_columns(reaction_key, reaction_count).outerjoin(
            reactions, reactions.c.product_id == Product.product_id
        )
    else:
        # gift_feedback がまだない（sql/001 が未実行）：反応なしとして扱う
        reaction_key = literal(None)
        stmt = stmt.add_columns(reaction_key, literal(0))

    stmt = stmt.join(buyers, buyers.c.product_id == Product.product_id).where(*_product_conditions(query))
    if exclude_ids:
        stmt = stmt.where(Product.product_id.not_in(exclude_ids))

    # DESC では NULL が最後に来る（MySQL・SQLite とも NULL を最小として扱う）
    stmt = stmt.order_by(
        buyers.c.buyer_count.desc(),
        reaction_key.desc(),
        Product.rating.desc(),
        Product.sales_count.desc(),
        Product.product_id,  # すべて同じなら商品IDで固定（再現性。6.4 No.8）
    ).limit(limit)

    return [
        (row[0], int(row[1]), float(row[2]) if row[2] is not None else None, int(row[3]))
        for row in db.execute(stmt).all()
    ]


def situation_label(scene: str | None, relationship: str | None) -> str:
    return " × ".join(v for v in (scene, relationship) if v)


def build_reason(situation: str, buyer_count: int) -> str:
    """根拠の文（6.3 のテンプレート）。生成AIは使わず、並び順のキー①の集計値を入れる"""
    if buyer_count < settings.min_buyers_to_show:
        return f"{situation}での購入実績あり（少数）"
    return f"{situation} に贈った人が {buyer_count}人 選んでいます"


def _to_item(row: Row, rank: int, situation: str | None, is_supplemented: bool) -> SearchItem:
    product, buyer_count, reaction_avg, reaction_count = row
    shown_buyers = (
        buyer_count if buyer_count is not None and buyer_count >= settings.min_buyers_to_show else None
    )
    return SearchItem(
        product_id=product.product_id,
        product_name=product.product_name,
        category=product.category,
        brand=product.brand,
        price=product.price,
        rating=float(product.rating) if product.rating is not None else None,
        review_count=product.review_count,
        buyer_count=shown_buyers,
        reaction_avg=round(reaction_avg, 1) if reaction_avg is not None else None,
        reaction_count=reaction_count,
        rank=rank,
        reason=build_reason(situation, buyer_count) if situation and buyer_count is not None else None,
        is_supplemented=is_supplemented,
    )


def search_products(db: Session, query: ProductSearchQuery, base_date: date | None = None) -> SearchResponse:
    if not query.uses_purchase_history:
        rows = _fetch_by_sales(db, query)
        items = [_to_item(r, i + 1, None, False) for i, r in enumerate(rows)]
        return SearchResponse(total=len(items), uses_purchase_history=False, supplemented=False, results=items)

    base = base_date or settings.search_base_date
    status = get_schema_status(db)
    primary = _fetch_by_history(
        db, query, _order_conditions(query.scene, query.relationship, base), status, [], query.limit
    )

    # シーンと関係性の両方を選んで候補が少ないときは、シーンだけ一致する注文で補う（6.2）
    extra: list[Row] = []
    can_supplement = query.scene is not None and query.relationship is not None
    if can_supplement and len(primary) < settings.min_candidates and len(primary) < query.limit:
        extra = _fetch_by_history(
            db,
            query,
            _order_conditions(query.scene, None, base),
            status,
            [p.product_id for p, *_ in primary],
            query.limit - len(primary),
        )

    situation = situation_label(query.scene, query.relationship)
    items = [_to_item(r, i + 1, situation, False) for i, r in enumerate(primary)]
    items += [
        _to_item(r, len(primary) + i + 1, situation_label(query.scene, None), True)
        for i, r in enumerate(extra)
    ]
    return SearchResponse(
        total=len(items),
        uses_purchase_history=True,
        supplemented=bool(extra),
        results=items,
    )
