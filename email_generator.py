# email_generator.py - 邮件生成模块
from datetime import datetime
from typing import List, Dict, Any
import re

class EmailGenerator:
    def __init__(self, config):
        self.config = config
    
    def generate_text_email(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """生成纯文本邮件"""
        today = datetime.now().strftime("%Y年%m月%d日")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        text = f"""
📰 {self.config.app_config.name} ({today})
============================================
更新时间: {current_time}
版本: {self.config.app_config.version}

"""
        
        for category, news_items in categorized_news.items():
            if news_items:
                text += f"\n【{category}】\n"
                for i, item in enumerate(news_items, 1):
                    text += f"  {i}. {item['title']} [{item['source']}]\n"
                text += "\n"
        
        text += """
============================================
本邮件由 GitHub Actions 自动发送
每日定时推送: 08:00 (北京时间)
"""
        
        return text
    
    def generate_html_email(self, categorized_news: Dict[str, List[Dict]], 
                           all_news: Dict[str, Any]) -> str:
        """生成HTML邮件"""
        today = datetime.now().strftime("%Y年%m月%d日")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 统计
        total_news = sum(len(items) for items in categorized_news.values())
        enabled_sources = [s for s in self.config.news_sources.values() if s.enabled]
        
        # 类别样式
        category_styles = {
            "时政": {"icon": "🏛️", "color": "#dc3545", "class": "category-1"},
            "经济": {"icon": "📈", "color": "#28a745", "class": "category-2"},
            "民生": {"icon": "🏠", "color": "#17a2b8", "class": "category-3"},
            "科技": {"icon": "💻", "color": "#ffc107", "class": "category-4"},
            "热点": {"icon": "🔥", "color": "#6f42c1", "class": "category-5"}
        }
        
        # 构建HTML
        html = f"""
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
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            padding: 30px;
            margin-top: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header .subtitle {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
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
            margin-bottom: 25px;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 20px;
            background: white;
        }}
        .category-title {{
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid;
            display: flex;
            align-items: center;
        }}
        .category-1 {{ color: #dc3545; border-color: #dc3545; }}
        .category-2 {{ color: #28a745; border-color: #28a745; }}
        .category-3 {{ color: #17a2b8; border-color: #17a2b8; }}
        .category-4 {{ color: #ffc107; border-color: #ffc107; }}
        .category-5 {{ color: #6f42c1; border-color: #6f42c1; }}
        
        .news-item {{
            margin-bottom: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        .news-title {{
            font-weight: 500;
            margin-bottom: 5px;
        }}
        .news-source {{
            font-size: 13px;
            color: #6c757d;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
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
            border-radius: 10px;
            font-size: 12px;
            margin-left: 8px;
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
                <div class="stat-value">{len(enabled_sources)}</div>
                <div>新闻来源</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(categorized_news)}</div>
                <div>新闻类别</div>
            </div>
        </div>
"""
        
        # 按类别显示新闻
        for category, items in categorized_news.items():
            if items:
                style = category_styles.get(category, category_styles['热点'])
                
                html += f"""
        <div class="category-section">
            <div class="category-title {style['class']}">
                <span class="category-icon">{style['icon']}</span>
                {category}
            </div>
"""
                
                for i, item in enumerate(items, 1):
                    hot_html = ""
                    if '🔥' in item['original']:
                        hot_match = re.search(r'🔥(\d+\w*)', item['original'])
                        if hot_match:
                            hot_html = f'<span class="hot-badge">🔥{hot_match.group(1)}</span>'
                    
                    html += f"""
            <div class="news-item">
                <div class="news-title">
                    <span class="news-rank">{i}</span>
                    {item['title']}
                    {hot_html}
                </div>
                <div class="news-source">{item['source']}</div>
            </div>
"""
                
                html += "        </div>"
        
        # 页脚
        html += f"""
        <div class="footer">
            <p>📧 本邮件由 GitHub Actions 自动生成并发送 | 每日早8点准时推送</p>
            <p>🔧 技术支持: {self.config.app_config.name} v{self.config.app_config.version}</p>
            <p>⏰ 数据采集时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
