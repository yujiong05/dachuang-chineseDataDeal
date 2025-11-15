import pandas as pd

# 读取Excel文件
file_path = '词频分析结果.xlsx'

# 读取中文词频
df_chinese = pd.read_excel(file_path, sheet_name='中文词频')
print("===== 中文词频分析结果 =====")
print(df_chinese.head(40))
print("\n")

# 读取英文词频
df_english = pd.read_excel(file_path, sheet_name='英文词频')
print("===== 英文词频分析结果 =====")
print(df_english.head(40)) 