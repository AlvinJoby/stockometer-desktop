import unittest
import pandas as pd

from graph import _compute_price_axis_range, _select_initial_start_date, generate_graph

from tests.test_app import make_price_frame


class GraphTests(unittest.TestCase):
    def test_select_initial_start_date_keeps_default_for_normal_chart(self):
        frame = make_price_frame()
        frame["High"] = 150
        frame["Low"] = 100

        start_date = _select_initial_start_date(frame)

        self.assertEqual(start_date, frame.index[-1] - pd.DateOffset(months=6))

    def test_select_initial_start_date_zooms_to_three_months_for_compressed_chart(self):
        frame = make_price_frame()
        frame.loc[:, "High"] = [140 + i for i in range(len(frame))]
        frame.loc[:, "Low"] = [100 + i for i in range(len(frame))]
        frame.loc[frame.index[-45]:, "High"] = 262
        frame.loc[frame.index[-45]:, "Low"] = 248

        start_date = _select_initial_start_date(frame)

        self.assertEqual(start_date, frame.index[-1] - pd.DateOffset(months=3))

    def test_compute_price_axis_range_preserves_normal_chart_range(self):
        frame = make_price_frame()
        frame["High"] = 150
        frame["Low"] = 100
        frame.loc[frame.index[-30]:, "High"] = 152
        frame.loc[frame.index[-30]:, "Low"] = 98
        visible_data = frame[frame.index >= frame.index[-1] - pd.DateOffset(months=6)]

        axis_range = _compute_price_axis_range(visible_data)

        expected_min = float(visible_data["Low"].min())
        expected_max = float(visible_data["High"].max())
        expected_padding = (expected_max - expected_min) * 0.1

        self.assertEqual(
            axis_range,
            [expected_min - expected_padding, expected_max + expected_padding],
        )

    def test_compute_price_axis_range_zooms_to_recent_trading_band(self):
        frame = make_price_frame()
        frame.loc[:, "High"] = [140 + i for i in range(len(frame))]
        frame.loc[:, "Low"] = [100 + i for i in range(len(frame))]
        frame.loc[frame.index[-45]:, "High"] = 262
        frame.loc[frame.index[-45]:, "Low"] = 248
        frame.loc[frame.index[-45]:, "Close"] = 255

        visible_data = frame[frame.index >= frame.index[-1] - pd.DateOffset(months=6)]
        axis_range = _compute_price_axis_range(visible_data)

        self.assertLess(axis_range[0], 248)
        self.assertGreater(axis_range[1], 262)
        self.assertLess(axis_range[1] - axis_range[0], 40)

    def test_compute_price_axis_range_ignores_extreme_outlier_spike(self):
        frame = make_price_frame()
        frame.loc[frame.index[30], "High"] = 800.0
        frame.loc[frame.index[30], "Low"] = 790.0

        visible_data = frame[frame.index >= frame.index[-1] - pd.DateOffset(months=6)]
        axis_range = _compute_price_axis_range(visible_data)

        self.assertLess(axis_range[1], 300.0)
        self.assertGreater(axis_range[1], float(visible_data["Close"].iloc[-1]))

    def test_compute_price_axis_range_tightens_for_moderate_outlier_cluster(self):
        frame = make_price_frame()
        frame.loc[frame.index[25:29], "High"] = [320, 330, 325, 318]
        frame.loc[frame.index[25:29], "Low"] = [300, 305, 302, 299]

        visible_data = frame[frame.index >= frame.index[-1] - pd.DateOffset(months=6)]
        axis_range = _compute_price_axis_range(visible_data)

        full_max = float(visible_data["High"].max())

        self.assertLess(axis_range[1], full_max)
        self.assertGreater(axis_range[1], float(visible_data["Close"].iloc[-1]))

    def test_generate_graph_returns_html_for_supported_indicators(self):
        graph_html = generate_graph(
            make_price_frame(),
            ["RSI", "SMA_20", "EMA_20", "EMA_50", "EMA_100", "MACD"],
        )

        self.assertIn("plotly", graph_html.lower())
        self.assertIn("Open:", graph_html)
        self.assertNotIn("BUY", graph_html)
        self.assertNotIn("SELL", graph_html)


if __name__ == "__main__":
    unittest.main()
