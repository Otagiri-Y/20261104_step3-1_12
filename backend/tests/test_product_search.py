"""商品検索（FR-02）のテスト。No は要件定義書 6.4 のテストケース番号"""
from fastapi.testclient import TestClient

from tests.conftest import OUT_OF_PERIOD, Seeder

SCENE = "送別"
REL = "同僚"


def _search(client: TestClient, **params: str | int) -> dict:
    res = client.get("/api/v1/search", params={"scene": SCENE, "relationship": REL, **params})
    assert res.status_code == 200, res.text
    return res.json()


def _ids(body: dict) -> list[str]:
    return [r["product_id"] for r in body["results"]]


def test_no1_ranks_by_buyers_in_same_situation(client: TestClient, seed: Seeder) -> None:
    seed.product("P1"); seed.product("P2"); seed.product("P3"); seed.product("P_OTHER")
    seed.orders("P1", SCENE, REL, buyers=5)
    seed.orders("P2", SCENE, REL, buyers=8)
    seed.orders("P3", SCENE, REL, buyers=3)
    seed.orders("P_OTHER", SCENE, "取引先", buyers=20)  # 関係性が違う注文は数えない
    seed.commit()

    body = _search(client)
    assert _ids(body) == ["P2", "P1", "P3"]
    assert body["supplemented"] is False
    assert body["results"][0]["buyer_count"] == 8
    assert body["results"][0]["reason"] == "送別 × 同僚 に贈った人が 8人 選んでいます"


def test_relationship_change_changes_candidates(client: TestClient, seed: Seeder) -> None:
    """BR-01 の確認方法：関係性を変えると候補が変わる"""
    for pid in ["A1", "A2", "A3", "B1", "B2", "B3"]:
        seed.product(pid)
    for pid in ["A1", "A2", "A3"]:
        seed.orders(pid, SCENE, REL, buyers=3)
    for pid in ["B1", "B2", "B3"]:
        seed.orders(pid, SCENE, "取引先", buyers=3)
    seed.commit()

    assert set(_ids(_search(client))) == {"A1", "A2", "A3"}
    assert set(_ids(_search(client, relationship="取引先"))) == {"B1", "B2", "B3"}


def test_no2_price_band(client: TestClient, seed: Seeder) -> None:
    seed.product("CHEAP", price=2000); seed.product("MID", price=4000); seed.product("HIGH", price=6000)
    for pid in ["CHEAP", "MID", "HIGH"]:
        seed.orders(pid, SCENE, REL, buyers=3)
    seed.commit()

    body = _search(client, price_min=3000, price_max=5000)
    assert "MID" in _ids(body)
    assert "CHEAP" not in _ids(body) and "HIGH" not in _ids(body)


def test_no4_tie_broken_by_reaction(client: TestClient, seed: Seeder) -> None:
    seed.product("LOW"); seed.product("HIGH"); seed.product("P3")
    seed.orders("LOW", SCENE, REL, buyers=4, reactions=[2, 2, 3])
    seed.orders("HIGH", SCENE, REL, buyers=4, reactions=[4, 4, 3])
    seed.orders("P3", SCENE, REL, buyers=3)
    seed.commit()

    body = _search(client)
    assert _ids(body)[:2] == ["HIGH", "LOW"]
    assert body["results"][0]["reaction_avg"] == 3.7
    assert body["results"][0]["reaction_count"] == 3


def test_reaction_under_three_is_hidden_and_not_used(client: TestClient, seed: Seeder) -> None:
    """反応2件は表示もしないし、並び順にも使わない（③レビューの星で決まる）"""
    seed.product("FEW_REACTIONS", rating=3.0); seed.product("HIGH_RATING", rating=4.8); seed.product("P3")
    seed.orders("FEW_REACTIONS", SCENE, REL, buyers=4, reactions=[4, 4])
    seed.orders("HIGH_RATING", SCENE, REL, buyers=4)
    seed.orders("P3", SCENE, REL, buyers=3)
    seed.commit()

    body = _search(client)
    assert _ids(body)[:2] == ["HIGH_RATING", "FEW_REACTIONS"]
    assert body["results"][1]["reaction_avg"] is None


