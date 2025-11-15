#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据验证脚本
"""

import mysql.connector
from mysql.connector import Error

def check_data():
    """检查数据导入结果"""

    try:
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '1234',
            'database': 'public-opinion-analysis-system',
            'charset': 'utf8mb4'
        }

        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print("=== 数据导入检查报告 ===")
        print()

        # 1. 检查corpus表总记录数
        cursor.execute("SELECT COUNT(*) FROM corpus")
        corpus_count = cursor.fetchone()[0]
        print(f"corpus表总记录数: {corpus_count}")

        # 2. 检查sentiment_analysis表总记录数
        cursor.execute("SELECT COUNT(*) FROM sentiment_analysis")
        sentiment_count = cursor.fetchone()[0]
        print(f"sentiment_analysis表总记录数: {sentiment_count}")

        # 3. 按来源统计
        print()
        print("按来源统计:")
        cursor.execute("SELECT source, COUNT(*) FROM corpus GROUP BY source")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}篇")

        # 4. 情感分析结果统计
        print()
        print("情感分析结果统计:")
        cursor.execute("""
            SELECT sa.sentiment, COUNT(*) as count, AVG(sa.sentiment_score) as avg_score
            FROM sentiment_analysis sa
            GROUP BY sa.sentiment
            ORDER BY count DESC
        """)

        for row in cursor.fetchall():
            sentiment, count, avg_score = row
            if sentiment:
                print(f"   {sentiment}: {count}篇 (平均得分: {avg_score:.2f})")

        # 5. 内容统计
        cursor.execute("SELECT COUNT(*) FROM corpus WHERE content IS NOT NULL AND content != ''")
        content_count = cursor.fetchone()[0]
        print(f"有内容的记录数: {content_count}")

        cursor.execute("SELECT COUNT(*) FROM corpus WHERE publish_date IS NOT NULL")
        date_count = cursor.fetchone()[0]
        print(f"有发布日期的记录数: {date_count}")

        cursor.execute("SELECT COUNT(*) FROM corpus WHERE image_url IS NOT NULL")
        image_count = cursor.fetchone()[0]
        print(f"有图片的记录数: {image_count}")

        # 6. 情感分析关联情况
        print()
        print("情感分析关联情况:")
        cursor.execute("""
            SELECT
                COUNT(*) as total_corpus,
                COUNT(sa.corpus_id) as with_sentiment,
                (COUNT(*) - COUNT(sa.corpus_id)) as without_sentiment
            FROM corpus c
            LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
        """)

        corpus_stats = cursor.fetchone()
        total_corpus, with_sentiment, without_sentiment = corpus_stats

        print(f"总文章数: {total_corpus}")
        print(f"有情感分析的: {with_sentiment}")
        print(f"无情感分析的: {without_sentiment}")

        if total_corpus > 0:
            coverage = (with_sentiment / total_corpus) * 100
            print(f"情感分析覆盖率: {coverage:.1f}%")

        # 7. 示例数据
        print()
        print("前5条记录示例:")
        cursor.execute("""
            SELECT
                c.id, c.title, c.source, c.publish_date,
                sa.sentiment, sa.sentiment_score
            FROM corpus c
            LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
            ORDER BY c.id
            LIMIT 5
        """)

        for row in cursor.fetchall():
            record_id, title, source, publish_date, sentiment, score = row
            print(f"ID:{record_id} | {source} | {title[:40]}... | {sentiment}({score})")

        print()
        print("数据检查完成！")

    except Error as e:
        print(f"数据库错误: {e}")
        return False
    except Exception as e:
        print(f"检查失败: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    return True

if __name__ == "__main__":
    check_data()