// components/SearchForm.tsx — 検索の入力欄（FR-02）
// キーワード欄の下に、カテゴリー・シーン・予算帯のドロップダウン（どれも任意・AND）。関係性は余力なので出さない
// 入力の初期値は URL の条件。URL が変わったら親が key を変えて作り直すので、戻る・進むでも入力欄がそろう
"use client"; // 入力の状態とボタンの処理があるため、ブラウザで動かす

import { useState } from "react";
import { PRICE_BANDS } from "@/lib/priceBands";
import type { SearchCondition, SearchOptions } from "@/types/search";

interface SearchFormProps {
  initial: SearchCondition;
  options: SearchOptions | null;  // null の間は読み込み中（カテゴリー・シーンは選べない）
  loading: boolean;
  onSubmit: (condition: SearchCondition) => void;
}

export default function SearchForm({ initial, options, loading, onSubmit }: SearchFormProps) {
  const [keyword, setKeyword] = useState(initial.keyword);
  const [category, setCategory] = useState(initial.category);
  const [scene, setScene] = useState(initial.scene);
  const [priceBandId, setPriceBandId] = useState(initial.priceBand?.id ?? ""); // "" は予算帯なし

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit({
      keyword,
      category,
      scene,
      priceBand: PRICE_BANDS.find((b) => b.id === priceBandId) ?? null,
    });
  }

  return (
    <form className="searchForm" onSubmit={handleSubmit}>
      <div className="searchRow">
        <input
          className="q"
          aria-label="キーワード"
          value={keyword}
          maxLength={100}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="キーワード（例：お菓子 個包装）"
        />
        <button type="submit" disabled={loading}>{loading ? "検索中…" : "検索"}</button>
      </div>
      <div className="filters">
        <select aria-label="カテゴリー" value={category} onChange={(e) => setCategory(e.target.value)} disabled={!options}>
          <option value="">すべてのカテゴリー</option>
          {options?.categories.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
        <select aria-label="贈るシーン" value={scene} onChange={(e) => setScene(e.target.value)} disabled={!options}>
          <option value="">シーン（指定なし）</option>
          {options?.scenes.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
        <select aria-label="予算帯" value={priceBandId} onChange={(e) => setPriceBandId(e.target.value)}>
          <option value="">予算帯（指定なし）</option>
          {PRICE_BANDS.map((b) => <option key={b.id} value={b.id}>{b.label}</option>)}
        </select>
      </div>
    </form>
  );
}
