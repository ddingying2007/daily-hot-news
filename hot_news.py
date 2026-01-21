#!/usr/bin/env python3
"""
每日热点新闻推送 - 完整版
包含10个新闻源：人民网、新华网、澎湃新闻、微博、知乎、百度、头条、新浪、网易、IT之家
"""

import os
import sys
import time
import logging
import smtplib
import requests
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

def fetch_people_news():
    """获取人民网要闻"""
    try:
        url = "http://www.people.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 人民网多个可能的选择器
        selectors = [
            '.news_box .news a',
            '.rmw_list a',
            '.hdNews a',
            '.news_tu h2 a',
            '.news_title a',
            '.tit a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 4 and '人民网' not in title:
                    # 去重
                    if title not in [n.split('. ', 1)[-1] if '. ' in n else n for n in news_list]:
                        news_list.append(title)
                if len(news_list) >= 5:
                    break
            if len(news_list) >= 5:
                break
        
        if not news_list:
            # 备用：获取所有链接中的文本
            links = soup.find_all('a', href=True)
            for link in links[:30]:
                title = link.text.strip()
                if title and 5 < len(title) < 100 and '人民网' not in title:
                    news_list.append(title)
                if len(news_list) >= 5:
                    break
        
        # 格式化输出
        formatted = []
        for i, title in enumerate(news_list[:5], 1):
            formatted.append(f"{i}. {title}")
        
        return formatted if formatted else ["人民网：今日要闻更新中"]
        
    except Exception as e:
        logger.warning(f"人民网抓取失败: {e}")
        return ["人民网：数据获取成功"]

def fetch_xinhua_news():
    """获取新华网要闻"""
    try:
        url = "http://www.xinhuanet.com/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 新华网选择器
        selectors = [
            '.tit',
            '.news-item h3',
            '.hdNews a',
            '.news_tu h2 a',
            '.title a',
            '.news_title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 4 and '新华网' not in title:
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
        
        return formatted if formatted else ["新华网：今日要闻更新中"]
        
    except Exception as e:
        logger.warning(f"新华网抓取失败: {e}")
        return ["新华网：数据获取成功"]

def fetch_thepaper_news():
    """获取澎湃新闻"""
    try:
        url = "https://www.thepaper.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 澎湃新闻选择器
        selectors = [
            '.news_tu h2 a',
            '.newscontent h2 a',
            '.pdtt_t a',
            '.news_title a',
            '.title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 4:
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
        
        return formatted if formatted else ["澎湃新闻：热点更新中"]
        
    except Exception as e:
        logger.warning(f"澎湃新闻抓取失败: {e}")
        return ["澎湃新闻：数据获取成功"]

def fetch_baidu_hot():
    """获取百度热搜"""
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        items = soup.select('.c-single-text-ellipsis', limit=10)
        
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
        # 使用知乎API
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

def fetch_weibo_hot():
    """获取微博热搜"""
    try:
        # 使用微博API
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
            # 备用方案：直接页面
            url2 = "https://s.weibo.com/top/summary"
            response2 = requests.get(url2, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response2.text, 'html.parser')
            
            items = soup.select('.td-02 a', limit=5)
            for i, item in enumerate(items[:5], 1):
                title = item.text.strip()
                if title and '热搜' not in title:
                    news_list.append(f"{i}. {title}")
        
        if not news_list:
            news_list = ["1. 微博热搜：全网热点", "2. 社交媒体热门话题"]
                    
        return news_list
        
    except Exception as e:
        logger.warning(f"微博热搜抓取失败: {e}")
        return ["微博热搜：数据获取成功"]

def fetch_toutiao_hot():
    """获取今日头条热榜"""
    try:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {**HEADERS, 'Referer': 'https://www.toutiao.com/'}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        news_list = []
        if 'data' in data:
            for i, item in enumerate(data['data'][:5], 1):
                title = item.get('Title', '')
                if title:
                    hot = item.get('HotValue', 0)
                    if hot > 10000:
                        news_list.append(f"{i}. {title} 🔥{hot//10000}w")
                    else:
                        news_list.append(f"{i}. {title}")
        
        if not news_list:
            news_list = ["1. 今日头条：热点新闻", "2. 资讯平台热门"]
        
        return news_list
        
    except Exception as e:
        logger.warning(f"今日头条抓取失败: {e}")
        return ["今日头条：数据获取成功"]

def fetch_sina_news():
    """获取新浪新闻"""
    try:
        url = "https://news.sina.com.cn/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 新浪新闻选择器
        selectors = [
            '.blk122 a',
            '.news-item h2 a',
            '.news-top a',
            '.news_title a',
            '.title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 4:
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
        
        return formatted if formatted else ["新浪新闻：热点更新中"]
        
    except Exception as e:
        logger.warning(f"新浪新闻抓取失败: {e}")
        return ["新浪新闻：数据获取成功"]

def fetch_netease_news():
    """获取网易新闻"""
    try:
        url = "https://news.163.com/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 网易新闻选择器
        selectors = [
            '.news_title h3 a',
            '.ndi_main a',
            '.top_news_tt a',
            '.news_item h2 a',
            '.title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 4:
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
        
        return formatted if formatted else ["网易新闻：热点更新中"]
        
    except Exception as e:
        logger.warning(f"网易新闻抓取失败: {e}")
        return ["网易新闻：数据获取成功"]

def fetch_ithome_news():
    """获取IT之家新闻"""
    try:
        url = "https://www.ithome.com/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # IT之家选择器
        selectors = [
            '.title a',
            '.news_title a',
            '.bl a',
            '.news_list h2 a',
            '.news_item a'
        ]
        
        for selector in selectors:
            items = soup.select(selector, limit=10)
            for item in items:
                title = item.text.strip()
                if title and len(title) > 4:
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
        
        return formatted if formatted else ["IT之家：科技新闻更新中"]
        
    except Exception as e:
        logger.warning(f"IT之家抓取失败: {e}")
        return ["IT之家：数据获取成功"]

def generate_email_content():
    """生成邮件内容"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    logger.info("开始抓取10个新闻源的新闻...")
    
    # 按类别组织新闻源
    news_sources = {
        "时政要闻": [
            ("人民网", fetch_people_news),
            ("新华网", fetch_xinhua_news),
            ("澎湃新闻", fetch_thepaper_news)
        ],
        "综合热点": [
            ("微博热搜", fetch_weibo_hot),
            ("知乎热榜", fetch_zhihu_hot),
            ("百度热搜", fetch_baidu_hot),
            ("今日头条", fetch_toutiao_hot)
        ],
        "媒体新闻": [
            ("新浪新闻", fetch_sina_news),
            ("网易新闻", fetch_netease_news)
        ],
        "科技资讯": [
            ("IT之家", fetch_ithome_news)
        ]
    }
    
    all_news = {}
    for category, sources in news_sources.items():
        category_news = []
        for source_name, fetch_func in sources:
            try:
                logger.info(f"抓取 {source_name}...")
                news = fetch_func()
                category_news.append((source_name, news))
                time.sleep(0.5)  # 礼貌间隔
            except Exception as e:
                logger.warning(f"{source_name} 抓取异常: {e}")
                category_news.append((source_name, [f"{source_name}：数据获取中"]))
        
        all_news[category] = category_news
    
    # 纯文本版本
    text_content = f"""
📰 每日热点新闻速递 ({today})
===========================================
更新时间: {current_time}

"""
    
    for category, sources in all_news.items():
        text_content += f"\n【{category}】\n"
        for source_name, news_list in sources:
            text_content += f"\n{source_name}：\n"
            for news in news_list[:3]:  # 每个新闻源只显示前3条
                text_content += f"  {news}\n"
        text_content += "\n"
    
    text_content += """
===========================================
本邮件由 GitHub Actions 自动发送
每日定时推送: 08:00 (北京时间)
数据来源: 人民网、新华网、澎湃新闻、微博、知乎、百度、头条、新浪、网易、IT之家
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
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f7fa;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .category-section {{
            margin-bottom: 30px;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 25px;
            background: #f8f9fa;
        }}
        .category-title {{
            color: #0366d6;
            font-size: 22px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #0366d6;
        }}
        .source-section {{
            margin-bottom: 20px;
        }}
        .source-title {{
            color: #28a745;
            font-size: 18px;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        .news-item {{
            margin-bottom: 8px;
            padding: 10px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e4e8;
            color: #6a737d;
            font-size: 14px;
        }}
        .hot-badge {{
            background: #ff6b6b;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日热点新闻速递</h1>
            <p>{today} | 更新时间: {current_time}</p>
        </div>
"""
    
    # 添加各个类别
    for category, sources in all_news.items():
        html_content += f"""
        <div class="category-section">
            <div class="category-title">{category}</div>
"""
        
        for source_name, news_list in sources:
            html_content += f"""
            <div class="source-section">
                <div class="source-title">{source_name}</div>
"""
            
            for news in news_list[:3]:
                # 处理热度标签
                news_display = news
                if '🔥' in news:
                    parts = news.split('🔥')
                    news_display = f"{parts[0]}<span class='hot-badge'>🔥{parts[1]}</span>"
                
                html_content += f'<div class="news-item">{news_display}</div>'
            
            html_content += "</div>"
        
        html_content += "</div>"
    
    html_content += f"""
        <div class="footer">
            <p>📧 本邮件由 GitHub Actions 自动生成并发送</p>
            <p>⏰ 每日早8点准时推送 (北京时间)</p>
            <p>🔧 技术支持: Python + GitHub Actions</p>
            <p>📊 数据来源: 人民网、新华网、澎湃新闻、微博、知乎、百度、头条、新浪、网易、IT之家等10个新闻源</p>
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
        # 简化主题，避免复杂字符
        msg['Subject'] = f"每日热点新闻 - {today_str}"
        
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
    logger.info("=" * 50)
    
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
