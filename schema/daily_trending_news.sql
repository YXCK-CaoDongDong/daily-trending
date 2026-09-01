CREATE TABLE IF NOT EXISTS `daily_trending_news` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `run_date` date NOT NULL COMMENT '榜单日期（Asia/Shanghai）',
  `rank_no` int NOT NULL COMMENT '当日排名，1-50',
  `title` varchar(512) NOT NULL COMMENT '新闻事实标题',
  `source` varchar(128) DEFAULT NULL COMMENT '来源平台/媒体',
  `url` varchar(2048) DEFAULT NULL COMMENT '原文链接',
  `region` varchar(16) DEFAULT NULL COMMENT 'domestic=国内 international=国际',
  `raw_line` varchar(1024) DEFAULT NULL COMMENT '原始输出行（可选）',
  `content` mediumtext DEFAULT NULL COMMENT '新闻正文（纯文本）',
  `created_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '写入时间',
  `updated_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_run_date_rank` (`run_date`, `rank_no`),
  KEY `idx_run_date` (`run_date`),
  KEY `idx_source` (`source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='每日热榜精选新闻';
