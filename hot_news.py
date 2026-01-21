# hot_news.py - 主程序入口
import os
import sys
import time
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import get_config
    from news_fetcher import NewsFetcher
    from news_processor import NewsProcessor
    from email_generator import EmailGenerator
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保以下文件存在:")
    print("1. config.py")
    print("2. news_fetcher.py")
    print("3. news_processor.py")
    print("4. email_generator.py")
    IMPORT_SUCCESS = False

def setup_logger(log_level="INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def main():
    """主函数"""
    if not IMPORT_SUCCESS:
        print("❌ 模块导入失败，无法继续执行")
        return False
    
    try:
        # 初始化配置和日志
        config = get_config()
        logger = setup_logger(config.app_config.log_level)
        
        logger.info("🚀 开始执行每日新闻收集任务")
        logger.info("=" * 60)
        logger.info(f"应用: {config.app_config.name} v{config.app_config.version}")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取环境变量
        sender = os.getenv('EMAIL_SENDER')
        password = os.getenv('EMAIL_PASSWORD')
        receiver = os.getenv('EMAIL_RECEIVER')
        
        if not all([sender, password, receiver]):
            logger.error("❌ 错误：环境变量未完全设置")
            logger.error("请在GitHub Secrets中设置:")
            logger.error("1. EMAIL_SENDER: 发件邮箱")
            logger.error("2. EMAIL_PASSWORD: 邮箱密码/授权码")
            logger.error("3. EMAIL_RECEIVER: 收件邮箱")
            return False
        
        logger.info(f"发件人: {sender}")
        logger.info(f"收件人: {receiver}")
        
        # 初始化组件
        fetcher = NewsFetcher(config)
        processor = NewsProcessor(config)
        email_gen = EmailGenerator(config)
        
        # 获取所有新闻
        logger.info("\n📡 开始抓取新闻...")
        all_news = {}
        
        enabled_sources = config.get_enabled_sources()
        logger.info(f"共有 {len(enabled_sources)} 个新闻源启用")
        
        for source_config in enabled_sources:
            logger.info(f"正在抓取: {source_config.name}")
            try:
                news_list = fetcher.fetch_news(source_config)
                all_news[source_config.id] = {
                    'name': source_config.name,
                    'news': news_list,
                    'category': source_config.category
                }
                logger.info(f"  ✅ 成功获取 {len(news_list)} 条新闻")
                
                # 礼貌间隔
                time.sleep(config.app_config.request_delay)
                
            except Exception as e:
                logger.error(f"  ❌ 抓取失败: {e}")
                all_news[source_config.id] = {
                    'name': source_config.name,
                    'news': ["数据获取失败"],
                    'category': source_config.category
                }
        
        # 处理并分类新闻
        logger.info("\n📊 正在分类整理新闻...")
        categorized_news = processor.categorize_news(all_news)
        
        # 统计信息
        total_news = sum(len(items) for items in categorized_news.values())
        logger.info(f"📈 分类统计:")
        for category, items in categorized_news.items():
            if items:
                logger.info(f"  {category}: {len(items)} 条")
        
        if total_news == 0:
            logger.warning("⚠️ 没有获取到任何新闻，将发送空邮件")
        
        # 生成并发送邮件
        logger.info(f"\n📧 正在生成并发送邮件到 {receiver}...")
        
        try:
            # 生成邮件内容
            text_content = email_gen.generate_text_email(categorized_news)
            html_content = email_gen.generate_html_email(categorized_news, all_news)
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{config.email_config.from_name} <{sender}>"
            msg['To'] = receiver
            
            # 邮件主题
            today_str = datetime.now().strftime('%m月%d日')
            subject = config.email_config.subject_template.format(date=today_str)
            msg['Subject'] = subject
            
            # 添加纯文本版本
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)
            
            # 添加HTML版本
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # 发送邮件
            server = smtplib.SMTP(config.email_config.smt
