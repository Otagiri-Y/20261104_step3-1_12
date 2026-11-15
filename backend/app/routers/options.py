"""選択肢 API（/api/v1/options）"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import OptionsResponse
from app.services.options import get_options

router = APIRouter(prefix="/api/v1/options", tags=["options"])


@router.get("", response_model=OptionsResponse)
def options(db: Annotated[Session, Depends(get_db)]) -> OptionsResponse:
    """検索画面で選べるシーンと関係性の一覧"""
    return get_options(db)
