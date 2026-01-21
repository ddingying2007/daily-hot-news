# email_generator.py - 邮件生成模块
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailGenerator:
    def __init__(self, config):
        self.config = config
    
    def generate_email_content(self, categorized_news: Dict[str, List[Dict]], 
                              all_news: Dict[str, Any],
                              sender: str,
                              receiver: str):
        """生成邮件内容"""
        # 生成纯文本
        text_content = self._generate_text_email(categorized_news)
        
        # 生成HTML
        html_content = self._generate_html_email(categorized_news, all_news)
        
        return text_content, html_content
    
    def _generate_text_email(self, categorized_news: Dict[str, List[Dict]]) -> str:
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
    
    def _generate_html_email(self, categorized_news: Dict[str, List[Dict]], 
                            all_news: Dict[str, Any]) -> str:
        """生成HTML邮件"""
        today = datetime.now().strftime("%Y年%m月%d日")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 统计
        total_news = sum(len(items) for items in categorized_news.values())
        enabled_count = len([s for s in self.config.news_sources.values() if s.enabled])
        
        # 构建HTML
        html = self._get_html_template().format(
            app_name=self.config.app_config.name,
            version=self.config.app_config.version,
            date=today,
            time=current_time,
            total_news=total_news,
            source_count=enabled_count,
            categories_html=self._generate_categories_html(categorized_news),
            sources_html=self._generate_sources_html(all_news)
        )
        
        return html
    
    def _generate_categories_html(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """生成分类HTML"""
        html = ""
        category_styles = self._get_category_styles()
        
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
                        hot_match = re.search(r'🔥(\d+w)', item['original'])
                        if hot_match:
                            hot_html = f'<span class="hot-badge">🔥{hot_match.group(1)}</span>'
                    
                    html += f"""
                    <div class="news-item">
                        <span class="news-rank">{i}</span>
                        <div class="news-title">
                            {
