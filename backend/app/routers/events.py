"""計測の記録 API（POST /api/v1/events）。受け取った行動を確かめて、Service に渡す"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.events import EventCreate, EventCreated
from app.services.events import product_exists, record_event
from app.services.options import list_scenes

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventCreated, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Annotated[Session, Depends(get_db)]) -> EventCreated:
    """FR-11・FR-12：商品詳細を見た／カートに入れた（模擬）を1行記録する。
    event_type が2つ以外・session_id が空や37文字以上なら、FastAPI が自動で 422 にする"""
    scene = event.scene or None  # 空文字は「指定なし」
    if scene is not None and scene not in list_scenes():
        raise HTTPException(status_code=422, detail=f"選べないシーンです：{scene}")
    if not product_exists(db, event.product_id):
        raise HTTPException(status_code=422, detail=f"商品が見つかりません：{event.product_id}")
    return record_event(db, event.model_copy(update={"scene": scene}))
