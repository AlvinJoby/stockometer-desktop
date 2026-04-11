from flask import Flask, jsonify, render_template, request
from validation import validateInput
from retrieveData import retrieve_data, retrieve_ltp, retrieve_companyInfo, normalize_columns, return_timeframePeriod
from graph import generate_graph
from yfinance.exceptions import YFRateLimitError
from analysis.rsi_indicator import calculate_rsi, mark_signals
from analysis.ma_indicator import calculate_sma, calculate_ema
from analysis.periodic_returns import periodic_returns
from analysis.company_data import companyData, format_number
from analysis.daily_returns import price_change, dailyReturns
from analysis.macd_indicator import calculate_macd
from analysis.buysell_marker import marking_bs
from analysis.breakout_engine.breakout import breakout_behavior
from stockIndex.getIndex import get_index, get_index_display_name
from stockIndex.indexPerformance import index_performance_pipeline
from symbol_search import search_symbols
import pandas as pd
from datetime import time
from zoneinfo import ZoneInfo

import config


app = Flask(__name__)

DEFAULT_VISIBLE_INDICATORS = ["RSI", "MACD"]
SELECTABLE_OVERLAY_INDICATORS = ["SMA_20", "SMA_50", "SMA_100", "EMA_20", "EMA_50", "EMA_100"]
ALL_CHART_INDICATORS = DEFAULT_VISIBLE_INDICATORS + SELECTABLE_OVERLAY_INDICATORS


def _format_decimal(value, digits=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.{digits}f}"


