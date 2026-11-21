-- 004_conversion_rate.sql
-- 読むだけの SQL（班の DB は変わらない）。何回流してもよい。
-- 要件定義書 FR-11・要求定義書 6章：商品詳細→カート投入率を出し、今の数値（8%）と比べる。
--   分母：商品詳細を見たセッション（pdp_view が1回以上ある）
--   分子：そのうち、カートに入れたセッション（add_to_cart も1回以上ある）
--   1つのセッションで商品詳細を2回見てカートに1回入れたら、分母1・分子1（6.4 No.18）
-- ※ 手元の率は協力者の数字で、8%は本番の数字。使う人もセッションの決め方も違うので、
--    効果の証拠ではなく、仕組みが動くことの確認と傾向を見るために使う。

-- 1. 全体
SELECT
  COUNT(*)                                   AS viewed_sessions,  -- 分母
  SUM(carted)                                AS carted_sessions,  -- 分子
  ROUND(100.0 * SUM(carted) / COUNT(*), 1)   AS rate_pct          -- 今の数値 8% と比べる
FROM (
  SELECT session_id,
         MAX(event_type = 'add_to_cart') AS carted
  FROM site_event_log
  GROUP BY session_id
  HAVING MAX(event_type = 'pdp_view') = 1
) AS s;

-- 2. シーン別（シーンを選ばずに開いた商品詳細は「指定なし」）
--    1つのセッションが2つのシーンで商品詳細を見たら、両方に数える。そのため合計は全体と一致しないことがある
SELECT
  scene,
  COUNT(*)                                   AS viewed_sessions,
  SUM(carted)                                AS carted_sessions,
  ROUND(100.0 * SUM(carted) / COUNT(*), 1)   AS rate_pct
FROM (
  SELECT session_id,
         COALESCE(scene, '指定なし')        AS scene,
         MAX(event_type = 'add_to_cart')    AS carted
  FROM site_event_log
  GROUP BY session_id, COALESCE(scene, '指定なし')
  HAVING MAX(event_type = 'pdp_view') = 1
) AS s
GROUP BY scene
ORDER BY viewed_sessions DESC;

-- 3. 記録の中身を見る（新しい順に20行）
SELECT * FROM site_event_log ORDER BY event_id DESC LIMIT 20;
