"""班のDB（Azure MySQL）への接続。接続情報は .env から読む（GitHub に上げない）。"""
import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings  # noqa: F401  .env の読み込みを先に済ませる

REQUIRED_ENV = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]


def _ssl_args() -> dict:
    """Azure は暗号化しない接続を断る。証明書のパスがあれば、相手が Azure のサーバーかも確かめる"""
    ca = os.environ.get("DB_SSL_CA")
    return {"ssl": {"ca": ca}} if ca else {"ssl": {"ssl_disabled": False}}


@lru_cache
def get_engine() -> Engine:
    """最初に使うときに1回だけ engine を作る（テストでは DB につながずに import できる）"""
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f".env に設定がありません: {', '.join(missing)}"
            "（.env.example を .env にコピーして埋める）"
        )
    url = URL.create(
        "mysql+pymysql",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],  # 記号を含んでも URL.create がエスケープする
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ["DB_NAME"],
        query={"charset": "utf8mb4"},
    )
    return create_engine(
        url,
        connect_args={"connect_timeout": 10, **_ssl_args()},
        pool_pre_ping=True,
    )


def get_db() -> Iterator[Session]:
    """FastAPI の Depends で使う。リクエストごとに Session を開いて閉じる"""
    session_factory = sessionmaker(bind=get_engine(), autoflush=False)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
