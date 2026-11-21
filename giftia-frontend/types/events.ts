// types/events.ts — 計測の記録（POST /api/v1/events・FR-11・FR-12）で使う型
// API の形を変えたら、backend/app/schemas/events.py と同時に直す（AGENTS.md）

// 記録する行動は2つだけ
export type EventType = "pdp_view" | "add_to_cart"; // 商品詳細を見た／カートに入れた（模擬）

// 画面から送るもの。時刻は送らない（API が受け取った時刻を付ける）
export type EventCreate = {
  session_id: string;     // lib/session.ts で作るランダムな文字列
  event_type: EventType;
  product_id: string;
  scene: string | null;   // 検索で選んだシーン。なしは null
};

// API が返すもの
export type EventCreated = {
  event_id: number;
  occurred_at: string;    // "2026-11-21T21:30:00"（日本時間）
};
