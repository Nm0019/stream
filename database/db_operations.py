import sqlite3
import pandas as pd
import os
from config import TIMEFRAME_MAP

# ------------------------ مسیر و اتصال ------------------------

def get_db_path(symbol: str) -> str:
    base_dir = "data/db_per_symbol"
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"{symbol}.db")

def connect(symbol: str):
    path = get_db_path(symbol)
    return sqlite3.connect(path)

# ------------------------ جدول بر اساس تایم‌فریم ------------------------

def get_table_name(timeframe: str) -> str:
    return f"ohlcv_{timeframe}"

# ------------------------ ساختار اولیه دیتابیس برای هر نماد ------------------------

def initialize_symbol_db(symbol: str, timeframes: list = None):
    if timeframes is None:
        timeframes = ["M1", "M5", "M15", "M30", "H1", "H4"]

    conn = connect(symbol)
    cursor = conn.cursor()

    # ستون‌های اضافی 
    indicator_columns = {
        

    }

    for tf in timeframes:
        # اگر ورودی عددی باشد، آن را به رشته‌ی صحیح نگاشت کن
        if isinstance(tf, int):
            tf_str = TIMEFRAME_MAP.get(tf)
            if tf_str is None:
                print(f"⚠️ Unsupported timeframe ENUM: {tf}")
                continue
        else:
            tf_str = tf

        table = get_table_name(tf_str)

        # ساخت جدول اولیه OHLCV
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table} (
                time TEXT PRIMARY KEY,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL
            )
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_{table}_time ON {table}(time DESC)
        ''')

        # افزودن ستون‌های اندیکاتورها در صورت نیاز
        existing_cols = [row[1] for row in cursor.execute(f'PRAGMA table_info({table})')]
        for col_name, col_type in indicator_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col_name} {col_type}')

    # ساخت جدول متادیتا
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()

# ------------------------ درج داده‌ها ------------------------

def insert_ohlcv_data(df: pd.DataFrame, symbol: str, timeframe: str):
    if isinstance(timeframe, int):
        timeframe = TIMEFRAME_MAP.get(timeframe, str(timeframe))

    if df.empty:
        print(f"⚠️ Empty DataFrame for {symbol} {timeframe}")
        return

    initialize_symbol_db(symbol, [timeframe])  # اطمینان از وجود جدول

    table = get_table_name(timeframe)

    # تبدیل زمان به رشته برای مقایسه با دیتابیس (در قالب یکنواخت)
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # دریافت آخرین زمان موجود در دیتابیس
    last_time_in_db = get_last_ohlcv_time(symbol, timeframe)

    # فیلتر کردن فقط رکوردهایی که جدیدترند
    if last_time_in_db:
        df = df[df['time'] > last_time_in_db]

    if df.empty:
        print(f"⚪️ No new rows to insert for {symbol} {timeframe}")
        return

    # آماده‌سازی داده‌ها برای درج
    data = list(zip(
        df['time'], df['open'], df['high'], df['low'], df['close'], df['tick_volume']
    ))

    conn = connect(symbol)
    cursor = conn.cursor()

    try:
        cursor.executemany(f'''
            INSERT INTO {table} (time, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        print(f"✅ Inserted {cursor.rowcount} rows into {symbol}.{table}")
    except Exception as e:
        print(f"❌ Insert Error ({symbol}.{table}): {e}")
    finally:
        conn.close()


# ------------------------ واکشی داده‌ها ------------------------

def fetch_recent_data(symbol: str, timeframe: str, limit: int = 5000):
    """
    خواندن همه‌ی ستون‌های جدول مربوط به نماد و تایم‌فریم.
    """
    table = get_table_name(timeframe)
    conn = connect(symbol)
    cursor = conn.cursor()

    # خواندن نام ستون‌ها به‌صورت داینامیک
    cursor.execute(f'''
        SELECT * FROM {table}
        ORDER BY time DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    conn.close()

    df = pd.DataFrame(rows[::-1], columns=columns)  # ترتیب قدیمی به جدید
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])

    return df

# ------------------------ واکشی داده‌ها اندیکاتورها ------------------------

def fetch_indicator_data(symbol: str, timeframe: str, indicator_name: str, limit: int = 5000):
    """
    واکشی اطلاعات اندیکاتور ذخیره‌شده در دیتابیس نماد.
    """
    table = f"{indicator_name}_{timeframe}".lower()
    conn = connect(symbol)
    cursor = conn.cursor()

    cursor.execute(f'''
        SELECT * FROM {table}
        ORDER BY time DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    conn.close()

    df = pd.DataFrame(rows[::-1], columns=columns)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])

    return df



# ------------------------ حذف داده‌های قدیمی ------------------------

def delete_old_data(symbol: str, timeframe: str, keep_last_n: int = 5000):
    table = get_table_name(timeframe)
    conn = connect(symbol)
    cursor = conn.cursor()

    cursor.execute(f'''
        SELECT time FROM {table}
        ORDER BY time DESC
        LIMIT 1 OFFSET ?
    ''', (keep_last_n,))
    result = cursor.fetchone()

    if result:
        cutoff_time = result[0]
        cursor.execute(f'''
            DELETE FROM {table}
            WHERE time < ?
        ''', (cutoff_time,))
        conn.commit()
        print(f"🧹 Deleted old data in {symbol}.{table} before {cutoff_time}")
    conn.close()

# ------------------------ دریافت آخرین زمان ------------------------

def get_last_ohlcv_time(symbol: str, timeframe: str):
    table = get_table_name(timeframe)
    conn = connect(symbol)
    cursor = conn.cursor()
    try:
        cursor.execute(f'''
            SELECT MAX(time) FROM {table}
        ''')
        result = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        result = None
    conn.close()
    return result

# ------------------------ متادیتا ------------------------

def update_symbol_metadata(symbol: str, key: str, value: str):
    conn = connect(symbol)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES (?, ?)
    ''', (key, value))
    conn.commit()
    conn.close()

def get_metadata(symbol: str, key: str):
    conn = connect(symbol)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM metadata WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
