import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from charting.channel_plotter import add_channels_to_figure

# ثابت‌ها
VISIBLE_CANDLES_PRICE = 100
VISIBLE_CANDLES_ATR = 20
VISIBLE_CANDLES_EMA = 100

# ----------------------------------------------------
def plot_price_action_chart(df: pd.DataFrame, channels: list = None, title="Price Action"):
    df = df[df['time'].notna()].copy()

    visible_start = df['time'].iloc[-VISIBLE_CANDLES_PRICE]
    visible_end = df['time'].iloc[-1]
    visible_df = df[(df['time'] >= visible_start) & (df['time'] <= visible_end)]

    min_price = visible_df['low'].min()
    max_price = visible_df['high'].max()
    padding_ratio = 0.10
    y_min = min_price - (max_price - min_price) * padding_ratio
    y_max = max_price + (max_price - min_price) * padding_ratio

    fig = go.Figure()

    # کندل‌ها
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name="Price", increasing_line_color='green', decreasing_line_color='red'
    ))

    # Swing High
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['swing_high'],
        mode='markers+text', name='Swing High',
        marker=dict(color='blue', size=6, symbol='triangle-up'),
        text=df['structure'], textposition="top center", textfont=dict(size=10)
    ))

    # Swing Low
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['swing_low'],
        mode='markers+text', name='Swing Low',
        marker=dict(color='orange', size=6, symbol='triangle-down'),
        text=df['structure'], textposition="bottom center", textfont=dict(size=10)
    ))

    # BOS
    bos_mask = df['bos'].notna() & (df['bos'] != '')
    fig.add_trace(go.Scatter(
        x=df.loc[bos_mask, 'time'], y=df.loc[bos_mask, 'close'],
        mode='text', name='BoS',
        text=df.loc[bos_mask, 'bos'],
        textposition='top right',
        textfont=dict(color='rgba(255,0,255,0.9)', size=12)
    ))

    # CHoCH
    choch_mask = df['choch'].notna() & (df['choch'] != '')
    fig.add_trace(go.Scatter(
        x=df.loc[choch_mask, 'time'], y=df.loc[choch_mask, 'close'],
        mode='text', name='CHoCH',
        text=df.loc[choch_mask, 'choch'],
        textposition='bottom right',
        textfont=dict(color='rgba(255,50,50,0.9)', size=12)
    ))

    # کانال‌ها
    if channels and isinstance(channels, list):
        fig = add_channels_to_figure(fig, df, channels)

    fig.update_layout(
        title=title,
        xaxis=dict(range=[visible_start, visible_end], rangeslider=dict(visible=True), type='date'),
        yaxis=dict(range=[y_min, y_max]),
        height=800, template='plotly_dark',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ----------------------------------------------------
def plot_atr_chart(df: pd.DataFrame, title: str = "ATR Chart"):
    figATR = go.Figure()
    df = df.copy()
    df['ATR'] = df['TR']
    df['momentum_strength'] = df['ATR'].diff().abs().clip(lower=1e-6)

    min_strength, max_strength = df['momentum_strength'].min(), df['momentum_strength'].max()
    df['normalized_strength'] = 0.0 if max_strength - min_strength == 0 else \
        (df['momentum_strength'] - min_strength) / (max_strength - min_strength)

    df['expansion'] = 0.05 + df['normalized_strength'] * 0.6
    df['ATR_upper'] = df['ATR'] * (1 + df['expansion'])
    df['ATR_lower'] = df['ATR'] * (1 - df['expansion'])
    df['alpha'] = (0.05 + df['normalized_strength'] * 0.4).fillna(0.1)

    df = df.tail(VISIBLE_CANDLES_ATR)
    df['trend_group'] = (df['Trend_Signal'] != df['Trend_Signal'].shift()).cumsum()

    for _, group in df.groupby('trend_group'):
        trend = group['Trend_Signal'].iloc[0]
        base_color = (0, 255, 0) if trend == 'Uptrend' else (255, 0, 0)
        line_color = f"rgba({base_color[0]}, {base_color[1]}, {base_color[2]}, 1)"
        avg_alpha = max(0.01, min(group['alpha'].mean(), 2.5))
        fillcolor = f"rgba({base_color[0]}, {base_color[1]}, 0, {avg_alpha:.2f})"

        # خط ATR
        figATR.add_trace(go.Scatter(
            x=group['time'], y=group['ATR'], mode='lines',
            line=dict(color=line_color, width=2),
            name=f"ATR ({trend})",
            customdata=group[['Trend_Signal']],   # ستون ترند رو پاس بده
            hovertemplate="ATR: %{y:.2f}<br>Trend: %{customdata[0]}"
        ))

        # هاله ATR
        figATR.add_trace(go.Scatter(
            x=group['time'].tolist() + group['time'][::-1].tolist(),
            y=group['ATR_upper'].tolist() + group['ATR_lower'][::-1].tolist(),
            fill='toself', fillcolor=fillcolor,
            line=dict(color='rgba(255,255,255,0)'), showlegend=False, hoverinfo="skip"
        ))

    figATR.update_layout(
        title=title, height=220, margin=dict(l=30, r=30, t=30, b=30),
        template="plotly_dark",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis_title="ATR (True Range)"
    )
    return figATR

# ----------------------------------------------------
def plot_atr_momentum_chart(df: pd.DataFrame, title: str = "ATR Momentum"):
    figATRMO = go.Figure()
    df = df.copy().tail(VISIBLE_CANDLES_ATR)
    df['ATR_Momentum'] = df['ATR_Momentum'].fillna(0)
    df['trend_group'] = (df['Trend_Signal'] != df['Trend_Signal'].shift()).cumsum()

    for _, group in df.groupby('trend_group'):
        trend = group['Trend_Signal'].iloc[0]
        base_color = (0, 255, 0) if trend == 'Uptrend' else (255, 0, 0)
        momentum_factor = min(max(group['ATR_Momentum'].abs().mean(), 0.1), 5)

        alpha = min(0.05 + (momentum_factor / 10), 0.35)
        linecolor = f"rgba({base_color[0]}, {base_color[1]}, {base_color[2]}, 1)"
        fillcolor = f"rgba({base_color[0]}, {base_color[1]}, {base_color[2]}, {alpha})"

        # خط مومنتوم
        figATRMO.add_trace(go.Scatter(
            x=group['time'], y=group['ATR_Momentum'], mode='lines',
            line=dict(color=linecolor, width=2),
            name=f"Momentum ({trend})",
            customdata=group[['Trend_Signal']],   # ستون ترند رو پاس بده
            hovertemplate="Momentum:: %{y:.2f}<br>Trend: %{customdata[0]}"
            
        ))

        # ناحیه رنگی
        figATRMO.add_trace(go.Scatter(
            x=group['time'].tolist() + group['time'][::-1].tolist(),
            y=[0]*len(group) + group['ATR_Momentum'][::-1].tolist(),
            fill='toself', fillcolor=fillcolor,
            line=dict(color='rgba(255,255,255,0)'), showlegend=False, hoverinfo='skip'
        ))

    figATRMO.update_layout(
        title=title, height=280, margin=dict(l=10, r=10, t=25, b=25),
        template="plotly_dark",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis_title="ATR Momentum"
    )
    return figATRMO

#-----------------------------------------------------

#volatility_view.py
import streamlit as st

def show_volatility_info(df: pd.DataFrame, title: str = "Volatility Overview"):
    latest_value = df['Volatility_Percent'].iloc[-1]

    # تعیین وضعیت نوسان
    if latest_value < 0.5:
        status = "📘 آرام"
        color = "blue"
    elif 0.5 <= latest_value < 1:
        status = "🟢 نوسان نرمال"
        color = "green"
    elif 1 <= latest_value < 1.5:
        status = "🟠 نوسان زیاد"
        color = "orange"
    elif 1.5 <= latest_value < 2:
        status = "🟠 نوسان شدید"
        color = "red"
    else:
        status = "🔴 بسیار پرنوسان"
        color = "purple"

    # تقسیم صفحه به دو ستون
    col1, col2 = st.columns([1.3, 1.7])

    # ✅ کارت اطلاعاتی سمت چپ
    with col1:
        st.markdown(f"""
            <div style="padding:15px;border-radius:12px;background-color:#1e1e1e;border-left:8px solid {color};">
                <h4 style="color:white;margin:0;">Volatility Percent</h4>
                <h1 style="color:{color};margin:0;">{latest_value:.2f}%</h1>
                <p style="color:white;margin:0;">وضعیت: <b style="color:{color};">{status}</b></p>
            </div>
        """, unsafe_allow_html=True)

    # ✅ Gauge Chart سمت راست
    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=latest_value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 16}},
            delta={'reference': 2.5, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge={
                'axis': {'range': [0, 5], 'tickwidth': 0.5, 'tickcolor': "gray"},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 0.5], 'color': "rgba(0,0,255,0.2)"},
                    {'range': [0.5, 1], 'color': "rgba(0,255,0,0.2)"},
                    {'range': [1, 1.5], 'color': "rgba(255,165,0,0.3)"},
                    {'range': [1.5, 2], 'color': "rgba(255,0,0,0.3)"},
                    {'range': [2, 4], 'color': "rgba(255,0,0,0.3)"},
                ],
                'threshold': {
                    'line': {'color': color, 'width': 4},
                    'thickness': 0.75,
                    'value': latest_value
                }
            }
        ))

        fig.update_layout(
            margin=dict(l=20, r=20, t=30, b=10),
            height=180,
            template='plotly_dark'
        )
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
def plot_triple_ema_with_score(df: pd.DataFrame, title: str = "Triple EMA with Score"):
    df = df.copy().tail(VISIBLE_CANDLES_EMA)
    
    short_col = [col for col in df.columns if col.startswith("EMA_short_")][0]
    mid_col   = [col for col in df.columns if col.startswith("EMA_mid_")][0]
    long_col  = [col for col in df.columns if col.startswith("EMA_long_")][0]

    figEMA = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
        row_heights=[0.6, 0.25, 0.15],
        subplot_titles=(title, "Score EMA (Trend Strength)", "Volume")
    )

    # ----------------- کندل‌ها -----------------
    figEMA.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name="Candles", opacity=0.8
    ), row=1, col=1)

    # ----------------- EMA ها -----------------
    for col, color in [(short_col, 'orange'), (mid_col, 'blue'), (long_col, 'purple')]:
        figEMA.add_trace(go.Scatter(
            x=df['time'], y=df[col], mode='lines', name=col.upper(),
            line=dict(color=color, width=1.5)
        ), row=1, col=1)

    # ----------------- کراس EMA -----------------
    cross_up_mask   = (df[short_col] > df[mid_col]) & (df[short_col].shift() <= df[mid_col].shift())
    cross_down_mask = (df[short_col] < df[mid_col]) & (df[short_col].shift() >= df[mid_col].shift())

    figEMA.add_trace(go.Scatter(
        x=df.loc[cross_up_mask, 'time'], y=df.loc[cross_up_mask, short_col],
        mode='markers', name='Bullish Cross',
        marker=dict(color='lime', size=9, symbol='triangle-up', line=dict(width=1, color='black')),
        hovertemplate="Bullish Cross<br>Price: %{y:.2f}<extra></extra>"
    ), row=1, col=1)

    figEMA.add_trace(go.Scatter(
        x=df.loc[cross_down_mask, 'time'], y=df.loc[cross_down_mask, short_col],
        mode='markers', name='Bearish Cross',
        marker=dict(color='red', size=9, symbol='triangle-down', line=dict(width=1, color='black')),
        hovertemplate="Bearish Cross<br>Price: %{y:.2f}<extra></extra>"
    ), row=1, col=1)

    # ----------------- پس‌زمینه روند -----------------
    df['trend_group'] = (df['Trend_Signal'] != df['Trend_Signal'].shift()).cumsum()
    for _, group in df.groupby('trend_group'):
        trend = group['Trend_Signal'].iloc[0]
        bg_color = 'rgba(0,255,0,0.1)' if trend=='Uptrend' else 'rgba(255,0,0,0.1)'
        figEMA.add_trace(go.Scatter(
            x=group['time'].tolist() + group['time'][::-1].tolist(),
            y=[df['high'].max()]*len(group) + [df['low'].min()]*len(group),
            fill='toself', fillcolor=bg_color,
            line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip'
        ), row=1, col=1)
            # ----------------- Score EMA -----------------
    figEMA.add_trace(go.Scatter(
        x=df['time'], y=df['score_EMA'], mode='lines+markers', name='Score EMA',
        line=dict(color='cyan', width=2), marker=dict(size=4)
    ), row=2, col=1)

    # ----------------- Layout -----------------
    figEMA.update_layout(
        height=700, margin=dict(l=10, r=10, t=40, b=25),
        template="plotly_dark",
        xaxis=dict(rangeslider=dict(visible=False), type="date"),
        xaxis2=dict(rangeslider=dict(visible=False), type="date"),
        xaxis3=dict(rangeslider=dict(visible=False), type="date"),
        yaxis_title="Price", yaxis2_title="Score EMA", yaxis3_title="Volume"
    )
    return figEMA

