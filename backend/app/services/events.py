"""計測の記録（FR-11・FR-12）。商品詳細を見た・カートに入れた（模擬）を site_event_log に1行ずつ書く。

班の DB に書き込む、初めての処理。
  ・時刻は画面から受け取らず、API が受け取った時刻（日本時間）を付ける
  ・商品IDが products にない記録は残さない（router で 422 にする）
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, SiteEventLog
from app.schemas.events import EventCreate, EventCreated

# 日本時間（夏時間がないので、+9時間の固定でよい。Windows でも追加のライブラリなしで動く）
JST = timezone(timedelta(hours=9))


def now_jst() -> datetime:
    """いまの日本時間。DB の DATETIME はタイムゾーンを持たないので、+09:00 の印は外して入れる"""
    return datetime.now(JST).replace(tzinfo=None)


def product_exists(db: Session, product_id: str) -> bool:
    return db.scalar(select(Product.product_id).where(Product.product_id == product_id)) is not None


def record_event(db: Session, event: EventCreate, occurred_at: datetime | None = None) -> EventCreated:
    """1つの行動を1行として書き、書いた行の番号と時刻を返す"""
    row = SiteEventLog(
        session_id=event.session_id,
        event_type=event.event_type,
        product_id=event.product_id,
        scene=event.scene,
        occurred_at=occurred_at or now_jst(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return EventCreated(event_id=row.event_id, occurred_at=row.occurred_at)
