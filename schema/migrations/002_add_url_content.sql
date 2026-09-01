-- 已有库升级：为 daily_trending_news 增加原文链接与正文
-- 新库直接执行 schema/daily_trending_news.sql 即可，不必再跑本文件

ALTER TABLE `daily_trending_news`
  ADD COLUMN `url` varchar(2048) DEFAULT NULL COMMENT '原文链接' AFTER `source`,
  ADD COLUMN `content` mediumtext DEFAULT NULL COMMENT '新闻正文（纯文本）' AFTER `raw_line`;
