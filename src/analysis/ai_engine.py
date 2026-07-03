"""
AI 分析引擎
调用大模型生成股票分析报告
"""
import json
import logging
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class AIEngine:
    """AI 分析引擎，支持 DeepSeek / OpenAI 兼容接口"""

    def __init__(self, config: dict):
        """
        :param config: AI 配置字典，包含 api_key, base_url, model
        """
        self.provider = config.get("provider", "deepseek")
        self.model = config.get("model", "deepseek-chat")

        if self.provider == "ollama":
            self.client = OpenAI(
                base_url=config.get("ollama_url", "http://localhost:11434") + "/v1",
                api_key="ollama",
            )
            self.model = config.get("ollama_model", "qwen2.5:7b")
        else:
            self.client = OpenAI(
                api_key=config.get("api_key", ""),
                base_url=config.get("base_url", "https://api.deepseek.com"),
            )

    def analyze_stock(
        self,
        stock_name: str,
        stock_code: str,
        market: str,
        market_data: dict,
        indicators: dict,
        news: str = "",
    ) -> Optional[str]:
        """
        对单只股票进行 AI 分析
        :return: Markdown 格式的分析报告文本
        """
        prompt = self._build_prompt(
            stock_name, stock_code, market, market_data, indicators, news
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 分析 {stock_name}({stock_code}) 失败: {e}")
            return None

    def _system_prompt(self) -> str:
        return """你是一位专业的股票分析师，擅长技术分析和基本面分析。
你的分析风格简洁、有数据支撑、观点明确。
你必须在分析末尾加上风险提示：分析仅供参考，不构成投资建议。"""

    def _build_prompt(
        self,
        stock_name: str,
        stock_code: str,
        market: str,
        market_data: dict,
        indicators: dict,
        news: str,
    ) -> str:
        market_label = "A股" if market == "a" else "港股"

        prompt = f"""请对以下{market_label}进行综合分析：

【标的】{stock_name}（{stock_code}）

【最新行情】
{json.dumps(market_data, ensure_ascii=False, indent=2)}

【技术指标】
{json.dumps(indicators, ensure_ascii=False, indent=2)}
"""
        if news:
            prompt += f"""
【近期新闻/舆情】
{news}
"""

        prompt += """
请输出以下内容：
## 1. 决策建议
给出明确建议（强烈买入/买入/持有/观望/减仓/卖出）和置信度（0-100%）

## 2. 技术面分析
- 当前趋势判断（上涨/震荡/下跌）
- 关键支撑位和压力位
- 均线/MACD/KDJ 信号解读

## 3. 消息面分析
- 利好因素
- 利空因素

## 4. 风险提示
- 主要风险点

## 5. 操作建议
- 理想买入价
- 止损价
- 目标价
"""
        return prompt

    def generate_daily_summary(self, stock_reports: list[dict]) -> Optional[str]:
        """
        生成每日总结报告
        :param stock_reports: [{"name": ..., "code": ..., "report": ...}, ...]
        """
        summaries = []
        for sr in stock_reports:
            summaries.append(f"### {sr['name']}（{sr['code']}）\n{sr['report']}\n")

        combined = "\n---\n".join(summaries)

        prompt = f"""以下是今日各股票的独立分析报告，请生成一份精简的每日总结：

{combined}

请输出：
1. 今日市场整体情绪判断
2. 重点关注标的（列出最值得关注的2-3只）
3. 风险提醒
4. 明日操作建议概要

保持简洁，控制在 500 字以内。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"生成每日总结失败: {e}")
            return None
