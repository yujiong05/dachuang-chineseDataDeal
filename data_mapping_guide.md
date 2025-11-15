# 基于原表结构的数据映射指南

## 现有表结构分析

基于init.sql中的表结构，我们需要将爬取的数据映射到以下表中：

### 1. corpus 表（语料库表）
```sql
CREATE TABLE corpus (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL COMMENT '标题',
    content TEXT COMMENT '文本内容',
    source ENUM('china', 'usa', 'russia') NOT NULL COMMENT '媒体来源国家',
    media_name VARCHAR(200) COMMENT '具体媒体名称',
    type ENUM('text', 'image', 'video') NOT NULL COMMENT '内容类型',
    file_path VARCHAR(500) COMMENT '文件路径',
    image_url VARCHAR(500) COMMENT '图片URL',
    video_url VARCHAR(500) COMMENT '视频URL',
    publish_date DATE COMMENT '发布日期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. sentiment_analysis 表（情感分析结果表）
```sql
CREATE TABLE sentiment_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    corpus_id BIGINT COMMENT '关联语料ID',
    sentiment ENUM('positive', 'neutral', 'negative') NOT NULL,
    sentiment_score DECIMAL(3,2) COMMENT '情感得分(0-10)',
    confidence DECIMAL(5,2) COMMENT '置信度(%)',
    positive_rate DECIMAL(5,2) COMMENT '积极情感比例(%)',
    negative_rate DECIMAL(5,2) COMMENT '消极情感比例(%)',
    neutral_rate DECIMAL(5,2) COMMENT '中性情感比例(%)',
    emotion_joy DECIMAL(5,2) COMMENT '喜悦情绪(%)',
    emotion_trust DECIMAL(5,2) COMMENT '信任情绪(%)',
    emotion_fear DECIMAL(5,2) COMMENT '恐惧情绪(%)',
    emotion_surprise DECIMAL(5,2) COMMENT '惊讶情绪(%)',
    analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 数据映射规则

### 从texts文件夹解析的数据映射到corpus表：

| 数据源字段 | 表字段 | 说明 |
|-----------|--------|------|
| 标题: [文章标题] | title | 直接映射 |
| 网址: [URL] | 无对应字段（可考虑扩展） |
| 文章正文内容 | content | 直接映射 |
| 'China Daily'（默认） | source | 'china' |
| 'China Daily'（默认） | media_name | 默认值 |
| 文本内容 | type | 'text' |
| 文件路径（texts/文件名.txt） | file_path | 相对路径 |
| 图片列表数量 > 0 | image_url | 首张图片路径或null |
| 无 | video_url | null |
| 从文件名或内容提取日期 | publish_date | 需要解析 |

### 从sentiment_analysis_results.txt解析的数据映射到sentiment_analysis表：

| 数据源格式 | 表字段 | 转换规则 |
|-----------|--------|---------|
| 正向/负面/中性 | sentiment | 'positive'/'negative'/'neutral' |
| 得分: 0.991 | sentiment_score | 需要转换到0-10范围：(score+1)*5 |
| 文章标题 | corpus_id | 通过title查找corpus表获取id |

## 数据处理流程

### 1. 文本数据处理
```python
def parse_text_file(file_path):
    """解析文本文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析标题
    title_match = re.search(r'标题: (.+)', content)
    title = title_match.group(1) if title_match else "未知标题"

    # 解析URL
    url_match = re.search(r'网址: (.+)', content)
    url = url_match.group(1) if url_match else ""

    # 提取正文内容（移除标题、网址等元信息）
    text_content = re.sub(r'标题: .+\n网址: .+\n\n', '', content)

    return {
        'title': title,
        'content': text_content,
        'source': 'china',
        'media_name': 'China Daily',
        'type': 'text',
        'file_path': file_path,
        'publish_date': extract_date_from_content(content)  # 需要实现日期提取
    }
```

### 2. 情感分析数据处理
```python
def parse_sentiment_results(results_file):
    """解析情感分析结果"""
    sentiment_data = []

    with open(results_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = None

    for line in lines:
        if '正向报道列表' in line:
            current_section = 'positive'
        elif '负面报道列表' in line:
            current_section = 'negative'
        elif '中性报道列表' in line:
            current_section = 'neutral'
        elif '得分:' in line:
            # 解析文章标题和得分
            match = re.search(r'\d+\.\s+(.+?)\s+\(得分:\s+(-?\d+\.\d+)\)', line)
            if match:
                title = match.group(1).strip()
                score = float(match.group(2))

                sentiment_data.append({
                    'title': title,
                    'sentiment': current_section,
                    'raw_score': score,
                    'converted_score': (score + 1) * 5  # 转换到0-10范围
                })

    return sentiment_data
```

## 数据插入策略

### 1. 先插入corpus表数据
```sql
INSERT INTO corpus (title, content, source, media_name, type, file_path, publish_date)
VALUES (?, ?, ?, ?, ?, ?, ?);
```

### 2. 再插入sentiment_analysis表数据
```sql
INSERT INTO sentiment_analysis (
    corpus_id, sentiment, sentiment_score, confidence,
    positive_rate, negative_rate, neutral_rate,
    emotion_joy, emotion_trust, emotion_fear, emotion_surprise
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
);
```

## 注意事项

1. **情感得分转换**：原始得分范围为-1到1，需要转换为0-10范围
2. **日期处理**：需要从文件名或内容中提取发布日期
3. **图片URL处理**：如果文章包含图片，设置image_url字段
4. **数据关联**：通过文章标题关联corpus和sentiment_analysis表
5. **编码处理**：确保UTF-8编码正确处理中文字符

## 数据验证建议

1. 检查必填字段是否为空
2. 验证情感得分范围是否正确
3. 确保corpus_id关联正确
4. 检查日期格式有效性
5. 统计各类数据的数量是否匹配原始文件