"""「同じシーンで買った人」の集計（検索 FR-04・FR-06 と商品詳細 FR-01 で共通に使う）。

同じ集計を使い回すので、検索のカードと商品詳細で、買った人数・★の値が必ずそろう。
  ・買った人数     ：選んだシーンの直近1年の注文で、その商品を買った user_id の数（同じ人の2回目は数えない）
  ・同じシーンの★ ：そのシーンで直近1年に買った「人×商品」と、user_id・product_id が同じレビュー
                     （reviews に注文IDはないため。要件定義書 5.2）
  ・レビュー1件    ：同じシーンのレビューのうち、コメントがある最新の1件
"""
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import ColumnElement, Subquery, and_, distinct, func, select

from app.models import Order, OrderItem, Review


def recent_period(base_date: date) -> tuple[datetime, datetime]:
    """基準日を含む直近1年（365日）。[start, end) の半開区間で返す。
    基準日 2026-06-30 なら 2025-07-01 0:00 〜 2026-07-01 0:00 の手前"""
    end = datetime.combine(base_date + timedelta(days=1), datetime.min.time())
    return end - timedelta(days=365), end


def order_conditions(scene: str | None, relationship: str | None, base_date: date) -> list[ColumnElement[bool]]:
    """注文の条件：直近1年・シーン・関係性（余力）"""
    start, end = recent_period(base_date)
    conditions = [Order.ordered_at >= start, Order.ordered_at < end]
    if scene is not None:
        conditions.append(Order.estimated_scene == scene)
    if relationship is not None:
        conditions.append(Order.relationship == relationship)
    return conditions


def buyers_subquery(conditions: list[ColumnElement[bool]]) -> Subquery:
    """商品ごとの買った人数（product_id, buyer_count）"""
    return (
        select(OrderItem.product_id, func.count(distinct(Order.user_id)).label("buyer_count"))
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(*conditions)
        .group_by(OrderItem.product_id)
        .subquery()
    )


def scene_pairs_subquery(conditions: list[ColumnElement[bool]]) -> Subquery:
    """その条件で買った「人×商品」の組（user_id, product_id）。DISTINCT にして、
    同じ人が同じ商品を2回買っても、レビュー1件が2回数えられないようにする"""
    return (
        select(Order.user_id, OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(*conditions)
        .distinct()
        .subquery()
    )


def _scene_review_join(pairs: Subquery) -> ColumnElement[bool]:
    return and_(Review.user_id == pairs.c.user_id, Review.product_id == pairs.c.product_id)


def scene_review_stats_subquery(pairs: Subquery) -> Subquery:
    """商品ごとの同じシーンの★（product_id, scene_rating_avg, scene_review_count）"""
    return (
        select(
            Review.product_id,
            func.avg(Review.rating).label("scene_rating_avg"),
            func.count(Review.review_id).label("scene_review_count"),
        )
        .join(pairs, _scene_review_join(pairs))
        .group_by(Review.product_id)
        .subquery()
    )


def has_comment() -> ColumnElement[bool]:
    return and_(Review.comment.is_not(None), Review.comment != "")


def latest_comment_subquery(pairs: Subquery) -> Subquery:
    """商品ごとに、同じシーンでコメントがある最新のレビュー1件（product_id, review_rating, review_comment）。
    posted_at は日付だけなので、同じ日なら review_id の大きいほうを新しいとみなす"""
    ranked = (
        select(
            Review.product_id,
            Review.rating.label("review_rating"),
            Review.comment.label("review_comment"),
            func.row_number()
            .over(partition_by=Review.product_id, order_by=(Review.posted_at.desc(), Review.review_id.desc()))
            .label("rn"),
        )
        .join(pairs, _scene_review_join(pairs))
        .where(has_comment())
        .subquery()
    )
    return (
        select(ranked.c.product_id, ranked.c.review_rating, ranked.c.review_comment)
        .where(ranked.c.rn == 1)
        .subquery()
    )


def round_rating(value: float | Decimal | None) -> float | None:
    """★の平均を小数1桁に四捨五入する（表示用。Python の round は 3.25 → 3.2 になるため使わない）"""
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
