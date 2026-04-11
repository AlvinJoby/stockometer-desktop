import plotly.graph_objects as go

def add_rsi(fig,data,rows):
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["RSI"],
                mode="lines",
                name="RSI",
                line=dict(color="#3b82f6", width=3)
            ),
            row=rows, col=1
        )

        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=rows, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=rows, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=rows, col=1)

        fig.update_yaxes(range=[0, 100], row=rows, col=1)
