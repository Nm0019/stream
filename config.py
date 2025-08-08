import MetaTrader5 as mt5
from MetaTrader5 import TIMEFRAME_M5
from datetime import timedelta

MT5_LOGIN = 90488412
MT5_PASSWORD = 'Nm001970@'
MT5_SERVER = 'LiteFinance-MT5-Demo'

TIMEFRAME = TIMEFRAME_M5
HIST_CANDLES = 1000

SUPPORTED_TIMEFRAMES=[
    mt5.TIMEFRAME_M1,
    mt5.TIMEFRAME_M5,
    mt5.TIMEFRAME_M30,
    mt5.TIMEFRAME_H1,
    mt5.TIMEFRAME_H4
]


TIMEFRAME_MAP = {
    mt5.TIMEFRAME_M1: "M1",
    mt5.TIMEFRAME_M5: "M5",
    mt5.TIMEFRAME_M30: "M30",
    mt5.TIMEFRAME_H1: "H1",
    mt5.TIMEFRAME_H4: "H4"
}

def timeframe_to_timedelta(tf):
    return {
        mt5.TIMEFRAME_M1: timedelta(minutes=1),
        mt5.TIMEFRAME_M5: timedelta(minutes=5),
        mt5.TIMEFRAME_M15: timedelta(minutes=15),
        mt5.TIMEFRAME_M30: timedelta(minutes=30),
        mt5.TIMEFRAME_H1: timedelta(hours=1),
        mt5.TIMEFRAME_H4: timedelta(hours=4),
    }.get(tf, timedelta(minutes=1))