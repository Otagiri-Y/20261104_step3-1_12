"""検索 API（/api/v1/search）。クエリを受け取って検証し、Service に渡す"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SearchResponse
from app.services.options import list_categories, list_relationships, list_scenes
from app.services.product_search import ProductSearchQuery, search_products
from app.services.schema_status import get_schema_status

router = APIRouter(prefix="/api/v1/search", tags=["search"])


def _blank_to_none(value: str | None) -> str | None:
    """空文字は「指定なし」として扱う"""
    return value if value else None


def _validate(db: Session, query: ProductSearchQuery) -> None:
    """選べない値（/api/v1/options にない値）や、逆転した価格帯を断る"""
    if query.price_min is not None and query.price_max is not None and query.price_min > query.price_max:
        raise HTTPException(status_code=422, detail="価格の下限が上限より大きくなっています")
    if query.category is not None and query.category not in list_categories(db):
        raise HTTPException(status_code=422, detail=f"選べないカテゴリーです：{query.category}")
    if query.scene is not None and query.scene not in list_scenes(db):
        raise HTTPException(status_code=422, detail=f"選べないシーンです：{query.scene}")
    if query.relationship is not None and query.relationship not in list_relationships(db, get_schema_status(db)):
        raise HTTPException(status_code=422, detail=f"選べない関係性です：{query.relationship}")


@router.get("", response_model=SearchResponse)
def search(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(max_length=100, description="キーワード（空白区切りで複数。すべてを含む商品）")] = "",
    category: Annotated[str | None, Query(max_length=50, description="カテゴリー（/api/v1/options の値。空ならすべて）")] = None,
    scene: Annotated[str | None, Query(max_length=50, description="贈るシーン（/api/v1/options の値。空なら指定なし）")] = None,
    relationship: Annotated[str | None, Query(max_length=20, description="相手との関係（/api/v1/options の値。空なら指定なし）")] = None,
    price_min: Annotated[int | None, Query(ge=0, description="価格の下限（以上）")] = None,
    price_max: Annotated[int | None, Query(ge=0, description="価格の上限（以下）")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="返す件数")] = 20,
) -> SearchResponse:
    """FR-02：選んだ条件をすべて満たす商品を返す。
    シーンか関係性を選んだら、同じ状況の購入実績で絞り、決めた順（6.2）に並べる"""
    query = ProductSearchQuery(
        q=q.strip(),
        category=_blank_to_none(category),
        scene=_blank_to_none(scene),
        relationship=_blank_to_none(relationship),
        price_min=price_min,
        price_max=price_max,
        limit=limit,
    )
    _validate(db, query)
    return search_products(db, query)
