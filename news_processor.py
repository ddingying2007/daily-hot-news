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
            base_category = data['category'] if data.get('category') else '热点'
            
            for news_item in data['news']:
                clean_title = self._clean_title(news_item)
                if not clean_title or clean_title == '数据获取失败':
                    continue
                
                # 确定最终分类
                final_category = self._determine_category(
                    clean_title, 
                    base_category,
                    source_config
                )
                
                # 添加到对应分类
                if final_category in categorized:
                    categorized[final_category].append({
                        'source': data['name'],
                        'title': clean_title,
                        'original': news_item,
                        'source_category': base_category
                    })
        
        # 每个分类只保留前5条
        for category in categorized:
            categorized[category] = categorized[category][:5]
        
        return categorized
    
    def _clean_title(self, title: str) -> str:
        """清洗标题"""
        # 移除序号和热度标签
        clean = re.sub(r'^\d+\.\s*', '', title)  # 移除开头的序号
        clean = re.sub(r'\s*🔥\d+w', '', clean)  # 移除热度标签
        clean = clean.strip()
        return clean
    
    def _determine_category(self, title: str, base_category: str, source_config) -> str:
        """确定新闻分类"""
        # 如果有明确的基础分类且不是"热点"，直接使用
        if base_category != '热点':
            return base_category
        
        # 关键词匹配分类
        for category_name, category_config in self.config.categories.items():
            if category_name == '热点':
                continue
            
            # 检查关键词匹配
            keywords = category_config.keywords
            if keywords and any(keyword in title for keyword in keywords):
                return category_name
        
        # 默认返回"热点"
        return '热点'
