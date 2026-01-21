import requests
import smtplib
import os
import re
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup
import json

def get_people_daily():
    """获取人民网时政要闻"""
    try:
        url = "http://www.people.com.cn/rss/politics.xml"
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:10]
            
            news_list = []
            for i, item in enumerate(items, 1):
                title = item.title.text if item.title else "无标题"
                # 清理标题中的特殊字符
                title = re.sub(r'<.*?>', '', title)
                title = title.replace('&nbsp;', ' ').replace('&amp;', '&')
                news_list.append((title, ""))
            
            return "📰 人民网时政要闻", news_list
    except Exception as e:
        print(f"人民网获取失败: {e}")
    return None

def get_baidu_hot():
    """获取百度热搜"""
    try:
        url = "https://top.baidu.com/board?platform=pc&sa=pcindex_entry"
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 百度热搜的HTML结构
            items = soup.select('.category-wrap_iQLoo')[1:11]  # 跳过第一个推荐位
            
            news_list = []
            for i, item in enumerate(items, 1):
                title_elem = item.select_one('.c-single-text-ellipsis')
                hot_elem = item.select_one('.hot-index_1Bl1a')
                
                title = title_elem.text.strip() if title_elem else "无标题"
                hot = hot_elem.text.strip() if hot_elem else ""
                news_list.append((title, hot))
            
            return "🔍 百度实时热搜", news_list
    except Exception as e:
        print(f"百度热搜获取失败: {e}")
    
    # 备用API
    try:
        url = "https://api.oioweb.cn/api/news/baidu"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'result' in data:
            news_list = []
            for i, item in enumerate(data['result'][:10], 1):
                news_list.append((item['title'], item.get('hot', '')))
            return "🔍 百度热搜", news_list
    except:
        pass
    
    return None

def get_weibo_hot():
    """获取微博热搜"""
    try:
        # 使用稳定API
        url = "https://api.oioweb.cn/api/news/weibo"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'result' in data:
            news_list = []
            for i, item in enumerate(data['result'][:10], 1):
                hot = item.get('hot', '')
                # 格式化热度值
                if hot and hot.isdigit():
                    hot_num = int(hot)
                    if hot_num > 10000:
                        hot = f"{hot_num/10000:.1f}万"
                news_list.append((item['title'], hot))
            return "🔥 微博热搜榜", news_list
    except Exception as e:
        print(f"微博API1失败: {e}")
    
    # 备用API
    try:
        url = "https://api.vvhan.com/api/hotlist?type=weibo"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('success'):
            news_list = []
            for i, item in enumerate(data['data'][:10], 1):
                hot = item.get('hot', '')
                news_list.append((item['title'], hot))
            return "🔥 微博热搜", news_list
    except:
        pass
    
    return None

def get_zhihu_hot():
    """获取知乎热榜"""
    try:
        url = "https://api.oioweb.cn/api/news/zhihu"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'result' in data:
            news_list = []
            for i, item in enumerate(data['result'][:10], 1):
                news_list.append((item['title'], ""))
            return "💡 知乎热榜", news_list
    except Exception as e:
        print(f"知乎API1失败: {e}")
    
    # 备用API
    try:
        url = "https://api.vvhan.com/api/hotlist?type=zhihu"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('success'):
            news_list = []
            for i, item in enumerate(data['data'][:10], 1):
                news_list.append((item['title'], ""))
            return "💡 知乎热榜", news_list
    except:
        pass
    
    return None

def get_tencent_news():
    """获取腾讯新闻热点"""
    try:
        # 腾讯新闻API
        url = "https://rsshub.app/tencent/news/rank"
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:10]
            
            news_list = []
            for i, item in enumerate(items, 1):
                title = item.title.text if item.title else "无标题"
                # 清理HTML标签
                title = re.sub(r'<.*?>', '', title)
                news_list.append((title, ""))
            
            return "🆕 腾讯新闻热点", news_list
    except Exception as e:
        print(f"腾讯新闻获取失败: {e}")
    
    # 备用：使用通用新闻API
    try:
        url = "https://api.oioweb.cn/api/news"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'result' in data:
            news_list = []
            # 筛选可能的腾讯相关新闻
            for i, item in enumerate(data['result'][:10], 1):
                if any(keyword in item['title'].lower() for keyword in ['腾讯', '微信', 'qq']):
                    news_list.append((item['title'], item.get('hot', '')))
            if news_list:
                return "🆕 腾讯相关热点", news_list
    except:
        pass
    
    return None

