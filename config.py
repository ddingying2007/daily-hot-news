# config.py - 配置文件管理
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
    headers: Dict[str, str] = field(default_factory=dict)
    
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
    request_delay: float = 1.5
    max_retries: int = 3
    default_timeout: int = 15
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
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file):
                logger.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
                self._create_default_config()
                return
            
            # 读取配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    self.config_data = yaml.safe_load(f)
                elif self.config_file.endswith('.json'):
                    self.config_data = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_file}")
            
            # 解析配置
            self._parse_config()
            logger.info(f"配置文件 {self.config_file} 加载成功")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config_data = {
            'app': {
                'name': '每日新闻聚合系统',
                'version': '1.0.0',
                'timezone': 'Asia/Shanghai'
            },
            'news_sources': {
                'baidu': {
                    'enabled': True,
                    'name': '百度热搜',
                    'category': '热点',
                    'url': 'https://top.baidu.com/board?tab=realtime',
                    'selector': '.c-single-text-ellipsis',
                    'limit': 10
                },
                'zhihu': {
                    'enabled': True,
                    'name': '知乎热榜',
                    'category': '热点',
                    'url': 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50',
                    'api': True,
                    'limit': 10
                }
            }
        }
        self._parse_config()
    
    def _parse_config(self):
        """解析配置数据"""
        # 解析应用配置
        app_data = self.config_data.get('app', {})
        self.app_config = AppConfig(
            name=app_data.get('name', '每日新闻聚合系统'),
            version=app_data.get('version', '1.0.0'),
            timezone=app_data.get('timezone', 'Asia/Shanghai'),
            schedule_time=self.config_data.get('schedule', {}).get('time', '08:00'),
            request_delay=self.config_data.get('settings', {}).get('request_delay', 1.5),
            max_retries=self.config_data.get('settings', {}).get('max_retries', 3),
            default_timeout=self.config_data.get('settings', {}).get('timeout', 15),
            log_level=self.config_data.get('settings', {}).get('log_level', 'INFO')
        )
        
        # 解析邮件配置
        email_data = self.config_data.get('email', {})
        smtp_data = email_data.get('smtp', {})
        self.email_config = EmailConfig(
            subject_template=email_data.get('subject_template', '📰 每日新闻速递 {date}'),
            from_name=email_data.get('from_name', '每日新闻机器人'),
            smtp_server=smtp_data.get('server', 'smtp.qq.com'),
            smtp_port=smtp_data.get('port', 587),
            timeout=smtp_data.get('timeout', 10)
        )
        
        # 解析新闻源配置
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
        
        # 解析分类配置
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
        
        # 按优先级排序
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
    
    def save_config(self, file_path: str = None):
        """保存配置到文件"""
        if not file_path:
            file_path = self.config_file
        
        try:
            # 将配置转换回字典
            config_dict = {
                'app': {
                    'name': self.app_config.name,
                    'version': self.app_config.version,
                    'timezone': self.app_config.timezone
                },
                'schedule': {
                    'time': self.app_config.schedule_time,
                    'timezone': self.app_config.timezone
                },
                'email': {
                    'subject_template': self.email_config.subject_template,
                    'from_name': self.email_config.from_name,
                    'smtp': {
                        'server': self.email_config.smtp_server,
                        'port': self.email_config.smtp_port,
                        'timeout': self.email_config.timeout
                    }
                },
                'news_sources': {},
                'categories': {},
                'settings': {
                    'request_delay': self.app_config.request_delay,
                    'max_retries': self.app_config.max_retries,
                    'timeout': self.app_config.default_timeout,
                    'log_level': self.app_config.log_level
                }
            }
            
            # 添加新闻源
            for source_id, config in self.news_sources.items():
                config_dict['news_sources'][source_id] = {
                    'enabled': config.enabled,
                    'name': config.name,
                    'category': config.category,
                    'url': config.url,
                    'selector': config.selector,
                    'api': config.api,
                    'json_path': config.json_path,
                    'limit': config.limit,
                    'timeout': config.timeout,
                    'priority': config.priority
                }
            
            # 添加分类
            for category_name, config in self.categories.items():
                config_dict['categories'][category_name] = {
                    'icon': config.icon,
                    'color': config.color,
                    'keywords': config.keywords,
                    'limit': config.limit
                }
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.dump(config_dict, f, allow_unicode=True, sort_keys=False)
                elif file_path.endswith('.json'):
                    json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置文件已保存到 {file_path}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def update_source(self, source_id: str, **kwargs):
        """更新新闻源配置"""
        if source_id in self.news_sources:
            config = self.news_sources[source_id]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    def enable_source(self, source_id: str, enabled: bool = True):
        """启用/禁用新闻源"""
        self.update_source(source_id, enabled=enabled)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        enabled_sources = self.get_enabled_sources()
        disabled_sources = [config for config in self.news_sources.values() if not config.enabled]
        
        return {
            'app': {
                'name': self.app_config.name,
                'version': self.app_config.version
            },
            'email': {
                'from': self.email_config.from_name,
                'smtp_server': self.email_config.smtp_server
            },
            'sources': {
                'total': len(self.news_sources),
                'enabled': len(enabled_sources),
                'disabled': len(disabled_sources)
            },
            'categories': {
                'total': len(self.categories),
                'list': list(self.categories.keys())
            }
        }

# 全局配置实例
config_manager = None

def get_config() -> ConfigManager:
    """获取全局配置管理器"""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager()
    return config_manager

# 示例：如何使用
if __name__ == "__main__":
    # 初始化配置管理器
    config = get_config()
    
    # 获取配置摘要
    summary = config.get_config_summary()
    print("配置摘要:")
    print(f"应用名称: {summary['app']['name']}")
    print(f"版本: {summary['app']['version']}")
    print(f"新闻源总数: {summary['sources']['total']}")
    print(f"启用数: {summary['sources']['enabled']}")
    print(f"分类列表: {', '.join(summary['categories']['list'])}")
    
    # 获取启用的新闻源
    enabled_sources = config.get_enabled_sources()
    print(f"\n启用的新闻源 ({len(enabled_sources)}个):")
    for source in enabled_sources:
        print(f"  - {source.name} ({source.category})")