def test_buyers_under_three_shown_as_few(client: TestClient, seed: Seeder) -> None:
    seed.product("P1"); seed.product("P2"); seed.product("P3")
    seed.orders("P1", SCENE, REL, buyers=3)
    seed.orders("P2", SCENE, REL, buyers=2)
    seed.orders("P3", SCENE, REL, buyers=1)
    seed.commit()

    results = _search(client)["results"]
    assert results[0]["buyer_count"] == 3
    assert results[1]["buyer_count"] is None
    assert results[1]["reason"] == "送別 × 同僚での購入実績あり（少数）"


def test_no5_supplement_with_scene_only(client: TestClient, seed: Seeder) -> None:
    seed.product("REL1"); seed.product("REL2"); seed.product("SCENE_ONLY")
    seed.orders("REL1", SCENE, REL, buyers=1)
    seed.orders("REL2", SCENE, REL, buyers=1)
    seed.orders("SCENE_ONLY", SCENE, "家族", buyers=10)  # 人数は多いが、補った候補なので下
    seed.commit()

    body = _search(client)
    assert body["supplemented"] is True
    assert _ids(body) == ["REL1", "REL2", "SCENE_ONLY"]
    last = body["results"][2]
    assert last["is_supplemented"] is True
    assert last["rank"] == 3
    assert last["reason"] == "送別 に贈った人が 10人 選んでいます"


def test_no6_zero_results(client: TestClient, seed: Seeder) -> None:
    """送別×同僚の実績がなく、シーンだけで補っても在庫のある商品がない"""
    seed.product("P1")
    seed.orders("P1", "お礼", REL, buyers=5)  # 別シーンの実績
    seed.product("OUT_OF_STOCK", stock=0)
    seed.orders("OUT_OF_STOCK", SCENE, "家族", buyers=1)  # 送別の実績は在庫0の商品だけ
    seed.commit()

    body = _search(client)
    assert body["total"] == 0
    assert body["results"] == []
    assert body["supplemented"] is False


def test_no7_out_of_stock_excluded(client: TestClient, seed: Seeder) -> None:
    seed.product("IN"); seed.product("OUT", stock=0); seed.product("P3"); seed.product("P4")
    for pid in ["IN", "OUT", "P3", "P4"]:
        seed.orders(pid, SCENE, REL, buyers=3)
    seed.commit()

    assert "OUT" not in _ids(_search(client))


def test_old_orders_not_counted(client: TestClient, seed: Seeder) -> None:
    seed.product("OLD"); seed.product("P2"); seed.product("P3"); seed.product("P4")
    seed.orders("OLD", SCENE, REL, buyers=10, at=OUT_OF_PERIOD)
    for pid in ["P2", "P3", "P4"]:
        seed.orders(pid, SCENE, REL, buyers=3)
    seed.commit()

    assert "OLD" not in _ids(_search(client))


def test_no8_same_input_same_order(client: TestClient, seed: Seeder) -> None:
    for pid in ["P1", "P2", "P3", "P4"]:
        seed.product(pid)
        seed.orders(pid, SCENE, REL, buyers=3)
    seed.commit()

    assert _ids(_search(client)) == _ids(_search(client)) == ["P1", "P2", "P3", "P4"]


def test_unknown_scene_is_rejected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.orders("P1", SCENE, REL, buyers=3)
    seed.commit()

    res = client.get("/api/v1/search", params={"scene": "存在しない", "relationship": REL})
    assert res.status_code == 422
    assert "選べないシーン" in res.json()["detail"]


def test_price_range_reversed_is_rejected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.orders("P1", SCENE, REL, buyers=3)
    seed.commit()

    res = client.get("/api/v1/search", params={"scene": SCENE, "relationship": REL,
                                                "price_min": 5000, "price_max": 3000})
    assert res.status_code == 422


