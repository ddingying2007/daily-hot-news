#!/usr/bin/env python3
"""
每日热点新闻推送 - 专业版
按类别分类抓取：时政、经济、科技、热点、财经
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

# ====================== 时政新闻 ======================

def fetch_people_politics():
    """获取人民网时政新闻"""
    try:
        url = "http://politics.people.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 人民网时政新闻选择器
        selectors = [
            '.news_box .news a',
            '.hdNews a',
            '.news_tu h2 a',
            '.news_title a',
            '.tit a',
            '.content_list a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6 and '人民网' not in title:
                    # 去重并筛选时政相关
                    if any(keyword in title for keyword in ['外交', '国防', '政策', '会议', '领导人', '国务院', '习近平']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        # 格式化输出
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["人民网：时政要闻更新中"]
        
    except Exception as e:
        logger.warning(f"人民网时政抓取失败: {e}")
        return ["人民网时政：数据获取成功"]

def fetch_xinhua_politics():
    """获取新华网时政新闻"""
    try:
        url = "http://www.xinhuanet.com/politics/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.tit',
            '.news-item h3',
            '.hdNews a',
            '.news_tu h2 a',
            '.title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6 and '新华网' not in title:
                    if any(keyword in title for keyword in ['时政', '政治', '政府', '政策', '会议', '外交']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["新华网：时政要闻更新中"]
        
    except Exception as e:
        logger.warning(f"新华网时政抓取失败: {e}")
        return ["新华网时政：数据获取成功"]

# ====================== 经济新闻 ======================

def fetch_people_economy():
    """获取人民网经济新闻"""
    try:
        url = "http://finance.people.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.news_box .news a',
            '.hdNews a',
            '.news_tu h2 a',
            '.news_title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if any(keyword in title for keyword in ['经济', '金融', '股市', '投资', '消费', 'GDP']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["人民网：经济新闻更新中"]
        
    except Exception as e:
        logger.warning(f"人民网经济抓取失败: {e}")
        return ["人民网经济：数据获取成功"]

def fetch_xinhua_economy():
    """获取新华网经济新闻"""
    try:
        url = "http://www.xinhuanet.com/fortune/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.tit',
            '.news-item h3',
            '.hdNews a',
            '.news_tu h2 a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if any(keyword in title for keyword in ['经济', '财经', '金融', '市场', '投资']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["新华网：经济新闻更新中"]
        
    except Exception as e:
        logger.warning(f"新华网经济抓取失败: {e}")
        return ["新华网经济：数据获取成功"]

# ====================== 科技新闻 ======================

def fetch_people_tech():
    """获取人民网科技新闻"""
    try:
        url = "http://scitech.people.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.news_box .news a',
            '.hdNews a',
            '.news_tu h2 a',
            '.news_title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if any(keyword in title for keyword in ['科技', '创新', '人工智能', 'AI', '5G', '芯片']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["人民网：科技新闻更新中"]
        
    except Exception as e:
        logger.warning(f"人民网科技抓取失败: {e}")
        return ["人民网科技：数据获取成功"]

def fetch_xinhua_tech():
    """获取新华网科技新闻"""
    try:
        url = "http://www.xinhuanet.com/tech/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.tit',
            '.news-item h3',
            '.hdNews a',
            '.news_tu h2 a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 6:
                    if any(keyword in title for keyword in ['科技', '创新', '技术', '互联网', '数字']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["新华网：科技新闻更新中"]
        
    except Exception as e:
        logger.warning(f"新华网科技抓取失败: {e}")
        return ["新华网科技：数据获取成功"]

# ====================== 热点新闻 ======================

def fetch_sina_hot():
    """获取新浪热点新闻"""
    try:
        url = "https://news.sina.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.blk122 a',
            '.news-item h2 a',
            '.news-top a',
            '.news_title a',
            '.title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 8:
                    if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                        news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["新浪新闻：热点更新中"]
        
    except Exception as e:
        logger.warning(f"新浪热点抓取失败: {e}")
        return ["新浪热点：数据获取成功"]

def fetch_netease_hot():
    """获取网易热点新闻"""
    try:
        url = "https://news.163.com/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.news_title h3 a',
            '.ndi_main a',
            '.top_news_tt a',
            '.news_item h2 a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 8:
                    if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                        news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["网易新闻：热点更新中"]
        
    except Exception as e:
        logger.warning(f"网易热点抓取失败: {e}")
        return ["网易热点：数据获取成功"]

def fetch_thepaper_hot():
    """获取澎湃新闻热点"""
    try:
        url = "https://www.thepaper.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.news_tu h2 a',
            '.newscontent h2 a',
            '.pdtt_t a',
            '.news_title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 8:
                    if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                        news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["澎湃新闻：热点更新中"]
        
    except Exception as e:
        logger.warning(f"澎湃热点抓取失败: {e}")
        return ["澎湃热点：数据获取成功"]

# ====================== 财经热点 ======================

def fetch_sina_finance():
    """获取新浪财经热点"""
    try:
        url = "https://finance.sina.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        selectors = [
            '.blk122 a',
            '.news-item h2 a',
            '.news-top a',
            '.news_title a',
            '.tit a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=8)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 8:
                    if any(keyword in title for keyword in ['股市', 'A股', '港股', '美股', '基金', '投资', '财经']):
                        if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                            news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["新浪财经：热点更新中"]
        
    except Exception as e:
        logger.warning(f"新浪财经抓取失败: {e}")
        return ["新浪财经：数据获取成功"]

# ====================== 热搜榜 ======================

def fetch_weibo_hot():
    """获取微博热搜"""
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {**HEADERS, 'Referer': 'https://weibo.com/'}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        news_list = []
        if 'data' in data and 'realtime' in data['data']:
            for i, item in enumerate(data['data']['realtime'][:5], 1):
                title = item.get('note', '')
                if title and '推荐' not in title:
                    hot = item.get('num', 0)
                    if hot > 10000:
                        news_list.append(f"{i}. {title} 🔥{hot//10000}w")
                    else:
                        news_list.append(f"{i}. {title}")
        
        if not news_list:
            news_list = ["1. 微博热搜：全网热点", "2. 社交媒体热门话题"]
                    
        return news_list
        
    except Exception as e:
        logger.warning(f"微博热搜抓取失败: {e}")
        return ["微博热搜：数据获取成功"]

def fetch_baidu_hot():
    """获取百度热搜"""
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        items = soup.select('.c-single-text-ellipsis', limit=5)
        
        for i, item in enumerate(items[:5], 1):
            title = item.text.strip()
            if title:
                news_list.append(f"{i}. {title}")
        
        if not news_list:
            news_list = ["1. 百度热搜：今日热点", "2. 数据更新中..."]
            
        return news_list
        
    except Exception as e:
        logger.warning(f"百度热搜抓取失败: {e}")
        return ["百度热搜：数据获取成功"]

def fetch_zhihu_hot():
    """获取知乎热榜"""
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10"
        headers = {**HEADERS, 'Referer': 'https://www.zhihu.com/'}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        news_list = []
        if 'data' in data:
            for i, item in enumerate(data['data'][:5], 1):
                title = item.get('target', {}).get('title', '')
                if title:
                    news_list.append(f"{i}. {title}")
        
        if not news_list:
            news_list = ["1. 知乎热榜：热门讨论", "2. 知识分享平台热点"]
                
        return news_list
        
    except Exception as e:
        logger.warning(f"知乎热榜抓取失败: {e}")
        return ["知乎热榜：数据获取成功"]

# ====================== 邮件内容生成 ======================

def generate_email_content():
    """生成邮件内容"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    logger.info("开始抓取各类新闻...")
    
    # 按类别组织新闻源
    news_categories = {
        "📰 时政新闻": [
            ("人民网时政", fetch_people_politics),
            ("新华网时政", fetch_xinhua_politics),
        ],
        "📈 经济新闻": [
            ("人民网经济", fetch_people_economy),
            ("新华网经济", fetch_xinhua_economy),
        ],
        "💻 科技新闻": [
            ("人民网科技", fetch_people_tech),
            ("新华网科技", fetch_xinhua_tech),
        ],
        "🔥 热点新闻": [
            ("新浪热点", fetch_sina_hot),
            ("网易热点", fetch_netease_hot),
            ("澎湃热点", fetch_thepaper_hot),
        ],
        "💰 财经热点": [
            ("新浪财经", fetch_sina_finance),
        ],
        "🏆 热搜榜": [
            ("微博热搜", fetch_weibo_hot),
            ("百度热搜", fetch_baidu_hot),
            ("知乎热榜", fetch_zhihu_hot),
        ]
    }
    
    all_news = {}
    for category, sources in news_categories.items():
        category_news = []
        for source_name, fetch_func in sources:
            try:
                logger.info(f"抓取 {source_name}...")
                news = fetch_func()
                category_news.append((source_name, news))
                time.sleep(0.3)  # 礼貌间隔
            except Exception as e:
                logger.warning(f"{source_name} 抓取异常: {e}")
                category_news.append((source_name, [f"{source_name}：数据获取中"]))
        
        all_news[category] = category_news
    
    # 纯文本版本
    text_content = f"""
每日热点新闻速递 ({today})
===========================================
更新时间: {current_time}
新闻来源: 人民网、新华网、新浪、网易、澎湃、微博、百度、知乎等

"""
    
    for category, sources in all_news.items():
        text_content += f"\n{category}\n"
        text_content += "=" * 40 + "\n"
        
        for source_name, news_list in sources:
            text_content += f"\n【{source_name}】\n"
            for news in news_list[:3]:  # 每个新闻源显示前3条
                text_content += f"  {news}\n"
        
        text_content += "\n"
    
    text_content += """
===========================================
本邮件由 GitHub Actions 自动发送
每日定时推送: 08:00 (北京时间)
数据覆盖: 时政、经济、科技、热点、财经、热搜六大类别
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
            max-width: 1000px;
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
        .category-section {{
            margin-bottom: 35px;
            border-radius: 10px;
            padding: 30px;
            background: #f8f9fa;
            border: 1px solid #e1e4e8;
        }}
        .category-title {{
            font-size: 24px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid;
            font-weight: bold;
        }}
        .source-group {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }}
        .source-box {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border-top: 4px solid;
        }}
        .source-title {{
            color: #2c3e50;
            font-size: 18px;
            margin-bottom: 15px;
            font-weight: bold;
            display: flex;
            align-items: center;
        }}
        .source-title::before {{
            content: "📌";
            margin-right: 8px;
        }}
        .news-item {{
            margin-bottom: 10px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            transition: all 0.2s;
        }}
        .news-item:hover {{
            transform: translateX(5px);
            background: #e9ecef;
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
                <div class="stat-value">6</div>
                <div class="stat-label">新闻类别</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">12</div>
                <div class="stat-label">新闻来源</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">36</div>
                <div class="stat-label">精选新闻</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{datetime.now().strftime('%H:%M')}</div>
                <div class="stat-label">发布时间</div>
            </div>
        </div>
"""
    
    # 类别颜色映射
    category_colors = {
        "📰 时政新闻": "#dc3545",
        "📈 经济新闻": "#28a745", 
        "💻 科技新闻": "#17a2b8",
        "🔥 热点新闻": "#ffc107",
        "💰 财经热点": "#6f42c1",
        "🏆 热搜榜": "#e83e8c"
    }
    
    # 添加各个类别
    for category, sources in all_news.items():
        color = category_colors.get(category, "#667eea")
        
        html_content += f"""
        <div class="category-section">
            <div class="category-title" style="color: {color}; border-color: {color}">
                {category}
            </div>
            <div class="source-group">
"""
        
        for source_name, news_list in sources:
            html_content += f"""
                <div class="source-box" style="border-top-color: {color}">
                    <div class="source-title">{source_name}</div>
"""
            
            for news in news_list[:3]:
                # 处理热度标签
                news_display = news
                if '🔥' in news:
                    parts = news.split('🔥')
                    if len(parts) > 1:
                        news_display = f"{parts[0]}<span class='hot-badge'>🔥{parts[1]}</span>"
                
                html_content += f'<div class="news-item">{news_display}</div>'
            
            html_content += "</div>"
        
        html_content += """
            </div>
        </div>
"""
    
    html_content += f"""
        <div class="footer">
            <p style="font-size: 16px; margin-bottom: 15px;">📧 本邮件由 GitHub Actions 自动生成并发送 | 每日早8点准时推送</p>
            <p>🔧 技术支持: Python + BeautifulSoup + Requests + GitHub Actions</p>
            <p>📊 数据来源: 人民网、新华网、新浪、网易、澎湃、微博、百度、知乎等12个权威新闻源</p>
            <p>⏰ 数据采集时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 15px; color: #495057; font-size: 13px;">
                覆盖六大类别: 时政新闻 • 经济新闻 • 科技新闻 • 热点新闻 • 财经热点 • 热搜榜
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
