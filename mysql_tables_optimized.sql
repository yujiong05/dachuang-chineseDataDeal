-- 基于项目数据特点的优化数据库建表语句
-- 适用于中国情感分析项目

-- 1. 语料库主表（基于爬取数据特点优化）
CREATE TABLE corpus (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    title VARCHAR(500) NOT NULL COMMENT '文章标题',
    content TEXT COMMENT '文章内容',
    url VARCHAR(1000) COMMENT '原始网址',
    source ENUM('china', 'usa', 'russia') NOT NULL DEFAULT 'china' COMMENT '媒体来源国家',
    media_name VARCHAR(200) DEFAULT 'China Daily' COMMENT '具体媒体名称',
    content_type ENUM('text', 'image', 'video') NOT NULL COMMENT '内容类型',
    file_path VARCHAR(500) COMMENT '文件路径',
    image_count INT DEFAULT 0 COMMENT '关联图片数量',
    video_count INT DEFAULT 0 COMMENT '关联视频数量',
    publish_date DATE COMMENT '发布日期',
    crawl_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '爬取日期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_source (source),
    INDEX idx_content_type (content_type),
    INDEX idx_publish_date (publish_date),
    INDEX idx_crawl_date (crawl_date),
    FULLTEXT INDEX idx_title_content (title, content) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语料库主表';

-- 2. 情感分析结果表（基于实际分析结果优化）
CREATE TABLE sentiment_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    corpus_id BIGINT NOT NULL COMMENT '关联语料ID',
    sentiment ENUM('positive', 'neutral', 'negative') NOT NULL COMMENT '情感倾向',
    sentiment_score DECIMAL(4,3) NOT NULL COMMENT '情感得分(-1到1)',
    confidence DECIMAL(5,2) COMMENT '置信度(%)',
    analysis_method VARCHAR(50) DEFAULT 'textblob' COMMENT '分析方法',
    analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',

    FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE,
    INDEX idx_corpus_id (corpus_id),
    INDEX idx_sentiment (sentiment),
    INDEX idx_score (sentiment_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情感分析结果表';

-- 3. 图片资源表
CREATE TABLE images (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    corpus_id BIGINT NOT NULL COMMENT '关联语料ID',
    file_name VARCHAR(200) NOT NULL COMMENT '图片文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size INT COMMENT '文件大小(字节)',
    width INT COMMENT '图片宽度',
    height INT COMMENT '图片高度',
    format ENUM('jpg', 'jpeg', 'png', 'gif', 'webp') COMMENT '图片格式',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE,
    INDEX idx_corpus_id (corpus_id),
    INDEX idx_format (format)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片资源表';

-- 4. 视频资源表
CREATE TABLE videos (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    corpus_id BIGINT NOT NULL COMMENT '关联语料ID',
    file_name VARCHAR(200) NOT NULL COMMENT '视频链接文件名',
    video_url VARCHAR(1000) NOT NULL COMMENT '视频URL',
    platform VARCHAR(100) COMMENT '视频平台',
    duration INT COMMENT '视频时长(秒)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE,
    INDEX idx_corpus_id (corpus_id),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频资源表';

-- 5. 关键词提取表
CREATE TABLE keywords (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    corpus_id BIGINT NOT NULL COMMENT '关联语料ID',
    keyword VARCHAR(100) NOT NULL COMMENT '关键词',
    keyword_type ENUM('person', 'organization', 'location', 'technology', 'other') DEFAULT 'other' COMMENT '关键词类型',
    frequency INT DEFAULT 1 COMMENT '在文档中出现频率',
    importance_score DECIMAL(5,2) COMMENT '重要性得分',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE,
    INDEX idx_corpus_id (corpus_id),
    INDEX idx_keyword (keyword),
    INDEX idx_type (keyword_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词提取表';

-- 6. 媒体统计表（按时间维度统计）
CREATE TABLE media_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    stat_date DATE NOT NULL COMMENT '统计日期',
    stat_month VARCHAR(7) NOT NULL COMMENT '统计月份(YYYY-MM)',
    source ENUM('china', 'usa', 'russia') NOT NULL COMMENT '媒体来源',
    total_articles INT DEFAULT 0 COMMENT '总文章数',
    text_articles INT DEFAULT 0 COMMENT '文字文章数',
    image_articles INT DEFAULT 0 COMMENT '含图片文章数',
    video_articles INT DEFAULT 0 COMMENT '含视频文章数',
    positive_articles INT DEFAULT 0 COMMENT '积极文章数',
    neutral_articles INT DEFAULT 0 COMMENT '中性文章数',
    negative_articles INT DEFAULT 0 COMMENT '消极文章数',
    avg_sentiment_score DECIMAL(4,3) COMMENT '平均情感得分',
    total_images INT DEFAULT 0 COMMENT '总图片数',
    total_videos INT DEFAULT 0 COMMENT '总视频数',

    UNIQUE KEY uk_date_source (stat_date, source),
    INDEX idx_stat_date (stat_date),
    INDEX idx_stat_month (stat_month),
    INDEX idx_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体统计表';

-- 7. 热点话题表
CREATE TABLE hot_topics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    topic_name VARCHAR(200) NOT NULL COMMENT '话题名称',
    topic_keywords JSON COMMENT '话题关键词(JSON数组)',
    article_count INT DEFAULT 1 COMMENT '相关文章数',
    heat_score DECIMAL(6,2) DEFAULT 0 COMMENT '热度得分',
    avg_sentiment_score DECIMAL(4,3) COMMENT '平均情感得分',
    stat_date DATE NOT NULL COMMENT '统计日期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_topic_name (topic_name),
    INDEX idx_stat_date (stat_date),
    INDEX idx_heat_score (heat_score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='热点话题表';

-- 8. 数据处理日志表
CREATE TABLE processing_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    process_type ENUM('crawl', 'sentiment_analysis', 'keyword_extraction', 'statistics') NOT NULL COMMENT '处理类型',
    status ENUM('success', 'failed', 'running') NOT NULL COMMENT '处理状态',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    processed_count INT DEFAULT 0 COMMENT '处理数量',
    error_message TEXT COMMENT '错误信息',
    details JSON COMMENT '处理详情(JSON格式)',

    INDEX idx_process_type (process_type),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据处理日志表';

-- 创建视图：情感分析概览
CREATE VIEW v_sentiment_overview AS
SELECT
    DATE_FORMAT(c.publish_date, '%Y-%m') as month,
    c.source,
    COUNT(*) as total_articles,
    SUM(CASE WHEN sa.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN sa.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
    SUM(CASE WHEN sa.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
    AVG(sa.sentiment_score) as avg_sentiment_score,
    ROUND(SUM(CASE WHEN sa.sentiment = 'positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as positive_rate
FROM corpus c
LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
WHERE c.publish_date IS NOT NULL
GROUP BY DATE_FORMAT(c.publish_date, '%Y-%m'), c.source
ORDER BY month DESC, c.source;

-- 创建视图：内容类型统计
CREATE VIEW v_content_type_stats AS
SELECT
    DATE_FORMAT(c.publish_date, '%Y-%m') as month,
    c.content_type,
    c.source,
    COUNT(*) as count,
    AVG(c.image_count) as avg_images,
    AVG(c.video_count) as avg_videos,
    COUNT(DISTINCT c.media_name) as media_count
FROM corpus c
WHERE c.publish_date IS NOT NULL
GROUP BY DATE_FORMAT(c.publish_date, '%Y-%m'), c.content_type, c.source
ORDER BY month DESC, c.content_type, c.source;

-- 创建存储过程：更新月度统计数据
DELIMITER //
CREATE PROCEDURE UpdateMonthlyStatistics(IN stat_month VARCHAR(7))
BEGIN
    -- 删除当月已存在的统计数据
    DELETE FROM media_statistics WHERE stat_month = stat_month;

    -- 插入新的统计数据
    INSERT INTO media_statistics (
        stat_date, stat_month, source, total_articles, text_articles,
        image_articles, video_articles, positive_articles, neutral_articles,
        negative_articles, avg_sentiment_score, total_images, total_videos
    )
    SELECT
        LAST_DAY(CONCAT(stat_month, '-01')) as stat_date,
        stat_month,
        c.source,
        COUNT(*) as total_articles,
        SUM(CASE WHEN c.content_type = 'text' THEN 1 ELSE 0 END) as text_articles,
        SUM(CASE WHEN c.image_count > 0 THEN 1 ELSE 0 END) as image_articles,
        SUM(CASE WHEN c.video_count > 0 THEN 1 ELSE 0 END) as video_articles,
        SUM(CASE WHEN sa.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_articles,
        SUM(CASE WHEN sa.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_articles,
        SUM(CASE WHEN sa.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_articles,
        AVG(sa.sentiment_score) as avg_sentiment_score,
        SUM(c.image_count) as total_images,
        SUM(c.video_count) as total_videos
    FROM corpus c
    LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
    WHERE DATE_FORMAT(c.publish_date, '%Y-%m') = stat_month
    GROUP BY c.source;

    SELECT CONCAT('Updated statistics for month: ', stat_month) as result;
END //
DELIMITER ;

-- 创建触发器：自动更新图片和视频计数
DELIMITER //
CREATE TRIGGER tr_update_media_counts
AFTER INSERT ON images FOR EACH ROW
BEGIN
    UPDATE corpus SET image_count = image_count + 1 WHERE id = NEW.corpus_id;
END //

CREATE TRIGGER tr_update_video_counts
AFTER INSERT ON videos FOR EACH ROW
BEGIN
    UPDATE corpus SET video_count = video_count + 1 WHERE id = NEW.corpus_id;
END //
DELIMITER ;

-- 性能优化建议：
-- 1. 对于大量文本数据，建议使用全文索引进行搜索优化
-- 2. 定期执行 ANALYZE TABLE 更新表统计信息
-- 3. 考虑对历史数据进行分区，如按月份分区
-- 4. 对于频繁查询的字段组合，可创建复合索引