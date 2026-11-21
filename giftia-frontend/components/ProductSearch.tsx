// components/ProductSearch.tsx — 商品検索（FR-02・FR-04・FR-06）
// 検索条件は URL（/?q=…&category=…&scene=…&price=…）に持たせる。
//   「検索」を押す → URL を変える → URL の条件で API に聞く
// こうすると、商品詳細から戻っても同じ結果が出て、URL を貼れば同じ画面を見せられる
"use client"; // URL の読み取り・入力・API 呼び出しがあるため、ブラウザで動かす

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ProductCard from "@/components/ProductCard";
import SearchForm from "@/components/SearchForm";
import { fetchSearchOptions, searchProducts } from "@/lib/api";
import { conditionFromParams, conditionToQuery, rememberLastSearch, searchHref } from "@/lib/searchQuery";
import type { SearchCondition, SearchOptions, SearchResponse } from "@/types/search";

const SCENE_NOTICE = "シーンはGiftiaが注文ごとに推定したものです";

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

// 結果の上に出す「何で探したか」の文
function describeCondition(c: SearchCondition): string {
  const parts: string[] = [];
  if (c.keyword.trim()) parts.push(`「${c.keyword.trim()}」`);
  if (c.category) parts.push(c.category);
  if (c.scene) parts.push(c.scene);
  if (c.priceBand) parts.push(c.priceBand.label);
  return parts.length > 0 ? parts.join("・") : "すべての商品";
}

// どの URL の条件で出した結果か。URL と違えば、まだ読み込み中
type SearchResult = {
  query: string;
  response: SearchResponse | null;
  error: string;
};

export default function ProductSearch() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL の条件。並び順や余計なキーの違いをならした文字列を、結果の見分けに使う
  const condition = useMemo(() => conditionFromParams(new URLSearchParams(searchParams.toString())), [searchParams]);
  const query = conditionToQuery(condition);

  const [options, setOptions] = useState<SearchOptions | null>(null); // 選べる値
  const [optionsError, setOptionsError] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const loading = result?.query !== query;

  // ① 画面を開いたら、選べる値を API から取る。取れなくてもキーワード検索はできる
  useEffect(() => {
    let active = true;
    fetchSearchOptions()
      .then((o) => { if (active) setOptions(o); })
      .catch((err: unknown) => { if (active) setOptionsError(errorMessage(err, "選択肢を読み込めませんでした")); });
    return () => { active = false; };
  }, []);

  // ② URL の条件が変わったら、その条件で API に聞く（条件なしなら、よく売れている順に全部）
  useEffect(() => {
    let active = true;
    rememberLastSearch(query); // 商品詳細の「検索結果に戻る」の行き先
    searchProducts(condition)
      .then((response) => { if (active) setResult({ query, response, error: "" }); })
      .catch((err: unknown) => {
        if (active) setResult({ query, response: null, error: errorMessage(err, "検索できませんでした") });
      });
    return () => { active = false; };
  }, [query, condition]);

  // ③ 検索ボタン：入力した条件を URL にする（URL が変わると②が動く）
  function handleSubmit(next: SearchCondition) {
    router.push(searchHref(conditionToQuery(next)));
  }

  const response = !loading ? result?.response ?? null : null;
  const error = !loading ? result?.error ?? "" : "";

  return (
    <>
      <SearchForm key={query} initial={condition} options={options} loading={loading} onSubmit={handleSubmit} />

      {optionsError && <p className="error" role="alert">{optionsError}（キーワードと予算帯では探せます）</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {loading && <p className="summary">検索しています…</p>}

      {response && (
        <section>
          {response.total === 0 ? (
            <p className="summary">
              {condition.scene
                ? "このシーンで買われた商品はまだありません。条件を変えて探してください"
                : "条件に合う商品が見つかりませんでした。条件を変えて探してください"}
            </p>
          ) : (
            <>
              <p className="summary">
                {describeCondition(condition)}：{response.total} 件
                {response.uses_purchase_history ? "（同じシーンで買った人数の多い順）" : "（よく売れている順）"}
              </p>
              {condition.scene && <p className="sceneNote">{SCENE_NOTICE}</p>}
              <div className="grid">
                {response.results.map((item) => (
                  <ProductCard
                    key={item.product_id}
                    item={item}
                    scene={condition.scene}
                    showRank={!response.uses_purchase_history}
                  />
                ))}
              </div>
            </>
          )}
        </section>
      )}
    </>
  );
}
