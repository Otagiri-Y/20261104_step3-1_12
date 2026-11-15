"""アプリ全体の設定。値は .env（環境変数）から読み、なければ要件定義書の値を使う。"""
import os
from dataclasses import dataclass, field
from datetime import date

from dotenv import load_dotenv

# backend/.env を読み、os.environ に入れる。
# テストでは GIFTIA_SKIP_DOTENV=1 にして読まない（接続情報に触れず、班の DB にもつながない）
if os.environ.get("GIFTIA_SKIP_DOTENV") != "1":
    load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    # CORS：この API を呼んでよい画面の URL（カンマ区切り）
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.environ.get("CORS_ORIGINS", ""))
    )
    # 「直近1年」の基準日（要件定義書 3章 FR-02・6.2：2026-06-30）
    search_base_date: date = field(
        default_factory=lambda: date.fromisoformat(
            os.environ.get("SEARCH_BASE_DATE") or "2026-06-30"
        )
    )
    # 購入人数をこの人数以上のときだけ画面に出す（FR-04）
    min_buyers_to_show: int = 3
    # 相手の反応をこの件数以上のときだけ出し、並び順にも使う（FR-01・FR-04）
    min_reactions_to_show: int = 3
    # 候補がこの件数未満なら、シーンだけ一致する注文で補う（6.2）
    min_candidates: int = 3


settings = Settings()
