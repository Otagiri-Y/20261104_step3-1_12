// app/page.tsx — Giftia 検索画面（要件定義書 4.2）
// 検索の入力と結果は ProductSearch（Client Component）に任せ、このページはサーバーで描く。
// ProductSearch は URL の条件（useSearchParams）を読むので、Suspense で包む（Next.js の決まり）
import { Suspense } from "react";
import ProductSearch from "@/components/ProductSearch";

export default function Home() {
  return (
    <main className="page">
      <header className="header"><h1>Giftia</h1></header>
      <Suspense fallback={<p className="summary">読み込んでいます…</p>}>
        <ProductSearch />
      </Suspense>
    </main>
  );
}
