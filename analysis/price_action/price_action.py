import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from analysis.price_action.base_price_action import BasePriceAction

class SwingPointDetector(BasePriceAction):
    def calculate(self, df, timeframe=None):
        df = df.copy()

        # تنظیم فاصله و حداقل prominence بر اساس تایم‌فریم
        if timeframe in ['M1', 'M5']:
            distance = 3
            min_prom = 0.1
        elif timeframe in ['M15', 'M30']:
            distance = 4
            min_prom = 0.2
        else:
            distance = 5
            min_prom = 0.3

        # محاسبه prominence تطبیقی
        atr_period=14
        atr_multiplier= 0.8
        
        df['high_low'] = abs(df['high'] - df['low'])
        df['high_close'] = abs(df['high'] - df['close'].shift(1))
        df['low_close'] = abs(df['low'] - df['close'].shift(1))
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['true_range'].rolling(window=atr_period).mean()
        dynamic_prominence = df['atr'].mean() * atr_multiplier

        # تشخیص سوینگ‌ها
        peaks_high, _ = find_peaks(df['high'], prominence=dynamic_prominence, distance=distance)
        peaks_low, _ = find_peaks(-df['low'], prominence=dynamic_prominence, distance=distance)

        df['swing_high'] = np.nan
        df['swing_low'] = np.nan
        df.loc[df.index[peaks_high], 'swing_high'] = df.loc[df.index[peaks_high], 'high']
        df.loc[df.index[peaks_low], 'swing_low'] = df.loc[df.index[peaks_low], 'low']

        # ساختار بازار (HH, HL, LH, LL)
        structure_labels = ['']
        last_high = None
        last_low = None
        for i in range(1, len(df)):
            curr = df.iloc[i]
            label = ''
            if not pd.isna(curr['swing_high']):
                if last_high is not None:
                    label = 'HH' if curr['swing_high'] > last_high else 'LH'
                last_high = curr['swing_high']
            elif not pd.isna(curr['swing_low']):
                if last_low is not None:
                    label = 'HL' if curr['swing_low'] > last_low else 'LL'
                last_low = curr['swing_low']
            structure_labels.append(label)
        df['structure'] = structure_labels

        # تشخیص BoS
        bos_list = ['']
        last_hh = None
        last_ll = None
        for i in range(1, len(df)):
            row = df.iloc[i]
            bos = ''
            if df['structure'].iloc[i] == 'HH':
                if last_hh is not None and not pd.isna(row['swing_high']) and row['swing_high'] > last_hh:
                    bos = 'BoS ↓'
                last_hh = row['swing_high']
            elif df['structure'].iloc[i] == 'LL':
                if last_ll is not None and not pd.isna(row['swing_low']) and row['swing_low'] < last_ll:
                    bos = 'BoS ↑'
                last_ll = row['swing_low']
            bos_list.append(bos)
        df['bos'] = bos_list

        # تشخیص CHoCH
        choch_list = [np.nan]
        last_trend = None
        last_hl = None
        last_lh = None
        confirmed_bull = False
        confirmed_bear = False
        for i in range(1, len(df)):
            row = df.iloc[i]
            structure = row['structure']
            price = None
            if structure == 'HL':
                price = row['swing_low']
            elif structure == 'LH':
                price = row['swing_high']
            elif structure == 'LL':
                price = row['swing_low']
            elif structure == 'HH':
                price = row['swing_high']
            label = np.nan
            if structure == 'HH' and last_trend != 'bullish':
                confirmed_bull = True
                last_trend = 'bullish'
            elif structure == 'LL' and last_trend != 'bearish':
                confirmed_bear = True
                last_trend = 'bearish'
            if structure == 'HL' and price is not None:
                last_hl = price
            elif structure == 'LH' and price is not None:
                last_lh = price
            if confirmed_bull and structure == 'LL' and last_hl is not None and price < last_hl:
                label = 'CHoCH ↑'
                confirmed_bull = False
                last_trend = 'bearish'
            if confirmed_bear and structure == 'HH' and last_lh is not None and price > last_lh:
                label = 'CHoCH ↓'
                confirmed_bear = False
                last_trend = 'bullish'
            choch_list.append(label)
        df['choch'] = choch_list

        # حذف اضافات
        df.drop(columns=['high_low', 'high_close', 'low_close', 'true_range', 'atr'], inplace=True, errors='ignore')

        return df[['swing_high', 'swing_low', 'structure', 'bos', 'choch']]
