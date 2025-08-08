# app.py

import streamlit as st
import pandas as pd
from mt5_connector.historical_fetcher import download_btcusd
from database.db_operations import fetch_recent_data
from analysis.price_action.price_action import SwingPointDetector
from analysis.channel_detector import PriceChannelDetector
from visualization.charts import plot_price_action_chart
import subprocess

st.title("🔍 BTCUSD Price Action Viewer")

symbol = "BTCUSD"
timeframe = "H4"
download_btcusd()

with st.spinner("در حال اجرای اندیکاتورها..."):
    subprocess.run(["python", "run_indicators_launcher.py"])

df = fetch_recent_data(symbol, timeframe)

if df.empty:
    st.warning("داده‌ای برای نمایش وجود ندارد.")
else:
    # تحلیل ساختار
    detector = SwingPointDetector(symbol, timeframe)
    result_df = df.copy()
    result_df[['swing_high', 'swing_low', 'structure', 'bos', 'choch']] = detector.calculate(df, timeframe)

    # تشخیص کانال‌ها
    channel_detector = PriceChannelDetector()
    channels = channel_detector.detect_channels(result_df)

    # فقط یکبار چارت بساز — همه چیز را در این تابع بفرست
    chart = plot_price_action_chart(result_df, channels=channels, title=f"{symbol} [{timeframe}] - Price Action")

    st.plotly_chart(chart, use_container_width=True)
