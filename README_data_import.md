# 数据导入指南

## 概述

本指南介绍如何将爬取的情感分析数据导入到MySQL数据库中，严格按照init.sql中定义的表结构进行数据映射。

## 文件说明

1. **setup_database.py** - 数据库初始化脚本
2. **data_processor.py** - 数据处理和导入脚本
3. **data_mapping_guide.md** - 数据映射详细说明

## 使用步骤

### 1. 环境准备

```bash
# 安装依赖
pip install mysql-connector-python
```

### 2. 修改数据库配置

编辑 `setup_database.py` 和 `data_processor.py` 中的数据库配置：

```python
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_actual_password',  # 修改为实际密码
    'charset': 'utf8mb4'
}
```

### 3. 初始化数据库

```bash
python setup_database.py
```

此脚本将：
- 创建 `sentiment_analysis` 数据库
- 创建所有必要的表（基于init.sql）
- 创建视图和索引

### 4. 导入数据

```bash
python data_processor.py
```

此脚本将：
- 解析texts文件夹中的所有文本文件
- 解析text_sentiment_analysis_results.txt中的情感分析结果
- 将数据插入到相应的表中

## 数据映射说明

### corpus表数据来源

- **texts文件夹中的.txt文件**
  - 标题：从文件内容提取
  - 内容：正文部分（排除元数据）
  - 来源：默认为'china'
  - 媒体名称：默认为'China Daily'
  - 类型：'text'
  - 文件路径：相对路径
  - 图片URL：如果包含图片

### sentiment_analysis表数据来源

- **text_sentiment_analysis_results.txt**
  - 情感分类：positive/neutral/negative
  - 情感得分：转换为0-10范围
  - 各种情感比例：基于分类设置默认值
  - 通过标题关联到corpus表

## 数据处理规则

### 1. 情感得分转换
```
原始得分范围: -1 到 1
目标得分范围: 0 到 10
转换公式: (原始得分 + 1) * 5
```

### 2. 情感比例设置
- **正向报道**：
  - positive_rate: 90%
  - negative_rate: 5%
  - neutral_rate: 5%

- **负面报道**：
  - positive_rate: 5%
  - negative_rate: 90%
  - neutral_rate: 5%

- **中性报道**：
  - positive_rate: 50%
  - negative_rate: 25%
  - neutral_rate: 25%

### 3. 日期提取
从文本内容中尝试提取日期，支持多种格式：
- 2024年1月15日
- 2024-01-15
- 01/15/2024
- 2024.01.15

## 验证数据导入

### 1. 检查corpus表数据量
```sql
SELECT COUNT(*) as total_articles FROM corpus;
SELECT source, COUNT(*) FROM corpus GROUP BY source;
```

### 2. 检查sentiment_analysis表数据量
```sql
SELECT COUNT(*) as total_sentiments FROM sentiment_analysis;
SELECT sentiment, COUNT(*) FROM sentiment_analysis GROUP BY sentiment;
```

### 3. 检查数据关联
```sql
SELECT c.id, c.title, sa.sentiment, sa.sentiment_score
FROM corpus c
LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
LIMIT 10;
```

## 常见问题解决

### 1. 编码问题
确保所有文本文件使用UTF-8编码保存。

### 2. 数据库连接失败
- 检查MySQL服务是否启动
- 验证用户名和密码
- 确认网络连接正常

### 3. 重复数据导入
脚本会尝试查找已存在的记录，避免重复插入。

### 4. 日期格式错误
如果日期提取失败，publish_date字段将设置为NULL。

## 数据库结构

### 主要表结构

1. **corpus** - 语料库主表
2. **sentiment_analysis** - 情感分析结果
3. **keywords** - 关键词表
4. **polish_records** - 润色记录表
5. **statistics** - 统计数据表
6. **hot_keywords** - 热门关键词表
7. **media_activity** - 媒体活跃度表
8. **operation_logs** - 操作日志表

### 视图

1. **v_corpus_statistics** - 语料库统计视图
2. **v_sentiment_statistics** - 情感分析统计视图

## 性能优化建议

1. 定期执行 `ANALYZE TABLE` 更新统计信息
2. 对大量数据导入时考虑禁用索引
3. 使用批量插入提高导入效率
4. 定期备份数据库

## 后续使用

数据导入完成后，您可以通过SQL查询进行各种分析：

```sql
-- 按月统计情感分析结果
SELECT
    DATE_FORMAT(c.publish_date, '%Y-%m') as month,
    sa.sentiment,
    COUNT(*) as count
FROM corpus c
JOIN sentiment_analysis sa ON c.id = sa.corpus_id
GROUP BY month, sa.sentiment
ORDER BY month DESC;
```