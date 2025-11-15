import os
import re
import jieba
import pandas as pd
from collections import Counter

# 文件夹路径
texts_folder = 'texts'
output_file = '词频分析结果.xlsx'

# 常见中文停用词
chinese_stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', 
                         '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', 
                         '自己', '这', '这个', '来', '什么', '那', '可以', '中', '大', '为', '他', '她',
                         '标题', '网址', '图片', '列表', '视频', '尺寸', '所示'])

# 常见英文停用词
english_stopwords = set(['the', 'and', 'of', 'to', 'in', 'for', 'is', 'on', 'that', 'with', 'by', 
                        'at', 'as', 'it', 'be', 'this', 'an', 'are', 'was', 'from', 'has', 'have', 
                        'will', 'its', 'which', 'not', 'or', 'a', 'also', 'can', 'their', 'they', 
                        'said', 'were', 'been', 'would', 'more', 'we', 'other', 'year', 'all', 
                        'had', 'our', 'new', 'one', 'two', 'his', 'her', 'him', 'she', 'he', 'i'])

# 用于存储所有文章的内容
all_text = ''

# 处理文本文件
def extract_main_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查文件是否包含中文
        if not re.search(r'[\u4e00-\u9fa5]', content):
            return ""  # 如果没有中文，则返回空字符串
            
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
    print("没有找到有效的中文文本文件，程序退出")
    exit()

# 使用jieba进行中文分词
print("正在进行中文分词...")
words = jieba.cut(all_text)
words_list = list(words)  # 将生成器转换为列表

# 过滤停用词和单字词
valid_words = []
for word in words_list:
    word = word.strip()
    # 如果是中文词且长度大于1且不是停用词
    if re.search(r'[\u4e00-\u9fa5]', word) and len(word) > 1 and word not in chinese_stopwords:
        valid_words.append(word)
    # 如果是英文词且长度大于2且不是停用词 
    elif re.match(r'^[a-zA-Z]+$', word) and len(word) > 2 and word.lower() not in english_stopwords:
        valid_words.append(word)

print(f"有效词数量: {len(valid_words)}")

# 统计词频
word_count = Counter(valid_words)
total_words = sum(word_count.values())

print(f"词汇总数: {total_words}")
print(f"独立词汇数: {len(word_count)}")

# 获取频率最高的词
top_words = word_count.most_common(50)  # 取50个，确保至少有40个

# 准备数据
data = {
    '词语': [],
    '出现次数': [],
    '频率 (%)': [],
    '语言': []
}

for word, count in top_words:
    if count < 3:  # 出现次数太少的不考虑
        continue
    frequency = (count / total_words) * 100
    data['词语'].append(word)
    data['出现次数'].append(count)
    data['频率 (%)'].append(round(frequency, 4))
    # 判断词语是中文还是英文
    if re.search(r'[\u4e00-\u9fa5]', word):
        data['语言'].append('中文')
    else:
        data['语言'].append('英文')

# 创建DataFrame
df = pd.DataFrame(data)

# 分别获取中文和英文词频
df_chinese = df[df['语言'] == '中文']
df_english = df[df['语言'] == '英文']

print("保存结果到Excel...")

try:
    # 使用ExcelWriter保存到不同的sheet
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='所有词频', index=False)
        df_chinese.to_excel(writer, sheet_name='中文词频', index=False)
        df_english.to_excel(writer, sheet_name='英文词频', index=False)
    print(f'词频分析完成，结果已保存到 {output_file}')
except Exception as e:
    print(f"保存Excel文件时出错: {e}")
    
    # 尝试保存为CSV文件作为备选
    try:
        df.to_csv('词频分析结果.csv', index=False, encoding='utf-8-sig')
        print("词频分析结果已保存为CSV文件")
    except Exception as e2:
        print(f"保存CSV文件也失败: {e2}") 