def get_all_hot_news():
    """获取所有平台的热点新闻"""
    platforms = [
        ("人民网", get_people_daily),
        ("百度", get_baidu_hot),
        ("微博", get_weibo_hot),
        ("知乎", get_zhihu_hot),
        ("腾讯", get_tencent_news)
    ]
    
    all_news = []
    success_count = 0
    
    for platform_name, platform_func in platforms:
        print(f"正在获取{platform_name}...")
        result = platform_func()
        
        if result:
            section_title, news_list = result
            all_news.append(f"\n{section_title} Top {len(news_list)}：")
            
            for i, (title, hot) in enumerate(news_list, 1):
                hot_text = f" ({hot})" if hot else ""
                # 限制标题长度
                if len(title) > 40:
                    title = title[:40] + "..."
                all_news.append(f"{i}. {title}{hot_text}")
            
            success_count += 1
        else:
            all_news.append(f"\n⚠️ {platform_name}：暂时无法获取")
    
    # 如果所有平台都失败，使用模拟数据
    if success_count == 0:
        all_news = [
            "\n📰 人民网时政要闻 Top 5：",
            "1. 国家重要政策发布",
            "2. 经济发展新动态",
            "3. 国际关系最新进展",
            "4. 民生政策解读",
            "5. 时政热点分析",
            "\n🔍 百度实时热搜 Top 5：",
            "1. 今日热点事件 (100万+)",
            "2. 热门搜索话题 (80万+)",
            "3. 实时热点追踪 (60万+)",
            "4. 热门资讯 (50万+)",
            "5. 搜索趋势 (40万+)",
            "\n🔥 微博热搜榜 Top 5：",
            "1. #热门话题讨论# (爆)",
            "2. #社会热点事件# (热)",
            "3. #娱乐新闻速递# (新)",
            "4. #科技前沿动态#",
            "5. #生活实用信息#",
            "\n💡 知乎热榜 Top 5：",
            "1. 如何评价当前热点事件？",
            "2. 专业知识深度解析",
            "3. 行业趋势分析与展望",
            "4. 实用生活经验分享",
            "5. 社会现象深度讨论",
            "\n🆕 腾讯新闻热点 Top 5：",
            "1. 腾讯最新动态",
            "2. 互联网行业资讯",
            "3. 科技产品发布",
            "4. 数字经济发展",
            "5. 网络热点追踪",
            "\n⚠️ 注意：当前使用模拟数据，正在优化API连接"
        ]
    
    return "\n".join(all_news), success_count

def send_email(content):
    """发送邮件"""
    try:
        # 从GitHub Secrets获取配置
        sender = os.environ['EMAIL_SENDER']
        password = os.environ['EMAIL_PASSWORD']
        receiver = os.environ['EMAIL_RECEIVER']
        
        # 创建邮件
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f'📊 全网热点新闻日报 {datetime.now().strftime("%Y-%m-%d")}'
        
        # 发送邮件
        with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        print(f"邮件发送错误：{e}")
        return False

if __name__ == '__main__':
    print("开始获取全网热点新闻...")
    
    # 获取所有平台新闻
    news_content, success_count = get_all_hot_news()
    
    # 添加统计信息和时间戳
    stats = f"\n📈 今日数据统计：成功获取 {success_count}/5 个平台"
    time_info = f"⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer = "💡 数据来源：人民网、百度、微博、知乎、腾讯等平台"
    
    full_content = f"{news_content}\n{stats}\n{time_info}\n{footer}"
    
    print(f"获取完成，成功平台数：{success_count}/5")
    print("开始发送邮件...")
    
    if send_email(full_content):
        print("✅ 邮件发送成功！")
    else:
        print("❌ 邮件发送失败")
