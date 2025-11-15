import os
import re
import pandas as pd
from collections import Counter

# 文件夹路径
texts_folder = 'texts'
output_file = '英文词频分析结果.xlsx'

# 英文停用词（扩展更多常见停用词）
english_stopwords = set(['the', 'and', 'of', 'to', 'in', 'for', 'is', 'on', 'that', 'with', 'by', 
                        'at', 'as', 'it', 'be', 'this', 'an', 'are', 'was', 'from', 'has', 'have', 
                        'will', 'its', 'which', 'not', 'or', 'a', 'also', 'can', 'their', 'they', 
                        'said', 'were', 'been', 'would', 'more', 'we', 'other', 'year', 'all', 
                        'had', 'our', 'new', 'one', 'two', 'his', 'her', 'him', 'she', 'he', 'i',
                        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                        'have', 'has', 'had', 'do', 'does', 'did', 'but', 'if', 'or', 'because',
                        'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
                        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
                        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
                        'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                        'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'some', 'such',
                        'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'now'])

# 用于存储所有文章的内容
all_text = ''

# 处理文本文件
def extract_main_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        
        # 跳过前面的标题和网址
        start_line = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('标题:') and not line.startswith('网址:'):
                start_line = i
                break
        
        # 找到图片列表的位置
        end_line = len(lines)
        for i, line in enumerate(lines):
            if '图片列表:' in line or '视频列表:' in line:
                end_line = i
                break
        
        # 提取正文
        main_content = '\n'.join(lines[start_line:end_line])
        return main_content
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return ""

print(f"开始处理 {texts_folder} 文件夹中的文本文件...")

# 处理所有文本文件
file_count = 0
for filename in os.listdir(texts_folder):
    if filename.endswith('.txt'):
        file_path = os.path.join(texts_folder, filename)
        content = extract_main_content(file_path)
        if content:  # 确保内容不为空
            all_text += content + '\n'
            file_count += 1

print(f"成功处理了 {file_count} 个文本文件")

if file_count == 0:
    print("没有找到有效的文本文件，程序退出")
    exit()

# 提取英文词汇
print("正在提取和分析英文词汇...")
english_text = re.findall(r'\b[a-zA-Z]+\b', all_text)
valid_english_words = []

for word in english_text:
    word = word.lower().strip()
    if len(word) > 1 and word not in english_stopwords:  # 只保留长度大于1的词且不在停用词中
        valid_english_words.append(word)

print(f"有效英文词数量: {len(valid_english_words)}")

# 统计词频
word_count = Counter(valid_english_words)
total_words = sum(word_count.values())

print(f"词汇总数: {total_words}")
print(f"独立词汇数: {len(word_count)}")

# 获取频率最高的词
top_words = word_count.most_common(100)  # 取100个，确保至少有40个

# 准备数据
data = {
    '词语': [],
    '出现次数': [],
    '频率 (%)': [],
    '累计频率 (%)': []
}

cumulative_frequency = 0
for word, count in top_words:
    if count < 3:  # 出现次数太少的不考虑
        continue
    frequency = (count / total_words) * 100
    cumulative_frequency += frequency
    
    data['词语'].append(word)
    data['出现次数'].append(count)
    data['频率 (%)'].append(round(frequency, 4))
    data['累计频率 (%)'].append(round(cumulative_frequency, 4))

# 创建DataFrame
df = pd.DataFrame(data)

# 按出现次数排序
df_by_count = df.sort_values(by='出现次数', ascending=False)

# 按词语字母排序
df_alphabetical = df.sort_values(by='词语')

print("保存结果到Excel...")

try:
    # 使用ExcelWriter保存到不同的sheet
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_by_count.to_excel(writer, sheet_name='按频率排序', index=False)
        df_alphabetical.to_excel(writer, sheet_name='按字母排序', index=False)
    print(f'词频分析完成，结果已保存到 {output_file}')
except Exception as e:
    print(f"保存Excel文件时出错: {e}")
    
    # 尝试保存为CSV文件作为备选
    try:
        df_by_count.to_csv('英文词频分析结果.csv', index=False, encoding='utf-8-sig')
        print("词频分析结果已保存为CSV文件")
    except Exception as e2:
        print(f"保存CSV文件也失败: {e2}") 