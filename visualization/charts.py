import plotly.graph_objects as go
import pandas as pd
from charting.channel_plotter import add_channels_to_figure


def plot_price_action_chart(df: pd.DataFrame, channels: list = None, title="Price Action"):
    fig = go.Figure()

    # محدوده زمانی برای 10 کندل آخر
    visible_start = df['time'].iloc[-70]
    visible_end = df['time'].iloc[-1]
    visible_df = df[(df['time'] >= visible_start) & (df['time'] <= visible_end)]

    # محاسبه min و max فقط بر اساس کندل‌های در حال نمایش
    min_price = visible_df['low'].min()
    max_price = visible_df['high'].max()
    price_range = max_price - min_price
    padding_ratio = 0.10

    y_min = min_price - price_range * padding_ratio
    y_max = max_price + price_range * padding_ratio

    # 📉 کندل‌ها
    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Price",
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    # 📌 سوینگ‌ها
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['swing_high'],
        mode='markers+text',
        name='Swing High',
        marker=dict(color='blue', size=6, symbol='triangle-up'),
        text=df['structure'],
        textposition="top center",
        textfont=dict(size=10)
    ))

    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['swing_low'],
        mode='markers+text',
        name='Swing Low',
        marker=dict(color='orange', size=6, symbol='triangle-down'),
        text=df['structure'],
        textposition="bottom center",
        textfont=dict(size=10)
    ))

    # ⚡ BoS
    bos_mask = df['bos'].notna() & (df['bos'] != '')
    fig.add_trace(go.Scatter(
        x=df.loc[bos_mask, 'time'],
        y=df.loc[bos_mask, 'close'],
        mode='text',
        name='BoS',
        text=df.loc[bos_mask, 'bos'],
        textposition='top right',
        textfont=dict(color='magenta', size=12),
        showlegend=True
    ))

    # 🔁 CHoCH
    choch_mask = df['choch'].notna() & (df['choch'] != '')
    fig.add_trace(go.Scatter(
        x=df.loc[choch_mask, 'time'],
        y=df.loc[choch_mask, 'close'],
        mode='text',
        name='CHoCH',
        text=df.loc[choch_mask, 'choch'],
        textposition='bottom right',
        textfont=dict(color='red', size=12),
        showlegend=True
    ))

    # 📐 کانال‌ها
    if channels:
        fig = add_channels_to_figure(fig, df, channels)

    # ✨ تنظیمات نهایی
    fig.update_layout(
        title=title,
        xaxis=dict(
            range=[visible_start, visible_end],
            rangeslider=dict(visible=True),
            type='date'
        ),
        yaxis=dict(
            range=[y_min, y_max]  # داینامیک و فقط برای بازه نمایش داده‌شده
        ),
        height=1000,
        template='plotly_dark',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