#------------------------------------------------------------------------------------
def plot_adx_chart(df: pd.DataFrame, title: str = "ADX Indicator"):
    df = df.copy().tail(VISIBLE_CANDLES_EMA)

    figADX = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, "Volume")
    )

    # ----------------- خطوط ADX -----------------
    figADX.add_trace(go.Scatter(
        x=df['time'], y=df['ADX'], mode='lines', name='ADX',
        line=dict(color='orange', width=2)
    ), row=1, col=1)

    figADX.add_trace(go.Scatter(
        x=df['time'], y=df['diplusn'], mode='lines', name='+DI',
        line=dict(color='green', width=1.5, dash='dot')
    ), row=1, col=1)

    figADX.add_trace(go.Scatter(
        x=df['time'], y=df['diminusn'], mode='lines', name='-DI',
        line=dict(color='red', width=1.5, dash='dot')
    ), row=1, col=1)

    # ----------------- پس‌زمینه روند -----------------
    df['trend_group'] = (df['Trend_Signal'] != df['Trend_Signal'].shift()).cumsum()
    for _, group in df.groupby('trend_group'):
        trend = group['Trend_Signal'].iloc[0]
        bg_color = 'rgba(0,255,0,0.1)' if trend=='Uptrend' else 'rgba(255,0,0,0.1)'
        figADX.add_trace(go.Scatter(
            x=group['time'].tolist() + group['time'][::-1].tolist(),
            y=[df[['ADX','diplusn','diminusn']].max().max()]*len(group) + [df[['ADX','diplusn','diminusn']].min().min()]*len(group),
            fill='toself', fillcolor=bg_color,
            line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip'
        ), row=1, col=1)

    # ----------------- سیگنال‌ها -----------------
    figADX.add_trace(go.Scatter(
        x=df.loc[df['sig_final']=='Buy', 'time'], y=df.loc[df['sig_final']=='Buy', 'ADX'],
        mode='markers', name='ADX Buy',
        marker=dict(color='green', size=8, symbol='triangle-up')
    ), row=1, col=1)

    figADX.add_trace(go.Scatter(
        x=df.loc[df['sig_final']=='Sell', 'time'], y=df.loc[df['sig_final']=='Sell', 'ADX'],
        mode='markers', name='ADX Sell',
        marker=dict(color='red', size=8, symbol='triangle-down')
    ), row=1, col=1)

    # ----------------- Volume -----------------
    if 'volume' in df.columns:
        figADX.add_trace(go.Bar(
            x=df['time'], y=df['volume'], name='Volume', marker_color='gray', opacity=0.5
        ), row=2, col=1)

    # ----------------- Annotation آخرین سیگنال -----------------
    last_row = df.iloc[-1]
    signal_text = "📈 خرید" if last_row['sig_final']=='Buy' else ("📉 فروش" if last_row['sig_final']=='Sell' else "⚪ خنثی")
    figADX.add_annotation(
        xref="paper", yref="paper", x=0.98, y=0.95, showarrow=False,
        text=f"{signal_text} | ADX: {round(last_row['ADX'],2)}",
        font=dict(size=12, color="white"),
        align="right", bgcolor="rgba(0,0,0,0.6)", bordercolor="white", borderwidth=1
    )

    figADX.update_layout(
        height=500, margin=dict(l=10, r=10, t=40, b=25),
        template="plotly_dark",
        xaxis=dict(rangeslider=dict(visible=False), type="date"),
        xaxis2=dict(rangeslider=dict(visible=False), type="date"),
        yaxis_title="ADX / DI", yaxis2_title="Volume"
    )

    return figADX


