import pandas as pd
import numpy as np
from indicators.base_indicator import BaseIndicator

class TripleEMAIndicator(BaseIndicator):
    def __init__(self, symbol, timeframe, params=None):
        super().__init__(symbol, timeframe, params)
        self.short_period = self.params.get("short_period", 9)
        self.mid_period = self.params.get("mid_period", 50)
        self.long_period = self.params.get("long_period", 200)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # === محاسبه EMA ها (هماهنگ با Pine Script) ===
        df[f"EMA_short_{self.short_period}"] = df["close"].ewm(alpha=2/(self.short_period+1), adjust=False).mean()
        df[f"EMA_mid_{self.mid_period}"] = df["close"].ewm(alpha=2/(self.mid_period+1), adjust=False).mean()
        df[f"EMA_long_{self.long_period}"] = df["close"].ewm(alpha=2/(self.long_period+1), adjust=False).mean()

        # === شاخص ترکیبی فاصله ===
        df["value_EMA"] = (
            (df[f"EMA_short_{self.short_period}"] - df[f"EMA_mid_{self.mid_period}"]) +
            (df[f"EMA_mid_{self.mid_period}"] - df[f"EMA_long_{self.long_period}"])
        ) / 2

        # === سیگنال کلی (روند) ===
        df["sig_EMA"] = np.where(
            (df[f"EMA_short_{self.short_period}"] > df[f"EMA_mid_{self.mid_period}"]) &
            (df[f"EMA_mid_{self.mid_period}"] > df[f"EMA_long_{self.long_period}"]),
            1,  # صعودی
            np.where(
                (df[f"EMA_short_{self.short_period}"] < df[f"EMA_mid_{self.mid_period}"]) &
                (df[f"EMA_mid_{self.mid_period}"] < df[f"EMA_long_{self.long_period}"]),
                -1,  # نزولی
                0    # خنثی
            )
        )

        # === کراس ها ===
        df["cross_short_mid"] = np.where(
            (df[f"EMA_short_{self.short_period}"].shift(1) < df[f"EMA_mid_{self.mid_period}"].shift(1)) &
            (df[f"EMA_short_{self.short_period}"] > df[f"EMA_mid_{self.mid_period}"]), 1,
            np.where(
                (df[f"EMA_short_{self.short_period}"].shift(1) > df[f"EMA_mid_{self.mid_period}"].shift(1)) &
                (df[f"EMA_short_{self.short_period}"] < df[f"EMA_mid_{self.mid_period}"]), -1, 0
            )
        )

        # === امتیاز نرمال‌شده (rolling) ===
        max_diff = df["value_EMA"].rolling(window=50).apply(lambda x: np.max(np.abs(x)), raw=True)
        df["score_EMA"] = np.where(max_diff != 0, df["value_EMA"] / max_diff, 0)

        # === توضیح متنی ===
        def explain(row):
            if row["sig_EMA"] == 1:
                if row["cross_short_mid"] == 1:
                    return "📈 کراس صعودی EMA کوتاه از میانی → تأیید روند صعودی"
                return f"سه EMA صعودی (کوتاه>{self.short_period}, میانی>{self.mid_period}, بلند>{self.long_period}) → روند صعودی"
            elif row["sig_EMA"] == -1:
                if row["cross_short_mid"] == -1:
                    return "📉 کراس نزولی EMA کوتاه از میانی → تأیید روند نزولی"
                return "سه EMA نزولی → روند نزولی"
            else:
                return "سه EMA در هم تنیده یا نامرتب → بازار خنثی/نوسانی"

        df["reason_EMA"] = df.apply(explain, axis=1)

        return df
