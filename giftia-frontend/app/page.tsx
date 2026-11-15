// app/page.tsx — Giftia 検索画面（要件定義書 4.2）
// 検索の入力と結果は ProductSearch（Client Component）に任せ、このページはサーバーで描く
import ProductSearch from "@/components/ProductSearch";

export default function Home() {
  return (
    <main className="page">
      <header className="header"><h1>Giftia</h1></header>
      <ProductSearch />
    </main>
  );
}
