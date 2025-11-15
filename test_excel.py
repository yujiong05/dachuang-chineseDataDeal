import pandas as pd
import sys

def test_excel_reading(excel_path):
    """
    测试Excel文件的读取和列识别功能
    """
    print(f"正在测试Excel文件: {excel_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        # 打印DataFrame的基本信息
        print(f"\n文件中共有 {len(df)} 行数据")
        print(f"列名: {list(df.columns)}")
        
        # 移除全空行
        df_cleaned = df.dropna(how='all')
        print(f"移除全空行后剩余 {len(df_cleaned)} 行数据")
        
        # 检查可能的标题和URL列
        possible_title_cols = ['标题', '文章标题', 'title', 'Title', '字段1_文本_文本']
        possible_url_cols = ['网址', '链接', 'url', 'URL', 'link', 'Link', '字段1_链接_链接']
        
        title_col = None
        for col in possible_title_cols:
            if col in df.columns:
                title_col = col
                break
        
        url_col = None
        for col in possible_url_cols:
            if col in df.columns:
                url_col = col
                break
        
        if title_col and url_col:
            print(f"\n成功识别标题列: {title_col}")
            print(f"成功识别URL列: {url_col}")
            
            # 显示前5行有效数据
            valid_data = df_cleaned.dropna(subset=[title_col, url_col], how='any')
            print(f"\n有效数据行数: {len(valid_data)}")
            print("\n前5行有效数据:")
            for i, (idx, row) in enumerate(valid_data.head(5).iterrows()):
                title = row[title_col]
                url = row[url_col]
                print(f"{i+1}. 标题: {title}")
                print(f"   URL: {url}")
                print("-" * 50)
        else:
            if not title_col:
                print(f"\n错误: 未能识别标题列，可用列: {list(df.columns)}")
            if not url_col:
                print(f"\n错误: 未能识别URL列，可用列: {list(df.columns)}")
    
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "各文章网址.xlsx"
    
    test_excel_reading(excel_path) 