import plotly.graph_objects as go


def add_price(fig, data, rows):
    hover_text = [
        (
            f"Open: {open_price:.2f}<br>"
            f"High: {high_price:.2f}<br>"
            f"Low: {low_price:.2f}<br>"
            f"Close: {close_price:.2f}"
        )
        for open_price, high_price, low_price, close_price in zip(
            data["Open"],
            data["High"],
            data["Low"],
            data["Close"],
        )
    ]

    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Price",

            increasing=dict(
                line=dict(color="#22c55e", width=1),
                fillcolor="#22c55e"
            ),
            decreasing=dict(
                line=dict(color="#ef4444", width=1),
                fillcolor="#ef4444"
            ),
            text=hover_text,
            hoverinfo="text"
        ),
        row=rows,
        col=1
    )
