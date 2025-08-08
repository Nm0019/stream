# indicators/inds/ema_indicator.py

import pandas as pd
from indicators.base_indicator import BaseIndicator

class EMAIndicator(BaseIndicator):
    """
    EMA Indicator
    """

    def __init__(self, symbol, timeframe, params):
        super().__init__(symbol, timeframe, params)
        self.period = params.get("period", 14)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")

        ema_col = f"value_ema_{self.period}"
        df[ema_col] = df['close'].ewm(span=self.period, adjust=False).mean()

        # سیگنال
        def make_signal(row):
            if row['close'] > row[ema_col]:
                return 'Buy'
            elif row['close'] < row[ema_col]:
                return 'Sell'
            return 'Hold'

        df[f"sig_ema_{self.period}"] = df.apply(make_signal, axis=1)

        # امتیاز (در اینجا صفر)
        df[f"score_ema_{self.period}"] = 0

        # دلیل سیگنال
        df[f"reason_ema_{self.period}"] = df[f"sig_ema_{self.period}"].map({
            'Buy': 'Price is above EMA',
            'Sell': 'Price is below EMA',
            'Hold': 'Price is near EMA'
        })

        return df[[
            'time',
            ema_col,
            f"sig_ema_{self.period}",
            f"score_ema_{self.period}",
            f"reason_ema_{self.period}"
        ]]

    def get_ema_series(self, df: pd.DataFrame) -> pd.Series:
        return df['close'].ewm(span=self.period, adjust=False).mean()

    def get_ema_signal(self, df: pd.DataFrame) -> pd.Series:
        ema = self.get_ema_series(df)
        signal = df['close'].gt(ema).replace({True: 'Buy', False: 'Sell'})
        return signal.rename(f"sig_ema_{self.period}")
