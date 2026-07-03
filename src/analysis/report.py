"""
报告生成模块
将 AI 分析结果组装为完整的 Markdown 格式报告
"""
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_daily_report(
        self,
        stock_analyses: list[dict],
        daily_summary: Optional[str] = None,
        alerts: list[dict] = None,
    ) -> str:
        """
        生成完整的每日分析报告
        :param stock_analyses: [{"name", "code", "market", "report"}, ...]
        :param daily_summary: AI 生成的每日总结
        :param alerts: 触发的预警列表
        :return: 报告文件路径
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        report_lines = [
            f"# 📊 每日股票分析报告",
            f"",
            f"**日期**：{date_str} | **生成时间**：{time_str}",
            f"",
            f"---",
            f"",
        ]

        # 每日总结
        if daily_summary:
            report_lines.extend([
                "## 📋 今日总结",
                "",
                daily_summary,
                "",
                "---",
                "",
            ])

        # 预警信息
        if alerts:
            report_lines.extend([
                "## ⚠️ 预警触发",
                "",
            ])
            for alert in alerts:
                level_icon = {
                    "critical": "🔴",
                    "warning": "🟡",
                    "important": "🟠",
                    "info": "🔵",
                }.get(alert.get("level", "info"), "🔵")
                report_lines.append(
                    f"- {level_icon} **{alert['name']}**：{alert['stock_name']}（{alert['stock_code']}）- {alert.get('detail', '')}"
                )
            report_lines.extend(["", "---", ""])

        # 个股分析
        report_lines.extend([
            "## 📈 个股分析",
            "",
        ])

        for analysis in stock_analyses:
            market_tag = "A股" if analysis["market"] == "a" else "港股"
            report_lines.extend([
                f"### {analysis['name']}（{analysis['code']}）[{market_tag}]",
                "",
                analysis.get("report", "分析生成失败"),
                "",
                "---",
                "",
            ])

        # 免责声明
        report_lines.extend([
            "",
            "---",
            "",
            "> ⚠️ **免责声明**：本报告由 AI 自动生成，仅供学习研究参考，不构成任何投资建议。",
            "> 投资有风险，入市需谨慎。所有买卖决策和风险由投资者自行承担。",
        ])

        report_content = "\n".join(report_lines)

        # 保存到文件
        filename = f"report_{date_str}.md"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"报告已保存: {filepath}")
        return filepath

    def get_report_content(self, filepath: str) -> str:
        """读取报告内容"""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
