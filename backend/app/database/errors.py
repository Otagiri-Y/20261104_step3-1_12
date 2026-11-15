"""DB エラーの見分け方。画面に出すメッセージを原因ごとに分ける"""
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

# MySQL のエラー番号：1054 = 列がない、1146 = テーブルがない
MYSQL_MISSING_SCHEMA_CODES = {1054, 1146}
# SQLite（テスト）での同じエラーの文言
SQLITE_MISSING_SCHEMA_TEXTS = ("no such column", "no such table")


def is_missing_schema(exc: SQLAlchemyError) -> bool:
    """チームで追加する列・テーブル（sql/001）がまだ DB にないときのエラーか"""
    if not isinstance(exc, DBAPIError) or exc.orig is None:
        return False
    args = getattr(exc.orig, "args", ())
    if args and args[0] in MYSQL_MISSING_SCHEMA_CODES:
        return True
    message = str(exc.orig).lower()
    return any(text in message for text in SQLITE_MISSING_SCHEMA_TEXTS)