#---------------------------------------------------------------------

def plot_macd_chart(df: pd.DataFrame, title: str = "MACD Chart"):
    df = df.copy()

    # محدود کردن تعداد کندل‌ها برای سرعت نمایش
    VISIBLE_CANDLES = 100
    df = df.tail(VISIBLE_CANDLES).reset_index(drop=True)

    # ایجاد subplot: کندل + MACD
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
        subplot_titles=(title, "MACD / Signal / Histogram")
    )

    # ----------------- کندل‌ها -----------------
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name="Candles",
        increasing_line_color='lime', decreasing_line_color='red',
        opacity=0.7
    ), row=1, col=1)

    # ----------------- خطوط MA (EMA) -----------------
    ma_colors = {
        "EMA": "gray", "SMA": "orange", "RMA": "purple", "WMA": "brown",
        "DEMA": "cyan", "TEMA": "magenta", "VIDYA": "yellow"
    }

    for ma_name, color in ma_colors.items():
        if ma_name in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'], y=df[ma_name],
                mode='lines', name=ma_name,
                line=dict(color=color, width=1.5)
            ), row=1, col=1)

      # ----------------- MACD و Signal -----------------
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['MACD'],
        mode='lines', name='MACD',
        line=dict(color='blue', width=2)
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df['time'], y=df['Signal'],
        mode='lines', name='Signal',
        line=dict(color='red', width=1.5)
    ), row=2, col=1)

    # ----------------- Histogram -----------------
    hist_colors = []
    for i in range(len(df)):
        if df['Histogram'].iloc[i] >= 0:
            hist_colors.append('blue' if i == 0 or df['Histogram'].iloc[i] > df['Histogram'].iloc[i-1] else 'lightblue')
        else:
            hist_colors.append('magenta' if i == 0 or df['Histogram'].iloc[i] < df['Histogram'].iloc[i-1] else 'pink')

    fig.add_trace(go.Bar(
        x=df['time'], y=df['Histogram'],
        marker_color=hist_colors, name='Histogram'
    ), row=2, col=1)

    # ----------------- سیگنال‌های ورود و خروج -----------------
    fig.add_trace(go.Scatter(
        x=df.loc[df['long_entry'], 'time'], y=df.loc[df['long_entry'], 'close'],
        mode='markers', name='Long Entry',
        marker=dict(color='lime', size=10, symbol='triangle-up')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.loc[df['short_entry'], 'time'], y=df.loc[df['short_entry'], 'close'],
        mode='markers', name='Short Entry',
        marker=dict(color='red', size=10, symbol='triangle-down')
    ), row=1, col=1)

    # ----------------- پس‌زمینه روند (قیمت نسبت به EMA) -----------------
    df['trend_group'] = (df['isAboveMA'] != df['isAboveMA'].shift()).cumsum()
    for _, group in df.groupby('trend_group'):
        trend = group['isAboveMA'].iloc[0]
        bg_color = 'rgba(0,255,0,0.1)' if trend else 'rgba(255,0,0,0.1)'
        fig.add_trace(go.Scatter(
            x=group['time'].tolist() + group['time'][::-1].tolist(),
            y=[df['high'].max()]*len(group) + [df['low'].min()]*len(group),
            fill='toself', fillcolor=bg_color,
            line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip'
        ), row=1, col=1)

    # ----------------- Layout -----------------
    fig.update_layout(
        template="plotly_dark",
        height=700,
        margin=dict(l=10, r=10, t=40, b=25),
        xaxis=dict(rangeslider=dict(visible=False), type="date"),
        xaxis2=dict(rangeslider=dict(visible=False), type="date"),
        yaxis_title="Price",
        yaxis2_title="MACD"
    )

    return fig
