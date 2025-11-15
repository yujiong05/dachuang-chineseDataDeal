import os
import sys
from crawler import WebCrawler

def main():
    print("=" * 50)
    print("网页内容爬取工具")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        # 列出当前目录下的所有Excel文件
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') or f.endswith('.xls')]
        
        if not excel_files:
            print("当前目录下没有找到Excel文件！")
            excel_file = input("请输入Excel文件路径: ")
        elif len(excel_files) == 1:
            excel_file = excel_files[0]
            print(f"找到Excel文件: {excel_file}")
            confirm = input(f"是否使用此文件? (y/n, 默认y): ")
            if confirm.lower() not in ['', 'y', 'yes']:
                excel_file = input("请输入Excel文件路径: ")
        else:
            print("找到以下Excel文件:")
            for i, file in enumerate(excel_files):
                print(f"{i+1}. {file}")
            
            choice = input(f"请选择要使用的文件 (1-{len(excel_files)}, 或输入其他路径): ")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(excel_files):
                    excel_file = excel_files[idx]
                else:
                    excel_file = input("请输入Excel文件路径: ")
            except ValueError:
                excel_file = choice
    
    # 确认文件存在
    if not os.path.exists(excel_file):
        print(f"错误: 文件 '{excel_file}' 不存在！")
        return
    
    print(f"\n开始处理Excel文件: {excel_file}")
    print("文本将保存在 'texts' 文件夹")
    print("图片将保存在 'images' 文件夹")
    print("视频将保存在 'videos' 文件夹")
    print("\n开始爬取内容，详细信息请查看 crawler.log 日志文件...")
    
    # 创建爬虫实例并开始爬取
    crawler = WebCrawler(excel_file)
    crawler.start_crawling()

if __name__ == "__main__":
    main() 