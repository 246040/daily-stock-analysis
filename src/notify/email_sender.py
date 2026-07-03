"""
邮件推送模块
支持 SMTP/SSL 发送 HTML 格式的分析报告
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import markdown

logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config: dict):
        """
        :param config: 邮件配置字典
            - smtp_host: SMTP 服务器地址
            - smtp_port: 端口号
            - smtp_ssl: 是否使用 SSL
            - sender: 发件人邮箱
            - password: 密码/授权码
            - recipients: 收件人列表
        """
        self.smtp_host = config.get("smtp_host", "smtp.qq.com")
        self.smtp_port = config.get("smtp_port", 465)
        self.smtp_ssl = config.get("smtp_ssl", True)
        self.sender = config.get("sender", "")
        self.password = config.get("password", "")
        self.recipients = config.get("recipients", [])
        self.enabled = config.get("enabled", True)

    def send_report(self, subject: str, markdown_content: str) -> bool:
        """
        发送 Markdown 报告邮件
        :param subject: 邮件主题
        :param markdown_content: Markdown 格式的报告内容
        :return: 是否发送成功
        """
        if not self.enabled:
            logger.info("邮件通知已禁用")
            return False

        if not self._validate_config():
            return False

        html_content = self._markdown_to_html(markdown_content)
        return self._send_email(subject, html_content, markdown_content)

    def send_alert(self, alerts: list[dict]) -> bool:
        """
        发送预警邮件
        :param alerts: 预警列表
        :return: 是否发送成功
        """
        if not alerts:
            return True

        subject = f"⚠️ 股票预警 - 共 {len(alerts)} 条"
        lines = ["# ⚠️ 股票预警通知\n"]

        for alert in alerts:
            level_icon = {
                "critical": "🔴",
                "warning": "🟡",
                "important": "🟠",
                "info": "🔵",
            }.get(alert.get("level", "info"), "🔵")
            lines.append(
                f"- {level_icon} **{alert['name']}** | "
                f"{alert['stock_name']}（{alert['stock_code']}）\n"
                f"  - {alert.get('detail', '')}\n"
            )

        lines.append("\n---\n> 本通知由 AI Trade A 自动生成，仅供参考。")
        markdown_content = "\n".join(lines)

        return self.send_report(subject, markdown_content)

    def _validate_config(self) -> bool:
        """验证邮件配置是否完整"""
        if not self.sender:
            logger.error("邮件发件人未配置")
            return False
        if not self.password:
            logger.error("邮件密码/授权码未配置")
            return False
        if not self.recipients:
            logger.error("邮件收件人未配置")
            return False
        return True

    def _markdown_to_html(self, md_content: str) -> str:
        """将 Markdown 转为带样式的 HTML"""
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code"],
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f9f9f9;
}}
h1 {{
    color: #1a1a1a;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 10px;
}}
h2 {{
    color: #2c3e50;
    margin-top: 24px;
}}
h3 {{
    color: #34495e;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
}}
th, td {{
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}}
th {{
    background-color: #f2f2f2;
}}
blockquote {{
    border-left: 4px solid #e74c3c;
    margin: 16px 0;
    padding: 10px 16px;
    background-color: #fef9f9;
    color: #666;
}}
hr {{
    border: none;
    border-top: 1px solid #eee;
    margin: 24px 0;
}}
code {{
    background-color: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
}}
ul {{
    padding-left: 20px;
}}
li {{
    margin-bottom: 4px;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
        return html

    def _send_email(
        self, subject: str, html_content: str, text_content: str
    ) -> bool:
        """发送邮件"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        # 纯文本备选
        part_text = MIMEText(text_content, "plain", "utf-8")
        # HTML 版本
        part_html = MIMEText(html_content, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

        try:
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功: {subject} -> {self.recipients}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
