-- 002_seed_test_data.sql
-- ★ 班の DB はメンバー全員で共有している。流すと全員の環境が変わる。
--    流す前にチームで合意し、流す人と日時を決めて共有する（AGENTS.md「AI 利用ルール」）。
-- Phase1 のテスト用データ（要件定義書 5.4）：既存の注文に関係性と相手の反応を付ける。
-- 001 を流したあとに、班の DB に1回だけ流す。本番の購入者が入力した値ではない（デモ用）。
--
-- 値の付け方：注文IDのハッシュ（CRC32）で決めるので、何回流しても同じ注文に同じ値が付く。
--   ・シーンが入っている注文の約1/3に、6種類の関係性のどれかを付ける
--   ・関係性を付けた注文の約1/4に、相手の反応（1〜4。喜んだ側に寄せる）を付ける
-- 割合を変えたいときは、MOD(...) の数字を変える。

-- 1. 関係性
UPDATE orders
SET relationship = ELT(
      1 + MOD(CRC32(CONCAT(order_id, ':rel')), 6),
      '上司・先輩', '同僚', '部下・後輩', '取引先', '友人', '家族'
    )
WHERE estimated_scene IS NOT NULL
  AND MOD(CRC32(order_id), 3) = 0;

-- 2. 相手の反応（4:とても喜んだ 3:喜んだ 2:ふつう 1:いまひとつ。4と3が多くなるようにする）
--    要確認：注文日時の列名（ここでは ordered_at）
INSERT INTO gift_feedback (order_id, reaction, comment, answered_at)
SELECT
  order_id,
  ELT(1 + MOD(CRC32(CONCAT(order_id, ':fb')), 10), 4, 4, 4, 3, 3, 3, 3, 2, 2, 1),
  NULL,
  DATE_ADD(ordered_at, INTERVAL 7 DAY)
FROM orders
WHERE relationship IS NOT NULL
  AND MOD(CRC32(CONCAT(order_id, ':has_fb')), 4) = 0;

-- 3. 確認：組み合わせごとの件数（付録A「組み合わせごとの件数が少ない」の確認にも使う）
SELECT estimated_scene, relationship, COUNT(*) AS orders
FROM orders
WHERE relationship IS NOT NULL
GROUP BY estimated_scene, relationship
ORDER BY estimated_scene, relationship;

SELECT COUNT(*) AS feedback_rows FROM gift_feedback;
