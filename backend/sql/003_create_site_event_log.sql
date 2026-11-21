-- 003_create_site_event_log.sql
-- ★ 班の DB はメンバー全員で共有している。流すと全員の環境が変わる。
--    流す前にチームで合意し、流す人と日時を決めて共有する（AGENTS.md「書き込みのある API」）。
-- 要件定義書 5.2・FR-11：商品詳細→カート投入率を測るための記録の表を作る。
-- 班の DB に MySQL Workbench で1回だけ流す（2回流すと「すでにある」エラーになる）。
-- 1行が1つの行動。個人を特定する情報（名前・連絡先・会員ID）は持たない。
-- 型と照合順序は、配布の表（products.product_id・orders.estimated_scene）にそろえている。

CREATE TABLE site_event_log (
  event_id    BIGINT      NOT NULL AUTO_INCREMENT COMMENT '記録の通し番号',
  session_id  VARCHAR(36) NOT NULL COMMENT 'ブラウザで作ったランダムな文字列（タブを閉じるまで同じ）',
  event_type  VARCHAR(20) NOT NULL COMMENT 'pdp_view：商品詳細を見た／add_to_cart：カートに入れた（模擬）',
  product_id  VARCHAR(10) NOT NULL COMMENT 'products.product_id と同じ値',
  scene       VARCHAR(20) NULL     COMMENT '検索で選んだシーン。なしは NULL（集計では「指定なし」）',
  occurred_at DATETIME    NOT NULL COMMENT 'API が受け取った時刻（日本時間）',
  PRIMARY KEY (event_id),
  KEY idx_site_event_session (session_id, event_type),
  CONSTRAINT ck_site_event_type CHECK (event_type IN ('pdp_view', 'add_to_cart'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_ja_0900_as_cs
  COMMENT='商品詳細→カート投入率を測る記録（範囲B・FR-11）';

-- 確認：表ができたか（列の一覧が出れば成功）
DESCRIBE site_event_log;
