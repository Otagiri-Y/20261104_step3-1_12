"""sql/001（余力の関係性）を流す前でも検索が動き、テーブルが足りないときは理由が分かるかのテスト"""
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import MESSAGE_SCHEMA_MISSING
from tests.conftest import Seeder


def _drop_team_schema(db: Session) -> None:
    """sql/001 で足す列とテーブルを消して、配布データだけの状態にする（班の DB の今の状態）"""
    db.execute(text("DROP TABLE gift_feedback"))
    db.execute(text("ALTER TABLE orders DROP COLUMN relationship"))
    db.commit()


def test_options_without_team_schema(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("P1", category="食品")
    seed.commit()
    _drop_team_schema(db)

    res = client.get("/api/v1/options")
    assert res.status_code == 200
    body = res.json()
    assert body["categories"] == ["食品"]
    assert body["scenes"] == ["送別", "友人への誕生日", "家族への誕生日", "ビジネスのお礼"]
    assert body["relationships"] == []
    assert body["relationship_available"] is False


def test_search_and_detail_without_team_schema(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("P1", name="焼き菓子")
    users = seed.orders("P1", "送別", buyers=3)
    seed.review("P1", users[0], 4, "よかった")
    seed.commit()
    _drop_team_schema(db)

    keyword = client.get("/api/v1/search", params={"q": "焼き菓子"})
    assert keyword.status_code == 200
    assert [r["product_id"] for r in keyword.json()["results"]] == ["P1"]

    scene = client.get("/api/v1/search", params={"scene": "送別"})
    assert scene.status_code == 200
    item = scene.json()["results"][0]
    assert item["reason"] == "送別で選ばれた商品の中で 1位（3人）"
    assert item["review_comment"] == "よかった"

    detail = client.get("/api/v1/products/P1", params={"scene": "送別"})
    assert detail.status_code == 200
    assert detail.json()["buyer_count"] == 3


def test_relationship_without_team_schema_is_rejected(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("P1")
    seed.commit()
    _drop_team_schema(db)

    res = client.get("/api/v1/search", params={"relationship": "同僚"})
    assert res.status_code == 422


def test_missing_table_returns_clear_message(client: TestClient, db: Session, seed: Seeder) -> None:
    """想定外にテーブルが足りないときも、原因が分かるメッセージを返す"""
    seed.product("P1")
    seed.orders("P1", "送別", buyers=3)
    seed.commit()
    db.execute(text("DROP TABLE reviews"))
    db.commit()

    res = client.get("/api/v1/search", params={"scene": "送別"})
    assert res.status_code == 503
    assert res.json()["detail"] == MESSAGE_SCHEMA_MISSING
