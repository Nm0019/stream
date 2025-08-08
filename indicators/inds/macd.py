import pandas as pd
from indicators.base_indicator import BaseIndicator

class MACDIndicator(BaseIndicator):
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        fast = self.params.get("fast", 12)
        slow = self.params.get("slow", 26)
        signal = self.params.get("signal", 9)

        # محاسبه EMA و MACD
        df["EMA_FAST"] = df["close"].ewm(span=fast, adjust=False).mean()
        df["EMA_SLOW"] = df["close"].ewm(span=slow, adjust=False).mean()
        df["MACD"] = df["EMA_FAST"] - df["EMA_SLOW"]
        df["SIGNAL_LINE"] = df["MACD"].ewm(span=signal, adjust=False).mean()
        df["MACD_DIFF"] = df["MACD"] - df["SIGNAL_LINE"]

        # واگرایی‌ها (ساده‌شده)
        df["BullishDiv"] = (df["close"] < df["close"].shift(2)) & (df["MACD"] > df["MACD"].shift(2))
        df["BearishDiv"] = (df["close"] > df["close"].shift(2)) & (df["MACD"] < df["MACD"].shift(2))

        # محاسبه امتیاز و سیگنال عددی
        def evaluate(row):
            score = 0

            if row["MACD"] > row["SIGNAL_LINE"]:
                score += 1
            if row["MACD"] < row["SIGNAL_LINE"]:
                score -= 1
            if row["BullishDiv"]:
                score += 2
            elif row["BearishDiv"]:
                score -= 2

            # تبدیل score به سیگنال نهایی عددی
            if score >= 2:
                signal = 1  # Buy
            elif score <= -2:
                signal = -1  # Sell
            else:
                signal = 0  # Hold

            return pd.Series([signal, score])

        df[["signal_MACD", "score_MACD"]] = df.apply(evaluate, axis=1)

        return df[["MACD", "SIGNAL_LINE", "score_MACD", "signal_MACD"]]
