import pandas as pd
import numpy as np

class PriceChannelDetector:
    def __init__(self):
        pass

    def detect_channels(self, df: pd.DataFrame):
        df = df.copy()
        channels = []

        # استخراج نقاط معتبر
        swing_highs = df[df['swing_high'].notna()]
        swing_lows = df[df['swing_low'].notna()]

        # --------- کانال‌های صعودی (بین دو swing_low با highs در بین) ---------
        i = 0
        while i < len(swing_lows) - 1:
            low1_idx = swing_lows.index[i]
            low2_idx = swing_lows.index[i + 1]

            # high بین دو low
            highs_between = swing_highs[(swing_highs.index > low1_idx) & (swing_highs.index < low2_idx)]
            if len(highs_between) >= 1:
                high1_idx = highs_between.index[0]
                high2_idx = highs_between.index[-1]

                channel = {
                    "type": "bullish",
                    "start": low1_idx,
                    "end": low2_idx,
                    "lower_line": [(low1_idx, df.loc[low1_idx, 'swing_low']),
                                   (low2_idx, df.loc[low2_idx, 'swing_low'])],
                    "upper_line": [(high1_idx, df.loc[high1_idx, 'swing_high']),
                                   (high2_idx, df.loc[high2_idx, 'swing_high'])],
                }
                channels.append(channel)
                i += 2
            else:
                i += 1

        # --------- کانال‌های نزولی (بین دو swing_high با lows در بین) ---------
        j = 0
        while j < len(swing_highs) - 1:
            high1_idx = swing_highs.index[j]
            high2_idx = swing_highs.index[j + 1]

            # low بین دو high
            lows_between = swing_lows[(swing_lows.index > high1_idx) & (swing_lows.index < high2_idx)]
            if len(lows_between) >= 1:
                low1_idx = lows_between.index[0]
                low2_idx = lows_between.index[-1]

                channel = {
                    "type": "bearish",
                    "start": high1_idx,
                    "end": high2_idx,
                    "upper_line": [(high1_idx, df.loc[high1_idx, 'swing_high']),
                                   (high2_idx, df.loc[high2_idx, 'swing_high'])],
                    "lower_line": [(low1_idx, df.loc[low1_idx, 'swing_low']),
                                   (low2_idx, df.loc[low2_idx, 'swing_low'])],
                }
                channels.append(channel)
                j += 2
            else:
                j += 1

        return channels
