"""
预警规则引擎
检测技术面异动并触发通知
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AlertEngine:
    """预警规则引擎"""

    def __init__(self, rules: list[dict]):
        """
        :param rules: 从 stocks.yaml 加载的预警规则列表
        """
        self.rules = rules

    def check_alerts(
        self,
        stock_name: str,
        stock_code: str,
        indicators: dict,
        stock_config: dict,
    ) -> list[dict]:
        """
        对一只股票检测所有预警规则
        :param indicators: 技术指标摘要（含 prev_ 前缀的前一日数据）
        :param stock_config: 个股配置（含 stop_loss, target_price）
        :return: 触发的预警列表
        """
        triggered = []

        for rule in self.rules:
            result = self._evaluate_rule(rule, indicators, stock_config)
            if result:
                triggered.append({
                    "name": rule["name"],
                    "level": rule.get("level", "info"),
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "detail": result,
                })

        return triggered

    def _evaluate_rule(
        self, rule: dict, indicators: dict, stock_config: dict
    ) -> Optional[str]:
        """评估单条规则，返回触发详情或 None"""
        rule_type = rule.get("type", "")
        params = rule.get("params", {})

        try:
            if rule_type == "ma_cross":
                return self._check_ma_cross(indicators, params)
            elif rule_type == "macd_cross":
                return self._check_macd_cross(indicators, params)
            elif rule_type == "volume_surge":
                return self._check_volume_surge(indicators, params)
            elif rule_type == "stop_loss":
                return self._check_stop_loss(indicators, stock_config)
            else:
                return None
        except (KeyError, TypeError) as e:
            logger.debug(f"规则 {rule.get('name')} 评估跳过: {e}")
            return None

    def _check_ma_cross(self, ind: dict, params: dict) -> Optional[str]:
        """检测均线突破"""
        period = params.get("period", 20)
        direction = params.get("direction", "up")
        ma_key = f"ma{period}"
        prev_ma_key = f"prev_ma{period}"

        close = ind.get("close")
        ma = ind.get(ma_key)
        prev_close = ind.get("prev_close")
        prev_ma = ind.get(prev_ma_key)

        if None in (close, ma, prev_close, prev_ma):
            return None

        if direction == "up" and close > ma and prev_close <= prev_ma:
            return f"股价 {close} 向上突破 MA{period}（{ma:.2f}）"
        elif direction == "down" and close < ma and prev_close >= prev_ma:
            return f"股价 {close} 向下跌破 MA{period}（{ma:.2f}）"

        return None

    def _check_macd_cross(self, ind: dict, params: dict) -> Optional[str]:
        """检测 MACD 金叉/死叉"""
        direction = params.get("direction", "golden")

        dif = ind.get("dif")
        dea = ind.get("dea")
        prev_dif = ind.get("prev_dif")
        prev_dea = ind.get("prev_dea")

        if None in (dif, dea, prev_dif, prev_dea):
            return None

        if direction == "golden" and dif > dea and prev_dif <= prev_dea:
            return f"MACD 金叉（DIF={dif:.3f}, DEA={dea:.3f}）"
        elif direction == "dead" and dif < dea and prev_dif >= prev_dea:
            return f"MACD 死叉（DIF={dif:.3f}, DEA={dea:.3f}）"

        return None

    def _check_volume_surge(self, ind: dict, params: dict) -> Optional[str]:
        """检测放量"""
        multiplier = params.get("multiplier", 2.0)
        min_change = params.get("min_change_pct", 3.0)

        volume = ind.get("volume")
        vol_ma5 = ind.get("vol_ma5")
        change_pct = ind.get("change_pct")

        if None in (volume, vol_ma5, change_pct):
            return None

        if vol_ma5 > 0 and volume > vol_ma5 * multiplier and change_pct > min_change:
            ratio = volume / vol_ma5
            return f"放量上涨：成交量是5日均量的 {ratio:.1f} 倍，涨幅 {change_pct:.2f}%"

        return None

    def _check_stop_loss(self, ind: dict, stock_config: dict) -> Optional[str]:
        """检测跌破止损价"""
        close = ind.get("close")
        stop_loss = stock_config.get("stop_loss")

        if close is None or stop_loss is None:
            return None

        if close < stop_loss:
            return f"⚠️ 当前价 {close} 已跌破止损价 {stop_loss}"

        return None