#----------------------------------------------------------------------------------------


def plot_rsi_chart(df):
    VISIBLE_CANDLES = 100
    df = df.tail(VISIBLE_CANDLES).reset_index(drop=True)
    fig = go.Figure()

    # --- نواحی رنگی پشت RSI (بر اساس trendDirection) ---
    segments = []
    current_trend = df['RSI_trend'].iloc[0]
    seg_start = 0

    for i in range(1, len(df)):
        if df['RSI_trend'].iloc[i] != current_trend:
            segments.append((seg_start, i, current_trend))
            seg_start = i
            current_trend = df['RSI_trend'].iloc[i]
    segments.append((seg_start, len(df), current_trend))

    for start, end, trend in segments:
        color = 'rgba(0,255,0,0.15)' if trend == 1 else 'rgba(255,0,0,0.15)'
        fig.add_trace(go.Scatter(
            x=df['time'].iloc[start:end],
            y=df['RSI'].iloc[start:end],
            mode='lines',
            line=dict(width=0),
            fill='tozeroy',
            fillcolor=color,
            showlegend=False,
            hoverinfo='skip'
        ))

    # --- خط RSI ---
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='white', width=1.5)
    ))

    # --- خط Supertrend ---
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['RSI_ST'],
        mode='lines',
        name='RSI Supertrend',
        line=dict(color='cyan', width=2)
    ))

    # --- سیگنال ورود ---
    long_cross = df[df['long_entry'] == 1]
    fig.add_trace(go.Scatter(
        x=long_cross['time'], y=long_cross['RSI'],
        mode='markers',
        name='Long Entry',
        marker=dict(symbol='triangle-up', color='lime', size=10)
    ))

    # --- سیگنال خروج ---
    short_cross = df[df['short_entry'] == 1]
    fig.add_trace(go.Scatter(
        x=short_cross['time'], y=short_cross['RSI'],
        mode='markers',
        name='Short Entry',
        marker=dict(symbol='triangle-down', color='red', size=10)
    ))

    # --- خطوط Overbought / Oversold ---
    fig.add_hline(y=70, line=dict(color='red', width=1, dash='dash'),
                  annotation_text="Overbought", annotation_position="top left")
    fig.add_hline(y=30, line=dict(color='green', width=1, dash='dash'),
                  annotation_text="Oversold", annotation_position="bottom left")

    # --- تنظیمات نهایی ---
    fig.update_layout(
        title="Supertrended RSI Chart",
        yaxis=dict(title="RSI", range=[0, 100]),
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.2),
        height=500
    )

    return fig