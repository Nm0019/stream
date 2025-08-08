# price_action/price_action_runner.py

import traceback
from multiprocessing import Pool, cpu_count

from price_action.price_action_manager import calculate_and_store_price_action
from database.symbols_meta import get_all_registered_symbols
from config import SUPPORTED_TIMEFRAMES, TIMEFRAME_MAP


def _run_price_action_for_symbol_and_tf(args):
    symbol, tf_enum = args
    tf_str = TIMEFRAME_MAP[tf_enum]

    try:
        print(f"🔍 Running price action for {symbol} [{tf_str}]")
        calculate_and_store_price_action(symbol, tf_str)
        print(f"✅ Done: {symbol} [{tf_str}]")
    except Exception as e:
        print(f"❌ Error in {symbol} [{tf_str}]: {e}")
        traceback.print_exc()


def run_all_price_actions_parallel():
    symbols = get_all_registered_symbols()
    tasks = [(symbol, tf) for symbol in symbols for tf in SUPPORTED_TIMEFRAMES]

    print(f"🚀 Running {len(tasks)} price action jobs using {cpu_count()} cores...")
    with Pool(processes=cpu_count()) as pool:
        pool.map(_run_price_action_for_symbol_and_tf, tasks)

    print("🏁 All price actions processed.")
