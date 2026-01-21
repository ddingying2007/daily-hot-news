#!/usr/bin/env python3
"""
每日热点新闻推送 - 主程序
简化版本，确保能正常运行
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
import json

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_baidu_hot():
    """获取百度热搜"""
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        # 百度热搜标题
        items = soup.select('.c-single-text-ellipsis', limit=10)
        
        for i, item in enumerate(items[:10], 1):
            title = item.text.strip()
            if title and len(title) > 3:
                news_list.append(f"{i}. {title}")
        
        if not news_list:
            news_list = ["1. 百度热搜：数据获取中..."]
            
        return news_list
        
    except Exception as e:
        logger.error(f"百度热搜抓取失败: {e}")
        return ["百度热搜：暂时无法获取"]

def fetch_zhihu_hot():
    """获取知乎热榜"""
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.zhihu.com/'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        news_list = []
        for i, item in enumerate(data['data'][:10], 1):
            title = item['target']['title']
            if title:
                news_list.append(f"{i}. {title}")
                
        return news_list
        
    except Exception as e:
        logger.error(f"知乎热榜抓取失败: {e}")
        return ["知乎热榜：暂时无法获取"]

def fetch_weibo_hot():
    """获取微博热搜"""
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        news_list = []
        for i, item in enumerate(data['data']['realtime'][:10], 1):
            title = item['note']
            hot = item.get('num', 0)
            if title:
                if hot > 10000:
                    news_list.append(f"{i}. {title} 🔥{hot//10000}w")
                else:
                    news_list.append(f"{i}. {title}")
                    
        return news_list
        
    except Exception as e:
        logger.error(f"微博热搜抓取失败: {e}")
        return ["微博热搜：暂时无法获取"]

def generate_email_content():
    """生成邮件内容"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # 获取新闻
    logger.info("开始抓取新闻...")
    baidu_news = fetch_baidu_hot()
    zhihu_news = fetch_zhihu_hot()
    weibo_news = fetch_weibo_hot()
    
    # 纯文本版本
    text_content = f"""
📰 每日热点新闻速递 ({today})
===========================================
更新时间: {current_time}

【百度热搜】
{chr(10).join(baidu_news[:5])}

【知乎热榜】
{chr(10).join(zhihu_news[:5])}

【微博热搜】
{chr(10).join(weibo_news[:5])}

===========================================
本邮件由 GitHub Actions 自动发送
每日定时推送: 08:00 (北京时间)
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
            max-width: 800px;
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
        .section {{
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .section-title {{
            color: #0366d6;
            font-size: 20px;
            margin-bottom: 15px;
            border-bottom: 2px solid #0366d6;
            padding-bottom: 8px;
        }}
        .news-item {{
            margin-bottom: 10px;
            padding: 10px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #0366d6;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e4e8;
            color: #6a737d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日热点新闻速递</h1>
            <p>{today} | 更新时间: {current_time}</p>
        </div>
        
        <div class="section">
            <div class="section-title">🔥 百度热搜</div>
            {''.join([f'<div class="news-item">{news}</div>' for news in baidu_news[:5]])}
        </div>
        
        <div class="section">
            <div class="section-title">💡 知乎热榜</div>
            {''.join([f'<div class="news-item">{news}</div>' for news in zhihu_news[:5]])}
        </div>
        
        <div class="section">
            <div class="section-title">🐦 微博热搜</div>
            {''.join([f'<div class="news-item">{news}</div>' for news in weibo_news[:5]])}
        </div>
        
        <div class="footer">
            <p>📧 本邮件由 GitHub Actions 自动生成并发送</p>
            <p>⏰ 每日早8点准时推送 (北京时间)</p>
            <p>🔧 技术支持: Python + GitHub Actions</p>
        </div>
    </div>
</body>
</html>
"""
    
    return text_content, html_content

def send_email(text_content, html_content):
    """发送邮件"""
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
        msg['From'] = f"新闻速递 <{sender}>"
        msg['To'] = receiver
        msg['Subject'] = f"📰 每日热点新闻 - {datetime.now().strftime('%m月%d日')}"
        
        # 添加纯文本版本
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(part1)
        
        # 添加HTML版本
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        # 发送邮件
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
        success = send_email(text_content, html_content)
        
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
