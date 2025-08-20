import pandas as pd
import numpy as np
from indicators.base_indicator import BaseIndicator

class RSIIndicator(BaseIndicator):
    def __init__(self, symbol, timeframe, params):
        super().__init__(symbol, timeframe, params)
        
        # پارامترهای RSI
        self.rsi_length = params.get("rsi_length", 14)
        self.smooth_length = params.get("smooth_length", 21)
        self.trend_factor = params.get("trend_factor", 0.8)
        self.atr_length = params.get("atr_length", 10)
        self.source = params.get("source", "close")
        self.smooth_rsi = params.get("smooth_rsi", False)
        self.ma_lengths = params.get("ma_lengths", {"SMA":14,"EMA":14,"RMA":14,"WMA":14,"HMA":14,"VWMA":14})

    # تابع محاسبه MA روی سری
    def calculate_ma(self, series: pd.Series, length: int, ma_type: str, df=None):
        if ma_type == "SMA":
            return series.rolling(length).mean()
        elif ma_type == "EMA":
            return series.ewm(span=length, adjust=False).mean()
        elif ma_type == "RMA":
            return series.ewm(alpha=1/length, adjust=False).mean()
        elif ma_type == "WMA":
            return series.rolling(length).apply(
                lambda x: np.dot(x, np.arange(1, length+1))/np.arange(1, length+1).sum(),
                raw=True
            )
        elif ma_type == "HMA":
            half = int(length/2)
            wma1 = series.rolling(half).apply(
                lambda x: np.dot(x, np.arange(1, len(x)+1))/np.arange(1, len(x)+1).sum(),
                raw=True
            )
            wma2 = series.rolling(length).apply(
                lambda x: np.dot(x, np.arange(1, len(x)+1))/np.arange(1, len(x)+1).sum(),
                raw=True
            )
            return (2*wma1 - wma2).rolling(int(np.sqrt(length))).apply(
                lambda x: np.dot(x, np.arange(1, len(x)+1))/np.arange(1, len(x)+1).sum(),
                raw=True
            )
        elif ma_type == "VWMA" and df is not None:
            return (series * df['volume']).rolling(length).sum() / df['volume'].rolling(length).sum()
        else:
            return series

    # محاسبه ATR روی سری RSI (مطابق PineScript)
    def calculate_atr_on_rsi(self, rsi: pd.Series, length: int):
        highest_high = rsi.rolling(length).max()
        lowest_low = rsi.rolling(length).min()
        prev = rsi.shift(1)

        true_range = pd.concat([
            highest_high - lowest_low,
            (highest_high - prev).abs(),
            (lowest_low - prev).abs()
        ], axis=1).max(axis=1)

        # RMA = EMA با alpha = 1/length
        return true_range.ewm(alpha=1/length, adjust=False).mean()

    # محاسبه سوپرترند روی RSI
    def calculate_supertrend(self, factor: float, atr_length: int, rsi: pd.Series):
        atr = self.calculate_atr_on_rsi(rsi, atr_length)

        upper_band = rsi + factor * atr
        lower_band = rsi - factor * atr

        supertrend = pd.Series(index=rsi.index, dtype=float)
        trend_dir = pd.Series(index=rsi.index, dtype=int)

        # مقدار اولیه
        trend_dir.iloc[0] = 1
        supertrend.iloc[0] = lower_band.iloc[0]

        # پیمایش
        for i in range(1, len(rsi)):
            if pd.isna(atr.iloc[i-1]):
                trend_dir.iloc[i] = 1
                supertrend.iloc[i] = lower_band.iloc[i]
                continue

            prev_st = supertrend.iloc[i-1]
            prev_up = upper_band.iloc[i-1]
            prev_lo = lower_band.iloc[i-1]

            if prev_st == prev_up:
                # اگر سوپرترند قبلی روی upperBand بوده
                trend_dir.iloc[i] = 1 if rsi.iloc[i] >= upper_band.iloc[i] else -1
            else:
                # در غیر این صورت
                trend_dir.iloc[i] = -1 if rsi.iloc[i] <= lower_band.iloc[i] else 1

            # نگاشت باند درست
            if trend_dir.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]

        trend_dir = trend_dir.fillna(1).astype(int)
        supertrend = supertrend.fillna(method='bfill').fillna(method='ffill')

        return supertrend, trend_dir

    # محاسبه اصلی
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # محاسبه RSI
        delta = df[self.source].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)

        rsi = 100 - 100/(1 + rs)
        rsi.fillna(50, inplace=True)

        if self.smooth_rsi:
            rsi = rsi.ewm(span=self.smooth_length, adjust=False).mean()

        df['RSI'] = rsi

        # MAهای مختلف روی RSI
        for ma_type, length in self.ma_lengths.items():
            df[f'RSI_MA_{ma_type}'] = self.calculate_ma(df['RSI'], length, ma_type, df)

        # سوپرترند روی RSI
        df['RSI_ST'], df['RSI_trend'] = self.calculate_supertrend(
            self.trend_factor,
            self.atr_length,
            df['RSI']
        )

        # سیگنال‌ها
        df['long_entry'] = (df['RSI'] > df['RSI_ST']) & (df['RSI'].shift(1) <= df['RSI_ST'].shift(1))
        df['short_entry'] = (df['RSI'] < df['RSI_ST']) & (df['RSI'].shift(1) >= df['RSI_ST'].shift(1))
        df['long_exit'] = df['short_entry']
        df['short_exit'] = df['long_entry']

        cols = ['time', 'RSI', 'RSI_ST', 'RSI_trend', 'long_entry', 'short_entry', 'long_exit', 'short_exit']
        ma_cols = [f'RSI_MA_{ma}' for ma in self.ma_lengths.keys()]
        return df[cols + ma_cols]
