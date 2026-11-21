// components/ProductCard.tsx — 検索結果の1件（FR-04）
// いつも出す：商品名・価格・カテゴリー・ブランド・説明（先頭60文字）・商品全体の★・「商品詳細を見る」
// シーンを選んだときだけ出す：根拠①買った人数 ②同じシーンの★ ③同じシーンで買った人のレビュー1件
import Link from "next/link";
import { productDetailHref } from "@/lib/searchQuery";
import { formatRating, truncate } from "@/lib/text";
import type { SearchItem } from "@/types/search";

const DESCRIPTION_MAX = 60; // カードの説明は先頭60文字（FR-04）
const COMMENT_MAX = 40;     // レビューのコメントは40文字まで（FR-04）

interface ProductCardProps {
  item: SearchItem;
  scene: string;      // 検索で選んだシーン。"" は指定なし
  showRank: boolean;  // シーンなし（販売数の順）のときだけ、カードの上に「◯位」を出す
}

export default function ProductCard({ item, scene, showRank }: ProductCardProps) {
  return (
    <div className={item.is_supplemented ? "card supplemented" : "card"}>
      <p className="meta">
        {showRank && `${item.rank}位・`}
        {item.category}・{item.brand}
      </p>
      <h3 className="name">{item.product_name}</h3>
      <p className="price">{item.price.toLocaleString()}円</p>
      {item.description && <p className="description">{truncate(item.description, DESCRIPTION_MAX)}</p>}

      {scene && (
        <div className="evidence">
          {/* ① 買った人数 */}
          {item.reason && <p className="reason">{item.reason}</p>}
          {/* ② 同じシーンの★（1件からでも出す。0件なら出さない） */}
          {item.scene_rating_avg !== null && item.scene_review_count > 0 && (
            <p className="sceneRating">
              {scene}で買った人の評価 ★{formatRating(item.scene_rating_avg)}（{item.scene_review_count}件）
            </p>
          )}
          {/* ③ 同じシーンで買った人のレビュー1件（コメントがある最新の1件） */}
          {item.review_comment && item.review_rating !== null && (
            <p className="sceneReview">
              <span className="label">［{scene}で買った人のレビュー］</span>★{item.review_rating}「
              {truncate(item.review_comment, COMMENT_MAX)}」
            </p>
          )}
        </div>
      )}

      <p className="meta">
        {item.rating !== null ? `レビュー ★${formatRating(item.rating)}（${item.review_count}件）` : "レビューなし"}
      </p>
      <Link className="detailLink" href={productDetailHref(item.product_id, scene)}>
        商品詳細を見る
      </Link>
    </div>
  );
}
