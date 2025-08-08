import MetaTrader5 as mt5
import pandas as pd

from database.db_operations import (
    insert_ohlcv_data,
    initialize_symbol_db,
    get_db_path
)
from database.symbols_meta import register_symbol

from config import (
    MT5_LOGIN,
    MT5_PASSWORD,
    MT5_SERVER,
    HIST_CANDLES,
    SUPPORTED_TIMEFRAMES,
    TIMEFRAME_MAP
)


def connect_mt5():
    if not mt5.initialize(login=MT5_LOGIN, server=MT5_SERVER, password=MT5_PASSWORD):
        raise RuntimeError(f"MT5 connection failed: {mt5.last_error()}")
    print("✅ Connected to MetaTrader 5")


def shutdown_mt5():
    mt5.shutdown()
    print("🛑 MT5 connection closed")


def get_crypto_symbols():
    """
    دریافت لیست نمادهای کریپتو از متاتریدر
    """
    symbols = mt5.symbols_get()
    return [s.name for s in symbols if s.path and 'crypto' in s.path.lower()]


def download_historical_data(symbols: list[str]):
    """
    دانلود داده‌های تاریخی برای لیست نمادهای داده‌شده
    """
    for symbol in symbols:
        # ساخت دیتابیس و جدول‌های مرتبط با نماد
        initialize_symbol_db(symbol)

        # ثبت نماد در دیتابیس مرکزی
        db_path = get_db_path(symbol)
        register_symbol(symbol, db_path)

        for timeframe in SUPPORTED_TIMEFRAMES:
            tf_str = TIMEFRAME_MAP.get(timeframe, str(timeframe))
            print(f"📥 Fetching {HIST_CANDLES} candles for {symbol} [{tf_str}]...")

            if not mt5.symbol_select(symbol, True):
                print(f"❌ Cannot select symbol: {symbol}")
                continue

            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, HIST_CANDLES)

            if rates is None or len(rates) == 0:
                print(f"⚠️ No data for {symbol} [{tf_str}]")
                continue


            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            print(f"📝 Inserting {len(df)} rows into DB for {symbol} [{tf_str}]")
            insert_ohlcv_data(df, symbol, tf_str)

    print("✅ All historical data fetched.")


def download_btcusd():
    """
    تابع ساده برای دانلود فقط داده‌های BTCUSD
    """
    connect_mt5()
    try:
        download_historical_data(["BTCUSD"])
    finally:
        shutdown_mt5()
