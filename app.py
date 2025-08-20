# app.py

import streamlit as st
import pandas as pd
import subprocess

from mt5_connector.historical_fetcher import download_btcusd
from database.db_operations import fetch_recent_data
from analysis.price_action.price_action import SwingPointDetector
from analysis.channel_detector import PriceChannelDetector
from visualization.charts import (
    plot_price_action_chart,
    plot_atr_chart,
    plot_atr_momentum_chart,
    show_volatility_info,
    plot_triple_ema_with_score,
    plot_adx_chart,
    plot_macd_chart,
    plot_rsi_chart
)

st.set_page_config(layout="wide")
st.title("🔍 BTCUSD Price Action Viewer")

symbol = "BTCUSD"
timeframe = "H4"

# دانلود داده‌ها
download_btcusd()

with st.spinner("در حال اجرای اندیکاتورها..."):
    subprocess.run(["python", "run_indicators_launcher.py"])

df = fetch_recent_data(symbol, timeframe)

if df.empty:
    st.warning("داده‌ای برای نمایش وجود ندارد.")
    st.stop()

# محدود کردن حجم داده برای رسم سریع‌تر
MAX_ROWS = 5000
if len(df) > MAX_ROWS:
    df = df.tail(MAX_ROWS)

# محاسبه Swing Points
detector = SwingPointDetector(symbol, timeframe)
result_df = df.copy()
result_df[['swing_high', 'swing_low', 'structure', 'bos', 'choch']] = detector.calculate(df, timeframe)

# تشخیص کانال‌ها
channel_detector = PriceChannelDetector()
channels = channel_detector.detect_channels(result_df)

# نمایش درصد نوسان قیمت
st.subheader("درصد نوسان قیمت %")
chart = plot_price_action_chart(result_df, channels=channels, title=f"{symbol} [{timeframe}] - Price Action")
st.plotly_chart(chart, use_container_width=True)


# تب‌ها برای نمایش مرتب چارت‌ها
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Price Action", "ATR","EMA & ADX","MACD","RSI"])

with tab1:
    show_volatility_info(df)
    # chart = plot_price_action_chart(result_df, channels=channels, title=f"{symbol} [{timeframe}] - Price Action")
    # st.plotly_chart(chart, use_container_width=True)

with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 نوسان فعلی قیمت ")
            atr_chart = plot_atr_chart(df)
            st.plotly_chart(atr_chart, use_container_width=True)
        
        with col2:
            st.subheader("⚡   افزایش یا کاهش قدرت نوسان")
            atr_momentum_chart = plot_atr_momentum_chart(df)
            st.plotly_chart(atr_momentum_chart, use_container_width=True)

with tab3:
    try:
        figEMA = plot_triple_ema_with_score(df, title=f"Triple EMA - {symbol} ({timeframe})")
        st.plotly_chart(figEMA, use_container_width=True)

        figADX = plot_adx_chart(df, title=f"ADX Indicator - {symbol} ({timeframe})")
        st.plotly_chart(figADX, use_container_width=True)
    except Exception as e:
        st.error(f"❌ خطا در رسم EMA یا ADX: {e}")

with tab4:
    try:
        figMACD = plot_macd_chart(df)
        st.plotly_chart(figMACD, use_container_width=True)

    except Exception as e:
        st.error(f"❌ خطا در رسم MACD: {e}")

with tab5:
    try:
        figMACD = plot_rsi_chart(df)
        st.plotly_chart(figMACD, use_container_width=True)

    except Exception as e:
        st.error(f"❌ خطا در رسم rsi: {e}")

# DJANGO_API_URL = "http://127.0.0.1:8000/api/add_candle/"

# def send_candle_to_django(candle):
#     try:
#         response = requests.post(DJANGO_API_URL, json=candle)
#         if response.status_code in [200, 201]:
#             st.success(f"✅ کندل {candle['time']} ({candle['timeframe']}) ارسال شد")
#         else:
#             st.error(f"❌ خطا در ارسال کندل: {response.text}")
#     except Exception as e:
#         st.error(f"❌ خطای شبکه: {e}")

# # بعد از fetch_recent_data
# if not df.empty:
#     for _, row in df.iterrows():
#         candle = {
#             "symbol": "BTCUSD",
#             "timeframe": "H4",  # یا هر تایم‌فریم واقعی
#             "time": row['time'].replace(tzinfo=None).isoformat(),  # حذف timezone
#             "open": float(row['open']),
#             "high": float(row['high']),
#             "low": float(row['low']),
#             "close": float(row['close']),
#             "volume": float(row['volume'])
#         }
#         send_candle_to_django(candle)

