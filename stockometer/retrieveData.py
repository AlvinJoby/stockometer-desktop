import yfinance as yf
import pandas as pd
import time
import random
from yfinance.exceptions import YFRateLimitError

timeframe_period = "8y"

_cache = {}

CACHE_TTL = {
    "stock": 60 * 15,
    "index": 60 * 60,
}


def _get_cached(key):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < entry["ttl"]:
        return entry["data"]
    return None


def _set_cached(key, data, ttl):
    _cache[key] = {"data": data.copy(), "ts": time.time(), "ttl": ttl}


def _fetch_with_retry(fn, retries=3):
    for attempt in range(retries):
        try:
            return fn()
        except YFRateLimitError:
            if attempt == retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 0.5)
            print(f"[RATE LIMIT] Retrying in {wait:.1f}s (attempt {attempt + 1}/{retries})")
            time.sleep(wait)


def retrieve_data(symbol, ticker=None, is_index=False):
    cached = _get_cached(symbol)
    if cached is not None:
        print(f"[CACHE HIT] {symbol}")
        return cached

    try:
        t = ticker or yf.Ticker(symbol)

        data = _fetch_with_retry(
            lambda: t.history(period=timeframe_period, interval="1d", auto_adjust=True)
        )

        if data is None or data.empty:
            raise ValueError(f"No data fetched for symbol: {symbol}")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col) for col in data.columns]

        data = normalize_columns(data, symbol)

        ohlc_cols = [c for c in ["Open", "High", "Low", "Close"] if c in data.columns]
        if ohlc_cols:
            data = data.dropna(subset=ohlc_cols, how="all")

        if data.empty:
            raise ValueError(f"No valid data after cleaning for symbol: {symbol}")

        ttl = CACHE_TTL["index"] if is_index else CACHE_TTL["stock"]
        _set_cached(symbol, data, ttl)

        print(f"[CACHE SET] {symbol} (ttl={ttl}s)")
        return data

    except YFRateLimitError:
        raise

    except Exception as e:
        print(f"[ERROR] Data fetch failed for {symbol}: {e}")
        return pd.DataFrame()


def retrieve_ltp(data):
    price_col = "Close"

    if data is None or data.empty:
        raise ValueError("Data is empty")

    if price_col not in data.columns:
        raise ValueError(f"{price_col} not found in data")

    if len(data) < 2:
        raise ValueError("Not enough data to calculate LTP change")

    price_series = data[price_col]

    tLTP = price_series.iloc[-1]
    yLTP = price_series.iloc[-2]

    if yLTP == 0:
        percentChange = 0
    else:
        percentChange = ((tLTP - yLTP) / yLTP) * 100

    return {
        "tLTP": tLTP,
        "yLTP": yLTP,
        "percentChange": percentChange
    }


def retrieve_companyInfo(symbol):
    return yf.Ticker(symbol)


def normalize_columns(data, symbol):
    rename_map = {}
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        suffixed = f"{col}_{symbol}"
        if suffixed in data.columns:
            rename_map[suffixed] = col
    return data.rename(columns=rename_map)


def return_timeframePeriod():
    return timeframe_period