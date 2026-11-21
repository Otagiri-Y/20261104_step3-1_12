"""Giftia API の入り口。起動：backend フォルダで `uvicorn app.main:app --reload`"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database.errors import is_missing_schema
from app.routers import health, options, products, search

logger = logging.getLogger(__name__)

app = FastAPI(title="Giftia Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(options.router)
app.include_router(search.router)
app.include_router(products.router)


MESSAGE_ENV_MISSING = "データベースの設定が見つかりません"
MESSAGE_SCHEMA_MISSING = (
    "必要なテーブルや列がデータベースにありません。"
    "backend/sql の SQL が班の DB に流されているか確かめてください"
)
MESSAGE_DB_ERROR = "データベースに接続できません。時間をおいて試してください"


@app.exception_handler(EnvironmentError)
def handle_env_error(_: Request, exc: EnvironmentError) -> JSONResponse:
    """.env の設定漏れ。画面にはメッセージだけ返す"""
    logger.error("DB 設定エラー: %s", exc)
    return JSONResponse(status_code=503, content={"detail": MESSAGE_ENV_MISSING})


@app.exception_handler(SQLAlchemyError)
def handle_db_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    """SQL が失敗した。原因に合ったメッセージを返し、詳細はサーバーのログにだけ出す"""
    if is_missing_schema(exc):
        logger.error("DB の列・テーブルが足りません（backend/sql が未実行の可能性）: %s", exc.orig)
        return JSONResponse(status_code=503, content={"detail": MESSAGE_SCHEMA_MISSING})
    # ここはもう except の外なので、logger.exception ではなく exc_info で例外を渡す
    logger.error("DB エラー: %s", exc, exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": MESSAGE_DB_ERROR})
