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


# 検索で選べるシーン（要件定義書 3章 FR-02）。orders.estimated_scene の値と1文字も違わないこと。
# 「毎年決まった相手への贈答」は対象外。シーンを変えるときはここだけ直す（8章 運用・保守性）
TARGET_SCENES: tuple[str, ...] = ("送別", "友人への誕生日", "家族への誕生日", "ビジネスのお礼")


@dataclass(frozen=True)
class Settings:
    # CORS：この API を呼んでよい画面の URL（カンマ区切り）
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.environ.get("CORS_ORIGINS", ""))
    )
    # 「直近1年」の基準日（要件定義書 6.2：2026-06-30）
    search_base_date: date = field(
        default_factory=lambda: date.fromisoformat(
            os.environ.get("SEARCH_BASE_DATE") or "2026-06-30"
        )
    )
    # 検索で選べるシーン
    target_scenes: tuple[str, ...] = TARGET_SCENES
    # 買った人数がこの人数未満なら「購入実績あり（少数）」と出す（FR-04。3人は仮置き）
    min_buyers_to_show: int = 3
    # 根拠の文で順位を付けるのは、この順位まで（FR-04：上位3位）
    max_rank_to_show: int = 3
    # 余力（関係性）：候補がこの件数未満なら、シーンだけ一致する注文で補う（6.2）
    min_candidates: int = 3


settings = Settings()
