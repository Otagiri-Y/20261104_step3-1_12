"""チームで追加する列・テーブル（sql/001）が、いま DB にあるかを調べる。

共有 DB に 001 を流す前でも、キーワード・カテゴリー・シーンでは検索できるようにするために使う。
"""
from dataclasses import dataclass

from sqlalchemy import inspect
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class SchemaStatus:
    has_relationship: bool  # orders.relationship 列があるか
    has_feedback: bool      # gift_feedback テーブルがあるか


def get_schema_status(db: Session) -> SchemaStatus:
    inspector = inspect(db.get_bind())
    order_columns = {c["name"] for c in inspector.get_columns("orders")}
    return SchemaStatus(
        has_relationship="relationship" in order_columns,
        has_feedback=inspector.has_table("gift_feedback"),
    )
