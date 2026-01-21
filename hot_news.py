import os
import smtplib
import requests
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ====================== 新闻源配置 ======================
NEWS_SOURCES = {
    # 时政类
    "people": {"name": "人民网", "category": "时政", "enabled": True},
    "xinhua": {"name": "新华网", "category": "时政", "enabled": True},
    
    # 综合热点
    "weibo": {"name": "微博热搜", "category": "热点", "enabled": True},
    "zhihu": {"name": "知乎热榜", "category": "热点", "enabled": True},
    "baidu": {"name": "百度热搜", "category": "热点", "enabled": True},
    
    # 综合新闻
    "toutiao": {"name": "今日头条", "category": "热点", "enabled": True},
    "sina": {"name": "新浪新闻", "category": "热点", "enabled": True},
    "netease": {"name": "网易新闻", "category": "热点", "enabled": True},
    
    # 专业媒体
    "thepaper": {"name": "澎湃新闻", "category": "时政", "enabled": True},
    
    # 科技类
    "ithome": {"name": "IT之家", "category": "科技", "enabled": True},
}

# ====================== 新闻抓取函数 ======================

def get_people_news():
    """获取人民网要闻"""
    news_list = []
    try:
        url = "http://www.people.com.cn/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 人民网要闻
        items = soup.select('.news_box .news a, .rmw_list a, .hdNews a', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 4 and '人民网' not in title:
                news_list.append(f"{i}. {title}")
        
        if not news_list:
            items = soup.find_all('a', href=re.compile(r'/n1/'), limit=15)
            for i, item in enumerate(items[:15], 1):
                title = item.text.strip()
                if title and len(title) > 4:
                    news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"人民网抓取失败: {e}")
    
    return news_list[:10] if news_list else ["人民网：暂无数据"]

def get_xinhua_news():
    """获取新华网要闻"""
    news_list = []
    try:
        url = "http://www.xinhuanet.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 新华网头条新闻
        items = soup.select('.tit, .news-item h3, .hdNews a', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 4 and '新华网' not in title:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"新华网抓取失败: {e}")
    
    return news_list[:10] if news_list else ["新华网：暂无数据"]

def get_weibo_hot():
    """获取微博热搜"""
    news_list = []
    try:
        # 使用API接口
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://weibo.com/'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        for i, item in enumerate(data['data']['realtime'][:15], 1):
            title = item['note']
            hot = item.get('num', 0)
            if title and '推荐' not in title:
                if hot > 0:
                    news_list.append(f"{i}. {title} 🔥{hot//10000}w")
                else:
                    news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"微博热搜抓取失败: {e}")
        try:
            # 备用方案：直接抓取页面
            url = "https://s.weibo.com/top/summary"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = soup.select('.td-02 a', limit=15)
            for i, item in enumerate(items[:15], 1):
                title = item.text.strip()
                if title and '热搜' not in title:
                    news_list.append(f"{i}. {title}")
        except:
            pass
    
    return news_list[:10] if news_list else ["微博热搜：暂无数据"]

def get_zhihu_hot():
    """获取知乎热榜"""
    news_list = []
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.zhihu.com/hot'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        for i, item in enumerate(data['data'][:15], 1):
            title = item['target']['title']
            if title:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"知乎热榜抓取失败: {e}")
    
    return news_list[:10] if news_list else ["知乎热榜：暂无数据"]

def get_baidu_hot():
    """获取百度热搜"""
    news_list = []
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 百度热搜标题
        items = soup.select('.c-single-text-ellipsis', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 2:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"百度热搜抓取失败: {e}")
    
    return news_list[:10] if news_list else ["百度热搜：暂无数据"]

def get_toutiao_hot():
    """获取今日头条热榜"""
    news_list = []
    try:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.toutiao.com/'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        for i, item in enumerate(data['data'][:15], 1):
            title = item['Title']
            hot = item.get('HotValue', 0)
            if title:
                if hot > 10000:
                    news_list.append(f"{i}. {title} 🔥{hot//10000}w")
                else:
                    news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"今日头条抓取失败: {e}")
    
    return news_list[:10] if news_list else ["今日头条：暂无数据"]

