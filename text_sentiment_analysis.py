import os
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# 下载VADER词典（用于情感分析）
nltk.download('vader_lexicon', quiet=True)

# 初始化情感分析器
sia = SentimentIntensityAnalyzer()

# 统计变量
positive = 0
negative = 0
neutral = 0
positive_articles = []
negative_articles = []
neutral_articles = []

# 遍历texts文件夹中的所有txt文件
for file in os.listdir('texts'):
    if file.endswith('.txt'):
        file_path = os.path.join('texts', file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 使用文件名作为标题
                title = file.replace('.txt', '')
                
                # 进行情感分析
                scores = sia.polarity_scores(content)
                compound_score = scores['compound']
                
                # 根据复合得分分类
                if compound_score >= 0.05:
                    positive += 1
                    positive_articles.append((title, compound_score))
                elif compound_score <= -0.5:
                    negative += 1
                    negative_articles.append((title, compound_score))
                else:
                    neutral += 1
                    neutral_articles.append((title, compound_score))
        except Exception as e:
            print(f"处理文件 {file} 时出错: {e}")

# 按情感得分排序
positive_articles.sort(key=lambda x: x[1], reverse=True)
negative_articles.sort(key=lambda x: x[1])
neutral_articles.sort(key=lambda x: abs(x[1]))

# 打印汇总结果
print("=" * 60)
print("情感分析汇总结果")
print("=" * 60)
print(f"正向报道: {positive}篇")
print(f"负面报道: {negative}篇")
print(f"中性报道: {neutral}篇")
print(f"总计: {positive + negative + neutral}篇")
print("=" * 60)

# 保存详细分析结果到文件
with open('text_sentiment_analysis_results.txt', 'w', encoding='utf-8-sig') as f:
    f.write("情感分析详细结果\n")
    f.write("==============\n\n")
    
    f.write(f"汇总统计:\n")
    f.write(f"正向报道: {positive}篇\n")
    f.write(f"负面报道: {negative}篇\n")
    f.write(f"中性报道: {neutral}篇\n")
    f.write(f"总计: {positive + negative + neutral}篇\n\n")
    
    f.write("正向报道列表 (共{}篇):\n".format(positive))
    for i, (title, score) in enumerate(positive_articles, 1):
        f.write(f"{i}. {title} (得分: {score:.3f})\n")
    
    f.write("\n负面报道列表 (共{}篇):\n".format(negative))
    for i, (title, score) in enumerate(negative_articles, 1):
        f.write(f"{i}. {title} (得分: {score:.3f})\n")
    
    f.write("\n中性报道列表 (共{}篇):\n".format(neutral))
    for i, (title, score) in enumerate(neutral_articles, 1):
        f.write(f"{i}. {title} (得分: {score:.3f})\n")

print("\n详细分析结果已保存到 text_sentiment_analysis_results.txt")

# 显示最积极的5篇报道
print("\n最积极的5篇报道:")
print("-" * 60)
for i, (title, score) in enumerate(positive_articles[:5], 1):
    print(f"{i}. {title}")
    print(f"   得分: {score:.3f}")

# 显示最消极的5篇报道
print("\n最消极的5篇报道:")
print("-" * 60)
for i, (title, score) in enumerate(negative_articles[:5], 1):
    print(f"{i}. {title}")
    print(f"   得分: {score:.3f}") 