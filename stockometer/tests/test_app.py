import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

import app as stock_app


def make_price_frame():
    dates = pd.date_range("2026-01-01", periods=140, freq="D", name="Date")
    frame = pd.DataFrame(
        {
            "Open": [100 + i for i in range(140)],
            "High": [101 + i for i in range(140)],
            "Low": [99 + i for i in range(140)],
            "Close": [100.5 + i for i in range(140)],
            "Volume": [1_000_000 + i for i in range(140)],
            "Volume_TEST": [1_000_000 + i for i in range(140)],
        },
        index=dates,
    )
    frame["priceChange"] = frame["Close"].diff().fillna(0)
    frame["dailyReturns"] = frame["Close"].pct_change().fillna(0) * 100
    frame["RSI"] = 50.0
    frame["buy_RSI"] = None
    frame["sell_RSI"] = None
    frame["sma_indicator"] = frame["Close"].rolling(20).mean().bfill()
    frame["ema_20"] = frame["Close"]
    frame["ema_50"] = frame["Close"]
    frame["ema_100"] = frame["Close"]
    frame["macd_indicator"] = 1.0
    frame["macd_ema"] = 0.5
    frame["macd_histogram"] = 0.5
    return frame


class AnalyzeRouteTests(unittest.TestCase):
    def setUp(self):
        stock_app.app.config["TESTING"] = True
        self.client = stock_app.app.test_client()

    def test_missing_symbol_returns_400(self):
        response = self.client.post("/analyze", data={})

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"symbol is required", response.data)
        self.assertIn(b"Enter stock symbol", response.data)

    @patch("app.retrieve_data")
    def test_price_history_failure_renders_index_with_invalid_symbol_message(self, mock_retrieve_data):
        mock_retrieve_data.return_value = pd.DataFrame()

        response = self.client.post("/analyze", data={"symbol": "AAPL"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"We couldn&#39;t find that symbol", response.data)
        self.assertIn(b'value="AAPL"', response.data)

    @patch("app.generate_graph")
    @patch("app.index_performance_pipeline")
    @patch("app.mark_signals")
    @patch("app.marking_bs")
    @patch("app.calculate_macd")
    @patch("app.calculate_ema")
    @patch("app.calculate_sma")
    @patch("app.calculate_rsi")
    @patch("app.dailyReturns")
    @patch("app.price_change")
    @patch("app.periodic_returns")
    @patch("app.companyData")
    @patch("app.retrieve_companyInfo")
    @patch("app.retrieve_ltp")
    @patch("app.normalize_columns")
    @patch("app.retrieve_data")
    def test_successful_analyze_renders_page(
        self,
        mock_retrieve_data,
        mock_normalize_columns,
        mock_retrieve_ltp,
        mock_retrieve_company_info,
        mock_company_data,
        mock_periodic_returns,
        _mock_price_change,
        _mock_daily_returns,
        _mock_calculate_rsi,
        _mock_calculate_sma,
        _mock_calculate_ema,
        _mock_calculate_macd,
        _mock_marking_bs,
        _mock_mark_signals,
        mock_index_performance_pipeline,
        mock_generate_graph,
    ):
        stock_frame = make_price_frame()
        index_frame = make_price_frame()
        mock_retrieve_data.side_effect = [stock_frame.copy(), index_frame.copy()]
        mock_normalize_columns.side_effect = lambda data, _symbol: data
        mock_retrieve_ltp.return_value = {"tLTP": 123.45, "percentChange": 1.23}
        mock_retrieve_company_info.return_value = SimpleNamespace(
            info={"exchange": "NMS", "currency": "USD", "longName": "Mock Company"}
        )
        mock_company_data.return_value = {
            "longName": "Mock Company",
            "sector": "Tech",
            "marketCap": 1_000_000_000,
            "trailingPE": 18.25,
            "priceToBook": 4.321,
            "totalRevenue": 2_000_000_000,
            "netIncomeToCommon": 500_000_000,
            "profitMargins": 0.25,
            "beta": 1.111,
            "fiftyTwoWeekRange": "80-140",
            "currentPrice": 123.45,
            "dayHigh": 125.0,
            "dayLow": 120.0,
            "fiftyDayAverage": 110.0,
            "fiftyTwoWeekHigh": 140.0,
            "fiftyTwoWeekLow": 80.0,
            "dividendYield": 0.01,
        }
        mock_periodic_returns.return_value = {"1D": 1.0, "1W": 2.0, "1M": 3.0, "6M": 4.0}
        mock_index_performance_pipeline.return_value = {"summary": {"alpha": 2.5}}
        mock_generate_graph.return_value = "<div>chart</div>"

        response = self.client.post("/analyze", data={"symbol": "AAPL"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mock Company", response.data)
        self.assertIn(b"chart", response.data)
        self.assertIn(b"MARKET", response.data)

    @patch("app.generate_graph", side_effect=ValueError("Chart configuration failed"))
    @patch("app.periodic_returns", return_value={"1D": 1.0, "1W": 2.0, "1M": 3.0, "6M": 4.0})
    @patch("app.companyData")
    @patch("app.retrieve_companyInfo")
    @patch("app.retrieve_ltp", return_value={"tLTP": 123.45, "percentChange": 1.23})
    @patch("app.normalize_columns", side_effect=lambda data, _symbol: data)
    @patch("app.retrieve_data")
    def test_chart_generation_failures_return_500(
        self,
        mock_retrieve_data,
        _mock_normalize_columns,
        _mock_retrieve_ltp,
        mock_retrieve_company_info,
        mock_company_data,
        _mock_periodic_returns,
        _mock_generate_graph,
    ):
        stock_frame = make_price_frame()
        mock_retrieve_data.return_value = stock_frame
        mock_retrieve_company_info.return_value = SimpleNamespace(
            info={"exchange": None, "currency": "USD", "longName": "Mock Company"}
        )
        mock_company_data.return_value = {
            "longName": "Mock Company",
            "sector": "Tech",
            "marketCap": None,
            "trailingPE": None,
            "priceToBook": None,
            "totalRevenue": None,
            "netIncomeToCommon": None,
            "profitMargins": None,
            "beta": None,
            "fiftyTwoWeekRange": None,
            "currentPrice": None,
            "dayHigh": None,
            "dayLow": None,
            "fiftyDayAverage": None,
            "fiftyTwoWeekHigh": None,
            "fiftyTwoWeekLow": None,
            "dividendYield": None,
        }

        response = self.client.post("/analyze", data={"symbol": "AAPL"})

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Chart configuration failed", response.data)

    @patch("app.generate_graph", return_value="<div>chart</div>")
    @patch("app.periodic_returns", return_value={"1D": 1.0, "1W": 2.0, "1M": 3.0, "6M": 4.0})
    @patch("app.companyData")
    @patch("app.retrieve_companyInfo")
    @patch("app.retrieve_ltp", return_value={"tLTP": 123.45, "percentChange": 1.23})
    @patch("app.normalize_columns", side_effect=lambda data, _symbol: data)
    @patch("app.retrieve_data")
    def test_missing_company_fields_render_as_na(
        self,
        mock_retrieve_data,
        _mock_normalize_columns,
        _mock_retrieve_ltp,
        mock_retrieve_company_info,
        mock_company_data,
        _mock_periodic_returns,
        _mock_generate_graph,
    ):
        stock_frame = make_price_frame()
        mock_retrieve_data.return_value = stock_frame
        mock_retrieve_company_info.return_value = SimpleNamespace(
            info={"exchange": None, "currency": "USD", "longName": None}
        )
        mock_company_data.return_value = {
            "longName": None,
            "sector": None,
            "marketCap": None,
            "trailingPE": None,
            "priceToBook": None,
            "totalRevenue": None,
            "netIncomeToCommon": None,
            "profitMargins": None,
            "beta": None,
            "fiftyTwoWeekRange": None,
            "currentPrice": None,
            "dayHigh": None,
            "dayLow": None,
            "fiftyDayAverage": None,
            "fiftyTwoWeekHigh": None,
            "fiftyTwoWeekLow": None,
            "dividendYield": None,
        }

        response = self.client.post("/analyze", data={"symbol": "AAPL"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AAPL", response.data)
        self.assertIn(b"N/A", response.data)


class SymbolSuggestionRouteTests(unittest.TestCase):
    def setUp(self):
        stock_app.app.config["TESTING"] = True
        self.client = stock_app.app.test_client()

    @patch("app.search_symbols", return_value=[])
    def test_symbol_suggestions_empty_query_returns_empty_array(self, mock_search_symbols):
        response = self.client.get("/api/symbols")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])
        mock_search_symbols.assert_called_once_with("")

    @patch("app.search_symbols")
    def test_symbol_suggestions_return_json(self, mock_search_symbols):
        mock_search_symbols.return_value = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NMS",
                "type": "EQUITY",
            }
        ]

        response = self.client.get("/api/symbols?q=app")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "exchange": "NMS",
                    "type": "EQUITY",
                }
            ],
        )
        mock_search_symbols.assert_called_once_with("app")


