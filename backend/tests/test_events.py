"""計測の記録（FR-11・FR-12）と、率を出す SQL（sql/004）のテスト。No は要件定義書 6.4 のテストケース番号"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import SiteEventLog
from tests.conftest import Seeder

SESSION = "3f2a8c1e-0000-4000-8000-000000000001"
RATE_SQL = Path(__file__).resolve().parents[1] / "sql" / "004_conversion_rate.sql"


def _post(client: TestClient, **body: str | None) -> dict:
    payload = {"session_id": SESSION, "event_type": "pdp_view", "product_id": "G0001", "scene": "送別"}
    payload.update(body)
    return client.post("/api/v1/events", json=payload)


def _rows(db: Session) -> list[SiteEventLog]:
    return list(db.scalars(select(SiteEventLog).order_by(SiteEventLog.event_id)).all())


def _count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(SiteEventLog)) or 0


# ── 記録（POST /api/v1/events） ──────────────────────────

def test_no16_pdp_view_leaves_one_row(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    res = _post(client)
    assert res.status_code == 201, res.text
    rows = _rows(db)
    assert len(rows) == 1
    row = rows[0]
    assert (row.session_id, row.event_type, row.product_id, row.scene) == (SESSION, "pdp_view", "G0001", "送別")
    assert res.json()["event_id"] == row.event_id


def test_no17_add_to_cart_leaves_one_row_each_time(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    assert _post(client, event_type="add_to_cart").status_code == 201
    assert _post(client, event_type="add_to_cart").status_code == 201
    assert [r.event_type for r in _rows(db)] == ["add_to_cart", "add_to_cart"]


def test_occurred_at_is_japan_time_set_by_api(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    before = datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
    _post(client)
    after = datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
    assert before - timedelta(seconds=1) <= _rows(db)[0].occurred_at <= after + timedelta(seconds=1)


def test_scene_can_be_null_or_blank(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    assert _post(client, scene=None).status_code == 201
    assert _post(client, scene="").status_code == 201
    assert [r.scene for r in _rows(db)] == [None, None]


def test_no19_unknown_event_type_is_rejected(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    assert _post(client, event_type="purchase").status_code == 422
    assert _count(db) == 0


def test_unknown_product_is_rejected(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    res = _post(client, product_id="G9999")
    assert res.status_code == 422
    assert res.json()["detail"] == "商品が見つかりません：G9999"
    assert _count(db) == 0


def test_scene_outside_four_is_rejected(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    assert _post(client, scene="毎年決まった相手への贈答").status_code == 422
    assert _count(db) == 0


def test_bad_session_id_is_rejected(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()

    assert _post(client, session_id="").status_code == 422
    assert _post(client, session_id="x" * 37).status_code == 422
    assert _count(db) == 0


def test_no22_browser_can_post_from_frontend(client: TestClient) -> None:
    """CORS：画面（localhost:3000）から POST してよいと、ブラウザの事前確認に答える"""
    res = client.options("/api/v1/events", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert res.status_code == 200
    assert "POST" in res.headers["access-control-allow-methods"]


# ── 率を出す SQL（sql/004_conversion_rate.sql をそのまま流す） ──────────

def _rate_queries() -> list[str]:
    """ファイルを ; で区切り、コメントだけの部分を除いた SELECT を順に返す"""
    lines = [ln for ln in RATE_SQL.read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("--")]
    return [q.strip() for q in "\n".join(lines).split(";") if q.strip()]


def _record(client: TestClient, session: str, event_type: str, scene: str | None = "送別") -> None:
    assert _post(client, session_id=session, event_type=event_type, scene=scene).status_code == 201


def test_no18_rate_counts_sessions(client: TestClient, db: Session, seed: Seeder) -> None:
    """1つのセッションで商品詳細を2回見てカートに1回入れると、分母1・分子1"""
    seed.product("G0001")
    seed.commit()
    _record(client, "S1", "pdp_view")
    _record(client, "S1", "pdp_view")
    _record(client, "S1", "add_to_cart")

    overall = db.execute(text(_rate_queries()[0])).one()
    assert (overall.viewed_sessions, overall.carted_sessions, float(overall.rate_pct)) == (1, 1, 100.0)


def test_rate_overall_and_by_scene(client: TestClient, db: Session, seed: Seeder) -> None:
    seed.product("G0001")
    seed.commit()
    _record(client, "S1", "pdp_view")                      # 送別：見ただけ
    _record(client, "S2", "pdp_view")                      # 送別：見て入れた
    _record(client, "S2", "add_to_cart")
    _record(client, "S3", "pdp_view", scene="ビジネスのお礼")  # お礼：見ただけ
    _record(client, "S4", "pdp_view", scene=None)          # 指定なし：見て入れた
    _record(client, "S4", "add_to_cart", scene=None)

    queries = _rate_queries()
    overall = db.execute(text(queries[0])).one()
    assert (overall.viewed_sessions, overall.carted_sessions, float(overall.rate_pct)) == (4, 2, 50.0)

    by_scene = {r.scene: (r.viewed_sessions, r.carted_sessions, float(r.rate_pct)) for r in db.execute(text(queries[1]))}
    assert by_scene == {"送別": (2, 1, 50.0), "ビジネスのお礼": (1, 0, 0.0), "指定なし": (1, 1, 100.0)}


def test_rate_ignores_cart_without_view(client: TestClient, db: Session, seed: Seeder) -> None:
    """商品詳細を見ていないセッションは分母にも分子にも入らない"""
    seed.product("G0001")
    seed.commit()
    _record(client, "S1", "pdp_view")
    _record(client, "S2", "add_to_cart")

    overall = db.execute(text(_rate_queries()[0])).one()
    assert (overall.viewed_sessions, overall.carted_sessions) == (1, 0)
