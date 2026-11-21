"""商品詳細 API（/api/v1/products/{product_id}）"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import ProductDetail
from app.services.options import list_scenes
from app.services.product_detail import get_product_detail

router = APIRouter(prefix="/api/v1/products", tags=["products"])

MESSAGE_NOT_FOUND = "商品が見つかりません"


@router.get("/{product_id}", response_model=ProductDetail)
def product_detail(
    db: Annotated[Session, Depends(get_db)],
    product_id: Annotated[str, Path(max_length=10, description="商品ID（例：G0001）")],
    scene: Annotated[str | None, Query(max_length=20, description="検索で選んだシーン（空なら指定なし）")] = None,
) -> ProductDetail:
    """FR-01：商品の情報と、同じシーンで買った人の根拠を返す"""
    scene = scene or None  # 空文字は「指定なし」
    if scene is not None and scene not in list_scenes():
        raise HTTPException(status_code=422, detail=f"選べないシーンです：{scene}")
    detail = get_product_detail(db, product_id, scene)
    if detail is None:
        raise HTTPException(status_code=404, detail=MESSAGE_NOT_FOUND)
    return detail