class DividendYieldNormalizationTests(unittest.TestCase):
    def test_prepare_company_uses_dividend_rate_fallback(self):
        ticker = SimpleNamespace(
            info={
                "longName": "Mock Company",
                "sector": "Tech",
                "marketCap": 1_000_000_000,
                "trailingPE": 18.25,
                "priceToBook": 4.321,
                "totalRevenue": 2_000_000_000,
                "netIncomeToCommon": 500_000_000,
                "profitMargins": 0.25,
                "beta": 1.111,
                "fiftyTwoWeekRange": "80-140",
                "currentPrice": 100.0,
                "dayHigh": 125.0,
                "dayLow": 120.0,
                "fiftyDayAverage": 110.0,
                "fiftyTwoWeekHigh": 140.0,
                "fiftyTwoWeekLow": 80.0,
                "dividendYield": None,
                "dividendRate": 2.5,
            }
        )

        company = stock_app._prepare_company("AAPL", ticker)

        self.assertAlmostEqual(company["dividendYield"], 0.025)
        self.assertEqual(company["dividendYieldDisplay"], "2.50%")
        self.assertTrue(company["hasDividend"])

    def test_prepare_company_normalizes_whole_percent_dividend_yield(self):
        ticker = SimpleNamespace(
            info={
                "longName": "Mock Company",
                "sector": "Tech",
                "marketCap": 1_000_000_000,
                "trailingPE": 18.25,
                "priceToBook": 4.321,
                "totalRevenue": 2_000_000_000,
                "netIncomeToCommon": 500_000_000,
                "profitMargins": 0.25,
                "beta": 1.111,
                "fiftyTwoWeekRange": "80-140",
                "currentPrice": 100.0,
                "dayHigh": 125.0,
                "dayLow": 120.0,
                "fiftyDayAverage": 110.0,
                "fiftyTwoWeekHigh": 140.0,
                "fiftyTwoWeekLow": 80.0,
                "dividendYield": 2.5,
                "dividendRate": None,
            }
        )

        company = stock_app._prepare_company("AAPL", ticker)

        self.assertAlmostEqual(company["dividendYield"], 0.025)
        self.assertEqual(company["dividendYieldDisplay"], "2.50%")


if __name__ == "__main__":
    unittest.main()
