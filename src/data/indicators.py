"""
技术指标计算模块
基于历史K线数据计算常用技术指标
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标，返回带指标列的 DataFrame
        要求输入 df 包含列：日期, 收盘, 开盘, 最高, 最低, 成交量
        """
        if df is None or df.empty:
            return df

        df = df.copy()

        # 统一列名（AkShare A股和港股列名可能不同）
        df = self._normalize_columns(df)

        # 计算各项指标
        df = self._calc_ma(df)
        df = self._calc_macd(df)
        df = self._calc_rsi(df)
        df = self._calc_kdj(df)
        df = self._calc_bollinger(df)
        df = self._calc_volume_ma(df)

        return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一列名为标准格式"""
        column_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "change_pct",
            "涨跌额": "change",
            "振幅": "amplitude",
            "换手率": "turnover",
        }
        df = df.rename(columns=column_map)

        # 确保数值类型
        for col in ["open", "close", "high", "low", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def _calc_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算均线 MA5/MA10/MA20/MA60"""
        for period in [5, 10, 20, 60]:
            df[f"ma{period}"] = df["close"].rolling(window=period).mean()
        return df

    def _calc_macd(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """计算 MACD（DIF/DEA/MACD柱）"""
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        df["dif"] = ema_fast - ema_slow
        df["dea"] = df["dif"].ewm(span=signal, adjust=False).mean()
        df["macd"] = (df["dif"] - df["dea"]) * 2
        return df

    def _calc_rsi(self, df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """计算 RSI（6/12/24）"""
        if periods is None:
            periods = [6, 12, 24]

        delta = df["close"].diff()
        for period in periods:
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss.replace(0, np.nan)
            df[f"rsi{period}"] = 100 - (100 / (1 + rs))
        return df

    def _calc_kdj(self, df: pd.DataFrame, n: int = 9) -> pd.DataFrame:
        """计算 KDJ 指标"""
        low_n = df["low"].rolling(window=n).min()
        high_n = df["high"].rolling(window=n).max()
        rsv = (df["close"] - low_n) / (high_n - low_n) * 100

        df["k"] = rsv.ewm(com=2, adjust=False).mean()
        df["d"] = df["k"].ewm(com=2, adjust=False).mean()
        df["j"] = 3 * df["k"] - 2 * df["d"]
        return df

    def _calc_bollinger(
        self, df: pd.DataFrame, period: int = 20, std_dev: int = 2
    ) -> pd.DataFrame:
        """计算布林带"""
        df["boll_mid"] = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        df["boll_upper"] = df["boll_mid"] + std_dev * std
        df["boll_lower"] = df["boll_mid"] - std_dev * std
        return df

    def _calc_volume_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量均线"""
        if "volume" in df.columns:
            df["vol_ma5"] = df["volume"].rolling(window=5).mean()
            df["vol_ma10"] = df["volume"].rolling(window=10).mean()
        return df

    def get_latest_summary(self, df: pd.DataFrame) -> Optional[dict]:
        """获取最新一行的指标摘要，用于喂给 AI 分析"""
        if df is None or df.empty:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        summary = {
            "close": latest.get("close"),
            "change_pct": latest.get("change_pct"),
            "volume": latest.get("volume"),
            "ma5": latest.get("ma5"),
            "ma10": latest.get("ma10"),
            "ma20": latest.get("ma20"),
            "ma60": latest.get("ma60"),
            "dif": latest.get("dif"),
            "dea": latest.get("dea"),
            "macd": latest.get("macd"),
            "rsi6": latest.get("rsi6"),
            "rsi12": latest.get("rsi12"),
            "k": latest.get("k"),
            "d": latest.get("d"),
            "j": latest.get("j"),
            "boll_upper": latest.get("boll_upper"),
            "boll_mid": latest.get("boll_mid"),
            "boll_lower": latest.get("boll_lower"),
            # 用于判断金叉/死叉
            "prev_dif": prev.get("dif"),
            "prev_dea": prev.get("dea"),
            "prev_close": prev.get("close"),
            "prev_ma20": prev.get("ma20"),
        }

        # 格式化数值
        for key, val in summary.items():
            if isinstance(val, float) and not np.isnan(val):
                summary[key] = round(val, 3)

        return summary
