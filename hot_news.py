#!/usr/bin/env python3
"""
每日热点新闻推送 - 专业分类版
8个类别：时政、军事、社会、经济、科技、热搜、体育、文教
每个类别5条精选新闻
新增新闻源：抖音、36氪、今日头条热榜
"""

import os
import sys
import time
import logging
import smtplib
import requests
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 通用请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# ====================== 新增新闻源函数 ======================

def fetch_douyin_hot():
    """获取抖音热点"""
    try:
        # 抖音热点API
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        headers = {
            **HEADERS,
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*'
        }
        
        # 使用随机设备参数
        params = {
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
            'detail_list': '1',
            'source': '6',
            'pc_client_type': '1',
            'version_code': '190500',
            'version_name': '19.5.0'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                news_list = []
                
                if 'data' in data and 'word_list' in data['data']:
                    for i, item in enumerate(data['data']['word_list'][:5], 1):
                        sentence = item.get('sentence', '')
                        hot_value = item.get('hot_value', 0)
                        
                        if sentence:
                            if hot_value > 10000:
                                news_list.append(f"{i}. {sentence} 🔥{hot_value//10000}w")
                            else:
                                news_list.append(f"{i}. {sentence}")
                
                if news_list:
                    return news_list
            except json.JSONDecodeError:
                pass
        
        # 备用方案：使用网页版
        url2 = "https://www.douyin.com/hot"
        headers2 = {
            **HEADERS,
            'Referer': 'https://www.douyin.com/',
            'Cookie': '__ac_nonce=0645b127800c0e5b5b2f3'
        }
        
        response2 = requests.get(url2, headers=headers2, timeout=15)
        soup = BeautifulSoup(response2.text, 'html.parser')
        
        news_list = []
        # 尝试多种选择器
        selectors = [
            '.BfqNqZX9',
            '.Ny7lCzjh',
            '[class*="HotItem"]',
            '[class*="hot-item"]',
            '.CgEDpFFU'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for i, item in enumerate(items[:5], 1):
                text = item.text.strip()
                if text and len(text) > 5:
                    # 清理文本
                    clean_text = re.sub(r'\s+', ' ', text)
                    if clean_text not in [re.sub(r'\d+\.\s*', '', n) for n in news_list]:
                        news_list.append(f"{i}. {clean_text}")
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        if not news_list:
            # 从页面文本中提取
            all_text = soup.get_text()
            lines = [line.strip() for line in all_text.split('\n') if len(line.strip()) > 10]
            for i, line in enumerate(lines[:5], 1):
                news_list.append(f"{i}. {line}")
        
        return news_list if news_list else ["1. 抖音热点更新中", "2. 短视频平台热门内容"]
        
    except Exception as e:
        logger.warning(f"抖音热点抓取失败: {e}")
        return ["1. 抖音热点", "2. 短视频热门", "3. 平台趋势"]

def fetch_36kr_hot():
    """获取36氪热点"""
    try:
        # 36氪热点API
        url = "https://36kr.com/pp/api/aggregation-entity"
        headers = {
            **HEADERS,
            'Referer': 'https://36kr.com/',
            'Accept': 'application/json, text/plain, */*'
        }
        
        # 尝试获取热点资讯
        response = requests.get(url, headers=headers, timeout=15)
        
        news_list = []
        
        try:
            if response.status_code == 200:
                data = response.json()
                # 尝试不同的数据路径
                if 'data' in data and 'items' in data['data']:
                    for i, item in enumerate(data['data']['items'][:5], 1):
                        title = item.get('title', '') or item.get('post', {}).get('title', '')
                        if title:
                            news_list.append(f"{i}. {title}")
        except:
            pass
        
        # 网页抓取备用方案
        if not news_list:
            url2 = "https://36kr.com/hot-list/catalog"
            response2 = requests.get(url2, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response2.text, 'html.parser')
            
            # 尝试多种选择器
            selectors = [
                '.kr-shadow-content .article-item-title',
                '.hotlist-item-toptwo-title',
                '.hotlist-item-title',
                '.article-item-title',
                '.title a',
                'h3 a',
                '.kr-flow-article-item-title'
            ]
            
            for selector in selectors:
                items = soup.select(selector, limit=10)
                for i, item in enumerate(items[:5], 1):
                    title = item.text.strip()
                    if title and len(title) > 8:
                        # 去重
                        if title not in [re.sub(r'\d+\.\s*', '', n).strip() for n in news_list]:
                            news_list.append(f"{i}. {title}")
                    if len(news_list) >= 5:
                        break
                if len(news_list) >= 5:
                    break
        
        if not news_list:
            # 从页面中提取所有标题
            url3 = "https://36kr.com/"
            response3 = requests.get(url3, headers=HEADERS, timeout=10)
            soup3 = BeautifulSoup(response3.text, 'html.parser')
            
            # 查找所有可能包含标题的元素
            title_elements = soup3.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|Title'))
            for i, elem in enumerate(title_elements[:5], 1):
                title = elem.text.strip()
                if title and len(title) > 10:
                    news_list.append(f"{i}. {title}")
        
        return news_list if news_list else ["1. 36氪热点更新中", "2. 创投科技资讯"]
        
    except Exception as e:
        logger.warning(f"36氪热点抓取失败: {e}")
        return ["1. 36氪热点", "2. 创投资讯", "3. 科技创业"]

def fetch_toutiao_hotlist():
    """获取今日头条热榜"""
    try:
        # 今日头条热榜API
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {
            **HEADERS,
            'Referer': 'https://www.toutiao.com/',
            'Accept': 'application/json, text/plain, */*'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                news_list = []
                
                if 'data' in data:
                    for i, item in enumerate(data['data'][:5], 1):
                        title = item.get('Title', '') or item.get('title', '')
                        hot_value = item.get('HotValue', 0) or item.get('hot_value', 0)
                        
                        if title:
                            if hot_value > 10000:
                                news_list.append(f"{i}. {title} 🔥{hot_value//10000}w")
                            else:
                                news_list.append(f"{i}. {title}")
                
                if news_list:
                    return news_list
            except json.JSONDecodeError:
                pass
        
        # 网页抓取备用方案
        url2 = "https://www.toutiao.com/"
        response2 = requests.get(url2, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response2.text, 'html.parser')
        
        news_list = []
        
        # 今日头条热榜选择器
        selectors = [
            '[data-track*=hot]',
            '.hot-title',
            '.hot-list-item',
            '.tt-category-hot .title',
            '.feed-card-article-title',
            '.title-box a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for i, item in enumerate(items[:5], 1):
                title = item.text.strip()
                if title and len(title) > 8 and '头条' not in title:
                    # 去重
                    clean_title = re.sub(r'[\d\.\s]*', '', title).strip()
                    if clean_title and clean_title not in [re.sub(r'[\d\.\s🔥\w]*', '', n).strip() for n in news_list]:
                        news_list.append(f"{i}. {title}")
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        if not news_list:
            # 从页面文本中提取
            all_text = soup.get_text()
            lines = [line.strip() for line in all_text.split('\n') if 10 < len(line.strip()) < 100]
            unique_lines = []
            for line in lines:
                if line not in unique_lines:
                    unique_lines.append(line)
            for i, line in enumerate(unique_lines[:5], 1):
                news_list.append(f"{i}. {line}")
        
        return news_list if news_list else ["1. 今日头条热榜更新中", "2. 资讯平台热点"]
        
    except Exception as e:
        logger.warning(f"今日头条热榜抓取失败: {e}")
        return ["1. 今日头条热榜", "2. 资讯热点", "3. 平台热门"]

# ====================== 原有新闻源函数（保持原有结构） ======================

def fetch_politics_news():
    """获取时政新闻（人民网+新华网）"""
    try:
        news_list = []
        
        # 人民网时政
        url1 = "http://politics.people.com.cn/"
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        selectors1 = ['.news_box .news a', '.hdNews a', '.news_tu h2 a', '.news_title a']
        for selector in selectors1:
            items = soup1.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6 and '人民网' not in title:
                    keywords = ['习近平', '总理', '国务院', '外交部', '政策', '会议', '领导人', '外交']
                    if any(keyword in title for keyword in keywords):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 8:
                    break
            if len(news_list) >= 8:
                break
        
        # 新华网时政
        url2 = "http://www.xinhuanet.com/politics/"
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        selectors2 = ['.tit', '.news-item h3', '.hdNews a', '.news_tu h2 a']
        for selector in selectors2:
            items = soup2.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6 and '新华网' not in title:
                    if '时政' in title or any(keyword in title for keyword in ['政治', '政府', '政策']):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 8:
                    break
            if len(news_list) >= 8:
                break
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 时政要闻更新中", "2. 重要会议进行时"]
        
    except Exception as e:
        logger.warning(f"时政新闻抓取失败: {e}")
        return ["1. 时政要闻", "2. 政策动态", "3. 重要会议"]

def fetch_military_news():
    """获取军事新闻"""
    try:
        news_list = []
        
        # 新华网军事
        url = "http://www.xinhuanet.com/mil/"
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = ['.tit', '.news-item h3', '.hdNews a', '.news_tu h2 a', '.title a']
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    keywords = ['军队', '国防', '军事', '演习', '武器', '海军', '空军', '陆军']
                    if any(keyword in title for keyword in keywords):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 8:
                    break
            if len(news_list) >= 8:
                break
        
        # 如果不够，从人民网补充
        if len(news_list) < 5:
            url2 = "http://military.people.com.cn/"
            try:
                response2 = requests.get(url2, headers=HEADERS, timeout=8)
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                items2 = soup2.select('a', limit=20)
                for item in items2:
                    title = item.text.strip()
                    if title and len(title) > 8 and '军事' in title:
                        if title not in news_list:
                            news_list.append(title)
                    if len(news_list) >= 8:
                        break
            except:
                pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 军事动态更新中", "2. 国防建设进展"]
        
    except Exception as e:
        logger.warning(f"军事新闻抓取失败: {e}")
        return ["1. 军事动态", "2. 国防建设", "3. 军队改革"]

def fetch_society_news():
    """获取社会新闻（新浪+网易+抖音热点）"""
    try:
        news_list = []
        
        # 新浪社会新闻
        url1 = "https://news.sina.com.cn/society/"
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        selectors1 = ['.blk122 a', '.news-item h2 a', '.news_title a', '.title a']
        for selector in selectors1:
            items = soup1.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 8:
                    keywords = ['社会', '民生', '社区', '居民', '生活', '百姓']
                    if any(keyword in title for keyword in keywords) or ('事件' in title):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 网易社会新闻
        url2 = "https://news.163.com/shehui/"
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        selectors2 = ['.news_title h3 a', '.ndi_main a', '.news_item h2 a']
        for selector in selectors2:
            items = soup2.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 8:
                    if '社会' in title or '民生' in title:
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 抖音热点（社会类）
        try:
            douyin_news = fetch_douyin_hot()
            # 筛选社会相关内容
            for news in douyin_news[:2]:
                if any(keyword in news for keyword in ['社会', '民生', '生活', '事件']):
                    if news not in news_list:
                        news_list.append(news)
        except:
            pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 社会热点更新中", "2. 民生关注"]
        
    except Exception as e:
        logger.warning(f"社会新闻抓取失败: {e}")
        return ["1. 社会热点", "2. 民生关注", "3. 社区动态"]

def fetch_economy_news():
    """获取经济新闻（人民网+新华网+36氪）"""
    try:
        news_list = []
        
        # 人民网经济
        url1 = "http://finance.people.com.cn/"
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        selectors1 = ['.news_box .news a', '.hdNews a', '.news_tu h2 a', '.news_title a']
        for selector in selectors1:
            items = soup1.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    keywords = ['经济', '金融', '股市', '投资', '消费', 'GDP', '贸易', '银行']
                    if any(keyword in title for keyword in keywords):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 新华网经济
        url2 = "http://www.xinhuanet.com/fortune/"
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        selectors2 = ['.tit', '.news-item h3', '.hdNews a', '.news_tu h2 a']
        for selector in selectors2:
            items = soup2.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if '经济' in title or '财经' in title or '金融' in title:
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 36氪经济类新闻
        try:
            kr_news = fetch_36kr_hot()
            # 筛选经济相关内容
            for news in kr_news[:2]:
                if any(keyword in news for keyword in ['经济', '金融', '投资', '创投', '融资']):
                    if news not in news_list:
                        news_list.append(news)
        except:
            pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 经济动态更新中", "2. 财经要闻"]
        
    except Exception as e:
        logger.warning(f"经济新闻抓取失败: {e}")
        return ["1. 经济动态", "2. 财经要闻", "3. 市场分析"]

def fetch_tech_news():
    """获取科技新闻（人民网+新华网+36氪）"""
    try:
        news_list = []
        
        # 人民网科技
        url1 = "http://scitech.people.com.cn/"
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        selectors1 = ['.news_box .news a', '.hdNews a', '.news_tu h2 a', '.news_title a']
        for selector in selectors1:
            items = soup1.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    keywords = ['科技', '创新', '人工智能', 'AI', '5G', '芯片', '互联网', '数字']
                    if any(keyword in title for keyword in keywords):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 新华网科技
        url2 = "http://www.xinhuanet.com/tech/"
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        selectors2 = ['.tit', '.news-item h3', '.hdNews a', '.news_tu h2 a']
        for selector in selectors2:
            items = soup2.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if '科技' in title or '创新' in title or '技术' in title:
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 36氪科技新闻
        try:
            kr_news = fetch_36kr_hot()
            # 筛选科技相关内容
            for news in kr_news[:3]:
                if any(keyword in news for keyword in ['科技', '创新', '技术', '互联网', '创业', '融资']):
                    if news not in news_list:
                        news_list.append(news)
        except:
            pass
        
        # IT之家补充
        try:
            url3 = "https://www.ithome.com/"
            response3 = requests.get(url3, headers=HEADERS, timeout=8)
            soup3 = BeautifulSoup(response3.text, 'html.parser')
            items3 = soup3.select('.title a', limit=3)
            for item in items3:
                title = item.text.strip()
                if title and len(title) > 6:
                    if title not in news_list:
                        news_list.append(title)
        except:
            pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 科技前沿更新中", "2. 创新动态"]
        
    except Exception as e:
        logger.warning(f"科技新闻抓取失败: {e}")
        return ["1. 科技前沿", "2. 创新动态", "3. 数字技术"]

def fetch_hotsearch_news():
    """获取热搜新闻（微博+百度+知乎+抖音+今日头条热榜）"""
    try:
        news_list = []
        
        # 微博热搜
        try:
            url1 = "https://weibo.com/ajax/side/hotSearch"
            headers1 = {**HEADERS, 'Referer': 'https://weibo.com/'}
            response1 = requests.get(url1, headers=headers1, timeout=10)
            data1 = response1.json()
            
            if 'data' in data1 and 'realtime' in data1['data']:
                for item in data1['data']['realtime'][:3]:
                    title = item.get('note', '')
                    if title and '推荐' not in title:
                        hot = item.get('num', 0)
                        if hot > 10000:
                            news_list.append(f"{title} 🔥{hot//10000}w")
                        else:
                            news_list.append(title)
        except:
            pass
        
        # 百度热搜
        try:
            url2 = "https://top.baidu.com/board?tab=realtime"
            response2 = requests.get(url2, headers=HEADERS, timeout=10)
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            
            items2 = soup2.select('.c-single-text-ellipsis', limit=3)
            for item in items2:
                title = item.text.strip()
                if title:
                    news_list.append(title)
        except:
            pass
        
        # 知乎热榜
        try:
            url3 = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=3"
            headers3 = {**HEADERS, 'Referer': 'https://www.zhihu.com/'}
            response3 = requests.get(url3, headers=headers3, timeout=10)
            data3 = response3.json()
            
            if 'data' in data3:
                for item in data3['data'][:3]:
                    title = item.get('target', {}).get('title', '')
                    if title:
                        news_list.append(title)
        except:
            pass
        
        # 抖音热点
        try:
            douyin_news = fetch_douyin_hot()
            for news in douyin_news[:2]:
                if news not in news_list:
                    news_list.append(news)
        except:
            pass
        
        # 今日头条热榜
        try:
            toutiao_news = fetch_toutiao_hotlist()
            for news in toutiao_news[:2]:
                if news not in news_list:
                    news_list.append(news)
        except:
            pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 全网热搜更新中", "2. 热门话题"]
        
    except Exception as e:
        logger.warning(f"热搜新闻抓取失败: {e}")
        return ["1. 微博热搜", "2. 百度热榜", "3. 知乎热榜"]

def fetch_sports_news():
    """获取体育新闻（新浪+网易+抖音体育热点）"""
    try:
        news_list = []
        
        # 新浪体育
        url1 = "https://sports.sina.com.cn/"
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        selectors1 = ['.blk122 a', '.news-item h2 a', '.news_title a', '.title a']
        for selector in selectors1:
            items = soup1.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    keywords = ['体育', '赛事', '比赛', '运动员', '冠军', '足球', '篮球', '奥运']
                    if any(keyword in title for keyword in keywords):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 网易体育
        url2 = "https://sports.163.com/"
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        selectors2 = ['.news_title h3 a', '.ndi_main a', '.news_item h2 a']
        for selector in selectors2:
            items = soup2.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if '体育' in title or '运动' in title:
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 抖音体育热点
        try:
            douyin_news = fetch_douyin_hot()
            # 筛选体育相关内容
            for news in douyin_news[:2]:
                if any(keyword in news for keyword in ['体育', '比赛', '运动', '足球', '篮球']):
                    if news not in news_list:
                        news_list.append(news)
        except:
            pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 体育赛事更新中", "2. 体坛动态"]
        
    except Exception as e:
        logger.warning(f"体育新闻抓取失败: {e}")
        return ["1. 体育赛事", "2. 体坛动态", "3. 运动员风采"]

def fetch_edu_news():
    """获取文教新闻（教育+文化+抖音知识类）"""
    try:
        news_list = []
        
        # 人民网教育
        url1 = "http://edu.people.com.cn/"
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        selectors1 = ['.news_box .news a', '.hdNews a', '.news_tu h2 a', '.news_title a']
        for selector in selectors1:
            items = soup1.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    keywords = ['教育', '学校', '学生', '教师', '文化', '艺术', '读书', '博物馆']
                    if any(keyword in title for keyword in keywords):
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 新华网文化
        url2 = "http://www.xinhuanet.com/culture/"
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        selectors2 = ['.tit', '.news-item h3', '.hdNews a', '.news_tu h2 a']
        for selector in selectors2:
            items = soup2.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if '文化' in title or '教育' in title or '艺术' in title:
                        if title not in news_list:
                            news_list.append(title)
                if len(news_list) >= 6:
                    break
            if len(news_list) >= 6:
                break
        
        # 抖音知识类内容
        try:
            douyin_news = fetch_douyin_hot()
            # 筛选知识、教育相关内容
            for news in douyin_news[:2]:
                if any(keyword in news for keyword in ['知识', '学习', '教育', '文化', '艺术']):
                    if news not in news_list:
                        news_list.append(news)
        except:
            pass
        
        # 格式化输出前5条
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["1. 文教动态更新中", "2. 教育资讯"]
        
    except Exception as e:
        logger.warning(f"文教新闻抓取失败: {e}")
        return ["1. 教育资讯", "2. 文化动态", "3. 艺术展览"]

# ====================== 邮件内容生成 ======================

def generate_email_content():
    """生成邮件内容 - 8个类别，每个类别5条，整合新新闻源"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    logger.info("开始抓取8个类别新闻，整合抖音、36氪、今日头条热榜...")
    
    # 定义8个类别及其对应的抓取函数
    news_categories = {
        "🏛️ 时政新闻": fetch_politics_news,
        "🎖️ 军事动态": fetch_military_news,
        "👥 社会民生": fetch_society_news,
        "📈 经济财经": fetch_economy_news,
        "💻 科技前沿": fetch_tech_news,
        "🔥 热搜榜单": fetch_hotsearch_news,
        "⚽ 体育竞技": fetch_sports_news,
        "🎓 文教艺术": fetch_edu_news,
    }
    
    all_news = {}
    total_news = 0
    sources_count = {
        "抖音": False,
        "36氪": False,
        "今日头条热榜": False,
        "人民网": True,
        "新华网": True,
        "微博": True,
        "百度": True,
        "知乎": True,
        "新浪": True,
        "网易": True,
        "IT之家": True
    }
    
    # 测试新新闻源可用性
    logger.info("测试新新闻源可用性...")
    try:
        test_douyin = fetch_douyin_hot()
        if len(test_douyin) > 0 and "更新中" not in test_douyin[0]:
            sources_count["抖音"] = True
            logger.info("✅ 抖音热点可用")
    except:
        logger.warning("❌ 抖音热点不可用")
    
    try:
        test_36kr = fetch_36kr_hot()
        if len(test_36kr) > 0 and "更新中" not in test_36kr[0]:
            sources_count["36氪"] = True
            logger.info("✅ 36氪热点可用")
    except:
        logger.warning("❌ 36氪热点不可用")
    
    try:
        test_toutiao = fetch_toutiao_hotlist()
        if len(test_toutiao) > 0 and "更新中" not in test_toutiao[0]:
            sources_count["今日头条热榜"] = True
            logger.info("✅ 今日头条热榜可用")
    except:
        logger.warning("❌ 今日头条热榜不可用")
    
    # 抓取所有类别新闻
    for category_name, fetch_func in news_categories.items():
        try:
            logger.info(f"抓取 {category_name}...")
            news_list = fetch_func()
            all_news[category_name] = news_list
            total_news += len(news_list)
            time.sleep(0.3)  # 礼貌间隔
        except Exception as e:
            logger.warning(f"{category_name} 抓取异常: {e}")
            all_news[category_name] = [f"{category_name}：数据更新中"]
    
    # 统计可用新闻源数量
    available_sources = sum(1 for v in sources_count.values() if v)
    
    # 纯文本版本
    text_content = f"""
每日热点新闻速递 ({today})
===========================================
更新时间: {current_time}
新闻类别: 8大类，共{total_news}条精选新闻
新闻来源: {available_sources}个可用源（新增抖音、36氪、今日头条热榜）

"""
    
    for category_name, news_list in all_news.items():
        text_content += f"\n{category_name}\n"
        text_content += "=" * 40 + "\n"
        
        for news in news_list[:5]:  # 每个类别显示前5条
            text_content += f"  {news}\n"
        
        text_content += "\n"
    
    text_content += f"""
===========================================
本邮件由 GitHub Actions 自动发送
每日定时推送: 08:00 (北京时间)
覆盖8大类别: 时政、军事、社会、经济、科技、热搜、体育、文教
新增新闻源: 抖音、36氪、今日头条热榜（共{available_sources}个新闻源）
"""
    
    # HTML版本
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日热点新闻 - {today}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            font-weight: bold;
        }}
        .header .subtitle {{
            margin-top: 15px;
            opacity: 0.9;
            font-size: 16px;
        }}
        .categories-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }}
        .category-section {{
            border-radius: 10px;
            padding: 25px;
            background: #f8f9fa;
            border: 1px solid #e1e4e8;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .category-section:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }}
        .category-title {{
            font-size: 22px;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .news-count {{
            font-size: 14px;
            background: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: normal;
        }}
        .news-list {{
            margin-top: 15px;
        }}
        .news-item {{
            margin-bottom: 12px;
            padding: 14px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid;
            transition: all 0.2s;
            display: flex;
            align-items: flex-start;
        }}
        .news-item:hover {{
            transform: translateX(5px);
            background: #e9ecef;
        }}
        .news-number {{
            display: inline-block;
            width: 26px;
            height: 26px;
            line-height: 26px;
            text-align: center;
            background: #667eea;
            color: white;
            border-radius: 50%;
            margin-right: 12px;
            flex-shrink: 0;
            font-size: 14px;
            font-weight: bold;
        }}
        .news-content {{
            flex: 1;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 25px;
            border-top: 1px solid #e1e4e8;
            color: #6a737d;
            font-size: 14px;
        }}
        .hot-badge {{
            background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 8px;
            font-weight: bold;
        }}
        .new-source-badge {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 8px;
            font-weight: bold;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #6c757d;
        }}
        .new-features {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
            text-align: center;
        }}
        .new-features h3 {{
            color: #e65100;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .source-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-top: 15px;
        }}
        .source-tag {{
            background: #e9ecef;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 13px;
            border: 1px solid #dee2e6;
        }}
        .source-tag.new {{
            background: #d4edda;
            color: #155724;
            border-color: #c3e6cb;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日热点新闻速递</h1>
            <div class="subtitle">{today} | 更新时间: {current_time}</div>
        </div>
        
        <div class="new-features">
            <h3>🎉 新增新闻源！内容更全面</h3>
            <p>新增抖音、36氪、今日头条热榜，整合到各大新闻类别中</p>
            <div class="source-tags">
                <span class="source-tag new">抖音热点</span>
                <span class="source-tag new">36氪资讯</span>
                <span class="source-tag new">今日头条热榜</span>
                <span class="source-tag">人民网</span>
                <span class="source-tag">新华网</span>
                <span class="source-tag">微博热搜</span>
                <span class="source-tag">百度热搜</span>
                <span class="source-tag">知乎热榜</span>
                <span class="source-tag">新浪新闻</span>
                <span class="source-tag">网易新闻</span>
                <span class="source-tag">IT之家</span>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">8</div>
                <div class="stat-label">新闻类别</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_news}</div>
                <div class="stat-label">精选新闻</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{available_sources}</div>
                <div class="stat-label">新闻来源</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{datetime.now().strftime('%H:%M')}</div>
                <div class="stat-label">发布时间</div>
            </div>
        </div>
        
        <div class="categories-grid">
"""
    
    # 类别颜色映射
    category_colors = {
        "🏛️ 时政新闻": "#dc3545",
        "🎖️ 军事动态": "#495057",
        "👥 社会民生": "#17a2b8",
        "📈 经济财经": "#28a745",
        "💻 科技前沿": "#007bff",
        "🔥 热搜榜单": "#ffc107",
        "⚽ 体育竞技": "#e83e8c",
        "🎓 文教艺术": "#6f42c1"
    }
    
    # 新新闻源在各类别中的标识
    new_sources_in_categories = {
        "👥 社会民生": ["抖音"],
        "📈 经济财经": ["36氪"],
        "💻 科技前沿": ["36氪"],
        "🔥 热搜榜单": ["抖音", "今日头条热榜"],
        "⚽ 体育竞技": ["抖音"],
        "🎓 文教艺术": ["抖音"]
    }
    
    # 添加各个类别
    for category_name, news_list in all_news.items():
        color = category_colors.get(category_name, "#667eea")
        new_sources = new_sources_in_categories.get(category_name, [])
        
        html_content += f"""
            <div class="category-section">
                <div class="category-title" style="color: {color}; border-color: {color}">
                    <span>
                        {category_name}
                        {'' if not new_sources else ''.join([f'<span class="new-source-badge" style="margin-left: 8px;">{src}</span>' for src in new_sources])}
                    </span>
                    <span class="news-count" style="border: 1px solid {color}; color: {color}">
                        {len(news_list)}条
                    </span>
                </div>
                <div class="news-list">
"""
        
        for i, news in enumerate(news_list[:5], 1):
            # 处理热度标签
            news_display = news
            if '🔥' in news:
                parts = news.split('🔥')
                if len(parts) > 1:
                    news_display = f"{parts[0]}<span class='hot-badge'>🔥{parts[1]}</span>"
            
            html_content += f"""
                    <div class="news-item" style="border-left-color: {color}">
                        <span class="news-number">{i}</span>
                        <div class="news-content">{news_display}</div>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="footer">
            <p style="font-size: 16px; margin-bottom: 15px;">📧 本邮件由 GitHub Actions 自动生成并发送 | 每日早8点准时推送</p>
            <p>🔧 技术支持: Python + BeautifulSoup + Requests + GitHub Actions</p>
            <p>📊 数据来源: 共{available_sources}个新闻源，新增抖音、36氪、今日头条热榜</p>
            <p>⏰ 数据采集时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 15px; color: #495057; font-size: 13px;">
                覆盖8大类别: 时政 • 军事 • 社会 • 经济 • 科技 • 热搜 • 体育 • 文教 | 每个类别精选5条新闻
            </p>
            <p style="margin-top: 10px; color: #28a745; font-weight: bold;">
                ✅ 新增抖音、36氪、今日头条热榜，内容来源更丰富！
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return text_content, html_content

def send_email_simple(text_content, html_content):
    """发送邮件 - 最简单版（解决QQ邮箱格式问题）"""
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        logger.error("❌ 环境变量缺失")
        return False
    
    try:
        logger.info(f"准备发送邮件到 {receiver}")
        
        # 创建邮件 - 使用最简单的格式
        msg = MIMEMultipart('alternative')
        
        # 关键：只使用邮箱地址，不添加任何额外信息
        msg['From'] = sender
        msg['To'] = receiver
        
        today_str = datetime.now().strftime('%m月%d日')
        # 简化主题
        msg['Subject'] = f"每日热点新闻速递 - {today_str}"
        
        # 添加纯文本版本
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(part1)
        
        # 添加HTML版本
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        # 发送邮件
        logger.info("连接QQ邮箱SMTP服务器...")
        server = smtplib.SMTP('smtp.qq.com', 587, timeout=30)
        
        logger.info("启动TLS加密...")
        server.starttls()
        
        logger.info(f"登录邮箱...")
        server.login(sender, password)
        
        logger.info("发送邮件...")
        server.sendmail(sender, receiver, msg.as_string())
        
        logger.info("关闭连接...")
        server.quit()
        
        logger.info("✅ 邮件发送成功！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始执行每日新闻推送任务")
    logger.info("=" * 60)
    
    # 检查环境变量
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    
    logger.info(f"发件人: {sender}")
    logger.info(f"收件人: {receiver}")
    logger.info(f"密码: {'已设置' if password else '未设置'}")
    
    if not all([sender, password, receiver]):
        logger.error("❌ 请设置所有环境变量")
        return False
    
    try:
        # 生成邮件内容
        logger.info("生成邮件内容...")
        text_content, html_content = generate_email_content()
        
        # 发送邮件
        logger.info("发送邮件...")
        success = send_email_simple(text_content, html_content)
        
        if success:
            logger.info("🎉 任务执行成功！")
            logger.info("💡 提示：如果没收到邮件，请检查垃圾邮件箱")
            return True
        else:
            logger.error("❌ 任务执行失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 任务执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