def get_sina_news():
    """获取新浪新闻"""
    news_list = []
    try:
        url = "https://news.sina.com.cn/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 新浪头条新闻
        items = soup.select('.blk122, .news-item h2 a, .news-top a', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 4:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"新浪新闻抓取失败: {e}")
    
    return news_list[:10] if news_list else ["新浪新闻：暂无数据"]

def get_netease_news():
    """获取网易新闻"""
    news_list = []
    try:
        url = "https://news.163.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 网易新闻头条
        items = soup.select('.news_title h3 a, .ndi_main a, .top_news_tt a', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 4:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"网易新闻抓取失败: {e}")
    
    return news_list[:10] if news_list else ["网易新闻：暂无数据"]

def get_thepaper_news():
    """获取澎湃新闻"""
    news_list = []
    try:
        url = "https://www.thepaper.cn/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 澎湃新闻头条
        items = soup.select('.news_tu h2 a, .newscontent h2 a, .pdtt_t a', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 4:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"澎湃新闻抓取失败: {e}")
    
    return news_list[:10] if news_list else ["澎湃新闻：暂无数据"]

def get_ithome_news():
    """获取IT之家新闻"""
    news_list = []
    try:
        url = "https://www.ithome.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # IT之家新闻
        items = soup.select('.title a, .news_title a, .bl a', limit=15)
        
        for i, item in enumerate(items[:15], 1):
            title = item.text.strip()
            if title and len(title) > 4:
                news_list.append(f"{i}. {title}")
        
    except Exception as e:
        logging.error(f"IT之家抓取失败: {e}")
    
    return news_list[:10] if news_list else ["IT之家：暂无数据"]

# ====================== 新闻分类与整理 ======================

def categorize_news(news_data):
    """将新闻按照类别分类"""
    categorized = {
        "时政": [],
        "经济": [],
        "民生": [],
        "科技": [],
        "热点": []
    }
    
    # 源到类别的映射
    source_to_category = {
        "people": "时政",
        "xinhua": "时政",
        "thepaper": "时政",
        "weibo": "热点",
        "zhihu": "热点",
        "baidu": "热点",
        "toutiao": "热点",
        "sina": "热点",
        "netease": "热点",
        "ithome": "科技"
    }
    
    for source_id, data in news_data.items():
        category = source_to_category.get(source_id, "热点")
        for news in data['news']:
            # 清洗新闻标题
            clean_news = re.sub(r'\d+\.\s*', '', news)  # 移除前面的序号
            clean_news = re.sub(r'🔥\d+w', '', clean_news).strip()  # 移除热度标签
            
            # 根据关键词进一步分类
            final_category = category
            if category == "热点":
                # 关键词分类
                tech_keywords = ['AI', '人工智能', '芯片', '5G', '互联网', '科技', '数码', '手机', '电脑', '软件', '游戏']
                economy_keywords = ['经济', '股市', '金融', '投资', 'GDP', '消费', '贸易', '货币']
                people_keywords = ['民生', '教育', '医疗', '社保', '就业', '住房', '养老', '交通']
                politics_keywords = ['外交', '国防', '政府', '会议', '政策', '法律', '法规']
                
                if any(keyword in clean_news for keyword in tech_keywords):
                    final_category = "科技"
                elif any(keyword in clean_news for keyword in economy_keywords):
                    final_category = "经济"
                elif any(keyword in clean_news for keyword in people_keywords):
                    final_category = "民生"
                elif any(keyword in clean_news for keyword in politics_keywords):
                    final_category = "时政"
            
            categorized[final_category].append({
                'source': data['name'],
                'title': clean_news,
                'original': news
            })
    
    # 每个类别只保留前5条
    for category in categorized:
        categorized[category] = categorized[category][:5]
    
    return categorized

# ====================== 邮件生成函数 ======================

