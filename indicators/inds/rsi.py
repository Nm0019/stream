import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from indicators.base_indicator import BaseIndicator

class RSIIndicator(BaseIndicator):
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        # گرفتن پارامترها
        n = self.params.get("period", 14)
        short_window = self.params.get("sma_short", 20)
        long_window = self.params.get("sma_long", 50)
        order = self.params.get("divergence_window", 5)

        rsi_weight = self.params.get("rsi_weight", 1)
        trend_weight = self.params.get("trend_weight", 1)
        div_weight = self.params.get("divergence_weight", 1)

        df = df.copy()

        # ===== محاسبه RSI =====
        delta = df["close"].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)

        avg_gain = up.rolling(window=n).mean()
        avg_loss = down.rolling(window=n).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # ===== تبدیل RSI به امتیاز =====
        df["sig_RSI"] = df["RSI"].apply(self._signal_rsi_weight)

        # ===== محاسبه SMA =====
        df["SMA_short"] = df["close"].rolling(window=short_window).mean()
        df["SMA_long"] = df["close"].rolling(window=long_window).mean()

        # ===== محاسبه امتیاز اولیه =====
        def score_row(row):
            score = 0
            score += row["sig_RSI"] * rsi_weight
            if row["SMA_short"] > row["SMA_long"]:
                score -= trend_weight
            else:
                score += trend_weight
            return score

        df["score_RSI"] = df.apply(score_row, axis=1)

        # ===== تشخیص واگرایی‌ها =====
        df["has_bull_div"] = False
        df["has_bear_div"] = False
        divergences = self._detect_divergences(df, order)

        for idx, div_type in divergences:
            if idx < len(df):
                if "Bullish" in div_type:
                    df.at[idx, "score_RSI"] += div_weight
                    df.at[idx, "has_bull_div"] = True
                elif "Bearish" in div_type:
                    df.at[idx, "score_RSI"] -= div_weight
                    df.at[idx, "has_bear_div"] = True

        # ===== تصمیم نهایی سیگنال =====
        df["signal_RSI"] = df.apply(
            lambda row: self._final_signal(
                score=row["score_RSI"],
                sig_rsi=row["sig_RSI"],
                has_bull_div=row["has_bull_div"],
                has_bear_div=row["has_bear_div"],
                sma_short=row["SMA_short"],
                sma_long=row["SMA_long"]
            ),
            axis=1
        )

        return df[["RSI", "sig_RSI", "score_RSI", "signal_RSI"]]

    def _signal_rsi_weight(self, val: float) -> int:
        if val <= 10:
            return -3
        elif val <= 20:
            return -2
        elif val <= 30:
            return -1
        elif val <= 40:
            return 0
        elif val <= 60:
            return 0
        elif val <= 70:
            return 1
        elif val <= 80:
            return 2
        else:
            return 3

    def _detect_divergences(self, df: pd.DataFrame, order: int = 5) -> list:
        divergences = []

        # اندیس‌های کف و سقف محلی
        local_min_idx = argrelextrema(df["close"].values, np.less_equal, order=order)[0]
        local_max_idx = argrelextrema(df["close"].values, np.greater_equal, order=order)[0]

        # واگرایی مثبت (Bullish): کف پایین‌تر + RSI بالاتر
        for i in range(1, len(local_min_idx)):
            idx1, idx2 = local_min_idx[i - 1], local_min_idx[i]
            if idx2 - idx1 < 3:
                continue
            c1, c2 = df["close"].iloc[idx1], df["close"].iloc[idx2]
            r1, r2 = df["RSI"].iloc[idx1], df["RSI"].iloc[idx2]
            if c2 < c1 and r2 > r1:
                divergences.append((idx2, "Bullish Divergence"))

        # واگرایی منفی (Bearish): سقف بالاتر + RSI پایین‌تر
        for i in range(1, len(local_max_idx)):
            idx1, idx2 = local_max_idx[i - 1], local_max_idx[i]
            if idx2 - idx1 < 3:
                continue
            c1, c2 = df["close"].iloc[idx1], df["close"].iloc[idx2]
            r1, r2 = df["RSI"].iloc[idx1], df["RSI"].iloc[idx2]
            if c2 > c1 and r2 < r1:
                divergences.append((idx2, "Bearish Divergence"))

        return divergences

    def _final_signal(self, score, sig_rsi, has_bull_div, has_bear_div, sma_short, sma_long):
        # سیگنال خرید قوی
        if (
            sig_rsi >= 1 and
            sma_short > sma_long and
            
            score >= 2
        ):
            return 1 #"Buy"

        # سیگنال فروش قوی
        if (
            sig_rsi <= -1 and
            sma_short < sma_long and
            
            score <= -2
        ):
            return -1 #"Sell"

        return 0  #"Neutral"
