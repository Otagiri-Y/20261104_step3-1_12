// app/products/[id]/page.tsx — 商品詳細画面（要件定義書 4.2・FR-01）
// URL：/products/G0001?scene=送別（検索で選んだシーンを引き継ぐ）
// URL から商品IDとシーンを取り出して、表示は ProductDetailView（Client Component）に任せる
import ProductDetailView from "@/components/ProductDetailView";

export default async function ProductPage(props: PageProps<"/products/[id]">) {
  const { id } = await props.params;
  const searchParams = await props.searchParams;
  const scene = typeof searchParams.scene === "string" ? searchParams.scene : "";

  return (
    <main className="page">
      <header className="header"><h1>Giftia</h1></header>
      <ProductDetailView productId={id} scene={scene} />
    </main>
  );
}
