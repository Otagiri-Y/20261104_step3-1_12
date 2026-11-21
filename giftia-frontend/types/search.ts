// types/search.ts — 商品検索（FR-02）で使う型。API（/api/v1/search・/api/v1/options）の返す形と同じ

// 検索結果の1件
export type SearchItem = {
  product_id: string;
  product_name: string;
  category: string;
  brand: string;
  price: number;
  description: string;                 // 説明の全文。カードでは先頭60文字に切る
  rating: number | null;               // 商品全体の★。レビューなしは null
  review_count: number;                // 商品全体のレビュー件数
  rank: number;                        // 並び順の順位（1から）
  buyer_count: number | null;          // 選んだシーンで直近1年に買った人数。シーンなしは null
  reason: string | null;               // 根拠①の文（「送別で選ばれた商品の中で 2位（12人）」）。シーンなしは null
  scene_rating_avg: number | null;     // 根拠②同じシーンの★の平均。なし・シーンなしは null
  scene_review_count: number;          // 根拠②の件数。なし・シーンなしは 0
  review_rating: number | null;        // 根拠③コメントがある最新のレビューの★。なければ null
  review_comment: string | null;       // 根拠③のコメント（全文。カードでは40文字に切る）。なければ null
  is_supplemented: boolean;            // 余力（関係性）：シーンだけ一致する注文で補った候補か
};

export type SearchResponse = {
  total: number;
  uses_purchase_history: boolean; // シーンの購入実績で並べたか（false なら販売数の順）
  supplemented: boolean;          // 余力（関係性）：候補が少なく、シーンだけ一致する商品で補ったか
  results: SearchItem[];
};

// 検索画面で選べる値（/api/v1/options）
export type SearchOptions = {
  categories: string[];
  scenes: string[];
  relationships: string[];
  relationship_available: boolean; // 関係性の列が DB にあるか（sql/001 が未実行なら false）
};

// 予算帯の1つ分。min・max は円（null は上限・下限なし）
export type PriceBand = {
  id: string;
  label: string;
  min: number | null;
  max: number | null;
};

// 画面から API に渡す検索条件。空文字は「指定なし」
export type SearchCondition = {
  keyword: string;
  category: string;
  scene: string;
  relationship: string;
  priceBand: PriceBand | null;  // null なら予算帯で絞らない
};
