import plotly.graph_objects as go
import pandas as pd

def add_macd(fig,data,rows):
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["macd_histogram"],
                name="MACD Histogram",
                marker=dict(
                    color=[
                        "#22c55e" if (pd.notna(val) and val >= 0)
                        else "#ef4444" if (pd.notna(val) and val < 0)
                        else "rgba(0,0,0,0)"
                        for val in data["macd_histogram"]
                    ]
                )
            ),
            row=rows, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["macd_indicator"],
                mode="lines",
                name="MACD",
                line=dict(color="#3b82f6", width=2)
            ),
            row=rows, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["macd_ema"],
                mode="lines",
                name="Signal",
                line=dict(color="#facc15", width=2)
            ),
            row=rows, col=1
        )

        fig.add_hline(y=0, line_dash="dot", line_color="gray", row=rows, col=1)