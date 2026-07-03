"""
盯盘工具 - 实时监控港股/A股行情
每5分钟刷新一次，终端显示自选股实时数据
"""
import os
import sys
import time
from datetime import datetime

import akshare as ak
import pandas as pd
import yaml


def clear_screen():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def load_stocks(path: str = "config/stocks.yaml") -> dict:
    """加载自选股"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_a_stock_data(codes: list[str]) -> pd.DataFrame:
    """批量获取 A 股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        df = df[df["代码"].isin(codes)]
        return df[["代码", "名称", "最新价", "涨跌幅", "涨跌额", "成交量", "成交额", "今开", "最高", "最低", "昨收", "换手率"]]
    except Exception as e:
        print(f"  [错误] A股数据获取失败: {e}")
        return pd.DataFrame()


def get_hk_stock_data(codes: list[str]) -> pd.DataFrame:
    """批量获取港股实时行情"""
    try:
        df = ak.stock_hk_spot_em()
        df = df[df["代码"].isin(codes)]
        return df[["代码", "名称", "最新价", "涨跌幅", "涨跌额", "成交量", "成交额", "今开", "最高", "最低", "昨收"]]
    except Exception as e:
        print(f"  [错误] 港股数据获取失败: {e}")
        return pd.DataFrame()


def format_change(val) -> str:
    """格式化涨跌幅，带颜色"""
    try:
        v = float(val)
    except (ValueError, TypeError):
        return str(val)

    if v > 0:
        return f"\033[91m+{v:.2f}%\033[0m"  # 红色
    elif v < 0:
        return f"\033[92m{v:.2f}%\033[0m"   # 绿色
    else:
        return f"{v:.2f}%"


def format_price(val) -> str:
    """格式化价格"""
    try:
        return f"{float(val):.2f}"
    except (ValueError, TypeError):
        return str(val)


def format_volume(val) -> str:
    """格式化成交量（万手）"""
    try:
        v = float(val)
        if v >= 10000:
            return f"{v/10000:.1f}万"
        return f"{v:.0f}"
    except (ValueError, TypeError):
        return str(val)


def format_amount(val) -> str:
    """格式化成交额（亿）"""
    try:
        v = float(val)
        if v >= 100000000:
            return f"{v/100000000:.2f}亿"
        elif v >= 10000:
            return f"{v/10000:.0f}万"
        return f"{v:.0f}"
    except (ValueError, TypeError):
        return str(val)


def print_header():
    """打印表头"""
    print(f"{'代码':<8} {'名称':<8} {'最新价':>8} {'涨跌幅':>12} {'涨跌额':>8} {'成交量':>10} {'成交额':>10} {'今开':>8} {'最高':>8} {'最低':>8}")
    print("─" * 110)


def print_stock_row(row):
    """打印一行股票数据"""
    code = str(row.get("代码", ""))
    name = str(row.get("名称", ""))[:6]
    price = format_price(row.get("最新价"))
    change_pct = format_change(row.get("涨跌幅"))
    change = format_price(row.get("涨跌额"))
    volume = format_volume(row.get("成交量"))
    amount = format_amount(row.get("成交额"))
    open_p = format_price(row.get("今开"))
    high = format_price(row.get("最高"))
    low = format_price(row.get("最低"))

    # 涨跌额也带颜色
    try:
        cv = float(row.get("涨跌额", 0))
        if cv > 0:
            change = f"\033[91m+{cv:.2f}\033[0m"
        elif cv < 0:
            change = f"\033[92m{cv:.2f}\033[0m"
    except (ValueError, TypeError):
        pass

    print(f"{code:<8} {name:<8} {price:>8} {change_pct:>20} {change:>16} {volume:>10} {amount:>10} {open_p:>8} {high:>8} {low:>8}")


def run_monitor(interval: int = 300):
    """
    运行盯盘监控
    :param interval: 刷新间隔（秒），默认300秒=5分钟
    """
    stocks_config = load_stocks()
    watchlist = stocks_config.get("watchlist", {})

    a_stocks = watchlist.get("a_stock", [])
    hk_stocks = watchlist.get("hk_stock", [])

    a_codes = [s["code"] for s in a_stocks]
    hk_codes = [s["code"] for s in hk_stocks]

    print("🚀 AI Trade A - 盯盘模式启动")
    print(f"   监控 A股 {len(a_codes)} 只 | 港股 {len(hk_codes)} 只")
    print(f"   刷新间隔: {interval} 秒")
    print(f"   按 Ctrl+C 退出")
    print()

    cycle = 0
    while True:
        cycle += 1
        clear_screen()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  📊 AI Trade A 盯盘  |  {now}  |  第 {cycle} 轮  |  每 {interval}s 刷新  |  Ctrl+C 退出  ║")
        print(f"╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝")
        print()

        # A 股
        if a_codes:
            print("━━━ 🇨🇳 A 股 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print_header()
            a_df = get_a_stock_data(a_codes)
            if not a_df.empty:
                for _, row in a_df.iterrows():
                    print_stock_row(row)
            else:
                print("  数据获取中...")
            print()

        # 港股
        if hk_codes:
            print("━━━ 🇭🇰 港股 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print_header()
            hk_df = get_hk_stock_data(hk_codes)
            if not hk_df.empty:
                for _, row in hk_df.iterrows():
                    print_stock_row(row)
            else:
                print("  数据获取中...")
            print()

        print(f"⏱️  下次刷新: {interval} 秒后...")

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 盯盘结束，再见！")
            sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Trade A 盯盘工具")
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=300,
        help="刷新间隔（秒），默认 300 秒 = 5 分钟",
    )
    args = parser.parse_args()

    run_monitor(interval=args.interval)
