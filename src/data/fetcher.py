"""
行情数据抓取模块
使用 AkShare 获取 A股/港股 实时行情和历史K线数据
"""
import logging
from typing import Optional

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


class StockFetcher:
    """股票数据抓取器"""

    def get_a_stock_realtime(self, symbol: str) -> Optional[pd.Series]:
        """
        获取单只A股实时行情
        :param symbol: 股票代码，如 '600519'
        :return: 包含实时行情的 Series，失败返回 None
        """
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == symbol]
            if row.empty:
                logger.warning(f"A股 {symbol} 未找到")
                return None
            return row.iloc[0]
        except Exception as e:
            logger.error(f"获取A股 {symbol} 实时行情失败: {e}")
            return None

    def get_hk_stock_realtime(self, symbol: str) -> Optional[pd.Series]:
        """
        获取单只港股实时行情
        :param symbol: 股票代码，如 '00700'
        :return: 包含实时行情的 Series，失败返回 None
        """
        try:
            df = ak.stock_hk_spot_em()
            row = df[df["代码"] == symbol]
            if row.empty:
                logger.warning(f"港股 {symbol} 未找到")
                return None
            return row.iloc[0]
        except Exception as e:
            logger.error(f"获取港股 {symbol} 实时行情失败: {e}")
            return None

    def get_a_stock_history(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = "",
        end_date: str = "",
        adjust: str = "qfq",
    ) -> Optional[pd.DataFrame]:
        """
        获取A股历史K线数据
        :param symbol: 股票代码
        :param period: 周期 daily/weekly/monthly
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :param adjust: 复权类型 qfq前复权/hfq后复权/空字符串不复权
        """
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            if df.empty:
                logger.warning(f"A股 {symbol} 历史数据为空")
                return None
            return df
        except Exception as e:
            logger.error(f"获取A股 {symbol} 历史数据失败: {e}")
            return None

    def get_hk_stock_history(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = "",
        end_date: str = "",
        adjust: str = "qfq",
    ) -> Optional[pd.DataFrame]:
        """
        获取港股历史K线数据
        :param symbol: 股票代码，如 '00700'
        :param period: 周期 daily/weekly/monthly
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :param adjust: 复权类型
        """
        try:
            df = ak.stock_hk_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            if df.empty:
                logger.warning(f"港股 {symbol} 历史数据为空")
                return None
            return df
        except Exception as e:
            logger.error(f"获取港股 {symbol} 历史数据失败: {e}")
            return None

    def get_stock_history(
        self,
        symbol: str,
        market: str,
        period: str = "daily",
        start_date: str = "",
        end_date: str = "",
    ) -> Optional[pd.DataFrame]:
        """
        统一接口：根据市场获取历史数据
        :param market: 'a' 或 'hk'
        """
        if market == "a":
            return self.get_a_stock_history(symbol, period, start_date, end_date)
        elif market == "hk":
            return self.get_hk_stock_history(symbol, period, start_date, end_date)
        else:
            logger.error(f"不支持的市场类型: {market}")
            return None

    def get_a_stock_news(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取A股个股新闻"""
        try:
            df = ak.stock_news_em(symbol=symbol)
            return df.head(10) if not df.empty else None
        except Exception as e:
            logger.error(f"获取A股 {symbol} 新闻失败: {e}")
            return None
