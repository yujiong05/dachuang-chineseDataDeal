#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证脚本：检查数据导入结果
"""

import mysql.connector
from mysql.connector import Error
import sys

def validate_data():
    """验证数据导入结果"""

    try:
        # 数据库配置
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '1234',
            'database': 'public-opinion-analysis-system',
            'charset': 'utf8mb4'
        }

        # 连接数据库
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print("=== 数据导入验证报告 ===\n")

        # 1. 检查corpus表总记录数
        cursor.execute("SELECT COUNT(*) FROM corpus")
        corpus_count = cursor.fetchone()[0]
        print(f"📊 corpus表总记录数: {corpus_count}")

        # 2. 检查sentiment_analysis表总记录数
        cursor.execute("SELECT COUNT(*) FROM sentiment_analysis")
        sentiment_count = cursor.fetchone()[0]
        print(f"📊 sentiment_analysis表总记录数: {sentiment_count}")

        # 3. 检查按来源统计
        print("\n📈 按来源统计:")
        cursor.execute("SELECT source, COUNT(*) FROM corpus GROUP BY source")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}篇")

        # 4. 检查按情感分类统计
        print("\n📈 情感分析结果统计:")
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

        # 5. 检查有内容记录的数量
        cursor.execute("SELECT COUNT(*) FROM corpus WHERE content IS NOT NULL AND content != ''")
        content_count = cursor.fetchone()[0]
        print(f"\n📝 有内容的记录数: {content_count}")

        # 6. 检查有发布日期的记录数
        cursor.execute("SELECT COUNT(*) FROM corpus WHERE publish_date IS NOT NULL")
        date_count = cursor.fetchone()[0]
        print(f"📅 有发布日期的记录数: {date_count}")

        # 7. 检查有图片的记录数
        cursor.execute("SELECT COUNT(*) FROM corpus WHERE image_url IS NOT NULL")
        image_count = cursor.fetchone()[0]
        print(f"🖼️ 有图片的记录数: {image_count}")

        # 8. 检查最近导入的记录
        print("\n📋 最近导入的10条记录:")
        cursor.execute("""
            SELECT id, title, source, publish_date, create_time
            FROM corpus
            ORDER BY id DESC
            LIMIT 10
        """)

        for row in cursor.fetchall():
            record_id, title, source, publish_date, create_time = row
            print(f"   ID:{record_id} | {source} | {title[:50]}... | {publish_date or '无日期'}")

        # 9. 检查情感分析关联情况
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

        print(f"\n🔗 情感分析关联情况:")
        print(f"   总文章数: {total_corpus}")
        print(f"   有情感分析的: {with_sentiment}")
        print(f"   无情感分析的: {without_sentiment}")

        if total_corpus > 0:
            coverage = (with_sentiment / total_corpus) * 100
            print(f"   情感分析覆盖率: {coverage:.1f}%")

        # 10. 检查示例数据
        print("\n🔍 数据示例（前3条）:")
        cursor.execute("""
            SELECT
                c.id, c.title, c.content, c.source, c.type,
                sa.sentiment, sa.sentiment_score
            FROM corpus c
            LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
            WHERE c.id <= 3
            ORDER BY c.id
        """)

        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"\n   记录 {i}:")
            print(f"     ID: {row[0]}")
            print(f"     标题: {row[1]}")
            print(f"     来源: {row[3]}")
            print(f"     类型: {row[4]}")
            print(f"     情感: {row[5]}")
            print(f"     得分: {row[6]}")
            print(f"     内容长度: {len(row[2] or '')} 字符")

        # 11. 数据质量检查
        print("\n🔧 数据质量检查:")

        # 检查重复标题
        cursor.execute("""
            SELECT title, COUNT(*) as count
            FROM corpus
            GROUP BY title
            HAVING count > 1
            LIMIT 5
        """)

        duplicates = cursor.fetchall()
        if duplicates:
            print("   ⚠️ 发现重复标题:")
            for title, count in duplicates:
                print(f"     '{title}': {count}次")
        else:
            print("   ✅ 无重复标题")

        # 检查空标题
        cursor.execute("SELECT COUNT(*) FROM corpus WHERE title IS NULL OR title = ''")
        empty_title = cursor.fetchone()[0]
        if empty_title > 0:
            print(f"   ⚠️ {empty_title}条记录标题为空")
        else:
            print("   ✅ 所有记录都有标题")

        print(f"\n✅ 验证完成！共导入 {corpus_count} 篇文章，{sentiment_count} 条情感分析记录。")

    except Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    return True

if __name__ == "__main__":
    print("开始验证数据导入结果...")
    if validate_data():
        print("\n🎉 数据验证成功！")
    else:
        print("\n💥 数据验证失败！")
        sys.exit(1)