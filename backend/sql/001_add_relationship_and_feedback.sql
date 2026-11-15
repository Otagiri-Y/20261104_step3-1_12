-- 001_add_relationship_and_feedback.sql
-- ★ 班の DB はメンバー全員で共有している。流すと全員の環境が変わる。
--    流す前にチームで合意し、流す人と日時を決めて共有する（AGENTS.md「AI 利用ルール」）。
-- 要件定義書 5.2：orders に relationship を足し、gift_feedback を新しく作る。8章：検索に使う列にインデックスを張る。
-- 班の DB に MySQL Workbench で1回だけ流す（2回流すと「すでにある」エラーになる）。
-- 流す前に：orders.order_id の型（VARCHAR の長さ・照合順序）を配布のデータ定義で確かめ、
--           gift_feedback.order_id を同じ型にそろえる（違うと外部キーが作れない）。

-- 1. 関係性（購入者から見た、贈る相手との関係。未選択は NULL）
ALTER TABLE orders
  ADD COLUMN relationship VARCHAR(20) NULL COMMENT '贈る相手との関係（上司・先輩／同僚／部下・後輩／取引先／友人／家族）';

-- 2. 検索の応答を速くする（8章：検索APIが2秒以内）
--    要確認：注文日時の列名（ここでは ordered_at）。app/models/tables.py と同じ名前にする
CREATE INDEX idx_orders_scene_relationship_date
  ON orders (estimated_scene, relationship, ordered_at);

-- 3. 相手の反応（購入者が回答。1注文1回答）
CREATE TABLE gift_feedback (
  feedback_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '回答の通し番号',
  order_id    VARCHAR(20) NOT NULL COMMENT '回答した注文',
  reaction    TINYINT     NOT NULL COMMENT '4:とても喜んだ 3:喜んだ 2:ふつう 1:いまひとつ',
  comment     TEXT        NULL     COMMENT '任意のコメント',
  answered_at DATETIME    NOT NULL COMMENT '回答日時',
  CONSTRAINT uq_gift_feedback_order UNIQUE (order_id),
  CONSTRAINT fk_gift_feedback_order FOREIGN KEY (order_id) REFERENCES orders (order_id),
  CONSTRAINT ck_gift_feedback_reaction CHECK (reaction BETWEEN 1 AND 4)
);
