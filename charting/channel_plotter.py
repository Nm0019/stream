import plotly.graph_objects as go
import pandas as pd

def add_channels_to_figure(fig, df: pd.DataFrame, channels: list):
    """
    افزودن خطوط کانال و سایه‌ی بین آنها به شکل نمودار قیمت
    """
    for ch in channels:
        # استخراج نقاط پایینی (lower line)
        x_lower = [df.loc[i, 'time'] for i, _ in ch['lower_line']]
        y_lower = [price for _, price in ch['lower_line']]

        # استخراج نقاط بالایی (upper line)
        x_upper = [df.loc[i, 'time'] for i, _ in ch['upper_line']]
        y_upper = [price for _, price in ch['upper_line']]

        # رسم خط پایین کانال
        fig.add_trace(go.Scatter(
            x=x_lower,
            y=y_lower,
            mode='lines',
            line=dict(color='rgba(0, 0, 255, 0.8)', width=2, dash='dot'),
            name='Lower Channel' if ch['type'] == 'bullish' else 'Lower Bound',
            showlegend=False
        ))

        # رسم خط بالا کانال
        fig.add_trace(go.Scatter(
            x=x_upper,
            y=y_upper,
            mode='lines',
            line=dict(color='rgba(0, 0, 255, 0.8)', width=2),
            name='Upper Channel' if ch['type'] == 'bullish' else 'Upper Bound',
            showlegend=False
        ))

        # پر کردن ناحیه بین دو خط (حاله‌ی کانال)
        fig.add_trace(go.Scatter(
            x=x_lower + x_upper[::-1],
            y=y_lower + y_upper[::-1],
            fill='toself',
            fillcolor='rgba(0, 0, 255, 0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False,
            name='Channel Zone'
        ))

    return fig
