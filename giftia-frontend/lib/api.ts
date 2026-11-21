// lib/api.ts — FastAPI との通信はすべてここにまとめる（画面からは fetch を直接呼ばない）
import type { ProductDetail, SearchCondition, SearchOptions, SearchResponse } from "@/types/search";

// API の場所。NEXT_PUBLIC_ の値はブラウザに配られる＝秘密は置かない（.env.local に書く）
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// API がエラーのときに返す形（FastAPI の { detail: ... }）
type ApiErrorBody = { detail?: unknown };

// API の失敗。画面で 404 などを見分けられるよう、HTTP の番号を持つ
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// fetch して JSON を返す。失敗したら、画面に出せる日本語のメッセージで Error を投げる
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, init);
  } catch {
    throw new Error("APIにつながりません。バックエンドが起動しているか確かめてください");
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    const detail = typeof body.detail === "string" ? body.detail : `エラーが起きました（HTTP ${res.status}）`;
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

function withQuery(path: string, params: URLSearchParams): string {
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

// 検索画面で選べるカテゴリー・シーン
export async function fetchSearchOptions(): Promise<SearchOptions> {
  return requestJson<SearchOptions>("/api/v1/options");
}

// 商品を探す（FR-02・FR-04・FR-06）。選んだ条件だけを送る（空の条件は送らない）
export async function searchProducts(c: SearchCondition): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (c.keyword.trim()) params.set("q", c.keyword.trim());
  if (c.category) params.set("category", c.category);
  if (c.scene) params.set("scene", c.scene);
  if (c.priceBand?.min != null) params.set("price_min", String(c.priceBand.min));
  if (c.priceBand?.max != null) params.set("price_max", String(c.priceBand.max));
  return requestJson<SearchResponse>(withQuery("/api/v1/search", params));
}

// 商品詳細（FR-01）。scene を渡すと、同じシーンで買った人の根拠も返る
export async function fetchProductDetail(productId: string, scene: string): Promise<ProductDetail> {
  const params = new URLSearchParams();
  if (scene) params.set("scene", scene);
  return requestJson<ProductDetail>(withQuery(`/api/v1/products/${encodeURIComponent(productId)}`, params));
}
