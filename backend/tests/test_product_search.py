"""商品検索（FR-02・FR-04・FR-06）のテスト。No は要件定義書 6.4 のテストケース番号（No.20〜 は追加）"""
from datetime import date

from fastapi.testclient import TestClient

from tests.conftest import OUT_OF_PERIOD, Seeder

SCENE = "送別"
OTHER = "ビジネスのお礼"


def _get(client: TestClient, **params: str | int) -> dict:
    res = client.get("/api/v1/search", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def _ids(body: dict) -> list[str]:
    return [r["product_id"] for r in body["results"]]


# ── 候補と並び順（FR-02・FR-06） ──────────────────────────────

def test_no1_scene_ranks_by_buyers_and_excludes_other_scenes(client: TestClient, seed: Seeder) -> None:
    seed.product("P1"); seed.product("P2"); seed.product("P3"); seed.product("P_OTHER")
    seed.orders("P1", SCENE, buyers=5)
    seed.orders("P2", SCENE, buyers=8)
    seed.orders("P3", SCENE, buyers=3)
    seed.orders("P_OTHER", OTHER, buyers=20)  # 送別で買われていない商品は出ない
    seed.commit()

    body = _get(client, scene=SCENE)
    assert _ids(body) == ["P2", "P1", "P3"]
    assert body["uses_purchase_history"] is True
    assert [r["buyer_count"] for r in body["results"]] == [8, 5, 3]


def test_no2_price_band(client: TestClient, seed: Seeder) -> None:
    seed.product("CHEAP", price=2999); seed.product("MID", price=4000); seed.product("HIGH", price=5000)
    for pid in ["CHEAP", "MID", "HIGH"]:
        seed.orders(pid, SCENE, buyers=3)
    seed.commit()

    # 画面の予算帯「3,000〜5,000円」は 3000〜4999
    assert _ids(_get(client, scene=SCENE, price_min=3000, price_max=4999)) == ["MID"]


def test_no3_business_thanks(client: TestClient, seed: Seeder) -> None:
    seed.product("A"); seed.product("B")
    seed.orders("A", OTHER, buyers=2)
    seed.orders("B", OTHER, buyers=6)
    seed.orders("A", SCENE, buyers=10)  # 別シーンの人数は数えない
    seed.commit()

    body = _get(client, scene=OTHER)
    assert _ids(body) == ["B", "A"]
    assert body["results"][1]["buyer_count"] == 2


def test_no4_tie_broken_by_scene_rating(client: TestClient, seed: Seeder) -> None:
    seed.product("LOW", rating=4.9); seed.product("HIGH", rating=3.0)
    low = seed.orders("LOW", SCENE, buyers=4)
    high = seed.orders("HIGH", SCENE, buyers=4)
    seed.review("LOW", low[0], 2)
    seed.review("HIGH", high[0], 5)
    seed.review("HIGH", high[1], 4)
    seed.commit()

    body = _get(client, scene=SCENE)
    # 商品全体の★は LOW が高いが、②同じシーンの★が先に効く
    assert _ids(body) == ["HIGH", "LOW"]
    assert body["results"][0]["scene_rating_avg"] == 4.5
    assert body["results"][0]["scene_review_count"] == 2


def test_tie_without_scene_reviews_falls_back_to_product_rating_then_sales(client: TestClient, seed: Seeder) -> None:
    """同じシーンのレビューなしは後ろ。それも同じなら ③商品全体の★ → ④販売数"""
    seed.product("NO_REVIEW", rating=5.0, sales=999)
    seed.product("HAS_REVIEW", rating=1.0)
    seed.product("R_HIGH", rating=4.5, sales=1); seed.product("R_LOW", rating=3.5, sales=500)
    seed.product("S_HIGH", rating=3.0, sales=50); seed.product("S_LOW", rating=3.0, sales=40)
    users = seed.orders("HAS_REVIEW", SCENE, buyers=3)
    seed.review("HAS_REVIEW", users[0], 1)
    for pid in ["NO_REVIEW", "R_HIGH", "R_LOW", "S_HIGH", "S_LOW"]:
        seed.orders(pid, SCENE, buyers=3)
    seed.commit()

    assert _ids(_get(client, scene=SCENE)) == ["HAS_REVIEW", "NO_REVIEW", "R_HIGH", "R_LOW", "S_HIGH", "S_LOW"]


def test_no5_out_of_stock_excluded(client: TestClient, seed: Seeder) -> None:
    seed.product("IN"); seed.product("OUT", stock=0)
    seed.orders("IN", SCENE, buyers=3)
    seed.orders("OUT", SCENE, buyers=9)
    seed.commit()

    assert _ids(_get(client, scene=SCENE)) == ["IN"]


def test_old_orders_not_counted(client: TestClient, seed: Seeder) -> None:
    seed.product("OLD"); seed.product("NEW")
    seed.orders("OLD", SCENE, buyers=10, at=OUT_OF_PERIOD)
    seed.orders("NEW", SCENE, buyers=3)
    seed.commit()

    assert _ids(_get(client, scene=SCENE)) == ["NEW"]


def test_no10_same_input_same_order(client: TestClient, seed: Seeder) -> None:
    for pid in ["P1", "P2", "P3", "P4"]:
        seed.product(pid)
        seed.orders(pid, SCENE, buyers=3)
    seed.commit()

    assert _ids(_get(client, scene=SCENE)) == _ids(_get(client, scene=SCENE)) == ["P1", "P2", "P3", "P4"]


# ── 根拠①買った人数の文（FR-04・6.3） ─────────────────────────

def test_no6_rank_only_for_top3(client: TestClient, seed: Seeder) -> None:
    for pid, n in [("P1", 12), ("P2", 8), ("P3", 5), ("P4", 4)]:
        seed.product(pid)
        seed.orders(pid, SCENE, buyers=n)
    seed.commit()

    reasons = [r["reason"] for r in _get(client, scene=SCENE)["results"]]
    assert reasons == [
        "送別で選ばれた商品の中で 1位（12人）",
        "送別で選ばれた商品の中で 2位（8人）",
        "送別で選ばれた商品の中で 3位（5人）",
        "送別で 4人 が購入",
    ]


def test_buyers_under_three_shown_as_few_even_in_top3(client: TestClient, seed: Seeder) -> None:
    """決めたこと：1〜3位でも3人未満なら「少数」を優先し、順位を付けない"""
    seed.product("P1"); seed.product("P2")
    seed.orders("P1", SCENE, buyers=3)
    seed.orders("P2", SCENE, buyers=2)
    seed.commit()

    results = _get(client, scene=SCENE)["results"]
    assert results[0]["reason"] == "送別で選ばれた商品の中で 1位（3人）"
    assert results[1]["reason"] == "送別での購入実績あり（少数）"
    assert results[1]["buyer_count"] == 2  # 人数そのものは返す


def test_no21_same_person_counted_once(client: TestClient, seed: Seeder) -> None:
    """同じ人が同じ商品を送別で2回買い、レビューが1件：人数1人、同じシーンの★は1件"""
    seed.product("P1")
    seed.buy("U_SAME", "P1", SCENE)
    seed.buy("U_SAME", "P1", SCENE)
    seed.review("P1", "U_SAME", 4, "よかった")
    seed.commit()

    item = _get(client, scene=SCENE)["results"][0]
    assert item["buyer_count"] == 1
    assert item["scene_review_count"] == 1
    assert item["scene_rating_avg"] == 4.0


# ── 根拠②同じシーンの★・③レビュー1件（FR-04） ─────────────────

def test_no7_only_same_scene_reviews(client: TestClient, seed: Seeder) -> None:
    seed.product("SAME", rating=4.2); seed.product("OTHER_ONLY", rating=3.8)
    same = seed.orders("SAME", SCENE, buyers=3)
    seed.review("SAME", same[0], 5, "職場の皆で分けやすく、好評でした")
    other_buyers = seed.orders("OTHER_ONLY", OTHER, buyers=1)
    seed.orders("OTHER_ONLY", SCENE, buyers=3)
    seed.review("OTHER_ONLY", other_buyers[0], 5, "取引先に喜ばれました")  # 別シーンで買った人のレビュー
    seed.commit()

    results = {r["product_id"]: r for r in _get(client, scene=SCENE)["results"]}
    assert results["SAME"]["scene_rating_avg"] == 5.0
    assert results["SAME"]["review_comment"] == "職場の皆で分けやすく、好評でした"
    assert results["OTHER_ONLY"]["scene_rating_avg"] is None
    assert results["OTHER_ONLY"]["scene_review_count"] == 0
    assert results["OTHER_ONLY"]["review_comment"] is None
    # 商品全体の★はどちらにも出る
    assert results["SAME"]["rating"] == 4.2 and results["OTHER_ONLY"]["rating"] == 3.8


def test_no8_latest_commented_review(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    users = seed.orders("P1", SCENE, buyers=4)
    seed.review("P1", users[0], 3, "古いコメント", posted=date(2026, 1, 5))
    seed.review("P1", users[1], 5, "新しいコメント", posted=date(2026, 4, 1))
    seed.review("P1", users[2], 1, None, posted=date(2026, 5, 1))  # コメントなしは③に使わない
    seed.review("P1", users[3], 2, "", posted=date(2026, 6, 1))  # 空文字も使わない
    seed.commit()

    item = _get(client, scene=SCENE)["results"][0]
    assert item["review_comment"] == "新しいコメント"
    assert item["review_rating"] == 5
    assert item["scene_review_count"] == 4  # ②の件数はコメントなしも含む
    assert item["scene_rating_avg"] == 2.8  # (3+5+1+2)/4 = 2.75 → 四捨五入で 2.8


def test_scene_rating_rounds_half_up(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    users = seed.orders("P1", SCENE, buyers=4)
    for uid, rating in zip(users, [4, 3, 3, 3]):
        seed.review("P1", uid, rating)
    seed.commit()

    assert _get(client, scene=SCENE)["results"][0]["scene_rating_avg"] == 3.3  # 3.25 → 3.3


def test_no12_one_scene_review(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    users = seed.orders("P1", SCENE, buyers=3)
    seed.review("P1", users[0], 4)
    seed.commit()

    item = _get(client, scene=SCENE)["results"][0]
    assert item["scene_rating_avg"] == 4.0
    assert item["scene_review_count"] == 1


def test_reviews_from_old_orders_not_used(client: TestClient, seed: Seeder) -> None:
    """決めたこと：レビューを結ぶ注文も直近1年に限る"""
    seed.product("P1")
    seed.orders("P1", SCENE, buyers=3)
    old = seed.orders("P1", SCENE, buyers=1, at=OUT_OF_PERIOD)
    seed.review("P1", old[0], 5, "1年より前に買った人")
    seed.commit()

    item = _get(client, scene=SCENE)["results"][0]
    assert item["buyer_count"] == 3
    assert item["scene_review_count"] == 0
    assert item["review_comment"] is None


# ── シーンなし・キーワード・入力チェック ──────────────────────

def test_no15_no_scene_orders_by_sales_without_evidence(client: TestClient, seed: Seeder) -> None:
    seed.product("K1", sales=5, description="説明の全文")
    seed.product("K2", sales=50); seed.product("K3", stock=0)
    seed.commit()

    body = _get(client)
    assert _ids(body) == ["K2", "K1"]
    assert body["uses_purchase_history"] is False
    assert [r["rank"] for r in body["results"]] == [1, 2]
    first = body["results"][0]
    assert first["reason"] is None and first["buyer_count"] is None
    assert first["scene_rating_avg"] is None and first["review_comment"] is None
    assert body["results"][1]["description"] == "説明の全文"


def test_keyword_and_category(client: TestClient, seed: Seeder) -> None:
    seed.product("A", name="焼き菓子アソート", category="食品")
    seed.product("B", name="焼き菓子と紅茶", category="生活雑貨")
    seed.product("C", name="タオルセット", category="食品")
    seed.commit()

    assert set(_ids(_get(client, q="焼き菓子"))) == {"A", "B"}
    assert _ids(_get(client, q="焼き菓子", category="食品")) == ["A"]


def test_keyword_combined_with_scene(client: TestClient, seed: Seeder) -> None:
    seed.product("SWEETS", name="焼き菓子アソート")
    seed.product("TOWEL", name="タオルセット")
    seed.orders("SWEETS", SCENE, buyers=5)
    seed.orders("TOWEL", SCENE, buyers=9)
    seed.commit()

    body = _get(client, q="焼き菓子", scene=SCENE)
    assert _ids(body) == ["SWEETS"]
    assert body["results"][0]["reason"] == "送別で選ばれた商品の中で 1位（5人）"


def test_blank_values_mean_not_selected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1", sales=1); seed.product("P2", sales=2)
    seed.commit()

    body = _get(client, q="", category="", scene="", relationship="")
    assert _ids(body) == ["P2", "P1"]
    assert body["uses_purchase_history"] is False


def test_scene_outside_four_is_rejected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.orders("P1", "毎年決まった相手への贈答", buyers=3)
    seed.commit()

    res = client.get("/api/v1/search", params={"scene": "毎年決まった相手への贈答"})
    assert res.status_code == 422
    assert "選べないシーン" in res.json()["detail"]


def test_price_range_reversed_is_rejected(client: TestClient) -> None:
    res = client.get("/api/v1/search", params={"price_min": 5000, "price_max": 3000})
    assert res.status_code == 422


def test_unknown_category_is_rejected(client: TestClient, seed: Seeder) -> None:
    seed.product("P1")
    seed.commit()

    assert client.get("/api/v1/search", params={"category": "存在しない"}).status_code == 422


# ── 選択肢（No.9） ────────────────────────────────────────

def test_no9_options_lists_four_scenes(client: TestClient, seed: Seeder) -> None:
    seed.product("P1", category="食品"); seed.product("P2", category="コスメ")
    seed.orders("P1", "毎年決まった相手への贈答", buyers=1)
    seed.commit()

    body = client.get("/api/v1/options").json()
    assert body["categories"] == ["コスメ", "食品"]
    assert body["scenes"] == ["送別", "友人への誕生日", "家族への誕生日", "ビジネスのお礼"]


# ── 余力（関係性）。API の処理は残しているので、壊れていないことだけ確かめる ──

def test_relationship_filters_and_supplements_with_scene(client: TestClient, seed: Seeder) -> None:
    seed.product("REL1"); seed.product("SCENE_ONLY")
    seed.orders("REL1", SCENE, "同僚", buyers=1)
    seed.orders("SCENE_ONLY", SCENE, "家族", buyers=10)
    seed.commit()

    body = _get(client, scene=SCENE, relationship="同僚")
    assert _ids(body) == ["REL1", "SCENE_ONLY"]
    assert body["supplemented"] is True
    assert body["results"][0]["reason"] == "送別 × 同僚での購入実績あり（少数）"
    assert body["results"][1]["is_supplemented"] is True
    assert body["results"][1]["reason"] == "送別で選ばれた商品の中で 2位（10人）"
