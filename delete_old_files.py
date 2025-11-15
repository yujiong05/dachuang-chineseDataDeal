import os
import re
from datetime import datetime
import shutil

def extract_date_from_url(url):
    # 从URL中提取日期，格式如：2002-12/17
    match = re.search(r'(\d{4}-\d{2}/\d{2})', url)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, '%Y-%m/%d')
    return None

def get_media_files_list(file_path):
    media_files = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 查找文件末尾的图片和视频列表
        media_section = re.search(r'图片列表：(.*?)\n视频列表：(.*?)$', content, re.DOTALL)
        if media_section:
            images = media_section.group(1).strip().split('\n')
            videos = media_section.group(2).strip().split('\n')
            media_files.extend([img.strip() for img in images if img.strip()])
            media_files.extend([vid.strip() for vid in videos if vid.strip()])
    return media_files

def main():
    texts_dir = 'texts'
    images_dir = 'images'
    videos_dir = 'videos'
    
    # 确保目录存在
    for dir_path in [images_dir, videos_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # 遍历texts目录中的所有文件
    for filename in os.listdir(texts_dir):
        if not filename.endswith('.txt'):
            continue
            
        file_path = os.path.join(texts_dir, filename)
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取URL
        url_match = re.search(r'网址: (.*?)\n', content)
        if not url_match:
            continue
            
        url = url_match.group(1)
        date = extract_date_from_url(url)
        
        if date and date.year < 2015:
            print(f"删除文件: {filename} (日期: {date.strftime('%Y-%m-%d')})")
            
            # 获取关联的媒体文件
            media_files = get_media_files_list(file_path)
            
            # 删除文本文件
            os.remove(file_path)
            
            # 删除关联的媒体文件
            for media_file in media_files:
                # 尝试在images目录中删除
                image_path = os.path.join(images_dir, media_file)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"  删除图片: {media_file}")
                
                # 尝试在videos目录中删除
                video_path = os.path.join(videos_dir, media_file)
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"  删除视频: {media_file}")

if __name__ == '__main__':
    main() 