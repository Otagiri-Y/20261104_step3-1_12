"""商品詳細（FR-01）のテスト。No は要件定義書 6.4 のテストケース番号（No.20〜 は追加）"""
from datetime import date

from fastapi.testclient import TestClient

from tests.conftest import Seeder

SCENE = "送別"


def _detail(client: TestClient, pid: str, **params: str) -> dict:
    res = client.get(f"/api/v1/products/{pid}", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def test_no11_detail_has_full_description(client: TestClient, seed: Seeder) -> None:
    long_text = "あ" * 120
    seed.product("P1", description=long_text)
    seed.commit()

    body = _detail(client, "P1")
    assert body["description"] == long_text  # 全文（60文字で切るのはカードだけ）


def test_without_scene_has_no_evidence(client: TestClient, seed: Seeder) -> None:
    seed.product("P1", rating=4.2)
    users = seed.orders("P1", SCENE, buyers=3)
    seed.review("P1", users[0], 5, "よかった")
    seed.commit()

    body = _detail(client, "P1")
    assert body["scene"] is None
    assert body["buyer_count"] is None
    assert body["scene_rating_avg"] is None
    assert body["scene_review_count"] is None
    assert body["scene_reviews"] == []
    assert body["rating"] == 4.2  # 商品全体の★はいつも出す


def test_no14_scene_reviews_only_same_scene_newest_first(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    same = seed.orders("P1", SCENE, buyers=3)
    other = seed.orders("P1", "ビジネスのお礼", buyers=1)
    seed.review("P1", same[0], 3, "古い", posted=date(2026, 1, 1))
    seed.review("P1", same[1], 5, None, posted=date(2026, 5, 1))  # コメントなしも一覧に出す
    seed.review("P1", same[2], 4, "新しい", posted=date(2026, 3, 1))
    seed.review("P1", other[0], 1, "別のシーン")
    seed.commit()

    body = _detail(client, "P1", scene=SCENE)
    assert body["scene"] == SCENE
    assert body["buyer_count"] == 3
    assert body["scene_review_count"] == 3
    assert body["scene_rating_avg"] == 4.0
    assert [r["comment"] for r in body["scene_reviews"]] == [None, "新しい", "古い"]
    assert body["scene_reviews"][0]["posted_at"] == "2026-05-01"


def test_detail_values_match_search_card(client: TestClient, seed: Seeder) -> None:
    """検索のカードと商品詳細で、買った人数と★が同じになる"""
    seed.product("P1")
    seed.buy("U1", "P1", SCENE)
    seed.buy("U1", "P1", SCENE)  # 同じ人の2回目
    users = seed.orders("P1", SCENE, buyers=2)
    seed.review("P1", "U1", 5)
    seed.review("P1", users[0], 2)
    seed.commit()

    card = client.get("/api/v1/search", params={"scene": SCENE}).json()["results"][0]
    detail = _detail(client, "P1", scene=SCENE)
    assert card["buyer_count"] == detail["buyer_count"] == 3
    assert card["scene_rating_avg"] == detail["scene_rating_avg"] == 3.5
    assert card["scene_review_count"] == detail["scene_review_count"] == 2


def test_scene_not_bought_returns_zero(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.orders("P1", "ビジネスのお礼", buyers=3)
    seed.commit()

    body = _detail(client, "P1", scene=SCENE)
    assert body["buyer_count"] == 0
    assert body["scene_rating_avg"] is None
    assert body["scene_review_count"] == 0
    assert body["scene_reviews"] == []


def test_out_of_stock_product_still_opens(client: TestClient, seed: Seeder) -> None:
    seed.product("OUT", stock=0)
    seed.commit()

    assert _detail(client, "OUT")["product_id"] == "OUT"


def test_blank_scene_means_not_selected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.commit()

    assert _detail(client, "P1", scene="")["scene"] is None


def test_no20_unknown_product_is_404(client: TestClient) -> None:
    res = client.get("/api/v1/products/G9999")
    assert res.status_code == 404
    assert res.json()["detail"] == "商品が見つかりません"


def test_scene_outside_four_is_rejected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.commit()

    res = client.get("/api/v1/products/P1", params={"scene": "毎年決まった相手への贈答"})
    assert res.status_code == 422
