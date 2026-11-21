// lib/searchQuery.ts — 検索条件と、検索画面の URL（/?q=…&category=…&scene=…&price=…）の行き来
// 条件を URL に持たせるので、商品詳細から戻っても同じ結果が出て、URL を貼れば同じ画面を見せられる
import { PRICE_BANDS } from "@/lib/priceBands";
import type { SearchCondition } from "@/types/search";

// URL のキー
const KEY_Q = "q";
const KEY_CATEGORY = "category";
const KEY_SCENE = "scene";
const KEY_PRICE = "price"; // 予算帯の id（lib/priceBands.ts）

// 最後に見た検索結果の URL を覚える場所（商品詳細の「検索結果に戻る」で使う）
const LAST_SEARCH_KEY = "giftia_last_search";

// URL の ?… から検索条件を作る。知らない予算帯は「指定なし」
export function conditionFromParams(params: URLSearchParams): SearchCondition {
  const priceId = params.get(KEY_PRICE) ?? "";
  return {
    keyword: params.get(KEY_Q) ?? "",
    category: params.get(KEY_CATEGORY) ?? "",
    scene: params.get(KEY_SCENE) ?? "",
    priceBand: PRICE_BANDS.find((b) => b.id === priceId) ?? null,
  };
}

// 検索条件から URL の ?… を作る。空の条件は入れない
export function conditionToQuery(c: SearchCondition): string {
  const params = new URLSearchParams();
  if (c.keyword.trim()) params.set(KEY_Q, c.keyword.trim());
  if (c.category) params.set(KEY_CATEGORY, c.category);
  if (c.scene) params.set(KEY_SCENE, c.scene);
  if (c.priceBand) params.set(KEY_PRICE, c.priceBand.id);
  return params.toString();
}

export function searchHref(query: string): string {
  return query ? `/?${query}` : "/";
}

// 商品詳細の URL。シーンを選んでいたら引き継ぐ（FR-01）
export function productDetailHref(productId: string, scene: string): string {
  const path = `/products/${encodeURIComponent(productId)}`;
  return scene ? `${path}?${new URLSearchParams({ scene }).toString()}` : path;
}

// 最後に見た検索結果を覚える。sessionStorage が使えない環境では何もしない
export function rememberLastSearch(query: string): void {
  try {
    sessionStorage.setItem(LAST_SEARCH_KEY, query);
  } catch {
    // 覚えられなくても、戻り先がトップになるだけ
  }
}

// 「検索結果に戻る」の行き先。覚えていなければトップ
export function lastSearchHref(): string {
  try {
    return searchHref(sessionStorage.getItem(LAST_SEARCH_KEY) ?? "");
  } catch {
    return "/";
  }
}
