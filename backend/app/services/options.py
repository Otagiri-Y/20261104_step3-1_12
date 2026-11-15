"""検索画面で選べる値。DB に入っている値から作る（選択肢を変えるときは DB を直す。8章）"""
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models import Order, Product
from app.schemas.search import OptionsResponse
from app.services.schema_status import SchemaStatus, get_schema_status


def _distinct_values(db: Session, column: InstrumentedAttribute[str | None]) -> list[str]:
    stmt = select(column).where(column.is_not(None)).distinct().order_by(column)
    return [v for v in db.scalars(stmt).all() if v]


def list_categories(db: Session) -> list[str]:
    return _distinct_values(db, Product.category)


def list_scenes(db: Session) -> list[str]:
    return _distinct_values(db, Order.estimated_scene)


def list_relationships(db: Session, status: SchemaStatus) -> list[str]:
    """関係性の列がまだない（sql/001 が未実行）ときは空にする"""
    if not status.has_relationship:
        return []
    return _distinct_values(db, Order.relationship)


def get_options(db: Session) -> OptionsResponse:
    status = get_schema_status(db)
    return OptionsResponse(
        categories=list_categories(db),
        scenes=list_scenes(db),
        relationships=list_relationships(db, status),
        relationship_available=status.has_relationship,
    )
