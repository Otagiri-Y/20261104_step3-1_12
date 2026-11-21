"""計測の記録 API（POST /api/v1/events）の受け取る形・返す形（要件定義書 4.3・FR-11・FR-12）。
形を変えたら、画面の types/events.ts も同時に直す（AGENTS.md）"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# 記録する行動は2つだけ。これ以外は FastAPI が自動で 422 にする（6.4 No.19）
EventType = Literal["pdp_view", "add_to_cart"]


class EventCreate(BaseModel):
    session_id: str = Field(min_length=1, max_length=36, description="ブラウザで作ったランダムな文字列")
    event_type: EventType = Field(description="pdp_view：商品詳細を見た／add_to_cart：カートに入れた（模擬）")
    product_id: str = Field(min_length=1, max_length=10, description="商品ID")
    scene: str | None = Field(default=None, max_length=20, description="検索で選んだシーン。なしは null")


class EventCreated(BaseModel):
    event_id: int
    occurred_at: datetime = Field(description="API が受け取った時刻（日本時間）")
