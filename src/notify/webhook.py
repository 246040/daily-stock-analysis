"""
Webhook 推送模块
支持企业微信、飞书 Webhook 推送 Markdown 格式报告
"""
import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Webhook 通知器（企业微信 / 飞书）"""

    def __init__(self, config: dict):
        """
        :param config: webhook 配置字典
            - wechat_url: 企业微信 Webhook URL
            - feishu_url: 飞书 Webhook URL
        """
        self.wechat_url = config.get("wechat_url", "")
        self.feishu_url = config.get("feishu_url", "")

    def send_report(self, title: str, content: str) -> bool:
        """
        推送报告到所有已配置的渠道
        :param title: 报告标题
        :param content: Markdown 格式内容
        :return: 是否至少有一个渠道发送成功
        """
        success = False

        if self.wechat_url:
            if self._send_wechat(title, content):
                success = True

        if self.feishu_url:
            if self._send_feishu(title, content):
                success = True

        if not self.wechat_url and not self.feishu_url:
            logger.info("未配置 Webhook 推送渠道，跳过")

        return success

    def _send_wechat(self, title: str, content: str) -> bool:
        """
        发送到企业微信群机器人
        企业微信 Markdown 消息限制 4096 字节，超长时截断
        """
        # 企业微信 Markdown 限制 4096 字节
        max_bytes = 4000
        truncated = self._truncate_to_bytes(content, max_bytes)

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": truncated,
            },
        }

        try:
            resp = requests.post(
                self.wechat_url,
                json=payload,
                timeout=10,
            )
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("✅ 企业微信推送成功")
                return True
            else:
                logger.error(f"企业微信推送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"企业微信推送异常: {e}")
            return False

    def _send_feishu(self, title: str, content: str) -> bool:
        """
        发送到飞书群机器人
        使用富文本 post 格式（支持更长内容）
        """
        # 飞书 post 消息，按段落拆分
        paragraphs = []
        for line in content.split("\n"):
            paragraphs.append([{"tag": "text", "text": line}])

        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": paragraphs,
                    }
                }
            },
        }

        try:
            resp = requests.post(
                self.feishu_url,
                json=payload,
                timeout=10,
            )
            result = resp.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("✅ 飞书推送成功")
                return True
            else:
                logger.error(f"飞书推送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"飞书推送异常: {e}")
            return False

    def _truncate_to_bytes(self, text: str, max_bytes: int) -> str:
        """将文本截断到指定字节数（UTF-8），保证不截断在字符中间"""
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
        truncated += "\n\n... (内容过长已截断)"
        return truncated
