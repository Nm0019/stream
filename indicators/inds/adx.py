from indicators.base_indicator import BaseIndicator
import pandas as pd
import numpy as np

class ADXIndicator(BaseIndicator):
    def __init__(self, symbol, timeframe, params):
        super().__init__(symbol, timeframe, params)
        self.period = params.get('period', 14)
        self.ema_period = params.get('ema_period', 50)
        self.rsi_period = params.get('rsi_period', 14)
        self.macd_fast = params.get('macd_fast', 12)
        self.macd_slow = params.get('macd_slow', 26)
        self.macd_signal = params.get('macd_signal', 9)

    def calculate(self, df):
        df = df.copy()
        df.columns = [col.lower() for col in df.columns]

        # === محاسبه ADX ===
        high, low, close = df['high'], df['low'], df['close']
        period = self.period

        df['tr'] = np.maximum.reduce([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ])

        df['dmplus'] = np.where(
            (high - high.shift()) > (low.shift() - low),
            np.maximum(high - high.shift(), 0),
            0
        )

        df['dmminus'] = np.where(
            (low.shift() - low) > (high - high.shift()),
            np.maximum(low.shift() - low, 0),
            0
        )

        trn = df['tr'].ewm(alpha=1/period, adjust=False).mean()
        dmplusn = df['dmplus'].ewm(alpha=1/period, adjust=False).mean()
        dmminusn = df['dmminus'].ewm(alpha=1/period, adjust=False).mean()

        df['diplusn'] = 100 * (dmplusn / trn).replace([np.inf, -np.inf], np.nan)
        df['diminusn'] = 100 * (dmminusn / trn).replace([np.inf, -np.inf], np.nan)

        dx = 100 * np.abs(df['diplusn'] - df['diminusn']) / (df['diplusn'] + df['diminusn']).replace(0, np.nan)
        df['adx'] = dx.ewm(alpha=1/period, adjust=False).mean()

        # === EMA ===
        df[f"ema_{self.ema_period}"] = close.ewm(span=self.ema_period, adjust=False).mean()

        # === Volume MA ===
        if 'volume' not in df.columns:
            df['volume'] = 0
        df['volume_ma'] = df['volume'].rolling(window=period).mean()

        # === RSI ===
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(self.rsi_period).mean()
        avg_loss = loss.rolling(self.rsi_period).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # === MACD ===
        ema_fast = close.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.macd_slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()

        # === Signal Generation ===
        def full_signal(row):
            reason = []
            signal = "Hold"
            score = 0

            if pd.notna(row['adx']) and row['adx'] > 35:
                if row['diplusn'] > row['diminusn']:
                    signal = 'Buy'
                    score += 1
                    reason.append("DI+ > DI-")
                elif row['diminusn'] > row['diplusn']:
                    signal = 'Sell'
                    score -= 1
                    reason.append("DI- > DI+")

                reason.append("ADX > 25")

            if row['adx'] > 60:
                reason.append("⚠️ ADX بسیار بالا (اشباع روند)")

            if row['close'] > row[f"ema_{self.ema_period}"]:
                reason.append("قیمت بالای EMA")
            else:
                reason.append("قیمت زیر EMA")

            if row['volume'] > row['volume_ma']:
                reason.append("حجم بالای میانگین")

            if row['rsi'] > 70:
                reason.append("RSI در اشباع خرید")
            elif row['rsi'] < 30:
                reason.append("RSI در اشباع فروش")

            if signal == "Buy" and row['macd'] > row['macd_signal']:
                score += 1
                reason.append("کراس مثبت MACD")
            elif signal == "Sell" and row['macd'] < row['macd_signal']:
                score -= 1
                reason.append("کراس منفی MACD")

            return pd.Series([signal, ' | '.join(reason), score])

        result = df.apply(full_signal, axis=1)
        df[['sig_adx', 'sig_reason', 'score']] = result

        # === ستون‌های خروجی ===
        return df[['time', 'adx', 'diplusn', 'diminusn', 'sig_adx', 'sig_reason', 'score']]