def generate_html_email(categorized_news, news_data):
    """生成HTML格式的邮件"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # 统计信息
    total_news = sum(len(items) for items in categorized_news.values())
    source_count = len([s for s in NEWS_SOURCES if NEWS_SOURCES[s]['enabled']])
    
    html = f"""
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
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }}
            .container {{
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                padding: 30px;
                margin-top: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                border-radius: 12px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: bold;
            }}
            .header .subtitle {{
                margin-top: 10px;
                opacity: 0.9;
                font-size: 16px;
            }}
            .stats {{
                display: flex;
                justify-content: space-around;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 30px;
                font-size: 14px;
            }}
            .stat-item {{
                text-align: center;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }}
            .category-section {{
                margin-bottom: 40px;
                border: 1px solid #e1e4e8;
                border-radius: 12px;
                padding: 25px;
                background: white;
            }}
            .category-title {{
                font-size: 22px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid;
                display: flex;
                align-items: center;
            }}
            .category-1 {{ color: #dc3545; border-color: #dc3545; }} /* 时政 - 红色 */
            .category-2 {{ color: #28a745; border-color: #28a745; }} /* 经济 - 绿色 */
            .category-3 {{ color: #17a2b8; border-color: #17a2b8; }} /* 民生 - 青色 */
            .category-4 {{ color: #ffc107; border-color: #ffc107; }} /* 科技 - 黄色 */
            .category-5 {{ color: #6f42c1; border-color: #6f42c1; }} /* 热点 - 紫色 */
            
            .news-item {{
                margin-bottom: 15px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid;
                transition: all 0.3s ease;
            }}
            .news-item:hover {{
                transform: translateX(5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .news-title {{
                font-weight: 500;
                margin-bottom: 5px;
                font-size: 16px;
            }}
            .news-source {{
                font-size: 13px;
                color: #6c757d;
            }}
            .news-source::before {{
                content: "📰 ";
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #e1e4e8;
                color: #6a737d;
                font-size: 14px;
            }}
            .category-icon {{
                margin-right: 10px;
                font-size: 24px;
            }}
            .hot-badge {{
                background: #ff6b6b;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                margin-left: 8px;
                display: inline-block;
            }}
            .news-rank {{
                display: inline-block;
                width: 24px;
                height: 24px;
                line-height: 24px;
                text-align: center;
                background: #667eea;
                color: white;
                border-radius: 50%;
                margin-right: 10px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 每日热点新闻速递</h1>
            <div class="subtitle">{today} | 更新时间: {current_time}</div>
        </div>
        
        <div class="container">
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{total_news}</div>
                    <div>精选新闻</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{source_count}</div>
                    <div>新闻来源</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(categorized_news)}</div>
                    <div>新闻类别</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{datetime.now().strftime('%H:%M')}</div>
                    <div>发布时间</div>
                </div>
            </div>
    """
    
    # 类别映射
    category_info = {
        "时政": {"icon": "🏛️", "class": "category-1", "desc": "国家大事 政经要闻"},
        "经济": {"icon": "📈", "class": "category-2", "desc": "财经动态 市场趋势"},
        "民生": {"icon": "🏠", "class": "category-3", "desc": "社会生活 百姓关注"},
        "科技": {"icon": "💻", "class": "category-4", "desc": "科技创新 数码前沿"},
        "热点": {"icon": "🔥", "class": "category-5", "desc": "全网热议 焦点话题"}
    }
    
    # 按类别显示新闻
    for category_idx, (category, news_items) in enumerate(categorized_news.items(), 1):
        if news_items:
            info = category_info.get(category, {"icon": "📰", "class": "category-5", "desc": ""})
            
            html += f"""
            <div class="category-section">
                <div class="category-title {info['class']}">
                    <span class="category-icon">{info['icon']}</span>
                    {category} <small style="margin-left: 10px; font-size: 14px; opacity: 0.8;">{info['desc']}</small>
                </div>
            """
            
            for i, item in enumerate(news_items, 1):
                # 提取热度信息
                original_news = item['original']
                hot_html = ""
                if '🔥' in original_news:
                    hot_match = re.search(r'🔥(\d+w)', original_news)
                    if hot_match:
                        hot_html = f'<span class="hot-badge">🔥{hot_match.group(1)}</span>'
                
                html += f"""
                <div class="news-item" style="border-left-color: {info['class'].replace('category-', 'var(--color-')})">
                    <div class="news-title">
                        <span class="news-rank">{i}</span>
                        {item['title']}
                        {hot_html}
                    </div>
                    <div class="news-source">{item['source']}</div>
                </div>
                """
            
            html += "</div>"
    
    # 新闻来源说明
    html += """
            <div class="category-section" style="background: #f0f2f5;">
                <div class="category-title" style="color: #495057; border-color: #495057;">
                    📋 今日新闻来源
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
    """
    
    for source_id, config in NEWS_SOURCES.items():
        if config['enabled'] and source_id in news_data:
            html += f"""
                    <span style="background: #e9ecef; padding: 5px 12px; border-radius: 20px; font-size: 13px;">
                        {config['name']} ({len(news_data[source_id]['news'])}条)
                    </span>
            """
    
    html += """
                </div>
            </div>
            
            <div class="footer">
                <p>📧 本邮件由 GitHub Actions 自动生成并发送 | 每日早8点准时推送</p>
                <p>🔧 技术支持：Python + BeautifulSoup + Requests + GitHub Actions</p>
                <p>⏰ 数据采集时间：{}</p>
            </div>
        </div>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    return html

def generate_text_email(categorized_news):
    """生成纯文本格式的邮件"""
    today = datetime.now().strftime("%Y年%m月%d日")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    text = f"""
    📰 每日热点新闻速递 ({today})
    ============================================
    更新时间: {current_time}
    
    """
    
    for category, news_items in categorized_news.items():
        if news_items:
            text += f"\n【{category}】\n"
            for i, item in enumerate(news_items, 1):
                text += f"  {i}. {item['title']} [{item['source']}]\n"
            text += "\n"
    
    text += """
    ============================================
    来源：人民网、新华网、微博、知乎、百度、头条、新浪、网易、澎湃、IT之家等
    时间：每日早8点自动发送
    技术支持：GitHub Actions + Python
    """
    
    return text

# ====================== 主函数 ======================

def main():
    logging.info("🚀 开始执行每日热点新闻收集任务")
    logging.info("=" * 60)
    
    # 获取环境变量
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receiver = os.getenv('EMAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        logging.error("❌ 错误：环境变量未完全设置")
        return False
    
    # 新闻源函数映射
    source_functions = {
        'people': get_people_news,
        'xinhua': get_xinhua_news,
        'weibo': get_weibo_hot,
        'zhihu': get_zhihu_hot,
        'baidu': get_baidu_hot,
        'toutiao': get_toutiao_hot,
        'sina': get_sina_news,
        'netease': get_netease_news,
        'thepaper': get_thepaper_news,
        'ithome': get_ithome_news
    }
    
    # 收集所有新闻
    news_data = {}
    for source_id, config in NEWS_SOURCES.items():
        if config['enabled']:
            try:
                logging.info(f"📡 正在抓取 {config['name']}...")
                news_list = source_functions[source_id]()
                news_data[source_id] = {
                    'name': config['name'],
                    'news': news_list
                }
                logging.info(f"   ✅ 成功抓取 {len(news_list)} 条新闻")
                time.sleep(1.5)  # 礼貌访问间隔
            except Exception as e:
                logging.error(f"   ❌ 抓取失败: {e}")
                news_data[source_id] = {
                    'name': config['name'],
                    'news': [f"数据获取失败"]
                }
    
    # 分类整理新闻
    logging.info("\n📊 正在分类整理新闻...")
    categorized_news = categorize_news(news_data)
    
    # 统计信息
    total_by_category = {cat: len(items) for cat, items in categorized_news.items()}
    logging.info("📈 新闻分类统计:")
    for category, count in total_by_category.items():
        logging.info(f"   {category}: {count} 条")
    
    # 生成并发送邮件
    try:
        logging.info(f"\n📧 正在生成并发送邮件到 {receiver}...")
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = f"每日新闻速递 <{sender}>"
        msg['To'] = receiver
        today_str = datetime.now().strftime('%m月%d日')
        msg['Subject'] = f"📰 每日热点新闻速递 {today_str}"
        
        # 添加纯文本版本
        text_content = generate_text_email(categorized_news)
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(part1)
        
        # 添加HTML版本
        html_content = generate_html_email(categorized_news, news_data)
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        # 发送邮件
        smtp_server = 'smtp.qq.com'
        smtp_port = 587
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        
        logging.info("✅ 邮件发送成功！")
        return True
        
    except Exception as e:
        logging.error(f"❌ 邮件发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
