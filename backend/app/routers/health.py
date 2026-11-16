"""接続確認 API（/api/v1/health）"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health(db: Annotated[Session, Depends(get_db)]) -> dict[str, str | int]:
    """つながっているかの確認。DB に何件の商品があるか"""
    products = db.scalar(select(func.count()).select_from(Product)) or 0
    return {"status": "ok", "products": products}
