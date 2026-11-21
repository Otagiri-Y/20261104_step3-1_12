"""チームで追加する列（sql/001 の orders.relationship）が、いま DB にあるかを調べる。

関係性は余力。共有 DB に 001 を流す前でも、キーワード・カテゴリー・シーン・予算帯で検索できるようにするために使う。
"""
from dataclasses import dataclass

from sqlalchemy import inspect
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class SchemaStatus:
    has_relationship: bool  # orders.relationship 列があるか


def get_schema_status(db: Session) -> SchemaStatus:
    inspector = inspect(db.get_bind())
    order_columns = {c["name"] for c in inspector.get_columns("orders")}
    return SchemaStatus(has_relationship="relationship" in order_columns)
