import pandas as pd
import numpy as np
from indicators.base_indicator import BaseIndicator

class ATRIndicator(BaseIndicator):
    def __init__(self, symbol, timeframe, params):
        super().__init__(symbol, timeframe, params)
        self.nday = params.get("nday", 14)
        self.stop_loss_multiplier = params.get("stopLoss", 2)
        self.ema_period = params.get("ema_period", 20)  # پارامتری کردن EMA

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # === True Range ===
        tr = np.maximum.reduce([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift(1)).abs(),
            (df['low'] - df['close'].shift(1)).abs()
        ])
        df['TR'] = pd.Series(tr).ewm(alpha=1/self.nday, adjust=False).mean()  # Wilder's ATR

        # === Volatility ===
        df['Volatility_Percent'] = (df['TR'] / df['close']) * 100

        # === Trend filter ===
        df['EMA'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        df['Trend_Signal'] = np.where(df['close'] > df['EMA'], 'Uptrend', 'Downtrend')

        # === ATR-based signal ===
        df['Signal_ATR'] = np.where(
            (df['close'] > df['close'].shift(1)) & (df['TR'] > df['TR'].shift(1)), 1,
            np.where((df['close'] < df['close'].shift(1)) & (df['TR'] < df['TR'].shift(1)), -1, 0)
        )

        df['Contrarian_Signal'] = np.where(df['Signal_ATR'] == 1, -1,
                                           np.where(df['Signal_ATR'] == -1, 1, 0))
        df['Contrarian_Signal_Final'] = np.where(df['Contrarian_Signal'] == -1, 'Sell',
                                                 np.where(df['Contrarian_Signal'] == 1, 'Buy', 'Hold'))

        df['Final_Signal'] = np.where(
            (df['Signal_ATR'] == 1) & (df['Trend_Signal'] == 'Uptrend'), 'Buy',
            np.where((df['Signal_ATR'] == -1) & (df['Trend_Signal'] == 'Downtrend'), 'Sell', 'Hold')
        )

        # === Stop Loss ===
        df['Buy_Stop_Loss'] = df['close'] - (self.stop_loss_multiplier * df['TR'])
        df['Sell_Stop_Loss'] = df['close'] + (self.stop_loss_multiplier * df['TR'])

        # === Momentum & Alerts ===
        df['ATR_Momentum'] = df['TR'].diff()
        tr_mean = df['TR'].rolling(window=self.nday).mean()
        df['ATR_Alert'] = np.where(
            df['TR'] > 1.5 * tr_mean, 'High Volatility',
            np.where(df['TR'] < 0.5 * tr_mean, 'Low Volatility', 'Normal')
        )

        atr_mom_mean = df['ATR_Momentum'].rolling(window=self.nday).mean()
        df['Trend_Momentum_Status'] = np.where(
            df['ATR_Momentum'] > 1.5 * atr_mom_mean, 'Explosion',
            np.where(df['ATR_Momentum'] < 0.5 * atr_mom_mean, 'Calm', 'Normal')
        )

        # === Entry Text ===
        df['ATR_Entry'] = np.where(
            df['Signal_ATR'] == 1, '📈 ورود به معامله خرید (Buy)',
            np.where(df['Signal_ATR'] == -1, '📉 ورود به معامله فروش (Sell)', '⏸️ بی تصمیمی (No Entry)')
        )

        return df[['time', 'TR', 'Volatility_Percent', 'Trend_Signal', 'Final_Signal',
                   'Contrarian_Signal_Final', 'Buy_Stop_Loss', 'Sell_Stop_Loss',
                   'ATR_Momentum', 'ATR_Alert', 'Trend_Momentum_Status', 'ATR_Entry']]
