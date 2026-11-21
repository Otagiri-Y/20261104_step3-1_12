-- 003_rollback_site_event_log.sql
-- ★ 班の DB はメンバー全員で共有している。流すと全員の環境が変わる。
--    流す前にチームで合意し、流す人と日時を決めて共有する（AGENTS.md「書き込みのある API」）。
-- 003 で作った記録の表を消す（やり直したいとき）。記録したデータもすべて消える。
-- 999_rollback.sql（001・002 を戻す）とは別にしている。こちらは関係性（001）には触れない。

DROP TABLE IF EXISTS site_event_log;
