// components/ProductCard.tsx — 検索結果の1件。シーン・関係性を選んだときは根拠も見せる（FR-04）
import type { SearchItem } from "@/types/search";

interface ProductCardProps {
  item: SearchItem;
}

export default function ProductCard({ item }: ProductCardProps) {
  return (
    <div className={item.is_supplemented ? "card supplemented" : "card"}>
      <p className="meta">{item.rank}位・{item.category}・{item.brand}</p>
      <h3 className="name">{item.product_name}</h3>
      <p className="price">{item.price.toLocaleString()}円</p>
      {item.reason && <p className="reason">{item.reason}</p>}
      {item.reaction_avg !== null && (
        <p className="meta">相手の反応 ★{item.reaction_avg.toFixed(1)}（{item.reaction_count}件・贈った人の回答）</p>
      )}
      <p className="meta">
        {item.rating !== null ? `レビュー ★${item.rating.toFixed(1)}（${item.review_count}件）` : "レビューなし"}
      </p>
    </div>
  );
}
