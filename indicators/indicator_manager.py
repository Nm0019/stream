# indicators/manager_indicators.py

import pandas as pd
import sqlite3

from indicators.inds.rsi import RSIIndicator
from indicators.inds.macd import MACDIndicator
from indicators.inds.adx import ADXHybridIndicator
from indicators.inds.ema import TripleEMAIndicator
from indicators.inds.atr import ATRIndicator
from database.db_operations import fetch_recent_data, connect, get_table_name


def add_column_if_not_exists(conn: sqlite3.Connection, table: str, column: str):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        print(f"➕ Adding column '{column}' to {table}")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} REAL")
        conn.commit()


def calculate_and_store_indicators(symbol: str, timeframe: str):
    print(f"📈 Calculating indicators for {symbol} [{timeframe}]...")
    table = get_table_name(timeframe)
    conn = connect(symbol)

    # دریافت داده‌ها
    df_rows = fetch_recent_data(symbol, timeframe, limit=10100)
    df = pd.DataFrame(df_rows, columns=["time", "open", "high", "low", "close", "volume"])
    if df.empty:
        print("⚠️ No data available.")
        conn.close()
        return

    # لیست اندیکاتورها
    indicator_objects = [
        RSIIndicator(symbol, timeframe, params={
            "period": 14,
            "sma_short": 20,
            "sma_long": 50,
            "divergence_window": 20,
            "rsi_weight": 1,
            "trend_weight": 1,
            "divergence_weight": 1
        }),
        MACDIndicator(symbol, timeframe, params={
            "fast_period": 12,
              "slow_period": 26,
                "signal_period": 9
        }),
        ADXHybridIndicator(symbol, timeframe, params={
            "period": 14,
            "ema_period": 50,
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9
        }),
        TripleEMAIndicator(symbol, timeframe, params={
            "short_period": 9,
            "mid_period": 50,
            "long_period": 200}),
        ATRIndicator(symbol, timeframe, params= {
            "nday": 14,
            "stopLoss": 2
        })
    ]

    # اجرای محاسبات و ذخیره نتایج در حافظه
    cached_results = {}
    all_columns = set()

    for indicator in indicator_objects:
        result_df = indicator.calculate(df.copy())
        cached_results[indicator] = result_df
        all_columns.update([col for col in result_df.columns if col != "time"])

    # اطمینان از وجود همه ستون‌ها در دیتابیس
    for col in sorted(all_columns):
        add_column_if_not_exists(conn, table, col)

    # ادغام نتایج در دیتافریم اصلی
    for result_df in cached_results.values():
        for col in result_df.columns:
            if col != "time":
                df[col] = result_df[col]

    # فرمت‌دهی زمان
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # بروزرسانی دیتابیس
    cursor = conn.cursor()
    for idx, row in df.iterrows():
        update_fields = []
        update_values = []
        for col in all_columns:
            val = row.get(col)
            if pd.notna(val):
                update_fields.append(f"{col} = ?")
                update_values.append(val)
        if update_fields:
            sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE time = ?"
            cursor.execute(sql, (*update_values, row["time"]))

    conn.commit()
    conn.close()
    print(f"✅ Indicators stored for {symbol} [{timeframe}]")
