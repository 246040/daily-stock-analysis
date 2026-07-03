"""
AI Trade A - 主入口
调度数据采集、AI 分析、预警检测、报告生成和推送
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

import yaml

from src.alert.rules import AlertEngine
from src.analysis.ai_engine import AIEngine
from src.analysis.report import ReportGenerator
from src.data.fetcher import StockFetcher
from src.data.indicators import TechnicalIndicators
from src.notify.email_sender import EmailNotifier

logger = logging.getLogger(__name__)


def setup_logging(config: dict):
    """配置日志"""
    log_level = config.get("logging", {}).get("level", "INFO")
    log_file = config.get("logging", {}).get("file", "logs/app.log")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config(config_path: str = "config/config.yaml") -> dict:
    """加载主配置"""
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        logger.info("请复制 config/config.example.yaml 为 config/config.yaml 并填入配置")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_stocks(stocks_path: str = "config/stocks.yaml") -> dict:
    """加载自选股配置"""
    with open(stocks_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_daily_analysis(config: dict, stocks_config: dict):
    """
    执行每日分析流程
    1. 获取每只股票的历史数据
    2. 计算技术指标
    3. 调用 AI 分析
    4. 检测预警
    5. 生成报告
    6. 邮件推送
    """
    logger.info("=" * 50)
    logger.info("开始每日分析...")
    logger.info("=" * 50)

    # 初始化各模块
    fetcher = StockFetcher()
    indicator_calc = TechnicalIndicators()
    ai_engine = AIEngine(config.get("ai", {}))
    alert_engine = AlertEngine(stocks_config.get("alert_rules", []))
    report_gen = ReportGenerator()
    email_notifier = EmailNotifier(config.get("email", {}))

    # 计算日期范围（最近 90 天）
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

    stock_analyses = []
    all_alerts = []

    watchlist = stocks_config.get("watchlist", {})

    # 处理 A 股
    for stock in watchlist.get("a_stock", []):
        code = stock["code"]
        name = stock["name"]
        logger.info(f"分析 A股 {name}（{code}）...")

        result = _analyze_single_stock(
            fetcher, indicator_calc, ai_engine, alert_engine,
            code, name, "a", stock, start_date, end_date
        )
        if result:
            stock_analyses.append(result["analysis"])
            all_alerts.extend(result["alerts"])

    # 处理港股
    for stock in watchlist.get("hk_stock", []):
        code = stock["code"]
        name = stock["name"]
        logger.info(f"分析 港股 {name}（{code}）...")

        result = _analyze_single_stock(
            fetcher, indicator_calc, ai_engine, alert_engine,
            code, name, "hk", stock, start_date, end_date
        )
        if result:
            stock_analyses.append(result["analysis"])
            all_alerts.extend(result["alerts"])

    if not stock_analyses:
        logger.warning("没有成功分析任何股票")
        return

    # 生成每日总结
    logger.info("生成每日总结...")
    daily_summary = ai_engine.generate_daily_summary(stock_analyses)

    # 生成完整报告
    logger.info("生成报告...")
    report_path = report_gen.generate_daily_report(
        stock_analyses, daily_summary, all_alerts
    )
    report_content = report_gen.get_report_content(report_path)

    # 邮件推送
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"📊 每日股票分析报告 - {date_str}"
    if all_alerts:
        subject = f"⚠️📊 每日分析报告（{len(all_alerts)}条预警）- {date_str}"

    if email_notifier.send_report(subject, report_content):
        logger.info("✅ 报告邮件发送成功")
    else:
        logger.warning("❌ 报告邮件发送失败")

    # 单独发送预警邮件（如果有严重级别的预警）
    critical_alerts = [a for a in all_alerts if a["level"] in ("critical", "warning")]
    if critical_alerts:
        email_notifier.send_alert(critical_alerts)

    logger.info(f"分析完成！报告已保存: {report_path}")
    logger.info(f"共分析 {len(stock_analyses)} 只股票，触发 {len(all_alerts)} 条预警")


def _analyze_single_stock(
    fetcher, indicator_calc, ai_engine, alert_engine,
    code, name, market, stock_config, start_date, end_date
) -> dict | None:
    """分析单只股票，返回分析结果和预警"""
    # 获取历史数据
    hist_df = fetcher.get_stock_history(
        code, market, start_date=start_date, end_date=end_date
    )
    if hist_df is None or hist_df.empty:
        logger.warning(f"  跳过 {name}（{code}）：无历史数据")
        return None

    # 计算技术指标
    hist_df = indicator_calc.calculate_all(hist_df)
    indicators = indicator_calc.get_latest_summary(hist_df)
    if indicators is None:
        logger.warning(f"  跳过 {name}（{code}）：指标计算失败")
        return None

    # 获取实时行情作为补充
    if market == "a":
        realtime = fetcher.get_a_stock_realtime(code)
    else:
        realtime = fetcher.get_hk_stock_realtime(code)

    market_data = {}
    if realtime is not None:
        market_data = {
            "最新价": realtime.get("最新价"),
            "涨跌幅": realtime.get("涨跌幅"),
            "成交量": realtime.get("成交量"),
            "成交额": realtime.get("成交额"),
            "今开": realtime.get("今开"),
            "最高": realtime.get("最高"),
            "最低": realtime.get("最低"),
        }

    # 获取新闻（仅A股，港股新闻接口暂无）
    news_text = ""
    if market == "a":
        news_df = fetcher.get_a_stock_news(code)
        if news_df is not None:
            news_items = []
            for _, row in news_df.iterrows():
                title = row.get("新闻标题", row.get("title", ""))
                if title:
                    news_items.append(f"- {title}")
            news_text = "\n".join(news_items[:8])

    # AI 分析
    report = ai_engine.analyze_stock(
        name, code, market, market_data, indicators, news_text
    )
    if report is None:
        report = "AI 分析生成失败"

    # 预警检测
    alerts = alert_engine.check_alerts(name, code, indicators, stock_config)

    return {
        "analysis": {
            "name": name,
            "code": code,
            "market": market,
            "report": report,
        },
        "alerts": alerts,
    }


def run_alert_check(config: dict, stocks_config: dict):
    """
    仅执行预警检测（不生成完整报告）
    适用于盘中高频检测场景
    """
    logger.info("执行预警检测...")

    fetcher = StockFetcher()
    indicator_calc = TechnicalIndicators()
    alert_engine = AlertEngine(stocks_config.get("alert_rules", []))
    email_notifier = EmailNotifier(config.get("email", {}))

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")

    all_alerts = []
    watchlist = stocks_config.get("watchlist", {})

    for stock in watchlist.get("a_stock", []):
        hist_df = fetcher.get_stock_history(
            stock["code"], "a", start_date=start_date, end_date=end_date
        )
        if hist_df is not None and not hist_df.empty:
            hist_df = indicator_calc.calculate_all(hist_df)
            indicators = indicator_calc.get_latest_summary(hist_df)
            if indicators:
                alerts = alert_engine.check_alerts(
                    stock["name"], stock["code"], indicators, stock
                )
                all_alerts.extend(alerts)

    for stock in watchlist.get("hk_stock", []):
        hist_df = fetcher.get_stock_history(
            stock["code"], "hk", start_date=start_date, end_date=end_date
        )
        if hist_df is not None and not hist_df.empty:
            hist_df = indicator_calc.calculate_all(hist_df)
            indicators = indicator_calc.get_latest_summary(hist_df)
            if indicators:
                alerts = alert_engine.check_alerts(
                    stock["name"], stock["code"], indicators, stock
                )
                all_alerts.extend(alerts)

    if all_alerts:
        logger.info(f"触发 {len(all_alerts)} 条预警")
        email_notifier.send_alert(all_alerts)
    else:
        logger.info("无预警触发")


def main():
    parser = argparse.ArgumentParser(description="AI Trade A - 港股/A股智能监控分析平台")
    parser.add_argument(
        "--mode",
        choices=["daily", "alert", "test"],
        default="daily",
        help="运行模式: daily=每日分析, alert=仅预警检测, test=测试模式",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="配置文件路径",
    )
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    stocks_config = load_stocks()

    # 配置日志
    setup_logging(config)

    logger.info(f"AI Trade A 启动 | 模式: {args.mode}")

    if args.mode == "daily":
        run_daily_analysis(config, stocks_config)
    elif args.mode == "alert":
        run_alert_check(config, stocks_config)
    elif args.mode == "test":
        logger.info("测试模式：验证配置和连接...")
        # 简单测试数据源连接
        fetcher = StockFetcher()
        result = fetcher.get_a_stock_realtime("000001")
        if result is not None:
            logger.info(f"✅ A股数据源正常 | 平安银行最新价: {result.get('最新价')}")
        else:
            logger.error("❌ A股数据源连接失败")

        result = fetcher.get_hk_stock_realtime("00700")
        if result is not None:
            logger.info(f"✅ 港股数据源正常 | 腾讯控股最新价: {result.get('最新价')}")
        else:
            logger.error("❌ 港股数据源连接失败")

        logger.info("测试完成")


if __name__ == "__main__":
    main()
