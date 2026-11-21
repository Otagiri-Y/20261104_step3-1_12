// lib/session.ts — 計測用のセッションID（FR-11）
// 初めて開いたときにランダムな文字列を作り、タブを閉じるまで同じものを使う（sessionStorage はタブごとに消える）
// 名前・連絡先・会員IDとは結び付けない（要件定義書 8章）

const SESSION_KEY = "giftia_session_id";

// sessionStorage が使えない環境（プライベートブラウズの一部など）のための、画面を開いている間だけのID
let memorySessionId = "";

// ランダムな36文字（例：3f2a8c1e-9b7c-4d2e-8f10-1a2b3c4d5e6f）
function newSessionId(): string {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // randomUUID は https か localhost でしか使えない。スマホから IP アドレスで開いたときなどの予備
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // 形式を UUID v4 にそろえる
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// いまのタブのセッションID。なければ作って覚える
export function getSessionId(): string {
  try {
    const saved = sessionStorage.getItem(SESSION_KEY);
    if (saved) return saved;
    const created = newSessionId();
    sessionStorage.setItem(SESSION_KEY, created);
    return created;
  } catch {
    if (!memorySessionId) memorySessionId = newSessionId();
    return memorySessionId;
  }
}
