"""商品検索（FR-02・FR-04・FR-06）。キーワード・カテゴリー・シーン・予算帯を組み合わせて探す。

選んだ条件は、すべて満たす商品（AND）を返す。
  ・シーンを選んでいない：条件に合う商品を、直近1年の販売数の多い順に並べる
  ・シーンを選んだ：要件定義書 6.2 のとおり
      候補：直近1年の注文のうち、選んだシーンの注文に含まれる商品
      順位：① 買った人数 → ② 同じシーンの★ → ③ 商品全体の★ → ④ 販売数 → product_id
      根拠：① 買った人数の文（reason） ② 同じシーンの★と件数 ③ コメントがある最新のレビュー1件
  ・余力（関係性）：関係性も選んで候補が3件未満なら、シーンだけ一致する注文で補う（補った商品は下に並べる）
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product
from app.schemas.search import SearchItem, SearchResponse
from app.services.scene_stats import (
    buyers_subquery,
    latest_comment_subquery,
    order_conditions,
    round_rating,
    scene_pairs_subquery,
    scene_review_stats_subquery,
)


@dataclass(frozen=True)
class ProductSearchQuery:
    q: str = ""
    category: str | None = None
    scene: str | None = None
    relationship: str | None = None  # 余力
    price_min: int | None = None
    price_max: int | None = None
    limit: int = 20

    @property
    def uses_purchase_history(self) -> bool:
        return self.scene is not None or self.relationship is not None


@dataclass(frozen=True)
class Row:
    """1商品分の検索結果（並べる前）"""

    product: Product
    buyer_count: int | None = None
    scene_rating_avg: float | None = None
    scene_review_count: int = 0
    review_rating: int | None = None
    review_comment: str | None = None


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


def _fetch_by_sales(db: Session, query: ProductSearchQuery) -> list[Row]:
    """シーンを選んでいないとき：販売数の多い順"""
    stmt = (
        select(Product)
        .where(*_product_conditions(query))
        .order_by(Product.sales_count.desc(), Product.product_id)
        .limit(query.limit)
    )
    return [Row(product=p) for p in db.scalars(stmt).all()]


def _fetch_by_history(
    db: Session,
    query: ProductSearchQuery,
    scene: str | None,
    relationship: str | None,
    base_date: date,
    exclude_ids: list[str],
    limit: int,
) -> list[Row]:
    """選んだシーンの購入実績で候補を集計し、6.2 の順位で上位 limit 件を返す"""
    conditions = order_conditions(scene, relationship, base_date)
    buyers = buyers_subquery(conditions)
    pairs = scene_pairs_subquery(conditions)
    stats = scene_review_stats_subquery(pairs)
    latest = latest_comment_subquery(pairs)

    stmt = (
        select(
            Product,
            buyers.c.buyer_count,
            stats.c.scene_rating_avg,
            func.coalesce(stats.c.scene_review_count, 0),
            latest.c.review_rating,
            latest.c.review_comment,
        )
        .join(buyers, buyers.c.product_id == Product.product_id)
        .outerjoin(stats, stats.c.product_id == Product.product_id)
        .outerjoin(latest, latest.c.product_id == Product.product_id)
        .where(*_product_conditions(query))
    )
    if exclude_ids:
        stmt = stmt.where(Product.product_id.not_in(exclude_ids))

    # DESC では NULL が最後に来る（MySQL・SQLite とも NULL を最小として扱う）＝レビューなしは後ろ
    stmt = stmt.order_by(
        buyers.c.buyer_count.desc(),
        stats.c.scene_rating_avg.desc(),
        Product.rating.desc(),
        Product.sales_count.desc(),
        Product.product_id,  # すべて同じなら商品IDで固定（再現性。6.4 No.10）
    ).limit(limit)

    return [
        Row(
            product=r[0],
            buyer_count=int(r[1]),
            scene_rating_avg=round_rating(r[2]),
            scene_review_count=int(r[3]),
            review_rating=r[4],
            review_comment=r[5],
        )
        for r in db.execute(stmt).all()
    ]


def situation_label(scene: str | None, relationship: str | None) -> str:
    return " × ".join(v for v in (scene, relationship) if v)


def build_reason(situation: str, buyer_count: int, rank: int) -> str:
    """根拠①の文（6.3）。生成AIは使わず、並び順のキー①の値を決まった文に入れる。
    3人未満は順位より「少数」を優先する（2人で「1位」と見せると根拠として強すぎるため）"""
    if buyer_count < settings.min_buyers_to_show:
        return f"{situation}での購入実績あり（少数）"
    if rank <= settings.max_rank_to_show:
        return f"{situation}で選ばれた商品の中で {rank}位（{buyer_count}人）"
    return f"{situation}で {buyer_count}人 が購入"


def _to_item(row: Row, rank: int, situation: str | None, is_supplemented: bool) -> SearchItem:
    p = row.product
    return SearchItem(
        product_id=p.product_id,
        product_name=p.product_name,
        category=p.category,
        brand=p.brand,
        price=p.price,
        description=p.description or "",
        rating=float(p.rating) if p.rating is not None else None,
        review_count=p.review_count,
        rank=rank,
        buyer_count=row.buyer_count,
        reason=build_reason(situation, row.buyer_count, rank)
        if situation and row.buyer_count is not None
        else None,
        scene_rating_avg=row.scene_rating_avg,
        scene_review_count=row.scene_review_count,
        review_rating=row.review_rating,
        review_comment=row.review_comment,
        is_supplemented=is_supplemented,
    )


def search_products(db: Session, query: ProductSearchQuery, base_date: date | None = None) -> SearchResponse:
    if not query.uses_purchase_history:
        rows = _fetch_by_sales(db, query)
        items = [_to_item(r, i + 1, None, False) for i, r in enumerate(rows)]
        return SearchResponse(total=len(items), uses_purchase_history=False, supplemented=False, results=items)

    base = base_date or settings.search_base_date
    primary = _fetch_by_history(db, query, query.scene, query.relationship, base, [], query.limit)

    # 余力：シーンと関係性の両方を選んで候補が少ないときは、シーンだけ一致する注文で補う（6.2）
    extra: list[Row] = []
    can_supplement = query.scene is not None and query.relationship is not None
    if can_supplement and len(primary) < settings.min_candidates and len(primary) < query.limit:
        extra = _fetch_by_history(
            db,
            query,
            query.scene,
            None,
            base,
            [r.product.product_id for r in primary],
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
