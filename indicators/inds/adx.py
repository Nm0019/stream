from indicators.base_indicator import BaseIndicator
import pandas as pd
import numpy as np

class ADXHybridIndicator(BaseIndicator):
    def __init__(self, symbol, timeframe, params):
        super().__init__(symbol, timeframe, params)
        self.period = params.get('period', 14)
        self.ema_period = params.get('ema_period', 50)
        self.rsi_period = params.get('rsi_period', 14)
        self.macd_fast = params.get('macd_fast', 12)
        self.macd_slow = params.get('macd_slow', 26)
        self.macd_signal = params.get('macd_signal', 9)

    # ================== تابع RMA (Wilder’s) ==================
    def rma(self, series, period):
        return series.ewm(alpha=1/period, adjust=False).mean()

    def calculate(self, df):
        df = df.copy()

        # ===== مرحله ۱: محاسبه ADX و DI‌ها =====
        if 'ADX' not in df.columns:
            self._calculate_adx(df)
        if f'EMA_{self.ema_period}' not in df.columns:
            df[f'EMA_{self.ema_period}'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        if 'RSI' not in df.columns:
            self._calculate_rsi(df)
        if 'MACD' not in df.columns or 'MACD_signal' not in df.columns:
            self._calculate_macd(df)
        if 'volume_ma' not in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=self.period).mean()

        # ===== مرحله ۲: سیگنال پایه بر اساس کراس DI =====
        def base_signal(row):
            if row['ADX'] > 25:
                if row['diplusn'] > row['diminusn'] and row['close'] > row[f'EMA_{self.ema_period}']:
                    return 'Buy'
                elif row['diminusn'] > row['diplusn'] and row['close'] < row[f'EMA_{self.ema_period}']:
                    return 'Sell'
            return 'Hold'

        df['base_sig'] = df.apply(base_signal, axis=1)

        # ===== مرحله ۳: فیلتر و امتیازدهی =====
        def hybrid_signal(row):
            reasons = []
            score = 0
            signal = row['base_sig']

            # ADX قوی
            if row['ADX'] > 35:
                score += 1
                reasons.append("ADX > 35")
            if row['ADX'] > 60:
                reasons.append("⚠️ ADX بسیار بالا (اشباع روند)")

            # حجم
            if row['volume'] > row['volume_ma']:
                score += 1
                reasons.append("حجم بالای میانگین")

            # RSI
            if row['RSI'] > 70:
                score -= 1
                reasons.append("RSI اشباع خرید")
            elif row['RSI'] < 30:
                score -= 1
                reasons.append("RSI اشباع فروش")

            # MACD
            if signal == 'Buy' and row['MACD'] > row['MACD_signal']:
                score += 1
                reasons.append("کراس مثبت MACD")
            elif signal == 'Sell' and row['MACD'] < row['MACD_signal']:
                score += 1
                reasons.append("کراس منفی MACD")

            # تصمیم نهایی
            if score <= 0:
                signal = 'Hold'

            return pd.Series([signal, ' | '.join(reasons), score])

        df[['sig_final', 'sig_reason', 'score']] = df.apply(hybrid_signal, axis=1)

        # رنگ منطقه برای نمایش مثل Pine Script
        df['zone'] = np.where(df['diplusn'] > df['diminusn'], 'green', 'red')

        # حذف NaN‌های اولیه
        df.fillna(0, inplace=True)

        return df[['time', 'ADX', 'diplusn', 'diminusn', f'EMA_{self.ema_period}',
                   'RSI', 'MACD', 'MACD_signal', 'zone', 'sig_final', 'sig_reason', 'score']]

    # ================== زیر توابع محاسباتی ==================
    def _calculate_adx(self, df):
        high, low, close = df['high'], df['low'], df['close']

        tr = np.maximum.reduce([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ])
        dm_plus = np.where((high - high.shift()) > (low.shift() - low),
                           np.maximum(high - high.shift(), 0), 0)
        dm_minus = np.where((low.shift() - low) > (high - high.shift()),
                            np.maximum(low.shift() - low, 0), 0)

        trn = self.rma(pd.Series(tr), self.period)
        dm_plus_n = self.rma(pd.Series(dm_plus), self.period)
        dm_minus_n = self.rma(pd.Series(dm_minus), self.period)

        df['diplusn'] = 100 * (dm_plus_n / trn).replace([np.inf, -np.inf], np.nan)
        df['diminusn'] = 100 * (dm_minus_n / trn).replace([np.inf, -np.inf], np.nan)
        dx = 100 * np.abs(df['diplusn'] - df['diminusn']) / (df['diplusn'] + df['diminusn']).replace(0, np.nan)
        df['ADX'] = self.rma(dx, self.period)

    def _calculate_rsi(self, df):
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(self.rsi_period).mean()
        avg_loss = loss.rolling(self.rsi_period).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

    def _calculate_macd(self, df):
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=self.macd_signal, adjust=False).mean()
