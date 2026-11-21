// lib/text.ts — 表示用の文字の整形

// max 文字より長ければ先頭 max 文字＋「…」にする（カードの説明60文字・レビュー40文字）
export function truncate(text: string, max: number): string {
  const chars = Array.from(text); // 絵文字などを途中で切らないよう、文字単位で数える
  return chars.length > max ? `${chars.slice(0, max).join("")}…` : text;
}

// ★の平均を「4.0」のように小数1桁で
export function formatRating(value: number): string {
  return value.toFixed(1);
}
