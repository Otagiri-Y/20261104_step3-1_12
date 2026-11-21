// components/AddToCartButton.tsx — 「カートに入れる」ボタン（模擬・FR-12）
// 押すと「カートに入れた」を記録だけして、案内を出す。本当のカート・決済・注文は作らない
"use client";

import { useState } from "react";
import { postEvent } from "@/lib/api";
import { getSessionId } from "@/lib/session";

const MESSAGE_DONE = "カートに入れました（デモのため、実際には入りません）";
const MESSAGE_FAILED = "記録できませんでした。もう一度押してください";

interface AddToCartButtonProps {
  productId: string;
  scene: string | null; // 引き継いだシーン。なしは null
}

type Status = "idle" | "sending" | "done" | "failed";

export default function AddToCartButton({ productId, scene }: AddToCartButtonProps) {
  const [status, setStatus] = useState<Status>("idle");

  async function handleClick() {
    setStatus("sending");
    try {
      // 押すたびに1行残る。率はセッション単位で数えるので、何回押しても分子は1
      await postEvent({ session_id: getSessionId(), event_type: "add_to_cart", product_id: productId, scene });
      setStatus("done");
    } catch (err) {
      console.error("「カートに入れた」を記録できませんでした", err);
      setStatus("failed");
    }
  }

  return (
    <div className="cartArea">
      <button type="button" className="cartButton" onClick={handleClick} disabled={status === "sending"}>
        {status === "sending" ? "記録しています…" : "カートに入れる"}
      </button>
      {status === "done" && <p className="cartMessage" role="status">{MESSAGE_DONE}</p>}
      {status === "failed" && <p className="error" role="alert">{MESSAGE_FAILED}</p>}
    </div>
  );
}
