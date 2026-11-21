// components/ProductDetailView.tsx — 商品詳細（FR-01）
// いつも出す：商品名・価格・カテゴリー・ブランド・説明（全文）・商品全体の★
// シーンを引き継いだとき：買った人数・同じシーンの★と件数・同じシーンで買った人のレビュー一覧（新しい順）
// 「カートに入れる」は置き場所だけ用意する（記録と案内は PR③ で付ける）
"use client"; // API 呼び出しとボタンの処理があるため、ブラウザで動かす

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, fetchProductDetail } from "@/lib/api";
import { lastSearchHref } from "@/lib/searchQuery";
import { formatRating } from "@/lib/text";
import type { ProductDetail } from "@/types/search";

const MIN_BUYERS_TO_SHOW = 3; // 3人未満は「少数」と出す（API の min_buyers_to_show と同じ。仮置き）

interface ProductDetailViewProps {
  productId: string;
  scene: string; // URL の ?scene=。"" は指定なし
}

// どの商品・シーンで取った結果か。違えば、まだ読み込み中
type DetailResult = {
  key: string;
  detail: ProductDetail | null;
  notFound: boolean;
  error: string;
};

// シーンが4つ以外（URL を手で書き換えたなど）で 422 なら、シーンなしで開き直す
async function loadDetail(productId: string, scene: string): Promise<ProductDetail> {
  try {
    return await fetchProductDetail(productId, scene);
  } catch (err) {
    if (scene && err instanceof ApiError && err.status === 422) {
      return fetchProductDetail(productId, "");
    }
    throw err;
  }
}

function buyerText(scene: string, count: number): string {
  return count < MIN_BUYERS_TO_SHOW ? `${scene}での購入実績あり（少数）` : `${scene}で ${count}人 が購入`;
}

export default function ProductDetailView({ productId, scene }: ProductDetailViewProps) {
  const router = useRouter();
  const key = `${productId}|${scene}`;
  const [result, setResult] = useState<DetailResult | null>(null);
  const loading = result?.key !== key;

  useEffect(() => {
    let active = true;
    loadDetail(productId, scene)
      .then((detail) => { if (active) setResult({ key, detail, notFound: false, error: "" }); })
      .catch((err: unknown) => {
        if (!active) return;
        const notFound = err instanceof ApiError && err.status === 404;
        const error = err instanceof Error ? err.message : "商品を読み込めませんでした";
        setResult({ key, detail: null, notFound, error });
      });
    return () => { active = false; };
  }, [key, productId, scene]);

  // 「検索結果に戻る」：最後に見た検索結果（URL に条件が入っている）へ。覚えていなければトップ
  function backToSearch() {
    router.push(lastSearchHref());
  }

  const backButton = (
    <button type="button" className="backButton" onClick={backToSearch}>
      ← 検索結果に戻る
    </button>
  );

  if (loading) {
    return <>{backButton}<p className="summary">読み込んでいます…</p></>;
  }
  if (!result.detail) {
    return (
      <>
        {backButton}
        <p className="error" role="alert">{result.notFound ? "商品が見つかりません" : result.error}</p>
      </>
    );
  }

  const d = result.detail;
  return (
    <>
      {backButton}
      <article className="detail">
        <p className="meta">{d.category}・{d.brand}</p>
        <h2 className="name">{d.product_name}</h2>
        <p className="price">{d.price.toLocaleString()}円</p>
        <p className="meta">
          {d.rating !== null ? `レビュー ★${formatRating(d.rating)}（${d.review_count}件）` : "レビューなし"}
        </p>
        <p className="description">{d.description}</p>

        <div className="cartArea">
          {/* PR③：ここを AddToCartButton に置き換える（押すと記録を残し、「実際には入りません」の案内を出す） */}
          <button type="button" className="cartButton" disabled>
            カートに入れる
          </button>
        </div>

        {d.scene && d.buyer_count !== null && (
          <section className="evidence">
            <h3>{d.scene}で買った人の根拠</h3>
            <p className="reason">{buyerText(d.scene, d.buyer_count)}</p>
            {d.scene_rating_avg !== null && d.scene_review_count ? (
              <p className="sceneRating">
                {d.scene}で買った人の評価 ★{formatRating(d.scene_rating_avg)}（{d.scene_review_count}件）
              </p>
            ) : (
              <p className="meta">{d.scene}で買った人のレビューはまだありません</p>
            )}
            {d.scene_reviews.length > 0 && (
              <ul className="reviewList">
                {d.scene_reviews.map((r) => (
                  <li key={r.review_id}>
                    <p className="meta">
                      <span className="label">［{d.scene}で買った人のレビュー］</span>★{r.rating}・{r.posted_at}
                    </p>
                    <p>{r.comment ?? "（コメントなし）"}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </article>
    </>
  );
}
