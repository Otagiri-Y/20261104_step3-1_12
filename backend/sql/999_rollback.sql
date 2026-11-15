-- 999_rollback.sql
-- ★ 班の DB はメンバー全員で共有している。流すと全員の環境が変わる。
--    流す前にチームで合意し、流す人と日時を決めて共有する（AGENTS.md「AI 利用ルール」）。
-- 001・002 で足したものを元に戻す（やり直したいとき）。gift_feedback のデータも消える。
DROP TABLE IF EXISTS gift_feedback;
DROP INDEX idx_orders_scene_relationship_date ON orders;
ALTER TABLE orders DROP COLUMN relationship;
