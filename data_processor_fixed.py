#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理脚本：将爬取的数据解析并保存到MySQL数据库
基于init.sql中的表结构设计
"""

import os
import re
import json
import sys
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

# 尝试导入MySQL连接器
try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("错误: 未找到mysql-connector-python包")
    print("请运行: pip install mysql-connector-python")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, db_config: Dict):
        """初始化数据处理器"""
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect_db(self):
        """连接数据库"""
        try:
            logger.info(f"正在连接数据库 {self.db_config['database']}...")
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info("数据库连接成功")

            # 测试连接
            self.cursor.execute("SELECT 1")
            logger.info("数据库连接测试通过")

        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def disconnect_db(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
        logger.info("数据库连接已断开")

    def parse_text_file(self, file_path: str) -> Optional[Dict]:
        """解析文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取标题
            title_match = re.search(r'标题: (.+)', content)
            title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

            # 提取URL
            url_match = re.search(r'网址: (.+)', content)
            url = url_match.group(1).strip() if url_match else ""

            # 提取正文内容（移除标题、网址等元信息）
            text_content = content

            # 移除标题和网址行
            text_content = re.sub(r'标题: .+\n网址: .+\n\n', '', text_content)

            # 移除图片列表部分
            text_content = re.sub(r'图片列表:.*$', '', text_content, flags=re.DOTALL)

            # 移除特殊部分（如Specials, Videos等）
            text_content = re.sub(r'\n(?:Specials|Videos)\n.*$', '', text_content, flags=re.DOTALL)

            # 提取发布日期（尝试从内容中提取）
            publish_date = self.extract_date_from_content(text_content)

            # 检查是否包含图片
            has_images = '图片列表:' in content

            return {
                'title': title,
                'content': text_content.strip(),
                'source': 'china',  # 默认为中国
                'media_name': 'China Daily',  # 默认媒体
                'type': 'text',
                'file_path': file_path,
                'image_url': f"images/{title}_1.jpg" if has_images else None,
                'video_url': None,
                'publish_date': publish_date
            }

        except Exception as e:
            logger.error(f"解析文件 {file_path} 失败: {e}")
            return None

    def extract_date_from_content(self, content: str) -> Optional[date]:
        """从内容中提取日期"""
        # 尝试匹配日期格式
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}\.\d{1,2}\.\d{1,2})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
                    elif '-' in match.group(1):
                        return datetime.strptime(match.group(1), '%Y-%m-%d').date()
                except ValueError:
                    continue

        return None

    def parse_sentiment_results(self, results_file: str) -> List[Dict]:
        """解析情感分析结果"""
        sentiment_data = []

        try:
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
                elif '得分:' in line and current_section:
                    # 解析文章标题和得分
                    match = re.search(r'\d+\.\s+(.+?)\s+\(得分:\s+(-?\d+\.\d+)\)', line)
                    if match:
                        title = match.group(1).strip()
                        raw_score = float(match.group(2))

                        # 将-1到1范围的得分转换为0-10范围
                        converted_score = round((raw_score + 1) * 5, 2)

                        sentiment_data.append({
                            'title': title,
                            'sentiment': current_section,
                            'sentiment_score': converted_score,
                            'confidence': 85.0,  # 默认置信度
                            'positive_rate': 90.0 if current_section == 'positive' else (5.0 if current_section == 'negative' else 50.0),
                            'negative_rate': 5.0 if current_section == 'positive' else (90.0 if current_section == 'negative' else 25.0),
                            'neutral_rate': 5.0 if current_section == 'positive' else (5.0 if current_section == 'negative' else 25.0),
                            'emotion_joy': 80.0 if current_section == 'positive' else 10.0,
                            'emotion_trust': 75.0 if current_section == 'positive' else 15.0,
                            'emotion_fear': 10.0 if current_section == 'positive' else 70.0,
                            'emotion_surprise': 20.0 if current_section == 'positive' else 30.0
                        })

        except Exception as e:
            logger.error(f"解析情感分析结果失败: {e}")

        return sentiment_data

    def find_corpus_id_by_title(self, title: str) -> Optional[int]:
        """通过标题查找corpus表中的ID"""
        try:
            query = "SELECT id FROM corpus WHERE title = %s LIMIT 1"
            self.cursor.execute(query, (title,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            logger.error(f"查找corpus ID失败: {e}")
            return None

    def insert_corpus_data(self, corpus_data: Dict) -> Optional[int]:
        """插入corpus表数据"""
        try:
            query = """
            INSERT INTO corpus (
                title, content, source, media_name, type,
                file_path, image_url, video_url, publish_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                corpus_data['title'],
                corpus_data['content'],
                corpus_data['source'],
                corpus_data['media_name'],
                corpus_data['type'],
                corpus_data['file_path'],
                corpus_data['image_url'],
                corpus_data['video_url'],
                corpus_data['publish_date']
            )

            self.cursor.execute(query, values)
            self.conn.commit()

            # 获取插入的ID
            return self.cursor.lastrowid

        except Error as e:
            logger.error(f"插入corpus数据失败: {e}")
            self.conn.rollback()
            return None

    def insert_sentiment_data(self, sentiment_data: Dict, corpus_id: int):
        """插入sentiment_analysis表数据"""
        try:
            query = """
            INSERT INTO sentiment_analysis (
                corpus_id, sentiment, sentiment_score, confidence,
                positive_rate, negative_rate, neutral_rate,
                emotion_joy, emotion_trust, emotion_fear, emotion_surprise
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                corpus_id,
                sentiment_data['sentiment'],
                sentiment_data['sentiment_score'],
                sentiment_data['confidence'],
                sentiment_data['positive_rate'],
                sentiment_data['negative_rate'],
                sentiment_data['neutral_rate'],
                sentiment_data['emotion_joy'],
                sentiment_data['emotion_trust'],
                sentiment_data['emotion_fear'],
                sentiment_data['emotion_surprise']
            )

            self.cursor.execute(query, values)
            self.conn.commit()

        except Error as e:
            logger.error(f"插入sentiment数据失败: {e}")
            self.conn.rollback()

    def process_text_files(self, texts_dir: str = "texts"):
        """处理所有文本文件"""
        logger.info(f"开始处理文本文件目录: {texts_dir}")

        if not os.path.exists(texts_dir):
            logger.error(f"文本文件目录不存在: {texts_dir}")
            return

        processed_count = 0
        error_count = 0

        for filename in os.listdir(texts_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(texts_dir, filename)

                try:
                    corpus_data = self.parse_text_file(file_path)
                    if corpus_data:
                        corpus_id = self.insert_corpus_data(corpus_data)
                        if corpus_id:
                            processed_count += 1
                            logger.info(f"处理成功: {filename} (ID: {corpus_id})")
                        else:
                            error_count += 1
                            logger.error(f"插入失败: {filename}")
                    else:
                        error_count += 1
                        logger.error(f"解析失败: {filename}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"处理文件 {filename} 时发生错误: {e}")

        logger.info(f"文本文件处理完成。成功: {processed_count}, 失败: {error_count}")

    def process_sentiment_results(self, results_file: str = "text_sentiment_analysis_results.txt"):
        """处理情感分析结果"""
        logger.info(f"开始处理情感分析结果: {results_file}")

        if not os.path.exists(results_file):
            logger.error(f"情感分析结果文件不存在: {results_file}")
            return

        sentiment_data = self.parse_sentiment_results(results_file)
        processed_count = 0
        error_count = 0

        for data in sentiment_data:
            try:
                corpus_id = self.find_corpus_id_by_title(data['title'])
                if corpus_id:
                    self.insert_sentiment_data(data, corpus_id)
                    processed_count += 1
                    logger.info(f"情感数据插入成功: {data['title']} (corpus_id: {corpus_id})")
                else:
                    error_count += 1
                    logger.warning(f"未找到对应的corpus记录: {data['title']}")

            except Exception as e:
                error_count += 1
                logger.error(f"处理情感数据 {data['title']} 时发生错误: {e}")

        logger.info(f"情感分析结果处理完成。成功: {processed_count}, 失败: {error_count}")

    def process_all_data(self):
        """处理所有数据"""
        logger.info("开始数据处理流程")

        try:
            self.connect_db()

            # 1. 处理文本文件
            self.process_text_files()

            # 2. 处理情感分析结果
            self.process_sentiment_results()

            logger.info("数据处理流程完成")

        except Exception as e:
            logger.error(f"数据处理流程失败: {e}")
        finally:
            self.disconnect_db()


def main():
    """主函数"""
    print("数据处理器启动...")

    # 数据库配置（根据您的设置修改）
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '1234',
        'database': 'public-opinion-analysis-system',
        'charset': 'utf8mb4'
    }

    # 验证配置
    if not db_config['password']:
        print("警告: 数据库密码为空")

    print(f"数据库: {db_config['database']}")
    print(f"主机: {db_config['host']}")
    print(f"用户: {db_config['user']}")

    # 创建数据处理器
    processor = DataProcessor(db_config)

    # 处理所有数据
    try:
        processor.process_all_data()
        print("数据处理完成!")
    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()