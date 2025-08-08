# price_action/manager.py

import pandas as pd
import sqlite3

from database.db_operations import fetch_recent_data, connect, get_table_name
from price_action.swing_points import SwingPointDetector

def add_column_if_not_exists(conn: sqlite3.Connection, table: str, column: str):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        print(f"➕ Adding column '{column}' to {table}")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} REAL")
        conn.commit()

def calculate_and_store_price_action(symbol: str, timeframe: str):
    print(f"🔍 Calculating price action for {symbol} [{timeframe}]...")
    table = get_table_name(timeframe)
    conn = connect(symbol)

    # دریافت داده‌ها (تا 10100 کندل برای اطمینان)
    df_rows = fetch_recent_data(symbol, timeframe, limit=10100)
    df = pd.DataFrame(df_rows, columns=["time", "open", "high", "low", "close", "volume"])
    if df.empty:
        print("⚠️ No data available.")
        conn.close()
        return

    # لیست ماژول‌های پرایس اکشن
    price_action_objects = [
        SwingPointDetector(symbol, timeframe, params={
            "atr_period": 14,
            "atr_multiplier": 0.5,
            "distance": 1
        })
    ]

    cached_results = {}
    all_columns = set()

    for pa in price_action_objects:
        result = pa.calculate(df.copy())
        cached_results[pa] = result
        all_columns.update([c for c in result.columns if c != "time"])

    # اضافه کردن ستون‌ها به دیتابیس
    for col in sorted(all_columns):
        add_column_if_not_exists(conn, table, col)

    # ادغام نتایج در df اصلی
    for result in cached_results.values():
        for col in result.columns:
            if col != "time":
                df[col] = result[col]

    # تبدیل زمان به فرمت سازگار
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # بروزرسانی دیتابیس
    cursor = conn.cursor()
    for idx, row in df.iterrows():
        time_val = row["time"]
        update_fields = []
        update_values = []

        for col in all_columns:
            val = row.get(col)
            if pd.notna(val):
                update_fields.append(f"{col} = ?")
                update_values.append(str(val))

        if update_fields:
            sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE time = ?"
            cursor.execute(sql, (*update_values, time_val))

    conn.commit()
    conn.close()
    print(f"✅ Price action stored for {symbol} [{timeframe}]")
