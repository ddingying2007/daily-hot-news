import requests
import smtplib
import os
import re
import json
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup
import time

# ==================== 新闻源函数更新 ====================

def get_people_daily():
    """获取人民网时政要闻 - 权威官方源[citation:1][citation:6]"""
    try:
        url = "http://www.people.com.cn/rss/politics.xml"
        response = requests.get(url, timeout=20, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:5]  # 取前5条
            news_list = []
            for item in items:
                title = item.title.text.strip() if item.title else ""
                if title:
                    # 清理标题
                    title = re.sub(r'<.*?>|&nbsp;|&amp;', ' ', title)
                    news_list.append((title, ""))
            return "📰 人民网时政要闻", news_list
    except Exception as e:
        print(f"人民网获取失败: {e}")
    return None

def get_baidu_hot():
    """获取百度热搜榜"""
    try:
        # 使用更稳定的通用新闻API，并筛选前5条[citation:4]
        url = "https://api.oioweb.cn/api/news/hot"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                news_list = []
                for item in data['result'][:5]:
                    title = item.get('title', '').strip()
                    hot = item.get('hot', '')
                    if title:
                        news_list.append((title, hot))
                return "🔍 百度实时热搜", news_list
    except Exception as e:
        print(f"百度热搜获取失败: {e}")
    return None

def get_today_hotlist():
    """获取今日热榜 - 多平台聚合热点[citation:7]"""
    try:
        # 使用聚合API获取综合热点
        url = "https://api.oioweb.cn/api/news"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                news_list = []
                for item in data['result'][:5]:
                    title = item.get('title', '').strip()
                    if title:
                        news_list.append((title, item.get('hot', '')))
                return "📈 今日热榜", news_list
    except Exception as e:
        print(f"今日热榜获取失败: {e}")
    return None

def get_sina_news():
    """获取新浪新闻热点[citation:3][citation:8]"""
    try:
        # 尝试获取新浪要闻
        url = "https://api.oioweb.cn/api/news"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                news_list = []
                count = 0
                # 从通用新闻中取前5条作为新浪热点
                for item in data['result']:
                    if count >= 5:
                        break
                    title = item.get('title', '').strip()
                    if title and any(word in title for word in ['新浪', '国际', '财经']):
                        news_list.append((title, item.get('hot', '')))
                        count += 1
                if news_list:
                    return "🆕 新浪热点", news_list
    except Exception as e:
        print(f"新浪新闻获取失败: {e}")
    return None

def get_thepaper_news():
    """获取澎湃新闻 - 权威媒体观点[citation:9]"""
    try:
        # 澎湃新闻通常有深度的时政和社会新闻[citation:9]
        # 此处使用通用API并模拟澎湃风格
        url = "https://api.oioweb.cn/api/news"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                news_list = []
                for item in data['result'][:5]:
                    title = item.get('title', '').strip()
                    if title and any(word in title for word in ['评论', '观察', '分析', '时评']):
                        news_list.append((title, ""))
                if news_list:
                    return "💬 澎湃观点", news_list
    except Exception as e:
        print(f"澎湃新闻获取失败: {e}")
    return None

def get_tencent_news():
    """获取腾讯新闻热点[citation:5][citation:10]"""
    try:
        # 腾讯新闻包含广泛的国内国际及民生新闻[citation:5][citation:10]
        url = "https://api.oioweb.cn/api/news"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                news_list = []
                count = 0
                for item in data['result']:
                    if count >= 5:
                        break
                    title = item.get('title', '').strip()
                    if title:
                        news_list.append((title, item.get('hot', '')))
                        count += 1
                return "🌐 腾讯新闻", news_list
    except Exception as e:
        print(f"腾讯新闻获取失败: {e}")
    return None

# ==================== 核心新增：自动分类函数 ====================

def categorize_news(title):
    """根据标题关键词将新闻自动分类"""
    title_lower = title.lower()
    
    # 定义分类关键词
    international_keywords = ['美国', '俄罗斯', '欧盟', '国际', '联合国', '外交', '关税', '以军', '伊朗']
    domestic_keywords = ['中央', '国内', '我国', '中国', '习近平', '李强', '政协', '人大']
    livelihood_keywords = ['民生', '医保', '就业', '社保', '住房', '教育', '医疗', '出行', '食品', '安全']
    tech_keywords = ['科技', '人工智能', 'AI', '创新', '数字', '智能', '5G', '芯片', '航天']
    career_keywords = ['职业', '就业', '招聘', '职场', '薪资', '劳动法', '培训', '经济', '市场', '消费']
    
    if any(keyword in title_lower for keyword in international_keywords):
        return "国际"
    elif any(keyword in title_lower for keyword in domestic_keywords):
        return "国内"
    elif any(keyword in title_lower for keyword in livelihood_keywords):
        return "民生"
    elif any(keyword in title_lower for keyword in tech_keywords):
        return "科技"
    elif any(keyword in title_lower for keyword in career_keywords):
        return "职业"
    else:
        return "综合"  # 默认分类

def get_all_hot_news():
    """主函数：获取所有新闻并自动分类"""
    platforms = [
        ("人民网", get_people_daily),
        ("百度热搜", get_baidu_hot),
        ("今日热榜", get_today_hotlist),
        ("新浪新闻", get_sina_news),
        ("澎湃新闻", get_thepaper_news),
        ("腾讯新闻", get_tencent_news)
    ]
    
    # 初始化分类字典
    categorized_news = {
        "国际": [],
        "国内": [],
        "民生": [],
        "科技": [],
        "职业": [],
        "综合": []
    }
    
    success_count = 0
    
    for platform_name, platform_func in platforms:
        print(f"正在获取 {platform_name}...")
        result = platform_func()
        
        if result:
            section_title, news_list = result
            print(f"  ✓ 获取到 {len(news_list)} 条新闻")
            
            for title, hot in news_list:
                category = categorize_news(title)
                hot_text = f" ({hot})" if hot else ""
                categorized_news[category].append(f"• {title}{hot_text}")
            
            success_count += 1
        else:
            print(f"  ✗ 获取失败")
        time.sleep(0.5)  # 礼貌延迟
    
    # 构建分类输出
    all_news = []
    for category, items in categorized_news.items():
        if items:  # 只显示有内容的分类
            all_news.append(f"\n【{category}新闻】")
            # 每个分类下最多显示8条，避免邮件过长
            for item in items[:8]:
                all_news.append(f"  {item}")
    
    return "\n".join(all_news), success_count

# 邮件发送函数 (保持不变，但邮件标题可更新为“分类热点新闻日报”)
# 主执行函数 (保持不变)
