import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin
import random
import logging
import json
from datetime import datetime
from io import BytesIO
from PIL import Image

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

class WebCrawler:
    def __init__(self, excel_path):
        """
        初始化爬虫类
        :param excel_path: Excel文件的路径
        """
        self.excel_path = excel_path
        
        # 创建保存数据的文件夹
        self.text_folder = 'texts'
        self.image_folder = 'images'
        self.video_folder = 'videos'
        
        os.makedirs(self.text_folder, exist_ok=True)
        os.makedirs(self.image_folder, exist_ok=True)
        os.makedirs(self.video_folder, exist_ok=True)
        
        # 进度文件路径
        self.progress_file = 'crawler_progress.json'
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 图片筛选配置
        self.min_image_width = 300  # 降低最小图片宽度，以捕获更多正文中的图片
        self.min_image_height = 200  # 降低最小图片高度
        
        # 正文识别配置
        self.article_selectors = [
            'article', '.article', '.content', '.post', '.entry', '.main-content', 
            '#content', '#article', '.story', '.detail', '.article-content',
            '.article-body', '.post-content', '.entry-content', '.main',
            '.text', '.body', '#main', '.container', '.wrapper'
        ]

        # 加载爬取进度
        self.completed_urls = self.load_progress()
    
    def load_progress(self):
        """
        加载已爬取的URL进度
        :return: 已完成URL的集合
        """
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    logging.info(f"已加载爬取进度，已完成 {len(progress_data)} 个URL")
                    return set(progress_data)
            except Exception as e:
                logging.error(f"加载进度文件失败: {str(e)}")
                return set()
        return set()
    
    def save_progress(self, url):
        """
        保存当前URL到进度文件
        :param url: 已完成爬取的URL
        """
        self.completed_urls.add(url)
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.completed_urls), f)
        except Exception as e:
            logging.error(f"保存进度文件失败: {str(e)}")
    
    def read_excel(self):
        """
        读取Excel文件
        :return: 包含标题和URL的DataFrame
        """
        try:
            df = pd.read_excel(self.excel_path)
            # 移除NaN值的行
            df = df.dropna(how='all')
            logging.info(f"成功读取Excel文件: {self.excel_path}")
            return df
        except Exception as e:
            logging.error(f"读取Excel文件失败: {str(e)}")
            return None
    
    def extract_article_content(self, soup):
        """
        从BeautifulSoup对象中提取文章正文内容
        :param soup: BeautifulSoup对象
        :return: 文章正文内容，以及正文的HTML容器元素
        """
        article_container = None
        
        # 尝试使用常见的文章容器选择器查找
        for selector in self.article_selectors:
            if selector.startswith('#'):
                container = soup.find(id=selector[1:])
            elif selector.startswith('.'):
                container = soup.find(class_=selector[1:])
            else:
                container = soup.find(selector)
            
            if container and container.text.strip():
                article_container = container
                break
        
        # 如果没有找到明确的文章容器，尝试更一般的方法
        if not article_container:
            # 查找含有大量文本的div
            divs = soup.find_all('div')
            if divs:
                # 按文本长度排序，取最长的div作为文章容器
                article_container = max(divs, key=lambda x: len(x.get_text(strip=True)) if x.get_text(strip=True) else 0)
        
        # 如果找到了容器，提取文本
        if article_container:
            # 移除脚本、样式、导航和页脚等无关元素
            for elem in article_container.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                elem.decompose()
            
            # 提取文本，保留段落结构
            paragraphs = []
            for p in article_container.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            
            return '\n\n'.join(paragraphs), article_container
        else:
            # 回退方法：提取所有<p>标签
            paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 30:  # 降低段落文本长度阈值，以包含更多内容
                    paragraphs.append(text)
            
            return '\n\n'.join(paragraphs), soup.find('body')  # 如果找不到更好的容器，使用body作为容器
    
    def download_text(self, url, title, saved_images=None, saved_videos=None):
        """
        下载并保存文本内容
        :param url: 网页URL
        :param title: 文章标题
        :param saved_images: 已保存的图片列表，用于添加到文本末尾
        :param saved_videos: 已保存的视频列表，用于添加到文本末尾
        :return: 是否成功，以及提取到的文章容器元素
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章正文内容和容器
            content, article_container = self.extract_article_content(soup)
            
            # 清理文件名，去除不合法字符
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            
            # 创建带有标题和网址的完整内容
            full_content = f"标题: {title}\n网址: {url}\n\n{content}"
            
            # 如果有保存的图片列表，添加到文本末尾
            if saved_images and len(saved_images) > 0:
                full_content += "\n\n图片列表:\n"
                for i, img_info in enumerate(saved_images):
                    full_content += f"{i+1}. {img_info['file_name']} - 尺寸: {img_info['display_width']}x{img_info['display_height']}\n"
            
            # 如果有保存的视频列表，添加到文本末尾
            if saved_videos and len(saved_videos) > 0:
                full_content += "\n\n视频列表:\n"
                for i, video_info in enumerate(saved_videos):
                    full_content += f"{i+1}. {video_info['file_name']}\n"
            
            # 保存文本文件
            file_path = os.path.join(self.text_folder, f"{safe_title}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            logging.info(f"已保存文本: {file_path}")
            return True, article_container
        except Exception as e:
            logging.error(f"下载文本失败 - {url}: {str(e)}")
            return False, None
    
    def get_display_size(self, img_tag):
        """
        获取图片在HTML中的显示尺寸
        :param img_tag: BeautifulSoup中的img标签
        :return: 宽度和高度的元组，如果无法获取则返回(0, 0)
        """
        # 首先尝试从width和height属性获取
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        # 如果属性中有值，尝试转换为整数
        try:
            if width and height:
                # 检查是否为数字或带px的字符串
                if isinstance(width, str) and 'px' in width:
                    width = width.replace('px', '').strip()
                if isinstance(height, str) and 'px' in height:
                    height = height.replace('px', '').strip()
                
                return (int(float(width)), int(float(height)))
        except (ValueError, TypeError):
            pass
        
        # 尝试从style属性获取宽高
        style = img_tag.get('style', '')
        if style:
            # 查找width和height样式
            width_match = re.search(r'width\s*:\s*(\d+)(px|%|rem|em)?', style)
            height_match = re.search(r'height\s*:\s*(\d+)(px|%|rem|em)?', style)
            
            if width_match and height_match:
                try:
                    width = int(width_match.group(1))
                    height = int(height_match.group(1))
                    return (width, height)
                except (ValueError, IndexError):
                    pass
        
        # 如果无法从HTML属性获取，返回0, 0
        return (0, 0)
    
    def find_background_images(self, soup):
        """
        查找页面中的背景图片
        :param soup: BeautifulSoup对象
        :return: 背景图片URL列表
        """
        background_images = []
        
        # 查找具有背景图片的元素
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            bg_match = re.search(r'background(?:-image)?\s*:\s*url\([\'"]?(.*?)[\'"]?\)', style)
            if bg_match:
                img_url = bg_match.group(1)
                if img_url and not any(pattern in img_url.lower() for pattern in ['icon', 'logo', 'banner', 'button', 'bg-', 'background']):
                    background_images.append(img_url)
        
        return background_images
    
    def download_images(self, url, title, article_container=None):
        """
        下载并保存图片
        :param url: 网页URL
        :param title: 文章标题
        :param article_container: 文章正文容器元素，如果提供则只提取该容器内的图片
        :return: 下载的图片数量和图片信息列表
        """
        try:
            # 如果没有提供文章容器，需要先获取网页内容
            if not article_container:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取文章正文内容和容器
                _, article_container = self.extract_article_content(soup)
            
            # 如果找到了文章容器，从容器中提取图片
            if article_container:
                img_tags = article_container.find_all('img')
                # 查找具有data-original-src属性的图片（有些网站使用这种方式延迟加载图片）
                img_tags.extend(article_container.find_all(attrs={"data-original-src": True}))
                # 查找具有data-lazy-src属性的图片
                img_tags.extend(article_container.find_all(attrs={"data-lazy-src": True}))
                
                # 查找背景图片
                background_images = self.find_background_images(article_container)
            else:
                # 如果没有找到文章容器，从整个网页提取图片
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                img_tags = soup.find_all('img')
                img_tags.extend(soup.find_all(attrs={"data-original-src": True}))
                img_tags.extend(soup.find_all(attrs={"data-lazy-src": True}))
                
                # 查找背景图片
                background_images = self.find_background_images(soup)
            
            # 清理文件名
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            
            count = 0
            saved_images = []  # 保存图片信息的列表
            
            # 处理常规img标签图片
            for i, img in enumerate(img_tags):
                try:
                    # 获取图片URL
                    img_url = img.get('src') or img.get('data-src') or img.get('data-original') or img.get('data-original-src') or img.get('data-lazy-src')
                    if not img_url:
                        continue
                    
                    # 处理相对URL
                    img_url = urljoin(url, img_url)
                    
                    # 过滤常见的小图标、广告等图片
                    if any(pattern in img_url.lower() for pattern in ['icon', 'logo']):
                        logging.info(f"跳过图标图片: {img_url}")
                        continue
                    
                    # 过滤广告类图片，但保留banner可能是文章的主图
                    if any(pattern in img_url.lower() for pattern in ['ad.', 'ad/', 'advert', 'advertisement']):
                        logging.info(f"跳过广告图片: {img_url}")
                        continue
                    
                    # 获取图片在HTML中的显示尺寸
                    display_width, display_height = self.get_display_size(img)
                    
                    # 如果没有获取到显示尺寸，尝试通过下载图片获取实际尺寸
                    if display_width == 0 or display_height == 0:
                        # 下载图片以检查实际尺寸
                        img_response = requests.get(img_url, headers=self.headers, timeout=10)
                        img_response.raise_for_status()
                        
                        try:
                            img_data = BytesIO(img_response.content)
                            img_obj = Image.open(img_data)
                            display_width, display_height = img_obj.size
                        except Exception:
                            # 如果无法获取尺寸，跳过此图片
                            logging.warning(f"无法获取图片尺寸: {img_url}")
                            continue
                    else:
                        # 如果已经获取到显示尺寸，直接下载图片
                        img_response = requests.get(img_url, headers=self.headers, timeout=10)
                        img_response.raise_for_status()
                    
                    # 过滤小图片（通常是图标或广告）
                    if display_width < self.min_image_width or display_height < self.min_image_height:
                        logging.info(f"跳过小图片: {img_url} (显示尺寸: {display_width}x{display_height})")
                        continue
                    
                    # 保存图片
                    try:
                        img_data = BytesIO(img_response.content)
                        img_obj = Image.open(img_data)
                        img_format = img_obj.format.lower() if img_obj.format else 'jpg'
                        
                        img_filename = f"{safe_title}_{i+1}.{img_format}"
                        img_path = os.path.join(self.image_folder, img_filename)
                        
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # 将图片信息添加到保存列表
                        img_info = {
                            'file_name': img_filename,
                            'display_width': display_width,
                            'display_height': display_height,
                            'url': img_url
                        }
                        saved_images.append(img_info)
                        
                        count += 1
                        logging.info(f"已保存图片: {img_path} (显示尺寸: {display_width}x{display_height})")
                    except Exception as e:
                        logging.error(f"保存图片失败: {str(e)}")
                        
                        # 如果保存失败，尝试根据Content-Type确定类型并保存
                        content_type = img_response.headers.get('Content-Type', '')
                        if 'jpeg' in content_type or 'jpg' in content_type:
                            ext = 'jpg'
                        elif 'png' in content_type:
                            ext = 'png'
                        elif 'gif' in content_type:
                            ext = 'gif'
                        elif 'webp' in content_type:
                            ext = 'webp'
                        else:
                            ext = 'jpg'  # 默认使用jpg
                        
                        img_filename = f"{safe_title}_{i+1}.{ext}"
                        img_path = os.path.join(self.image_folder, img_filename)
                        
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # 将图片信息添加到保存列表
                        img_info = {
                            'file_name': img_filename,
                            'display_width': display_width,
                            'display_height': display_height,
                            'url': img_url
                        }
                        saved_images.append(img_info)
                        
                        count += 1
                        logging.info(f"已保存图片(备用方法): {img_path} (显示尺寸: {display_width}x{display_height})")
                    
                    # 随机延迟，避免请求过快
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logging.error(f"下载单张图片失败: {str(e)}")
            
            # 处理背景图片
            for i, bg_url in enumerate(background_images):
                try:
                    # 处理相对URL
                    bg_url = urljoin(url, bg_url)
                    
                    # 下载图片
                    img_response = requests.get(bg_url, headers=self.headers, timeout=10)
                    img_response.raise_for_status()
                    
                    try:
                        img_data = BytesIO(img_response.content)
                        img_obj = Image.open(img_data)
                        width, height = img_obj.size
                        
                        # 过滤小图片
                        if width < self.min_image_width or height < self.min_image_height:
                            logging.info(f"跳过小背景图片: {bg_url} (尺寸: {width}x{height})")
                            continue
                        
                        img_format = img_obj.format.lower() if img_obj.format else 'jpg'
                        
                        img_filename = f"{safe_title}_bg_{len(img_tags) + i + 1}.{img_format}"
                        img_path = os.path.join(self.image_folder, img_filename)
                        
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # 将图片信息添加到保存列表
                        img_info = {
                            'file_name': img_filename,
                            'display_width': width,
                            'display_height': height,
                            'url': bg_url
                        }
                        saved_images.append(img_info)
                        
                        count += 1
                        logging.info(f"已保存背景图片: {img_path} (尺寸: {width}x{height})")
                    except Exception:
                        logging.warning(f"无法处理背景图片: {bg_url}")
                    
                    # 随机延迟，避免请求过快
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    logging.error(f"下载背景图片失败: {str(e)}")
            
            return count, saved_images
        except Exception as e:
            logging.error(f"下载图片过程失败 - {url}: {str(e)}")
            return 0, []
    
    def find_additional_video_sources(self, soup):
        """
        查找页面中可能的视频源
        :param soup: BeautifulSoup对象
        :return: 视频源URL列表
        """
        video_sources = []
        
        # 查找包含视频相关属性或类名的元素
        video_elements = soup.find_all(class_=lambda x: x and any(v in x.lower() for v in ['video', 'player', 'media']))
        for elem in video_elements:
            # 查找data-video或data-src等属性
            for attr in ['data-video', 'data-src', 'data-video-src', 'data-source']:
                if elem.has_attr(attr):
                    src = elem[attr]
                    if src and ('mp4' in src or 'webm' in src or 'ogg' in src):
                        video_sources.append(src)
        
        # 查找脚本中可能包含的视频URL
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # 查找视频URL模式
                video_matches = re.findall(r'(?:video|source|media)(?:Url|URL|url|Src|src)(?:\s*:\s*|\s*=\s*)[\'"]([^"\']+\.(?:mp4|webm|ogg))[\'"]', script.string)
                for match in video_matches:
                    video_sources.append(match)
        
        return video_sources
    
    def download_videos(self, url, title, article_container=None):
        """
        下载并保存视频
        :param url: 网页URL
        :param title: 文章标题
        :param article_container: 文章正文容器元素，如果提供则只提取该容器内的视频
        :return: 下载的视频数量和视频信息列表
        """
        try:
            # 如果没有提供文章容器，需要先获取网页内容
            if not article_container:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取文章正文内容和容器
                _, article_container = self.extract_article_content(soup)
            
            # 如果找到了文章容器，从容器中提取视频
            if article_container:
                video_tags = article_container.find_all('video')
                iframes = article_container.find_all('iframe')
                # 查找其他可能的视频源
                additional_sources = self.find_additional_video_sources(article_container)
            else:
                # 如果没有找到文章容器，从整个网页提取视频
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                video_tags = soup.find_all('video')
                iframes = soup.find_all('iframe')
                # 查找其他可能的视频源
                additional_sources = self.find_additional_video_sources(soup)
            
            video_sources = []
            
            # 查找video标签中的source
            for video in video_tags:
                sources = video.find_all('source')
                for source in sources:
                    video_url = source.get('src')
                    if video_url:
                        video_sources.append(video_url)
                
                # 有些视频直接在video标签的src属性中
                video_url = video.get('src')
                if video_url:
                    video_sources.append(video_url)
            
            # 查找iframe中的视频，通常是嵌入式播放器
            for iframe in iframes:
                iframe_src = iframe.get('src')
                if iframe_src and ('video' in iframe_src or 'player' in iframe_src or 'youtube' in iframe_src or 'vimeo' in iframe_src):
                    video_sources.append(iframe_src)
            
            # 添加其他找到的视频源
            video_sources.extend(additional_sources)
            
            # 清理文件名
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            
            count = 0
            saved_videos = []  # 保存视频信息的列表
            
            for i, video_url in enumerate(video_sources):
                try:
                    # 处理相对URL
                    video_url = urljoin(url, video_url)
                    
                    # 下载视频或获取视频信息
                    # 对于嵌入式视频，我们可能无法直接下载，只记录URL
                    if 'youtube.com' in video_url or 'vimeo.com' in video_url or 'player' in video_url:
                        video_filename = f"{safe_title}_{i+1}_link.txt"
                        video_path = os.path.join(self.video_folder, video_filename)
                        
                        # 保存视频链接
                        with open(video_path, 'w', encoding='utf-8') as f:
                            f.write(f"视频链接: {video_url}")
                        
                        video_info = {
                            'file_name': video_filename,
                            'url': video_url,
                            'type': 'link'
                        }
                        saved_videos.append(video_info)
                        
                        count += 1
                        logging.info(f"已保存视频链接: {video_path}")
                    else:
                        # 下载直接的视频文件
                        video_response = requests.get(video_url, headers=self.headers, timeout=30, stream=True)
                        video_response.raise_for_status()
                        
                        # 确定视频扩展名
                        content_type = video_response.headers.get('Content-Type', '')
                        if 'mp4' in content_type:
                            ext = 'mp4'
                        elif 'webm' in content_type:
                            ext = 'webm'
                        elif 'ogg' in content_type:
                            ext = 'ogg'
                        elif '.mp4' in video_url:
                            ext = 'mp4'
                        elif '.webm' in video_url:
                            ext = 'webm'
                        elif '.ogg' in video_url:
                            ext = 'ogg'
                        else:
                            ext = 'mp4'  # 默认使用mp4
                        
                        video_filename = f"{safe_title}_{i+1}.{ext}"
                        video_path = os.path.join(self.video_folder, video_filename)
                        
                        with open(video_path, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        video_info = {
                            'file_name': video_filename,
                            'url': video_url,
                            'type': 'file'
                        }
                        saved_videos.append(video_info)
                        
                        count += 1
                        logging.info(f"已保存视频: {video_path}")
                    
                    # 随机延迟，避免请求过快
                    time.sleep(random.uniform(1.0, 3.0))
                    
                except Exception as e:
                    logging.error(f"下载单个视频失败: {str(e)}")
            
            return count, saved_videos
        except Exception as e:
            logging.error(f"下载视频过程失败 - {url}: {str(e)}")
            return 0, []
    
    def start_crawling(self):
        """
        开始爬取流程
        """
        df = self.read_excel()
        if df is None:
            return
        
        # 确定标题和URL列名（根据实际Excel文件调整）
        # 添加更多可能的列名，包括特定格式的字段名
        possible_title_cols = ['标题', '文章标题', 'title', 'Title', '字段1_文本_文本']
        possible_url_cols = ['网址', '链接', 'url', 'URL', 'link', 'Link', '字段1_链接_链接']
        
        title_col = None
        url_col = None
        
        # 查找标题列
        for col in possible_title_cols:
            if col in df.columns:
                title_col = col
                break
        
        # 查找URL列
        for col in possible_url_cols:
            if col in df.columns:
                url_col = col
                break
        
        if not title_col or not url_col:
            logging.error(f"无法在Excel中找到标题或URL列。可用列: {list(df.columns)}")
            return
        
        # 移除空值行
        df = df.dropna(subset=[title_col, url_col], how='any')
        
        total = len(df)
        completed = len(self.completed_urls)
        logging.info(f"开始爬取，共 {total} 篇文章，已完成 {completed} 篇")
        
        for index, row in df.iterrows():
            title = str(row[title_col])
            url = str(row[url_col])
            
            # 检查URL是否有效
            if not url.startswith('http'):
                logging.warning(f"跳过无效URL: {url}")
                continue
            
            # 检查是否已经爬取过该URL
            if url in self.completed_urls:
                logging.info(f"跳过已爬取的URL [{index+1}/{total}]: {title}")
                continue
            
            logging.info(f"正在处理 [{index+1}/{total}]: {title}")
            
            try:
                # 首先获取网页内容和文章容器
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                _, article_container = self.extract_article_content(soup)
                
                # 使用同一个文章容器处理文本、图片和视频，确保内容一致性
                # 下载图片
                img_count, saved_images = self.download_images(url, title, article_container)
                logging.info(f"已下载 {img_count} 张图片")
                
                # 下载视频
                video_count, saved_videos = self.download_videos(url, title, article_container)
                logging.info(f"已下载 {video_count} 个视频")
                
                # 下载并保存文本，包含图片和视频列表
                self.download_text(url, title, saved_images, saved_videos)
                
                # 保存进度
                self.save_progress(url)
                
                # 随机延迟，避免请求过快
                time.sleep(random.uniform(2.0, 5.0))
            
            except requests.exceptions.RequestException as e:
                logging.error(f"请求失败 - {url}: {str(e)}")
                logging.info(f"将在下次运行时重试该URL")
                # 网络错误时，不将URL加入已完成列表，以便下次重试
                time.sleep(10)  # 网络错误后较长时间等待
                continue
            except Exception as e:
                logging.error(f"处理文章失败 - {url}: {str(e)}")
                # 其他错误时，也不将URL加入已完成列表
                time.sleep(5)
                continue
        
        logging.info(f"爬取任务完成！共完成 {len(self.completed_urls)} 篇文章")

if __name__ == "__main__":
    # 使用示例
    excel_file = "各文章网址.xlsx"
    crawler = WebCrawler(excel_file)
    crawler.start_crawling() 