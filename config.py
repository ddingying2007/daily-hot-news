# config.py - 配置管理器
import os
import yaml
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class NewsSourceConfig:
    """新闻源配置类"""
    id: str
    enabled: bool = True
    name: str = ""
    category: str = "热点"
    url: str = ""
    selector: str = ""
    api: bool = False
    json_path: str = ""
    limit: int = 10
    timeout: int = 10
    priority: int = 1
    
@dataclass
class CategoryConfig:
    """新闻分类配置类"""
    name: str
    icon: str = "📰"
    color: str = "#6c757d"
    keywords: List[str] = field(default_factory=list)
    limit: int = 5

@dataclass
class EmailConfig:
    """邮件配置类"""
    subject_template: str = "📰 每日新闻速递 {date}"
    from_name: str = "每日新闻机器人"
    smtp_server: str = "smtp.qq.com"
    smtp_port: int = 587
    timeout: int = 10

@dataclass
class AppConfig:
    """应用配置类"""
    name: str = "每日新闻聚合系统"
    version: str = "1.0.0"
    timezone: str = "Asia/Shanghai"
    schedule_time: str = "08:00"
    request_delay: float = 1.0
    max_retries: int = 2
    default_timeout: int = 10
    log_level: str = "INFO"

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.news_sources: Dict[str, NewsSourceConfig] = {}
        self.categories: Dict[str, CategoryConfig] = {}
        self.email_config: EmailConfig = EmailConfig()
        self.app_config: AppConfig = AppConfig()
        
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_file):
                logger.error(f"配置文件 {self.config_file} 不存在")
                self._create_default_config()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            
            self._parse_config()
            logger.info(f"配置文件 {self.config_file} 加载成功")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config_data = {
            'app': {'name': '新闻系统', 'version': '1.0.0'},
            'news_sources': {
                'baidu': {
                    'enabled': True,
                    'name': '百度热搜',
                    'category': '热点',
                    'url': 'https://top.baidu.com/board?tab=realtime',
                    'selector': '.c-single-text-ellipsis',
                    'limit': 5
                }
            }
        }
        self._parse_config()
    
    def _parse_config(self):
        """解析配置数据"""
        # 应用配置
        app_data = self.config_data.get('app', {})
        self.app_config = AppConfig(
            name=app_data.get('name', '新闻系统'),
            version=app_data.get('version', '1.0.0'),
            timezone=app_data.get('timezone', 'Asia/Shanghai'),
            schedule_time=self.config_data.get('schedule', {}).get('time', '08:00'),
            request_delay=self.config_data.get('settings', {}).get('request_delay', 1.0),
            max_retries=self.config_data.get('settings', {}).get('max_retries', 2),
            default_timeout=self.config_data.get('settings', {}).get('timeout', 10),
            log_level=self.config_data.get('settings', {}).get('log_level', 'INFO')
        )
        
        # 邮件配置
        email_data = self.config_data.get('email', {})
        smtp_data = email_data.get('smtp', {})
        self.email_config = EmailConfig(
            subject_template=email_data.get('subject_template', '📰 每日新闻速递 {date}'),
            from_name=email_data.get('from_name', '新闻机器人'),
            smtp_server=smtp_data.get('server', 'smtp.qq.com'),
            smtp_port=smtp_data.get('port', 587),
            timeout=smtp_data.get('timeout', 10)
        )
        
        # 新闻源配置
        self.news_sources = {}
        sources_data = self.config_data.get('news_sources', {})
        for source_id, source_data in sources_data.items():
            try:
                config = NewsSourceConfig(
                    id=source_id,
                    enabled=source_data.get('enabled', True),
                    name=source_data.get('name', source_id),
                    category=source_data.get('category', '热点'),
                    url=source_data.get('url', ''),
                    selector=source_data.get('selector', ''),
                    api=source_data.get('api', False),
                    json_path=source_data.get('json_path', ''),
                    limit=source_data.get('limit', 10),
                    timeout=source_data.get('timeout', 10),
                    priority=source_data.get('priority', 1)
                )
                self.news_sources[source_id] = config
            except Exception as e:
                logger.error(f"解析新闻源 {source_id} 配置失败: {e}")
        
        # 分类配置
        self.categories = {}
        categories_data = self.config_data.get('categories', {})
        for category_name, category_data in categories_data.items():
            try:
                if isinstance(category_data, dict):
                    config = CategoryConfig(
                        name=category_name,
                        icon=category_data.get('icon', '📰'),
                        color=category_data.get('color', '#6c757d'),
                        keywords=category_data.get('keywords', []),
                        limit=category_data.get('limit', 5)
                    )
                else:
                    config = CategoryConfig(name=category_name)
                self.categories[category_name] = config
            except Exception as e:
                logger.error(f"解析分类 {category_name} 配置失败: {e}")
        
        # 确保有默认分类
        default_categories = ['时政', '经济', '民生', '科技', '热点']
        for cat in default_categories:
            if cat not in self.categories:
                self.categories[cat] = CategoryConfig(name=cat)
    
    def get_enabled_sources(self, category: str = None) -> List[NewsSourceConfig]:
        """获取启用的新闻源"""
        sources = [config for config in self.news_sources.values() if config.enabled]
        
        if category:
            sources = [config for config in sources if config.category == category]
        
        sources.sort(key=lambda x: x.priority)
        return sources
    
    def get_source(self, source_id: str) -> Optional[NewsSourceConfig]:
        """获取指定新闻源配置"""
        return self.news_sources.get(source_id)
    
    def get_category(self, category_name: str) -> Optional[CategoryConfig]:
        """获取指定分类配置"""
        return self.categories.get(category_name)
    
    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.categories.keys())

# 全局配置实例
_config_manager = None

def get_config() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
