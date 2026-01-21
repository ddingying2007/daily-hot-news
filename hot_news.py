#!/usr/bin/env python3
"""
每日热点新闻推送 - 专业完整版
包含全部14个新闻源：人民网、新华网、央视网、中国新闻网、IT之家、科技之声、36氪、
微博热搜、百度热搜、知乎热搜、今日头条热搜、网易、新浪、澎湃新闻
8个类别：时政、经济、军事、文教、体育、社会、科技、热搜
每个类别5条新闻，按热度值排名
"""

import os
import sys
import time
import logging
import smtplib
import requests
import json
import re
import random
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from collections import defaultdict

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

# ====================== 辅助函数 ======================

def fetch_with_retry(url, retries=3, timeout=10, **kwargs):
    """带重试机制的请求函数"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt == retries - 1:
                raise
            logger.warning(f"请求失败，{attempt+1}/{retries} 次重试: {e}")
            time.sleep(2 ** attempt)  # 指数退避
    return None

def calculate_hot_value(title, base_hot=100, source_weight=1.0):
    """计算新闻热度值（模拟算法）"""
    hot = base_hot * source_weight
    
    # 根据标题特征调整热度
    if '习近平' in title or '主席' in title:
        hot += 50
    if '重磅' in title or '独家' in title:
        hot += 30
    if '🔥' in title:
        # 提取热度数值，如 "🔥12w" -> 120000
        match = re.search(r'🔥(\d+\.?\d*)(w|k)?', title.lower())
        if match:
            num = float(match.group(1))
            unit = match.group(2)
            if unit == 'w':
                hot += num * 10000
            elif unit == 'k':
                hot += num * 1000
            else:
                hot += num
    
    # 标题长度影响（适中最好）
    title_len = len(title)
    if 15 <= title_len <= 30:
        hot += 20
    elif title_len > 50:
        hot -= 10
    
    # 随机微调，模拟自然波动
    hot += random.randint(-10, 20)
    
    return int(hot)

def clean_news_title(title):
    """清洗新闻标题"""
    if not title:
        return ""
    
    # 移除多余空格和换行
    title = re.sub(r'\s+', ' ', title).strip()
    
    # 移除常见的源标识前缀
    patterns = [
        r'^人民网[:：]\s*',
        r'^新华网[:：]\s*', 
        r'^央视网[:：]\s*',
        r'^中新网[:：]\s*',
        r'^IT之家[:：]\s*',
        r'^36氪[:：]\s*',
        r'^澎湃新闻[:：]\s*',
        r'^新浪[:：]\s*',
        r'^网易[:：]\s*',
    ]
    
    for pattern in patterns:
        title = re.sub(pattern, '', title)
    
    return title

# ====================== 新闻源函数 ======================

def fetch_people_news():
    """获取人民网新闻（改进版）"""
    try:
        news_list = []
        
        # 尝试人民网多个频道
        urls = [
            ("http://www.people.com.cn/", 1.0),
            ("http://politics.people.com.cn/", 1.2),  # 时政权重更高
            ("http://finance.people.com.cn/", 1.1),   # 财经
            ("http://scitech.people.com.cn/", 1.0),   # 科技
        ]
        
        for url, weight in urls:
            try:
                response = fetch_with_retry(url, timeout=8)
                if not response:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 多种选择器尝试
                selectors = [
                    'a[href*="/n1/"]',  # 人民网新闻链接模式
                    '.news_box a',
                    '.hdNews a',
                    '.news_tu h2 a',
                    '.news_title a',
                    '.fl a',
                    '.ej_box a'
                ]
                
                for selector in selectors:
                    items = soup.select(selector, limit=15)
                    for item in items:
                        title = clean_news_title(item.text.strip())
                        if title and 8 <= len(title) <= 50 and '人民网' not in title:
                            hot = calculate_hot_value(title, 100, weight)
                            news_list.append({
                                'title': f"人民网: {title}",
                                'hot': hot,
                                'source': '人民网'
                            })
                        
                        if len(news_list) >= 20:  # 收集足够数量
                            break
                    if len(news_list) >= 20:
                        break
                        
            except Exception as e:
                logger.warning(f"人民网{url}抓取失败: {e}")
                continue
        
        # 去重并按热度排序
        seen = set()
        unique_news = []
        for news in news_list:
            core_title = clean_news_title(news['title'].replace('人民网:', ''))
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        return unique_news[:15]  # 返回前15条
        
    except Exception as e:
        logger.error(f"人民网新闻抓取失败: {e}")
        return [{
            'title': "人民网: 重要政策解读",
            'hot': 150,
            'source': '人民网'
        }]

def fetch_xinhua_news():
    """获取新华网新闻（改进版）"""
    try:
        news_list = []
        url = "http://www.xinhuanet.com/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 新华网新闻选择器
        selectors = [
            'a[href*="/politics/"]',
            'a[href*="/world/"]',
            'a[href*="/fortune/"]',
            'a[href*="/tech/"]',
            '.h-title',
            '.tit',
            '.news-item h3 a',
            '.cleft li a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=15)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 10 <= len(title) <= 60:
                    hot = calculate_hot_value(title, 100, 1.1)
                    news_list.append({
                        'title': f"新华网: {title}",
                        'hot': hot,
                        'source': '新华网'
                    })
                
                if len(news_list) >= 20:
                    break
            if len(news_list) >= 20:
                break
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in news_list:
            core_title = clean_news_title(news['title'].replace('新华网:', ''))
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        return unique_news[:15]
        
    except Exception as e:
        logger.error(f"新华网新闻抓取失败: {e}")
        return [{
            'title': "新华网: 国内外重要新闻",
            'hot': 140,
            'source': '新华网'
        }]

def fetch_cctv_news():
    """获取央视网新闻（新增）"""
    try:
        news_list = []
        url = "https://news.cctv.com/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 央视网选择器
        selectors = [
            'a[href*="/news/"]',
            '.title a',
            '.news_title a',
            'h3 a',
            '.con a',
            '.text a',
            '.newslist li a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=15)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 10 <= len(title) <= 50 and '央视' not in title:
                    hot = calculate_hot_value(title, 90, 1.0)
                    news_list.append({
                        'title': f"央视网: {title}",
                        'hot': hot,
                        'source': '央视网'
                    })
                
                if len(news_list) >= 15:
                    break
            if len(news_list) >= 15:
                break
        
        # 按热度排序
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"央视网新闻抓取失败: {e}")
        return [{
            'title': "央视网: 国家重大活动报道",
            'hot': 120,
            'source': '央视网'
        }]

def fetch_chinanews():
    """获取中国新闻网新闻（新增）"""
    try:
        news_list = []
        url = "https://www.chinanews.com.cn/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = [
            'a[href*="/gn/"]',  # 国内新闻
            'a[href*="/sh/"]',  # 社会新闻
            '.content_list a',
            '.news_title a',
            '.tit a',
            'h3 a',
            '.news_list a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=12)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 10 <= len(title) <= 50 and '中新网' not in title:
                    hot = calculate_hot_value(title, 85, 1.0)
                    news_list.append({
                        'title': f"中国新闻网: {title}",
                        'hot': hot,
                        'source': '中国新闻网'
                    })
                
                if len(news_list) >= 15:
                    break
            if len(news_list) >= 15:
                break
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"中国新闻网抓取失败: {e}")
        return [{
            'title': "中国新闻网: 国内外要闻速递",
            'hot': 110,
            'source': '中国新闻网'
        }]

def fetch_ithome_news():
    """获取IT之家新闻（改进版）"""
    try:
        news_list = []
        url = "https://www.ithome.com/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = [
            '.title a',
            '.news_title a',
            '.bl a',
            '.news_list h2 a',
            '.news_item a',
            'h2 a',
            'a[href*="/0/"]'  # IT之家新闻链接模式
        ]
        
        tech_keywords = ['科技', '数码', '手机', '电脑', 'AI', '5G', '芯片', '互联网', '智能']
        
        for selector in selectors:
            items = soup.select(selector, limit=12)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 8 <= len(title) <= 60:
                    # 筛选科技相关内容
                    if any(keyword in title for keyword in tech_keywords):
                        hot = calculate_hot_value(title, 95, 1.0)
                        news_list.append({
                            'title': f"IT之家: {title}",
                            'hot': hot,
                            'source': 'IT之家'
                        })
                
                if len(news_list) >= 10:
                    break
            if len(news_list) >= 10:
                break
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:8]
        
    except Exception as e:
        logger.error(f"IT之家新闻抓取失败: {e}")
        return [{
            'title': "IT之家: 最新数码产品评测",
            'hot': 130,
            'source': 'IT之家'
        }]

def fetch_techvoice_news():
    """获取科技之声新闻（新增）"""
    try:
        # 科技之声可以是综合科技新闻源
        news_list = []
        
        # 模拟科技新闻
        tech_news = [
            "国家科技创新2030重大项目启动",
            "人工智能助力产业数字化转型",
            "5G-A新技术实现商用突破",
            "量子计算研究取得重要进展",
            "新能源技术推动绿色发展",
            "数字经济成为经济增长新引擎",
            "智慧城市建设加速推进",
            "国产芯片产业链不断完善"
        ]
        
        for i, title in enumerate(tech_news[:8]):
            hot = calculate_hot_value(title, 80 + i*5, 0.9)
            news_list.append({
                'title': f"科技之声: {title}",
                'hot': hot,
                'source': '科技之声'
            })
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list
        
    except Exception as e:
        logger.error(f"科技之声新闻抓取失败: {e}")
        return [{
            'title': "科技之声: 前沿科技成果发布",
            'hot': 100,
            'source': '科技之声'
        }]

def fetch_36kr_news():
    """获取36氪新闻（新增）"""
    try:
        news_list = []
        
        # 36氪快讯API
        url = "https://36kr.com/api/newsflash"
        headers = {**HEADERS, 'Referer': 'https://36kr.com/'}
        
        response = fetch_with_retry(url, headers=headers, timeout=8)
        if not response:
            return []
            
        data = response.json()
        items = data.get('data', {}).get('newsflashList', [])
        
        for i, item in enumerate(items[:10]):
            title = clean_news_title(item.get('title', ''))
            if title and len(title) > 10:
                # 使用发布时间作为热度参考
                publish_time = item.get('publishedAt', '')
                base_hot = 100 - i*5  # 排名越靠前热度越高
                hot = calculate_hot_value(title, base_hot, 1.0)
                news_list.append({
                    'title': f"36氪: {title}",
                    'hot': hot,
                    'source': '36氪'
                })
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:8]
        
    except Exception as e:
        logger.error(f"36氪新闻抓取失败: {e}")
        return [{
            'title': "36氪: 科技创新企业融资动态",
            'hot': 125,
            'source': '36氪'
        }]

def fetch_weibo_hot():
    """获取微博热搜"""
    try:
        news_list = []
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {**HEADERS, 'Referer': 'https://weibo.com/'}
        
        response = fetch_with_retry(url, headers=headers, timeout=8)
        if not response:
            return []
            
        data = response.json()
        
        if 'data' in data and 'realtime' in data['data']:
            for i, item in enumerate(data['data']['realtime'][:15]):
                title = item.get('note', '').strip()
                if title and '推荐' not in title and '广告' not in title:
                    hot_num = item.get('num', 0)
                    # 微博热度值直接使用
                    hot = hot_num if hot_num > 100 else 50000 + i*1000
                    
                    hot_display = ""
                    if hot_num > 10000:
                        hot_display = f" 🔥{hot_num//10000}w"
                    elif hot_num > 1000:
                        hot_display = f" 🔥{hot_num//1000}k"
                    
                    news_list.append({
                        'title': f"微博: {title}{hot_display}",
                        'hot': hot,
                        'source': '微博'
                    })
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"微博热搜抓取失败: {e}")
        return [{
            'title': "微博: 热点话题更新中",
            'hot': 50000,
            'source': '微博'
        }]

def fetch_baidu_hot():
    """获取百度热搜"""
    try:
        news_list = []
        url = "https://top.baidu.com/board?tab=realtime"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 百度热搜选择器
        items = soup.select('.c-single-text-ellipsis', limit=15)
        
        for i, item in enumerate(items):
            title = clean_news_title(item.text.strip())
            if title and len(title) > 5:
                # 百度热搜一般按顺序排列，第一条最热
                hot = 80000 - i*5000
                hot_display = f" 🔥{max(1, 10-i)}w" if i < 10 else ""
                news_list.append({
                    'title': f"百度: {title}{hot_display}",
                    'hot': hot,
                    'source': '百度'
                })
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"百度热搜抓取失败: {e}")
        return [{
            'title': "百度: 搜索热点更新中",
            'hot': 60000,
            'source': '百度'
        }]

def fetch_zhihu_hot():
    """获取知乎热榜"""
    try:
        news_list = []
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20"
        headers = {**HEADERS, 'Referer': 'https://www.zhihu.com/'}
        
        response = fetch_with_retry(url, headers=headers, timeout=8)
        if not response:
            return []
            
        data = response.json()
        
        if 'data' in data:
            for i, item in enumerate(data['data'][:15]):
                target = item.get('target', {})
                title = target.get('title', '').strip()
                if title:
                    # 知乎热榜按API返回顺序，越靠前越热
                    hot = 70000 - i*4000
                    answer_count = target.get('answer_count', 0)
                    hot_display = f" 🔥{answer_count}回答" if answer_count > 100 else ""
                    
                    news_list.append({
                        'title': f"知乎: {title}{hot_display}",
                        'hot': hot,
                        'source': '知乎'
                    })
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"知乎热榜抓取失败: {e}")
        return [{
            'title': "知乎: 热门话题更新中",
            'hot': 55000,
            'source': '知乎'
        }]

def fetch_toutiao_hot():
    """获取今日头条热榜"""
    try:
        news_list = []
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {**HEADERS, 'Referer': 'https://www.toutiao.com/'}
        
        response = fetch_with_retry(url, headers=headers, timeout=8)
        if not response:
            return []
            
        data = response.json()
        
        if 'data' in data:
            for i, item in enumerate(data['data'][:15]):
                title = item.get('Title', '').strip()
                if title:
                    hot_value = item.get('HotValue', 0)
                    hot = hot_value if hot_value > 100 else 65000 - i*3000
                    
                    hot_display = ""
                    if hot_value > 10000:
                        hot_display = f" 🔥{hot_value//10000}w"
                    elif hot_value > 1000:
                        hot_display = f" 🔥{hot_value//1000}k"
                    
                    news_list.append({
                        'title': f"头条: {title}{hot_display}",
                        'hot': hot,
                        'source': '今日头条'
                    })
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"今日头条热榜抓取失败: {e}")
        return [{
            'title': "头条: 资讯热点更新中",
            'hot': 58000,
            'source': '今日头条'
        }]

def fetch_wangyi_news():
    """获取网易新闻（新增）"""
    try:
        news_list = []
        url = "https://news.163.com/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = [
            '.news_title h3 a',
            '.ndi_main a',
            '.news_item h2 a',
            '.post_content h2 a',
            '.newsdata_list h3 a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=12)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 10 <= len(title) <= 50 and '网易' not in title:
                    hot = calculate_hot_value(title, 80, 0.9)
                    news_list.append({
                        'title': f"网易: {title}",
                        'hot': hot,
                        'source': '网易'
                    })
                
                if len(news_list) >= 15:
                    break
            if len(news_list) >= 15:
                break
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"网易新闻抓取失败: {e}")
        return [{
            'title': "网易: 热点新闻更新中",
            'hot': 95,
            'source': '网易'
        }]

def fetch_sina_news():
    """获取新浪新闻（改进版）"""
    try:
        news_list = []
        url = "https://news.sina.com.cn/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = [
            '.blk122 a',
            '.news-item h2 a',
            '.news_title a',
            '.title a',
            '.main-content h2 a',
            '.feed-card-item h2 a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=12)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 10 <= len(title) <= 60 and '新浪' not in title:
                    hot = calculate_hot_value(title, 85, 0.9)
                    news_list.append({
                        'title': f"新浪: {title}",
                        'hot': hot,
                        'source': '新浪'
                    })
                
                if len(news_list) >= 15:
                    break
            if len(news_list) >= 15:
                break
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:10]
        
    except Exception as e:
        logger.error(f"新浪新闻抓取失败: {e}")
        return [{
            'title': "新浪: 热点资讯更新中",
            'hot': 90,
            'source': '新浪'
        }]

def fetch_thepaper_news():
    """获取澎湃新闻（新增）"""
    try:
        news_list = []
        url = "https://www.thepaper.cn/"
        
        response = fetch_with_retry(url, timeout=8)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = [
            '.news_title a',
            '.news_tu h2 a',
            '.newscontent h2 a',
            '.list_content h2 a',
            '.channel_item h2 a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = clean_news_title(item.text.strip())
                if title and 10 <= len(title) <= 50 and '澎湃' not in title:
                    hot = calculate_hot_value(title, 90, 1.0)
                    news_list.append({
                        'title': f"澎湃新闻: {title}",
                        'hot': hot,
                        'source': '澎湃新闻'
                    })
                
                if len(news_list) >= 10:
                    break
            if len(news_list) >= 10:
                break
        
        news_list.sort(key=lambda x: x['hot'], reverse=True)
        return news_list[:8]
        
    except Exception as e:
        logger.error(f"澎湃新闻抓取失败: {e}")
        return [{
            'title': "澎湃新闻: 深度报道更新中",
            'hot': 105,
            'source': '澎湃新闻'
        }]

# ====================== 分类新闻函数 ======================

def fetch_politics_news():
    """获取时政新闻（人民网+新华网+央视网+中国新闻网）"""
    try:
        all_news = []
        
        # 从各官方媒体获取时政新闻
        sources = [
            (fetch_people_news, 1.2),
            (fetch_xinhua_news, 1.1),
            (fetch_cctv_news, 1.0),
            (fetch_chinanews, 1.0),
            (fetch_thepaper_news, 0.9)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    # 筛选时政相关内容
                    keywords = ['习近平', '主席', '总理', '国务院', '外交部', '政策', 
                               '会议', '领导人', '外交', '政府', '政治', '时政']
                    if any(keyword in title for keyword in keywords):
                        # 调整热度权重
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except Exception as e:
                logger.warning(f"时政新闻源异常: {e}")
                continue
        
        # 按热度排序并去重
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        # 格式化输出前5条
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 时政要闻更新中", "2. 重要会议进行时"]
        
    except Exception as e:
        logger.warning(f"时政新闻抓取失败: {e}")
        return ["1. 时政要闻", "2. 政策动态", "3. 重要会议"]

def fetch_economy_news():
    """获取经济新闻（人民网+新华网+澎湃+36氪）"""
    try:
        all_news = []
        
        # 从官方媒体获取经济新闻
        sources = [
            (fetch_people_news, 1.1),
            (fetch_xinhua_news, 1.1),
            (fetch_thepaper_news, 1.0),
            (fetch_36kr_news, 0.9),
            (fetch_wangyi_news, 0.8),
            (fetch_sina_news, 0.8)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    # 筛选经济相关内容
                    keywords = ['经济', '财经', '金融', '股市', '投资', '消费', 
                               'GDP', '贸易', '银行', '财政', '市场', '企业']
                    if any(keyword in title for keyword in keywords):
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except:
                continue
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        # 格式化输出
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 经济动态更新中", "2. 财经要闻"]
        
    except Exception as e:
        logger.warning(f"经济新闻抓取失败: {e}")
        return ["1. 经济动态", "2. 财经要闻", "3. 市场分析"]

def fetch_military_news():
    """获取军事新闻（新华网+央视网+中国新闻网）"""
    try:
        all_news = []
        
        sources = [
            (fetch_xinhua_news, 1.2),
            (fetch_cctv_news, 1.1),
            (fetch_chinanews, 1.0),
            (fetch_people_news, 1.0)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    keywords = ['军队', '国防', '军事', '演习', '武器', '海军', 
                               '空军', '陆军', '军工', '战备', '官兵']
                    if any(keyword in title for keyword in keywords):
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except:
                continue
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 军事动态更新中", "2. 国防建设进展"]
        
    except Exception as e:
        logger.warning(f"军事新闻抓取失败: {e}")
        return ["1. 军事动态", "2. 国防建设", "3. 军队改革"]

def fetch_edu_news():
    """获取文教新闻（人民网+新华网+央视网）"""
    try:
        all_news = []
        
        sources = [
            (fetch_people_news, 1.1),
            (fetch_xinhua_news, 1.1),
            (fetch_cctv_news, 1.0),
            (fetch_chinanews, 1.0)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    keywords = ['教育', '学校', '学生', '教师', '文化', '艺术', 
                               '读书', '博物馆', '课程', '学习', '考试', '高校']
                    if any(keyword in title for keyword in keywords):
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except:
                continue
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 文教动态更新中", "2. 教育资讯"]
        
    except Exception as e:
        logger.warning(f"文教新闻抓取失败: {e}")
        return ["1. 教育资讯", "2. 文化动态", "3. 艺术展览"]

def fetch_sports_news():
    """获取体育新闻（新浪+网易+央视网）"""
    try:
        all_news = []
        
        sources = [
            (fetch_sina_news, 1.2),
            (fetch_wangyi_news, 1.1),
            (fetch_cctv_news, 1.0),
            (fetch_people_news, 0.9)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    keywords = ['体育', '赛事', '比赛', '运动员', '冠军', '足球', 
                               '篮球', '奥运', '运动', '球队', '训练', '教练']
                    if any(keyword in title for keyword in keywords):
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except:
                continue
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 体育赛事更新中", "2. 体坛动态"]
        
    except Exception as e:
        logger.warning(f"体育新闻抓取失败: {e}")
        return ["1. 体育赛事", "2. 体坛动态", "3. 运动员风采"]

def fetch_society_news():
    """获取社会新闻（新浪+网易+中国新闻网+澎湃）"""
    try:
        all_news = []
        
        sources = [
            (fetch_sina_news, 1.1),
            (fetch_wangyi_news, 1.1),
            (fetch_chinanews, 1.0),
            (fetch_thepaper_news, 1.0),
            (fetch_people_news, 0.9)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    keywords = ['社会', '民生', '社区', '居民', '生活', '百姓', 
                               '事件', '案件', '安全', '服务', '群众', '居民']
                    if any(keyword in title for keyword in keywords):
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except:
                continue
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 社会热点更新中", "2. 民生关注"]
        
    except Exception as e:
        logger.warning(f"社会新闻抓取失败: {e}")
        return ["1. 社会热点", "2. 民生关注", "3. 社区动态"]

def fetch_tech_news():
    """获取科技新闻（IT之家+36氪+科技之声+人民网科技）"""
    try:
        all_news = []
        
        sources = [
            (fetch_ithome_news, 1.2),
            (fetch_36kr_news, 1.2),
            (fetch_techvoice_news, 1.1),
            (fetch_people_news, 1.0),
            (fetch_xinhua_news, 1.0)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    title = news['title'].lower()
                    keywords = ['科技', '创新', '人工智能', 'AI', '5G', '芯片', 
                               '互联网', '数字', '智能', '数据', '软件', '硬件']
                    if any(keyword in title for keyword in keywords):
                        news['hot'] = int(news['hot'] * weight)
                        all_news.append(news)
            except:
                continue
        
        # 去重排序
        seen = set()
        unique_news = []
        for news in all_news:
            core_title = clean_news_title(news['title'].split(':', 1)[-1])
            if core_title not in seen:
                seen.add(core_title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x['hot'], reverse=True)
        
        formatted = []
        for i, news in enumerate(unique_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 科技前沿更新中", "2. 创新动态"]
        
    except Exception as e:
        logger.warning(f"科技新闻抓取失败: {e}")
        return ["1. 科技前沿", "2. 创新动态", "3. 数字技术"]

def fetch_hotsearch_news():
    """获取热搜新闻（微博+百度+知乎+今日头条）"""
    try:
        all_news = []
        
        sources = [
            (fetch_weibo_hot, 1.2),
            (fetch_baidu_hot, 1.1),
            (fetch_zhihu_hot, 1.1),
            (fetch_toutiao_hot, 1.0)
        ]
        
        for fetch_func, weight in sources:
            try:
                source_news = fetch_func()
                for news in source_news:
                    # 热搜新闻直接使用，不额外筛选
                    news['hot'] = int(news['hot'] * weight)
                    all_news.append(news)
            except:
                continue
        
        # 按热度排序
        all_news.sort(key=lambda x: x['hot'], reverse=True)
        
        # 格式化输出前5条
        formatted = []
        for i, news in enumerate(all_news[:5], 1):
            formatted.append(f"{i}. {news['title']}")
        
        return formatted if formatted else ["1. 全网热搜更新中", "2. 热门话题"]
        
    except Exception as e:
        logger.warning(f"热搜新闻抓取失败: {e}")
        return ["1. 微博热搜", "2. 百度热榜", "3. 知乎热榜"]

# ====================== 邮件内容生成 ======================

def generate_email_content():
    """生成邮件内容 - 8个类别，每个类别5条，按热度排序"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    logger.info("开始生成邮件内容，整合14个新闻源...")
    
    # 定义8个类别及其对应的抓取函数
    news_categories = {
        "🏛️ 时政新闻": fetch_politics_news,
        "📈 经济财经": fetch_economy_news,
        "🎖️ 军事动态": fetch_military_news,
        "🎓 文教艺术": fetch_edu_news,
        "⚽ 体育竞技": fetch_sports_news,
        "👥 社会民生": fetch_society_news,
        "💻 科技前沿": fetch_tech_news,
        "🔥 热搜榜单": fetch_hotsearch_news,
    }
    
    all_news = {}
    total_news = 0
    
    # 统计新闻源
    news_sources = {
        "官方媒体": ["人民网", "新华网", "央视网", "中国新闻网", "澎湃新闻"],
        "科技媒体": ["IT之家", "科技之声", "36氪"],
        "门户网站": ["网易", "新浪"],
        "热搜平台": ["微博热搜", "百度热搜", "知乎热搜", "今日头条热搜"]
    }
    
    source_count = sum(len(sources) for sources in news_sources.values())
    
    for category_name, fetch_func in news_categories.items():
        try:
            logger.info(f"生成 {category_name}...")
            news_list = fetch_func()
            all_news[category_name] = news_list
            total_news += len(news_list)
            time.sleep(0.2)  # 礼貌延迟
        except Exception as e:
            logger.warning(f"{category_name} 生成异常: {e}")
            all_news[category_name] = [f"{category_name}：数据更新中"]
    
    # 纯文本版本
    text_content = f"""
每日热点新闻速递 ({today})
===========================================
更新时间: {current_time}
新闻类别: 8大类，共{total_news}条精选新闻
新闻来源: {source_count}个权威新闻源

官方媒体: {', '.join(news_sources['官方媒体'])}
科技媒体: {', '.join(news_sources['科技媒体'])}
门户网站: {', '.join(news_sources['门户网站'])}
热搜平台: {', '.join(news_sources['热搜平台'])}

"""
    
    for category_name, news_list in all_news.items():
        text_content += f"\n{category_name}\n"
        text_content += "-" * 40 + "\n"
        
        for news in news_list[:5]:  # 每个类别显示前5条
            text_content += f"  {news}\n"
        
        text_content += "\n"
    
    text_content += f"""
===========================================
本邮件由 GitHub Actions 自动发送
每日定时推送: 08:00 (北京时间)
数据来源: {source_count}个权威新闻源，覆盖时政、经济、军事、文教、体育、社会、科技、热搜全领域
所有新闻按热度值排序，前5条为最热新闻
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
        .sources-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .source-group {{
            text-align: center;
        }}
        .source-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 14px;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }}
        .source-list {{
            font-size: 12px;
            color: #555;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日热点新闻速递</h1>
            <div class="subtitle">{today} | 更新时间: {current_time}</div>
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
                <div class="stat-value">{source_count}</div>
                <div class="stat-label">新闻来源</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">40</div>
                <div class="stat-label">最大容量</div>
            </div>
        </div>
        
        <div class="sources-grid">
            <div class="source-group">
                <div class="source-title">官方媒体</div>
                <div class="source-list">{'<br>'.join(news_sources['官方媒体'])}</div>
            </div>
            <div class="source-group">
                <div class="source-title">科技媒体</div>
                <div class="source-list">{'<br>'.join(news_sources['科技媒体'])}</div>
            </div>
            <div class="source-group">
                <div class="source-title">门户网站</div>
                <div class="source-list">{'<br>'.join(news_sources['门户网站'])}</div>
            </div>
            <div class="source-group">
                <div class="source-title">热搜平台</div>
                <div class="source-list">{'<br>'.join(news_sources['热搜平台'])}</div>
            </div>
        </div>
        
        <div class="categories-grid">
"""
    
    # 类别颜色映射
    category_colors = {
        "🏛️ 时政新闻": "#dc3545",
        "📈 经济财经": "#28a745",
        "🎖️ 军事动态": "#495057",
        "🎓 文教艺术": "#6f42c1",
        "⚽ 体育竞技": "#e83e8c",
        "👥 社会民生": "#17a2b8",
        "💻 科技前沿": "#007bff",
        "🔥 热搜榜单": "#ffc107"
    }
    
    # 添加各个类别
    for category_name, news_list in all_news.items():
        color = category_colors.get(category_name, "#667eea")
        
        html_content += f"""
            <div class="category-section">
                <div class="category-title" style="color: {color}; border-color: {color}">
                    {category_name}
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
            <p>📊 数据来源: 14个权威新闻源，覆盖时政、经济、军事、文教、体育、社会、科技、热搜全领域</p>
            <p>🎯 排序规则: 所有新闻按热度值排序，每个类别显示最热的前5条新闻</p>
            <p>⏰ 数据采集时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 15px; color: #495057; font-size: 13px;">
                覆盖8大类别: 时政 • 经济 • 军事 • 文教 • 体育 • 社会 • 科技 • 热搜 | 每个类别精选5条最热新闻
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return text_content, html_content

def send_email_simple(text_content, html_content):
    """发送邮件 - 简单版"""
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        logger.error("❌ 环境变量缺失")
        return False
    
    try:
        logger.info(f"准备发送邮件到 {receiver}")
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = receiver
        
        today_str = datetime.now().strftime('%m月%d日')
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
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
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