def _format_ratio_as_percent(value, digits=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def _resolve_dividend_yield(company):
    dy = company.get("dividendYield")
    dr = company.get("dividendRate")
    price = company.get("currentPrice")

    candidates = []

    if dy is not None and not pd.isna(dy):
        candidates.append(dy)

    if dr is not None and price is not None and price > 0:
        candidates.append(dr / price)

    cleaned = []

    for val in candidates:
        if val is None or pd.isna(val) or val < 0:
            continue
        if val > 10:
            continue
        if val > 1:
            val = val / 100
        if val > 0.1:
            continue
        cleaned.append(val)

    if not cleaned:
        return None

    return min(cleaned)


def _is_greater(left, right):
    if left is None or right is None or pd.isna(left) or pd.isna(right):
        return False
    return left > right


def _first_valid_value(*values):
    for value in values:
        if value is None:
            continue
        if pd.isna(value):
            continue
        return value
    return None


def _prepare_company(symbol, ticker):
    company = companyData(ticker)

    try:
        ticker_info = dict(getattr(ticker, "fast_info", {}) or {})
    except Exception:
        ticker_info = {}

    try:
        fast_info = dict(getattr(ticker, "fast_info", {}) or {})
    except Exception:
        fast_info = {}

    company["twoHundredDayAverage"] = _first_valid_value(
        company.get("twoHundredDayAverage"),
        ticker_info.get("twoHundredDayAverage"),
        fast_info.get("twoHundredDayAverage"),
    )
    company["fiftyTwoWeekChange"] = _first_valid_value(
        company.get("52WeekChange"),
        ticker_info.get("52WeekChange"),
        ticker_info.get("fiftyTwoWeekChange"),
        fast_info.get("yearChange"),
    )
    company["averageVolume"] = _first_valid_value(
        company.get("averageVolume"),
        ticker_info.get("averageVolume"),
        fast_info.get("threeMonthAverageVolume"),
    )
    company["averageVolume10days"] = _first_valid_value(
        company.get("averageVolume10days"),
        ticker_info.get("averageVolume10days"),
        ticker_info.get("averageDailyVolume10Day"),
        fast_info.get("tenDayAverageVolume"),
    )
    company["volume"] = _first_valid_value(
        company.get("volume"),
        ticker_info.get("volume"),
        ticker_info.get("regularMarketVolume"),
        fast_info.get("lastVolume"),
    )

    company["dividendYield"] = _resolve_dividend_yield(company)
    company["longName"] = company.get("longName") or symbol.upper()
    company["marketCap"] = format_number(company.get("marketCap"))
    company["totalRevenue"] = format_number(company.get("totalRevenue"))
    company["netIncomeToCommon"] = format_number(company.get("netIncomeToCommon"))
    company["profitMargins"] = _format_ratio_as_percent(company.get("profitMargins"))

    company["dayHighDisplay"] = _format_decimal(company.get("dayHigh"))
    company["dayLowDisplay"] = _format_decimal(company.get("dayLow"))
    company["fiftyDayAverageDisplay"] = _format_decimal(company.get("fiftyDayAverage"))
    company["twoHundredDayAverageDisplay"] = _format_decimal(company.get("twoHundredDayAverage"))
    company["fiftyTwoWeekHighDisplay"] = _format_decimal(company.get("fiftyTwoWeekHigh"))
    company["fiftyTwoWeekLowDisplay"] = _format_decimal(company.get("fiftyTwoWeekLow"))
    company["fiftyTwoWeekChangeDisplay"] = _format_ratio_as_percent(company.get("fiftyTwoWeekChange"))
    company["averageVolumeDisplay"] = format_number(company.get("averageVolume"))
    company["averageVolume10daysDisplay"] = format_number(company.get("averageVolume10days"))
    company["volumeDisplay"] = format_number(company.get("volume"))
    company["trailingPEDisplay"] = _format_decimal(company.get("trailingPE"))
    company["dividendYieldDisplay"] = _format_ratio_as_percent(company.get("dividendYield"))
    company["betaDisplay"] = _format_decimal(company.get("beta"), digits=3)
    company["priceToBookDisplay"] = _format_decimal(company.get("priceToBook"), digits=3)

    company["isAbove50DayAverage"] = _is_greater(
        company.get("currentPrice"), company.get("fiftyDayAverage"),
    )
    company["isAbove52WeekLow"] = _is_greater(
        company.get("currentPrice"), company.get("fiftyTwoWeekLow"),
    )
    company["hasLowPE"] = (
        company.get("trailingPE") is not None and
        not pd.isna(company.get("trailingPE")) and
        company["trailingPE"] < 25
    )
    company["hasDividend"] = (
        company.get("dividendYield") is not None and
        not pd.isna(company.get("dividendYield")) and
        company["dividendYield"] > 0
    )
    return company


def _clean_series(series):
    return [
        None if (v is None or pd.isna(v)) else round(float(v), 4)
        for v in series
    ]


def _sticky_symbol(symbol):
    cleaned = (symbol or "").strip().upper()
    return cleaned.split(".", 1)[0] or cleaned


def _sticky_display_name(short_name, symbol):
    base_name = (short_name or "").strip()
    if not base_name:
        base_name = _sticky_symbol(symbol)
    return base_name[:1].upper() + base_name[1:].lower() if base_name else ""


MARKET_HOURS = {
    "NSE": (ZoneInfo("Asia/Kolkata"), time(9, 15), time(15, 30)),
    "NSI": (ZoneInfo("Asia/Kolkata"), time(9, 15), time(15, 30)),
    "BSE": (ZoneInfo("Asia/Kolkata"), time(9, 15), time(15, 30)),
    "BOM": (ZoneInfo("Asia/Kolkata"), time(9, 15), time(15, 30)),
    "NMS": (ZoneInfo("America/New_York"), time(9, 30), time(16, 0)),
    "NYQ": (ZoneInfo("America/New_York"), time(9, 30), time(16, 0)),
    "ASE": (ZoneInfo("America/New_York"), time(9, 30), time(16, 0)),
    "PCX": (ZoneInfo("America/New_York"), time(9, 30), time(16, 0)),
    "LSE": (ZoneInfo("Europe/London"), time(8, 0), time(16, 30)),
    "HKG": (ZoneInfo("Asia/Hong_Kong"), time(9, 30), time(16, 0)),
    "TYO": (ZoneInfo("Asia/Tokyo"), time(9, 0), time(15, 0)),
}


def _market_status(exchange):
    normalized_exchange = (exchange or "").upper().strip()
    market_hours = MARKET_HOURS.get(normalized_exchange)
    if not market_hours:
        return {"is_open": False, "label": "MARKET'S NOT LIVE"}

    timezone, open_time, close_time = market_hours
    now_local = pd.Timestamp.now(tz=timezone)
    current_time = now_local.time()
    is_open = now_local.weekday() < 5 and open_time <= current_time <= close_time
    return {"is_open": is_open, "label": "MARKET IS OPEN" if is_open else "MARKET IS CLOSED"}


def _is_equity_symbol(ticker_info):
    quote_type = (ticker_info.get("quoteType") or "").strip().upper()
    if quote_type:
        return quote_type == "EQUITY"

    quote_type_alt = (ticker_info.get("typeDisp") or "").strip().upper()
    if quote_type_alt:
        return quote_type_alt == "EQUITY"

    return True


@app.route('/')
def home():
    return render_template(
        "index.html",
        error_message=None,
        symbol_value="",
    )


@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template("terms_and_conditions.html")


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("404.html"), 404


@app.route('/api/symbols')
def symbol_suggestions():
    query = request.args.get("q", "")
    return jsonify(search_symbols(query))


@app.route('/analyze', methods=['POST'])
def analyze():
    symbol = (request.form.get("symbol") or "").strip()
    validation_result = validateInput(symbol)

    if not validation_result["status"]:
        return render_template(
            "index.html",
            error_message=validation_result["error"],
            symbol_value=symbol,
        ), 400

    try:
        symbol = symbol.upper()

        # Create Ticker once — reused for both data fetch and company info
        ticker = retrieve_companyInfo(symbol)

        data = retrieve_data(symbol, ticker=ticker)
        if data is None or data.empty:
            return render_template(
                "index.html",
                error_message="We couldn't find that symbol. Try a different one and check again.",
                symbol_value=symbol,
            ), 200

        data = normalize_columns(data, symbol)

        last_traded_date = data.index[-1].strftime("%d %b %Y")

        config.symbol = symbol
        config.data = data

        LTP = retrieve_ltp(data)

        try:
            ticker_info = dict(getattr(ticker, "fast_info", {}) or {})
        except Exception:
            ticker_info = {}

        if not _is_equity_symbol(ticker_info):
            return render_template(
                "index.html",
                error_message="Right now we only support equities",
                symbol_value=symbol,
            ), 400

        company = _prepare_company(symbol, ticker)

        timeframe_period = return_timeframePeriod()

        price_change(data)
        dailyReturns(data)
        calculate_rsi(data)
        calculate_sma(data, 20, cname="sma_20_indicator")
        calculate_sma(data, 50, cname="sma_50_indicator")
        calculate_sma(data, 100, cname="sma_100_indicator")
        calculate_ema(data, 20)
        calculate_ema(data, 50)
        calculate_ema(data, 100)
        calculate_macd(data)
        marking_bs(data)
        mark_signals(data)

        periodicReturns = periodic_returns(data)
        breakout_data = breakout_behavior(data)

        index_summary = None
        index_ts = None

        exchange = ticker_info.get("exchange")
        market_status = _market_status(exchange)
        index = get_index(exchange, symbol)
        index_name = get_index_display_name(index)

        if index:
            # is_index=True gives it a 1-hour TTL and is shared across all
            # stocks that map to the same index (e.g. ^NSEI for all NSE stocks)
            index_df = retrieve_data(index, is_index=True)
            if index_df is not None and not index_df.empty:
                index_df = normalize_columns(index_df, index)
                result = index_performance_pipeline(data, index_df)
                df_ts = result.get("timeseries")
                if result.get("summary") is not None and df_ts is not None and not df_ts.empty:
                    index_summary = result["summary"]
                    index_ts = {
                        "dates": df_ts.index.strftime("%Y-%m-%d").tolist(),
                        "stock_normalized": _clean_series(df_ts["normalized_stock"]),
                        "index_normalized": _clean_series(df_ts["normalized_index"]),
                        "alpha_cumulative": _clean_series(df_ts["alpha_cumulative"]),
                        "alpha_rolling": _clean_series(df_ts["alpha_rolling"] * 100),
                        "relative_strength": _clean_series(df_ts["relative_strength"]),
                        "rs_ma": _clean_series(df_ts["rs_ma"]),
                    }

        graphPlot = generate_graph(
            data,
            indicators=ALL_CHART_INDICATORS,
            visible_indicators=DEFAULT_VISIBLE_INDICATORS,
        )

        return render_template(
            "main.html",
            graph=graphPlot,
            symbol_name=ticker_info.get("longName") or company["longName"],
            stock_name=ticker_info.get("shortName") or company["longName"],
            sticky_name=_sticky_display_name(ticker_info.get("shortName"), symbol),
            tLTP=LTP["tLTP"],
            percentChange=LTP["percentChange"],
            currency=ticker_info.get("currency", "USD"),
            market_status=market_status,
            company=company,
            periodicReturns=periodicReturns,
            breakout_data=breakout_data,
            summary=index_summary,
            index_ts=index_ts,
            index_name=index_name,
            last_traded_date=last_traded_date,
            timeframe_period=timeframe_period,
            selectable_overlay_indicators=SELECTABLE_OVERLAY_INDICATORS,
        )

    except YFRateLimitError:
        return render_template(
            "index.html",
            error_message="Too many requests. Please wait a few seconds and try again.",
            symbol_value=symbol,
        ), 429

    except ValueError as exc:
        app.logger.exception("Analysis failed for symbol %s", symbol)
        return str(exc), 500

    except Exception:
        app.logger.exception("Unexpected error while analyzing symbol %s", symbol)
        return "Unable to analyze the requested symbol right now.", 500

if __name__ == "__main__":
    app.run()