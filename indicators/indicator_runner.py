# indicators/runner_indicator.py

import traceback
from multiprocessing import Pool, cpu_count
from indicators.indicator_manager import calculate_and_store_indicators
from database.symbols_meta import get_all_registered_symbols
from config import SUPPORTED_TIMEFRAMES, TIMEFRAME_MAP


def _run_for_symbol_and_timeframe(args):
    symbol, tf_enum = args
    tf_str = TIMEFRAME_MAP[tf_enum]
    try:
        print(f"🔍 Running indicators for {symbol} [{tf_str}]")
        calculate_and_store_indicators(symbol, tf_str)
        print(f"✅ Done: {symbol} [{tf_str}]")
    except Exception as e:
        print(f"❌ Error in {symbol} [{tf_str}]: {e}")
        traceback.print_exc()


def run_all_indicators_parallel():
    symbols = get_all_registered_symbols()
    tasks = [(symbol, tf) for symbol in symbols for tf in SUPPORTED_TIMEFRAMES]

    if not tasks:
        print("⚠️ No tasks to run.")
        return

    print(f"🚀 Running {len(tasks)} indicator jobs using {cpu_count()} cores...")

    with Pool(processes=cpu_count()) as pool:
        pool.map(_run_for_symbol_and_timeframe, tasks)

    print("🏁 All indicators processed.")