def _get(client: TestClient, **params: str | int) -> dict:
    """シーン・関係性を自分で指定して検索する"""
    res = client.get("/api/v1/search", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def test_no_conditions_orders_by_sales(client: TestClient, seed: Seeder) -> None:
    """何も選ばないとき：在庫のある商品を販売数の多い順（2週目と同じ）"""
    seed.product("K1", sales=5); seed.product("K2", sales=50); seed.product("K3", stock=0)
    seed.commit()

    body = _get(client)
    assert _ids(body) == ["K2", "K1"]
    assert body["uses_purchase_history"] is False
    assert body["results"][0]["reason"] is None


def test_keyword_and_category(client: TestClient, seed: Seeder) -> None:
    seed.product("A", name="焼き菓子アソート", category="食品")
    seed.product("B", name="焼き菓子と紅茶", category="生活雑貨")
    seed.product("C", name="タオルセット", category="食品")
    seed.commit()

    assert set(_ids(_get(client, q="焼き菓子"))) == {"A", "B"}
    assert _ids(_get(client, q="焼き菓子", category="食品")) == ["A"]


def test_keyword_combined_with_scene_and_relationship(client: TestClient, seed: Seeder) -> None:
    """キーワードとシーン×関係性の両方を満たす商品だけ（AND）"""
    seed.product("SWEETS", name="焼き菓子アソート")
    seed.product("TOWEL", name="タオルセット")
    seed.product("SWEETS_OTHER", name="焼き菓子ギフト")
    seed.orders("SWEETS", SCENE, REL, buyers=5)
    seed.orders("TOWEL", SCENE, REL, buyers=9)
    seed.orders("SWEETS_OTHER", "お礼", "取引先", buyers=7)
    seed.commit()

    body = _get(client, q="焼き菓子", scene=SCENE, relationship=REL, limit=1)
    assert _ids(body) == ["SWEETS"]
    assert body["results"][0]["reason"] == "送別 × 同僚 に贈った人が 5人 選んでいます"


def test_scene_only(client: TestClient, seed: Seeder) -> None:
    """シーンだけ選んだとき：関係性を問わず、そのシーンの購入人数の順"""
    seed.product("P1"); seed.product("P2"); seed.product("P3")
    seed.orders("P1", SCENE, REL, buyers=2)
    seed.orders("P1", SCENE, "家族", buyers=2)
    seed.orders("P2", SCENE, REL, buyers=3)
    seed.orders("P3", "お礼", REL, buyers=10)
    seed.commit()

    body = _get(client, scene=SCENE)
    assert _ids(body) == ["P1", "P2"]
    assert body["results"][0]["reason"] == "送別 に贈った人が 4人 選んでいます"
    assert body["supplemented"] is False


def test_relationship_only(client: TestClient, seed: Seeder) -> None:
    seed.product("P1"); seed.product("P2")
    seed.orders("P1", SCENE, "取引先", buyers=3)
    seed.orders("P1", "お礼", "取引先", buyers=3)
    seed.orders("P2", SCENE, REL, buyers=10)
    seed.commit()

    body = _get(client, relationship="取引先")
    assert _ids(body) == ["P1"]
    assert body["results"][0]["reason"] == "取引先 に贈った人が 6人 選んでいます"


def test_blank_values_mean_not_selected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1", sales=1); seed.product("P2", sales=2)
    seed.commit()

    body = _get(client, q="", category="", scene="", relationship="")
    assert _ids(body) == ["P2", "P1"]
    assert body["uses_purchase_history"] is False


def test_unknown_category_is_rejected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.commit()

    res = client.get("/api/v1/search", params={"category": "存在しない"})
    assert res.status_code == 422


def test_options_lists_values_in_db(client: TestClient, seed: Seeder) -> None:
    seed.product("P1", category="食品"); seed.product("P2", category="コスメ")
    seed.orders("P1", SCENE, REL, buyers=1)
    seed.orders("P1", "お礼", "取引先", buyers=1)
    seed.orders("P1", "誕生日", None, buyers=1)
    seed.commit()

    body = client.get("/api/v1/options").json()
    assert body["categories"] == ["コスメ", "食品"]
    assert set(body["scenes"]) == {SCENE, "お礼", "誕生日"}
    assert set(body["relationships"]) == {REL, "取引先"}
    assert body["relationship_available"] is True

