import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from plotly.subplots import make_subplots

from charts.price_chart import add_price
from charts.ma_chart import add_sma20,add_sma50,add_sma100,add_ema20,add_ema50,add_ema100
from charts.rsi_chart import add_rsi
from charts.macd_chart import add_macd

OVERLAY_INDICATORS = {
    "SMA_20": add_sma20,
    "SMA_50": add_sma50,
    "SMA_100": add_sma100,
    "EMA_20": add_ema20,
    "EMA_50": add_ema50,
    "EMA_100": add_ema100,
}

OVERLAY_TRACE_NAMES = {
    "SMA_20": ["SMA_20"],
    "SMA_50": ["SMA_50"],
    "SMA_100": ["SMA_100"],
    "EMA_20": ["EMA_20"],
    "EMA_50": ["EMA_50"],
    "EMA_100": ["EMA_100"],
}

PANEL_INDICATORS = {
    "RSI": add_rsi,
    "MACD": add_macd,
}

def _select_initial_start_date(data):
    end_date = data.index[-1]
    default_start = end_date - pd.DateOffset(months=6)
    visible_data = data[data.index >= default_start]

    low_series = visible_data["Low"].dropna()
    high_series = visible_data["High"].dropna()

    if low_series.empty or high_series.empty:
        return default_start

    full_span = float(high_series.max()) - float(low_series.min())

    recent_window = min(len(visible_data), 45)
    recent_low = float(low_series.tail(recent_window).min())
    recent_high = float(high_series.tail(recent_window).max())
    recent_span = recent_high - recent_low

    if recent_span > 0 and full_span > recent_span * 1.25:
        return end_date - pd.DateOffset(months=3)

    return default_start

def _compute_price_axis_range(visible_data):
    low_series = visible_data["Low"].dropna()
    high_series = visible_data["High"].dropna()
    close_series = visible_data["Close"].dropna()

    if low_series.empty or high_series.empty:
        return None

    y_min = float(low_series.min())
    y_max = float(high_series.max())
    full_span = y_max - y_min

    if close_series.empty:
        close_series = high_series

    recent_window = min(len(visible_data), 45)
    recent_low = float(low_series.tail(recent_window).min())
    recent_high = float(high_series.tail(recent_window).max())
    recent_span = recent_high - recent_low

    focused_low = float(low_series.quantile(0.03))
    focused_high = float(high_series.quantile(0.97))
    focused_span = focused_high - focused_low

    candidate_low = min(focused_low, recent_low)
    candidate_high = max(focused_high, recent_high)
    candidate_span = candidate_high - candidate_low

    latest_close = float(close_series.iloc[-1])

    # When the recent trading band is much tighter than the visible 6-month
    # history, prefer that band so the current candles are readable.
    if (
        recent_span > 0
        and full_span > recent_span * 1.25
        and recent_low <= latest_close <= recent_high
    ):
        y_min = recent_low
        y_max = recent_high
        span = recent_span
        padding_ratio = 0.06

    # Switch to a tighter range only when visible outliers are materially
    # compressing the candles and the latest price remains inside the focus band.
    elif (
        focused_span > 0
        and candidate_span > 0
        and full_span > candidate_span * 1.35
        and candidate_low <= latest_close <= candidate_high
    ):
        y_min = candidate_low
        y_max = candidate_high
        span = candidate_span
        padding_ratio = 0.06
    else:
        span = y_max - y_min
        padding_ratio = 0.1

    padding = span * padding_ratio if span > 0 else max(latest_close * 0.02, 1.0)

    return [y_min - padding, y_max + padding]

def generate_graph(data, indicators=None, visible_indicators=None):

    if indicators is None:
        indicators = []
    if visible_indicators is None:
        visible_indicators = indicators

    overlay_inds = [i for i in indicators if i in OVERLAY_INDICATORS]
    panel_inds = [i for i in indicators if i in PANEL_INDICATORS]
    
    #layout-calculation

    rows = 1 + len(panel_inds)

    
    row_heights = [3] + [1] * len(panel_inds)

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=row_heights
    )

    #row-mapping

    row_map = {"PRICE": 1}

    current_row = 2

    for ind in panel_inds:
        row_map[ind] = current_row
        current_row += 1

    add_price(fig, data, rows=row_map["PRICE"])

    for ind in overlay_inds:
        OVERLAY_INDICATORS[ind](fig, data, rows=row_map["PRICE"])

    for ind in panel_inds:
        PANEL_INDICATORS[ind](fig, data, rows=row_map[ind])

    hidden_overlay_traces = set()
    for ind in overlay_inds:
        if ind not in visible_indicators:
            hidden_overlay_traces.update(OVERLAY_TRACE_NAMES.get(ind, []))
    if hidden_overlay_traces:
        for trace in fig.data:
            if trace.name in hidden_overlay_traces:
                trace.visible = False

    if len(panel_inds)>0:
        height = 400 + (rows - 1) * 150
    else:
        height = 570

    # -----------------------
    # Layout
    # -----------------------
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#06090f",
        plot_bgcolor="#05080e",
        dragmode="pan",
        hovermode="x unified",
        height=height,
        margin=dict(l=10, r=150, t=20, b=40),
        showlegend=False,
        uirevision="main-chart",
        transition=dict(duration=0),

        hoverlabel=dict(
            bgcolor="#0d1117",
            bordercolor="#1e2330",
            font=dict(
                family="Inter, monospace",
                size=12,
                color="#e2e8f0"
            ),
            namelength=-1
        )
    )

    fig.update_layout(xaxis_rangeslider_visible=False)

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showspikes=True,
        spikecolor="gray",
        spikemode="across",
        spikesnap="cursor",
        rangebreaks=[dict(bounds=["sat", "mon"])]
    )

    fig.update_yaxes(
        side="right",
        tickformat=",.2f",
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False,
        showspikes=True,
        spikecolor="gray",
        spikemode="across",
        spikesnap="cursor",
        automargin=True,
        separatethousands=True
    )

    fig.update_yaxes(fixedrange=True)

    # -----------------------
    # Zoom (6 months)
    # -----------------------
    end_date = data.index[-1]
    start_date = _select_initial_start_date(data)

    visible_data = data[data.index >= start_date]
    price_axis_range = _compute_price_axis_range(visible_data)

    fig.update_xaxes(range=[start_date, end_date], fixedrange=False)

    if price_axis_range is not None:
        fig.update_yaxes(
                range=price_axis_range,
                autorange=False,
                fixedrange=False,
                row=1, col=1
        )

    # -----------------------
    # Export HTML
    # -----------------------
    graph_html = pio.to_html(
        fig,
        full_html=False,
        config={
            "scrollZoom": False,
            "displaylogo": False,
            "displayModeBar": False,
            "responsive": True
        }
    )

    return graph_html
