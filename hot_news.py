import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

def get_weibo_hot():
    """获取微博热搜"""
    try:
        url = "https://api.vvhan.com/api/hotlist?type=weibo"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("success"):
            news = []
            news.append("🔥 微博热搜 Top 10：")
            for i, item in enumerate(data["data"][:10], 1):
                hot = item.get("hot", "")
                news.append(f"{i}. {item['title']} {hot}")
            return "\n".join(news)
    except:
        pass
    return "微博热搜获取失败"

def get_zhihu_hot():
    """获取知乎热榜"""
    try:
        url = "https://api.vvhan.com/api/hotlist?type=zhihu"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("success"):
            news = []
            news.append("\n💡 知乎热榜 Top 10：")
            for i, item in enumerate(data["data"][:10], 1):
                news.append(f"{i}. {item['title']}")
            return "\n".join(news)
    except:
        pass
    return "\n知乎热榜获取失败"

def get_baidu_hot():
    """获取百度热搜"""
    try:
        url = "https://api.vvhan.com/api/hotlist?type=baidu"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("success"):
            news = []
            news.append("\n🔍 百度热搜 Top 10：")
            for i, item in enumerate(data["data"][:10], 1):
                news.append(f"{i}. {item['title']}")
            return "\n".join(news)
    except:
        pass
    return "\n百度热搜获取失败"
  
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
        msg['Subject'] = f'📰 今日热点新闻 {datetime.now().strftime("%Y-%m-%d")}'
        
        # 发送邮件（QQ邮箱示例）
        with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        print(f"错误：{e}")
        return False

if __name__ == '__main__':
    print("开始获取热点新闻...")
    
    # 获取新闻
    weibo = get_weibo_hot()
    zhihu = get_zhihu_hot()
    baidu = get_baidu_hot()
  
    # 组合内容
    content = f"{weibo}\n{zhihu}\n{baidu}"
    content += f"\n\n⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print("开始发送邮件...")
    if send_email(content):
        print("✅ 邮件发送成功！")
    else:
        print("❌ 邮件发送失败")
