// lib/api.ts — FastAPI との通信はすべてここにまとめる（画面からは fetch を直接呼ばない）
import type { SearchCondition, SearchOptions, SearchResponse } from "@/types/search";

// API の場所。NEXT_PUBLIC_ の値はブラウザに配られる＝秘密は置かない（.env.local に書く）
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// API がエラーのときに返す形（FastAPI の { detail: ... }）
type ApiError = { detail?: unknown };

// GET して JSON を返す。失敗したら、画面に出せる日本語のメッセージで Error を投げる
async function getJson<T>(path: string, params?: URLSearchParams): Promise<T> {
  const query = params && params.toString() ? `?${params.toString()}` : "";
  let res: Response;
  try {
    res = await fetch(`${API}${path}${query}`);
  } catch {
    throw new Error("APIにつながりません。バックエンドが起動しているか確かめてください");
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiError;
    const detail = typeof body.detail === "string" ? body.detail : `エラーが起きました（HTTP ${res.status}）`;
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

// 検索画面で選べるカテゴリー・シーン・関係性
export async function fetchSearchOptions(): Promise<SearchOptions> {
  return getJson<SearchOptions>("/api/v1/options");
}

// 商品を探す（FR-02・FR-04・FR-06）。選んだ条件だけを送る（空の条件は送らない）
export async function searchProducts(c: SearchCondition): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (c.keyword.trim()) params.set("q", c.keyword.trim());
  if (c.category) params.set("category", c.category);
  if (c.scene) params.set("scene", c.scene);
  if (c.relationship) params.set("relationship", c.relationship);
  if (c.priceBand?.min != null) params.set("price_min", String(c.priceBand.min));
  if (c.priceBand?.max != null) params.set("price_max", String(c.priceBand.max));
  return getJson<SearchResponse>("/api/v1/search", params);
}
