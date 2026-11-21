"""API のレスポンスの形（画面との約束。要件定義書 4.3）。
形を変えたら、画面の types/search.ts も同時に直す（AGENTS.md）"""
from datetime import date

from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    brand: str
    price: int
    description: str = Field(description="説明の全文。カードでは画面で先頭60文字に切る")
    rating: float | None = Field(description="商品全体の★（products.rating）。レビューなしは null")
    review_count: int = Field(description="商品全体のレビュー件数")
    rank: int = Field(description="並び順の順位（1から）")
    buyer_count: int | None = Field(
        description="選んだシーンで直近1年に買った人数。シーンを選んでいないときは null"
    )
    reason: str | None = Field(
        description="根拠①の文（6.3）。シーンを選んでいないときは null"
    )
    scene_rating_avg: float | None = Field(
        description="根拠②同じシーンで買った人のレビューの★の平均（小数1桁）。レビューなし・シーンなしは null"
    )
    scene_review_count: int = Field(description="根拠②の件数。なし・シーンなしは 0")
    review_rating: int | None = Field(
        description="根拠③同じシーンで買った人の、コメントがある最新のレビューの★。なければ null"
    )
    review_comment: str | None = Field(
        description="根拠③のコメント（全文。カードでは画面で40文字に切る）。なければ null"
    )
    is_supplemented: bool = Field(description="余力（関係性）：シーンだけ一致する注文で補った候補か")


class SearchResponse(BaseModel):
    total: int = Field(description="返した件数")
    uses_purchase_history: bool = Field(
        description="シーンの購入実績で絞り、6.2 の順に並べたか（false なら販売数の順）"
    )
    supplemented: bool = Field(description="余力（関係性）：候補が少なく、シーンだけ一致する商品で補ったか")
    results: list[SearchItem]


class SceneReview(BaseModel):
    review_id: str
    rating: int
    comment: str | None = Field(description="コメント。空のレビューは null")
    posted_at: date


class ProductDetail(BaseModel):
    product_id: str
    product_name: str
    category: str
    brand: str
    price: int
    description: str = Field(description="説明の全文")
    rating: float | None = Field(description="商品全体の★。レビューなしは null")
    review_count: int
    scene: str | None = Field(description="引き継いだシーン。なければ null")
    buyer_count: int | None = Field(description="そのシーンで直近1年に買った人数。シーンなしは null")
    scene_rating_avg: float | None = Field(description="同じシーンの★の平均。レビューなし・シーンなしは null")
    scene_review_count: int | None = Field(description="同じシーンのレビュー件数。シーンなしは null")
    scene_reviews: list[SceneReview] = Field(
        description="同じシーンで買った人のレビュー一覧（新しい順。コメントが空のものも含む）。シーンなしは空"
    )


class OptionsResponse(BaseModel):
    categories: list[str]
    scenes: list[str] = Field(description="選べるシーン（app/config.py の4つ）")
    relationships: list[str] = Field(description="余力。範囲Bの画面では使わない")
    relationship_available: bool = Field(
        description="関係性の列が DB にあるか（sql/001 が未実行なら false）"
    )
