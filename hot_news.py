import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

print("=== 开始执行 hot_news.py ===")

# 检查环境变量
sender = os.getenv('EMAIL_SENDER')
password = os.getenv('EMAIL_PASSWORD')
receiver = os.getenv('EMAIL_RECEIVER')

print(f"发送者邮箱: {sender}")
print(f"接收者邮箱: {receiver}")
print(f"密码是否设置: {'是' if password else '否'}")

if not all([sender, password, receiver]):
    print("错误：环境变量未完全设置！")
    exit(1)

try:
    # 创建邮件
    subject = "GitHub Actions 测试邮件"
    body = f"""
    这是一封来自 GitHub Actions 的测试邮件。
    
    发送时间: {datetime.now()}
    发送者: {sender}
    接收者: {receiver}
    
    如果收到此邮件，说明配置成功！
    """
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 根据邮箱类型选择服务器
    if 'gmail.com' in sender:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
    elif 'qq.com' in sender:
        smtp_server = 'smtp.qq.com'
        smtp_port = 587
    elif '163.com' in sender or '126.com' in sender:
        smtp_server = 'smtp.163.com'
        smtp_port = 25
    else:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
    
    print(f"使用 SMTP 服务器: {smtp_server}:{smtp_port}")
    
    # 发送邮件
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # 加密传输
    print("正在登录邮箱...")
    server.login(sender, password)
    print("登录成功，正在发送邮件...")
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()
    
    print(f"✅ 邮件发送成功到 {receiver}")
    
except Exception as e:
    print(f"❌ 发送邮件失败: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
