// components/ProductSearch.tsx — 商品検索（FR-02）
// キーワード欄の下に、カテゴリー・シーン・関係性・予算帯のドロップダウン。選んだ条件をすべて満たす商品を表示する
"use client"; // 入力の状態とボタンの処理があるため、ブラウザで動かす

import { useEffect, useState } from "react";
import ProductCard from "@/components/ProductCard";
import { fetchSearchOptions, searchProducts } from "@/lib/api";
import { PRICE_BANDS } from "@/lib/priceBands";
import type { SearchCondition, SearchOptions, SearchResponse } from "@/types/search";

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

// 結果の上に出す「何で探したか」の文
function describeCondition(c: SearchCondition): string {
  const parts: string[] = [];
  if (c.keyword.trim()) parts.push(`「${c.keyword.trim()}」`);
  if (c.category) parts.push(c.category);
  const situation = [c.scene, c.relationship].filter(Boolean).join(" × ");
  if (situation) parts.push(situation);
  if (c.priceBand) parts.push(c.priceBand.label);
  return parts.length > 0 ? parts.join("・") : "すべての商品";
}

export default function ProductSearch() {
  const [options, setOptions] = useState<SearchOptions | null>(null); // 選べる値
  const [optionsError, setOptionsError] = useState("");
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("");
  const [scene, setScene] = useState("");
  const [relationship, setRelationship] = useState("");
  const [priceBandId, setPriceBandId] = useState("");                  // "" は予算帯なし
  const [searched, setSearched] = useState<SearchCondition | null>(null); // 結果を出した条件
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ① 画面を開いたら、選べる値を API から取る。取れなくてもキーワード検索はできる
  useEffect(() => {
    let active = true;
    fetchSearchOptions()
      .then((o) => { if (active) setOptions(o); })
      .catch((err: unknown) => { if (active) setOptionsError(errorMessage(err, "選択肢を読み込めませんでした")); });
    return () => { active = false; };
  }, []);

  // ② 検索ボタン：入力した条件で API に聞く
  async function onSearch(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const condition: SearchCondition = {
      keyword,
      category,
      scene,
      relationship,
      priceBand: PRICE_BANDS.find((b) => b.id === priceBandId) ?? null,
    };
    setError("");
    setLoading(true);
    try {
      setResponse(await searchProducts(condition));
      setSearched(condition);
    } catch (err) {
      setResponse(null);
      setError(errorMessage(err, "検索できませんでした"));
    } finally {
      setLoading(false);
    }
  }

  const relationshipUnavailable = options !== null && !options.relationship_available;

  return (
    <>
      <form className="searchForm" onSubmit={onSearch}>
        <div className="searchRow">
          <input
            className="q"
            aria-label="キーワード"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="キーワード（例：送別 お菓子）"
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
          <select
            aria-label="相手との関係"
            value={relationship}
            onChange={(e) => setRelationship(e.target.value)}
            disabled={!options || relationshipUnavailable}
          >
            <option value="">関係性（指定なし）</option>
            {options?.relationships.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
          <select aria-label="予算帯" value={priceBandId} onChange={(e) => setPriceBandId(e.target.value)}>
            <option value="">予算帯（指定なし）</option>
            {PRICE_BANDS.map((b) => <option key={b.id} value={b.id}>{b.label}</option>)}
          </select>
        </div>
      </form>

      {optionsError && <p className="error" role="alert">{optionsError}（キーワードと予算帯では探せます）</p>}
      {relationshipUnavailable && (
        <p className="notice">関係性のデータがまだデータベースにないため、関係性は選べません（backend/sql の 001・002 が未実行）</p>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      {loading && <p className="summary">検索しています…</p>}

      {!loading && response && searched && (
        <section>
          {response.total === 0 ? (
            <p className="summary">条件に合う商品が見つかりませんでした。条件を減らすか、関係性を変えて探してください。</p>
          ) : (
            <>
              <p className="summary">
                {describeCondition(searched)}：{response.total} 件
                {response.uses_purchase_history ? "（同じ状況で買った人数の多い順）" : "（よく売れている順）"}
              </p>
              {response.supplemented && (
                <p className="notice">同じ関係性の実績が少ないため、{searched.scene}で選ばれた商品も表示しています</p>
              )}
              <div className="grid">
                {response.results.map((item) => <ProductCard key={item.product_id} item={item} />)}
              </div>
            </>
          )}
        </section>
      )}
    </>
  );
}
