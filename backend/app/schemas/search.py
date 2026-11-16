"""API のレスポンスの形（画面との約束。要件定義書 4.3）"""
from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    brand: str
    price: int
    rating: float | None = Field(description="レビューの平均星。レビューなしは null")
    review_count: int
    buyer_count: int | None = Field(
        description="選んだシーン・関係性で直近1年に買った人数。3人未満、またはシーン・関係性を選んでいないときは null"
    )
    reaction_avg: float | None = Field(description="相手の反応の平均（1〜4）。3件未満は null")
    reaction_count: int = Field(description="相手の反応の件数")
    rank: int
    reason: str | None = Field(
        description="根拠の文（6.3 のテンプレート）。シーン・関係性を選んでいないときは null"
    )
    is_supplemented: bool = Field(description="シーンだけ一致する注文で補った候補か")


class SearchResponse(BaseModel):
    total: int = Field(description="返した件数")
    uses_purchase_history: bool = Field(
        description="シーン・関係性の購入実績で絞り、6.2 の順に並べたか（false なら販売数の順）"
    )
    supplemented: bool = Field(description="候補が少なく、シーンだけ一致する商品で補ったか")
    results: list[SearchItem]


class OptionsResponse(BaseModel):
    categories: list[str]
    scenes: list[str]
    relationships: list[str]
    relationship_available: bool = Field(
        description="関係性の列が DB にあるか（sql/001 が未実行なら false）"
    )
