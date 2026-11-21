// components/RecordPdpView.tsx — 「商品詳細を見た」を記録する（FR-11）
// 商品詳細を表示できたときに1回だけ送る。画面には何も出さない
// 失敗しても利用者には出さない（開発中はブラウザのコンソールで分かる）
"use client";

import { useEffect, useRef } from "react";
import { postEvent } from "@/lib/api";
import { getSessionId } from "@/lib/session";

interface RecordPdpViewProps {
  productId: string;
  scene: string | null; // 引き継いだシーン。なしは null
}

export default function RecordPdpView({ productId, scene }: RecordPdpViewProps) {
  // どの商品・シーンで送ったかを覚える。開発中（npm run dev）は React が確認のため
  // useEffect を2回動かすので、これがないと「見た」が2行残る（6.4 No.23）
  const sentFor = useRef("");

  useEffect(() => {
    const key = `${productId}|${scene ?? ""}`;
    if (sentFor.current === key) return;
    sentFor.current = key;
    postEvent({ session_id: getSessionId(), event_type: "pdp_view", product_id: productId, scene }).catch(
      (err: unknown) => {
        console.error("「商品詳細を見た」を記録できませんでした", err);
      },
    );
  }, [productId, scene]);

  return null;
}
