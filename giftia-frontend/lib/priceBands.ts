// lib/priceBands.ts — 検索画面で選べる予算帯。帯を変えるときはここだけ直す
import type { PriceBand } from "@/types/search";

export const PRICE_BANDS: PriceBand[] = [
  { id: "under3000", label: "3,000円未満", min: null, max: 2999 },
  { id: "3000to5000", label: "3,000〜5,000円", min: 3000, max: 4999 },
  { id: "5000to10000", label: "5,000〜10,000円", min: 5000, max: 9999 },
  { id: "over10000", label: "10,000円以上", min: 10000, max: null },
];
