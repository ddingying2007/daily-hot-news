# news_fetcher.py - 新闻抓取模块
import requests
import json
import random
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
from jsonpath_ng import parse

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self, config):
        self.config = config
        
    def fetch_news(self, source_config) -> List[str]:
        """根据配置抓取新闻"""
        try:
            if source_config.api:
                return self._fetch_api_news(source_config)
            else:
                return self._fetch_html_news(source_config)
        except Exception as e:
            logger.error(f"抓取 {source_config.name} 失败: {e}")
            return []
    
    def _fetch_api_news(self, source_config) -> List[str]:
        """抓取API类型的新闻"""
        headers = self._get_headers()
        response = requests.get(
            source_config.url, 
            headers=headers, 
            timeout=source_config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        
        # 使用jsonpath提取数据
        if source_config.json_path:
            jsonpath_expr = parse(source_config.json_path)
            matches = [match.value for match in jsonpath_expr.find(data)]
            news_list = self._parse_api_data(matches, source_config)
        else:
            news_list = self._parse_api_data(data, source_config)
        
        return news_list[:source_config.limit]
    
    def _fetch_html_news(self, source_config) -> List[str]:
        """抓取HTML类型的新闻"""
        headers = self._get_headers()
        response = requests.get(
            source_config.url, 
            headers=headers, 
            timeout=source_config.timeout
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select(source_config.selector)
        
        news_list = []
        for i, item in enumerate(items[:source_config.limit * 2], 1):
            title = item.text.strip()
            if title and len(title) > 3:
                # 添加排名
                news_list.append(f"{i}. {title}")
        
        return news_list[:source_config.limit]
    
    def _parse_api_data(self, data, source_config) -> List[str]:
        """解析API数据"""
        news_list = []
        
        if isinstance(data, list):
            for i, item in enumerate(data, 1):
                title = self._extract_title(item, source_config.id)
                if title:
                    # 添加热度信息（如果有）
                    hot_text = self._extract_hot(item, source_config.id)
                    if hot_text:
                        news_list.append(f"{i}. {title} {hot_text}")
                    else:
                        news_list.append(f"{i}. {title}")
        
        return news_list
    
    def _extract_title(self, item, source_id: str) -> str:
        """提取标题"""
        if isinstance(item, dict):
            # 根据不同的API返回结构提取标题
            if source_id == 'zhihu':
                return item.get('target', {}).get('title', '')
            elif source_id == 'weibo':
                return item.get('note', '')
            elif source_id == 'toutiao':
                return item.get('Title', '')
            else:
                return item.get('title', '') or item.get('name', '')
        elif isinstance(item, str):
            return item
        return ''
    
    def _extract_hot(self, item, source_id: str) -> str:
        """提取热度信息"""
        if isinstance(item, dict):
            if source_id == 'weibo':
                hot = item.get('num', 0)
                if hot > 10000:
                    return f"🔥{hot//10000}w"
            elif source_id == 'toutiao':
                hot = item.get('HotValue', 0)
                if hot > 10000:
                    return f"🔥{hot//10000}w"
        return ''
    
    def _get_headers(self) -> Dict[str, str]:
        """获取随机User-Agent"""
        user_agents = self.config.config_data.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ])
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
