CREATE TABLE corpus (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                        title VARCHAR(500) NOT NULL COMMENT '标题',
                        content TEXT COMMENT '文本内容',
                        source ENUM('china', 'usa', 'russia') NOT NULL COMMENT '媒体来源国家',
                        media_name VARCHAR(200) COMMENT '具体媒体名称',
                        type ENUM('text', 'image', 'video') NOT NULL COMMENT '内容类型',
                        file_path VARCHAR(500) COMMENT '文件路径',
                        image_url VARCHAR(500) COMMENT '图片URL',
                        video_url VARCHAR(500) COMMENT '视频URL',
                        publish_date DATE COMMENT '发布日期',
                        create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        INDEX idx_source (source),
                        INDEX idx_type (type),
                        INDEX idx_publish_date (publish_date),
                        FULLTEXT INDEX idx_title_content (title, content) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='语料库表';

-- 2. 情感分析结果表
CREATE TABLE sentiment_analysis (
                                    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                                    corpus_id BIGINT COMMENT '关联语料ID',
                                    sentiment ENUM('positive', 'neutral', 'negative') NOT NULL COMMENT '情感倾向',
                                    sentiment_score DECIMAL(3,2) COMMENT '情感得分(0-10)',
                                    confidence DECIMAL(5,2) COMMENT '置信度(%)',
                                    positive_rate DECIMAL(5,2) COMMENT '积极情感比例(%)',
                                    negative_rate DECIMAL(5,2) COMMENT '消极情感比例(%)',
                                    neutral_rate DECIMAL(5,2) COMMENT '中性情感比例(%)',
                                    emotion_joy DECIMAL(5,2) COMMENT '喜悦情绪(%)',
                                    emotion_trust DECIMAL(5,2) COMMENT '信任情绪(%)',
                                    emotion_fear DECIMAL(5,2) COMMENT '恐惧情绪(%)',
                                    emotion_surprise DECIMAL(5,2) COMMENT '惊讶情绪(%)',
                                    analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
                                    FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE,
                                    INDEX idx_corpus_id (corpus_id),
                                    INDEX idx_sentiment (sentiment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情感分析结果表';

-- 3. 关键词表
CREATE TABLE keywords (
                          id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                          corpus_id BIGINT NOT NULL COMMENT '关联语料ID',
                          keyword VARCHAR(100) NOT NULL COMMENT '关键词',
                          weight DECIMAL(5,2) COMMENT '权重',
                          frequency INT DEFAULT 1 COMMENT '出现频率',
                          create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                          FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE,
                          INDEX idx_corpus_id (corpus_id),
                          INDEX idx_keyword (keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关键词表';

-- 4. 报道润色记录表
CREATE TABLE polish_records (
                                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                                original_text TEXT NOT NULL COMMENT '原始文本',
                                polished_text TEXT COMMENT '润色后文本',
                                polish_type VARCHAR(50) COMMENT '润色类型',
                                fluency_score INT COMMENT '流畅度得分',
                                professionalism_score INT COMMENT '专业性得分',
                                objectivity_score INT COMMENT '客观性得分',
                                readability_score INT COMMENT '可读性得分',
                                suggestions JSON COMMENT '修改建议(JSON格式)',
                                create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报道润色记录表';

-- 5. 统计数据表
CREATE TABLE statistics (
                            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                            stat_date DATE NOT NULL COMMENT '统计日期',
                            source ENUM('china', 'usa', 'russia') NOT NULL COMMENT '媒体来源',
                            total_count INT DEFAULT 0 COMMENT '总报道数',
                            text_count INT DEFAULT 0 COMMENT '文字报道数',
                            image_count INT DEFAULT 0 COMMENT '图片报道数',
                            video_count INT DEFAULT 0 COMMENT '视频报道数',
                            positive_count INT DEFAULT 0 COMMENT '积极报道数',
                            neutral_count INT DEFAULT 0 COMMENT '中性报道数',
                            negative_count INT DEFAULT 0 COMMENT '消极报道数',
                            avg_sentiment DECIMAL(3,2) COMMENT '平均情感得分',
                            create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            UNIQUE KEY uk_date_source (stat_date, source),
                            INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='统计数据表';

-- 6. 热门关键词统计表
CREATE TABLE hot_keywords (
                              id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                              keyword VARCHAR(100) NOT NULL COMMENT '关键词',
                              source ENUM('china', 'usa', 'russia', 'all') DEFAULT 'all' COMMENT '媒体来源',
                              count INT DEFAULT 1 COMMENT '出现次数',
                              heat_score DECIMAL(5,2) COMMENT '热度得分',
                              stat_date DATE NOT NULL COMMENT '统计日期',
                              create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                              update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                              INDEX idx_keyword (keyword),
                              INDEX idx_stat_date (stat_date),
                              INDEX idx_heat_score (heat_score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='热门关键词统计表';

-- 7. 媒体活跃度表
CREATE TABLE media_activity (
                                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                                media_name VARCHAR(200) NOT NULL COMMENT '媒体名称',
                                source ENUM('china', 'usa', 'russia') NOT NULL COMMENT '媒体来源国家',
                                article_count INT DEFAULT 0 COMMENT '报道数量',
                                activity_score DECIMAL(5,2) COMMENT '活跃度得分',
                                stat_month VARCHAR(7) NOT NULL COMMENT '统计月份(YYYY-MM)',
                                create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                                UNIQUE KEY uk_media_month (media_name, stat_month),
                                INDEX idx_stat_month (stat_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='媒体活跃度表';

-- 8. 用户操作日志表
CREATE TABLE operation_logs (
                                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
                                operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
                                operation_desc VARCHAR(500) COMMENT '操作描述',
                                request_params TEXT COMMENT '请求参数',
                                response_result TEXT COMMENT '响应结果',
                                ip_address VARCHAR(50) COMMENT 'IP地址',
                                create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                INDEX idx_operation_type (operation_type),
                                INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户操作日志表';

-- 插入示例数据
INSERT INTO corpus (title, content, source, media_name, type, publish_date) VALUES
                                                                                ('中国成功发射神舟十八号载人飞船', '北京时间10月25日，中国在酒泉卫星发射中心成功发射神舟十八号载人飞船...', 'china', '新华社', 'text', '2024-10-25'),
                                                                                ('China launches Shenzhou-18 spacecraft', 'China successfully launched the Shenzhou-18 manned spacecraft...', 'usa', 'CNN', 'text', '2024-10-25'),
                                                                                ('Китай запустил космический корабль Шэньчжоу-18', 'Китай успешно запустил пилотируемый космический корабль...', 'russia', 'TASS', 'text', '2024-10-25');

-- 创建视图：语料库统计视图
CREATE VIEW v_corpus_statistics AS
SELECT
    source,
    type,
    COUNT(*) as count,
    DATE_FORMAT(publish_date, '%Y-%m') as month
FROM corpus
GROUP BY source, type, DATE_FORMAT(publish_date, '%Y-%m');

-- 创建视图：情感分析统计视图
CREATE VIEW v_sentiment_statistics AS
SELECT
    c.source,
    sa.sentiment,
    COUNT(*) as count,
    AVG(sa.sentiment_score) as avg_score
FROM corpus c
         LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
GROUP BY c.source, sa.sentiment;