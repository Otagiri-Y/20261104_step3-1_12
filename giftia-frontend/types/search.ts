// types/search.ts — 商品検索（FR-02）で使う型。API（/api/v1/search・/api/v1/options）の返す形と同じ

// 検索結果の1件
export type SearchItem = {
  product_id: string;
  product_name: string;
  category: string;
  brand: string;
  price: number;
  rating: number | null;        // レビューの平均星。レビューなしは null
  review_count: number;
  buyer_count: number | null;   // 選んだシーン・関係性で直近1年に買った人数。3人未満・未選択は null
  reaction_avg: number | null;  // 相手の反応の平均（1〜4）。3件未満は null
  reaction_count: number;       // 相手の反応の件数
  rank: number;
  reason: string | null;        // 根拠の文（「送別 × 同僚 に贈った人が 12人 選んでいます」）。未選択は null
  is_supplemented: boolean;     // シーンだけ一致する注文で補った候補か
};

export type SearchResponse = {
  total: number;
  uses_purchase_history: boolean; // シーン・関係性の購入実績で並べたか（false なら販売数の順）
  supplemented: boolean;          // 候補が少なく、シーンだけ一致する商品で補ったか
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
