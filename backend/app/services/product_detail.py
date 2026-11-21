"""商品詳細（FR-01）。

商品の情報（説明は全文）を返す。シーンを引き継いだときは、検索と同じ集計（scene_stats）で
買った人数・同じシーンの★と件数・同じシーンで買った人のレビュー一覧（新しい順・コメントが空のものも含む）を返す。
"""
from datetime import date

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Order, OrderItem, Product, Review
from app.schemas.search import ProductDetail, SceneReview
from app.services.scene_stats import order_conditions, round_rating, scene_pairs_subquery


def get_product_detail(
    db: Session, product_id: str, scene: str | None, base_date: date | None = None
) -> ProductDetail | None:
    """商品がなければ None（router で 404 にする）"""
    product = db.get(Product, product_id)
    if product is None:
        return None

    detail = ProductDetail(
        product_id=product.product_id,
        product_name=product.product_name,
        category=product.category,
        brand=product.brand,
        price=product.price,
        description=product.description or "",
        rating=float(product.rating) if product.rating is not None else None,
        review_count=product.review_count,
        scene=scene,
        buyer_count=None,
        scene_rating_avg=None,
        scene_review_count=None,
        scene_reviews=[],
    )
    if scene is None:
        return detail

    conditions = order_conditions(scene, None, base_date or settings.search_base_date)

    # 買った人数（検索と同じ数え方）
    buyer_count = db.scalar(
        select(func.count(distinct(Order.user_id)))
        .join(OrderItem, OrderItem.order_id == Order.order_id)
        .where(OrderItem.product_id == product_id, *conditions)
    ) or 0

    # 同じシーンで買った人のレビュー（新しい順）
    pairs = scene_pairs_subquery(conditions)
    reviews = db.scalars(
        select(Review)
        .join(pairs, (Review.user_id == pairs.c.user_id) & (Review.product_id == pairs.c.product_id))
        .where(Review.product_id == product_id)
        .order_by(Review.posted_at.desc(), Review.review_id.desc())
    ).all()

    scene_reviews = [
        SceneReview(review_id=r.review_id, rating=r.rating, comment=r.comment or None, posted_at=r.posted_at)
        for r in reviews
    ]
    average = sum(r.rating for r in reviews) / len(reviews) if reviews else None

    return detail.model_copy(
        update={
            "buyer_count": buyer_count,
            "scene_rating_avg": round_rating(average),
            "scene_review_count": len(reviews),
            "scene_reviews": scene_reviews,
        }
    )
