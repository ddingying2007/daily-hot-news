# news_processor.py - 新闻处理模块
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class NewsProcessor:
    def __init__(self, config):
        self.config = config
    
    def categorize_news(self, all_news: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """分类整理新闻"""
        categorized = {cat: [] for cat in self.config.get_all_categories()}
        
        for source_id, data in all_news.items():
            source_config = self.config.get_source(source_id)
            base_category = data.get('category', '热点')
            
            for news_item in data['news']:
                if '抓取失败' in news_item:
                    continue
                    
                clean_title = self._clean_title(news_item)
                if not clean_title or len(clean_title) < 3:
                    continue
                
                # 确定最终分类
                final_category = self._determine_category(clean_title, base_category)
                
                # 添加到对应分类
                if final_category in categorized:
                    categorized[final_category].append({
                        'source': data['name'],
                        'title': clean_title,
                        'original': news_item
                    })
        
        # 每个分类只保留前5条
        for category in categorized:
            categorized[category] = categorized[category][:5]
        
        return categorized
    
    def _clean_title(self, title: str) -> str:
        """清洗标题"""
        # 移除序号和热度标签
        clean = re.sub(r'^\d+\.\s*', '', title)
        clean = re.sub(r'\s*🔥\d+\w*', '', clean)
        clean = clean.strip()
        return clean
    
    def _determine_category(self, title: str, base_category: str) -> str:
        """确定新闻分类"""
        if base_category != '热点':
            return base_category
        
        # 关键词匹配分类
        for category_name, category_config in self.config.categories.items():
            if category_name == '热点':
                continue
            
            keywords = category_config.keywords
            if keywords:
                for keyword in keywords:
                    if keyword in title:
                        return category_name
        
        return '热点'
