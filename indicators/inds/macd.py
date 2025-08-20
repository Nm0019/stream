import pandas as pd
import numpy as np
from indicators.base_indicator import BaseIndicator

class MACDIndicator(BaseIndicator):
    def __init__(self, symbol, timeframe, params):
        super().__init__(symbol, timeframe, params)

        # پارامترها
        self.fast_period = params.get("fast_period", 12)
        self.slow_period = params.get("slow_period", 26)
        self.signal_period = params.get("signal_period", 9)
        self.ma_period = params.get("ma_period", 50)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # === Moving Averages ===
        df["EMA"] = df["close"].ewm(span=self.ma_period, adjust=False).mean()
        df["SMA"] = df["close"].rolling(self.ma_period).mean()
        df["RMA"] = df["close"].ewm(alpha=1/self.ma_period, adjust=False).mean()
        df["WMA"] = df["close"].rolling(self.ma_period).apply(
            lambda x: np.dot(x, np.arange(1, self.ma_period+1)) / np.arange(1, self.ma_period+1).sum(), raw=True
        )
        df["DEMA"] = 2*df["EMA"] - df["EMA"].ewm(span=self.ma_period, adjust=False).mean()
        ema1 = df["EMA"]
        ema2 = ema1.ewm(span=self.ma_period, adjust=False).mean()
        ema3 = ema2.ewm(span=self.ma_period, adjust=False).mean()
        df["TEMA"] = 3*(ema1 - ema2) + ema3
        df["VIDYA"] = df["close"].ewm(span=self.ma_period, adjust=False).mean()

        # === MACD ===
        ema_fast = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow_period, adjust=False).mean()
        df["MACD"] = ema_fast - ema_slow
        df["Signal"] = df["MACD"].ewm(span=self.signal_period, adjust=False).mean()
        df["Histogram"] = df["MACD"] - df["Signal"]

        # === رنگ‌بندی Histogram / MACD ===
        df["MACD_prev"] = df["MACD"].shift(1)
        df["isBrightBlue"] = ((df["MACD"] > df["MACD_prev"]) & (df["MACD"] > 0)).astype(bool)
        df["isDarkBlueTransp"] = ((df["MACD"] < df["MACD_prev"]) & (df["MACD"] > 0)).astype(bool)
        df["isBrightMagenta"] = ((df["MACD"] < df["MACD_prev"]) & (df["MACD"] < 0)).astype(bool)
        df["isDarkMagentaTransp"] = ((df["MACD"] > df["MACD_prev"]) & (df["MACD"] < 0)).astype(bool)

        # === منطق سیگنال سیستم‌ها ===
        df["long_fast"] = (df["isBrightBlue"] | df["isDarkMagentaTransp"]).astype(bool)
        df["short_fast"] = (df["isDarkBlueTransp"] | df["isBrightMagenta"]).astype(bool)
        df["long_normal"] = (df["MACD"] > df["Signal"]).astype(bool)
        df["short_normal"] = (df["MACD"] < df["Signal"]).astype(bool)
        df["long_safe"] = df["isBrightBlue"]
        df["short_safe"] = df["isDarkBlueTransp"] | df["isBrightMagenta"] | df["isDarkMagentaTransp"]
        df["long_crossover"] = ((df["MACD"] > df["Signal"]) & (df["MACD"].shift(1) <= df["Signal"].shift(1))).astype(bool)
        df["short_crossover"] = ((df["MACD"] < df["Signal"]) & (df["MACD"].shift(1) >= df["Signal"].shift(1))).astype(bool)

        # === ورود و خروج ===
        df["long_entry"] = (df["long_fast"] & ~df["long_fast"].shift(1).fillna(False)).astype(bool)
        df["short_entry"] = (df["short_fast"] & ~df["short_fast"].shift(1).fillna(False)).astype(bool)
        df["long_exit"] = (df["short_fast"] & ~df["short_fast"].shift(1).fillna(False)).astype(bool)
        df["short_exit"] = (df["long_fast"] & ~df["long_fast"].shift(1).fillna(False)).astype(bool)

        # === روند نسبت به EMA ===
        df["isAboveMA"] = (df["close"] > df["EMA"]).astype(bool)
        df["isBelowMA"] = (df["close"] < df["EMA"]).astype(bool)

        # === رنگ کندل برای رسم چارت ===
        conditions = [df["long_entry"], df["short_entry"]]
        choices = ["BrightBlue", "BrightMagenta"]
        df["candleColor"] = np.select(conditions, choices, default="Neutral")

        # === ستون‌های ذخیره در DB ===
        return df[[
            "time",
            "EMA", "SMA", "RMA", "WMA", "DEMA", "TEMA", "VIDYA",
            "MACD", "Signal", "Histogram",
            "long_fast", "short_fast",
            "long_normal", "short_normal",
            "long_safe", "short_safe",
            "long_crossover", "short_crossover",
            "long_entry", "short_entry", "long_exit", "short_exit",
            "isAboveMA", "isBelowMA",
            "candleColor"
        ]]
