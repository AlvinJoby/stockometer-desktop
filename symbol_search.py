from difflib import SequenceMatcher

import requests
from yfinance import Search


ALLOWED_QUOTE_TYPES = {"EQUITY"}
STOCK_SCREENERS = (
    "most_actives",
    "day_gainers",
    "aggressive_small_caps",
    "undervalued_growth_stocks",
)


def normalize_quote(quote, allowed_types=None):
    symbol = (quote.get("symbol") or "").strip()
    if not symbol:
        return None

    quote_type = (quote.get("quoteType") or "").strip().upper()
    if allowed_types and quote_type not in allowed_types:
        return None

    name = (
        (quote.get("shortname") or "").strip() or
        (quote.get("longname") or "").strip() or
        symbol
    )

    return {
        "symbol": symbol,
        "name": name,
        "exchange": (quote.get("exchange") or "").strip(),
        "type": quote_type,
    }


def score_symbol_match(query, item):
    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return 0

    symbol = item["symbol"].lower()
    name = " ".join(item["name"].lower().split())

    score = 0

    if symbol == normalized_query:
        score += 200
    elif symbol.startswith(normalized_query):
        score += 140
    elif normalized_query in symbol:
        score += 90

    if name == normalized_query:
        score += 220
    elif name.startswith(normalized_query):
        score += 170
    elif normalized_query in name:
        score += 120

    tokens = name.replace(".", " ").replace(",", " ").split()
    if any(token.startswith(normalized_query) for token in tokens):
        score += 80

    score += int(SequenceMatcher(None, normalized_query, symbol).ratio() * 70)
    score += int(SequenceMatcher(None, normalized_query, name).ratio() * 100)

    return score


def search_symbols(query, max_results=8, allowed_types=None):
    normalized_query = (query or "").strip()
    if len(normalized_query) < 2:
        return []

    allowed_types = allowed_types or ALLOWED_QUOTE_TYPES

    try:
        results = Search(
            query=normalized_query,
            max_results=max(max_results * 3, 20),
            news_count=0,
            lists_count=0,
            include_cb=False,
            include_nav_links=False,
            include_research=False,
            include_cultural_assets=False,
            enable_fuzzy_query=True,
            recommended=0,
            raise_errors=True,
        )
    except Exception:
        return []

    symbols = []
    seen = set()

    for quote in getattr(results, "quotes", []) or []:
        normalized = normalize_quote(quote, allowed_types=allowed_types)
        if not normalized:
            continue
        symbol = normalized["symbol"]
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(normalized)

    symbols.sort(
        key=lambda item: (
            score_symbol_match(normalized_query, item),
            item["name"].lower(),
            item["symbol"],
        ),
        reverse=True,
    )

    return symbols[:max_results]


def trending_symbols(limit=10):
    seen = set()
    symbols = []
    session = requests.Session()
    session.trust_env = False
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }

    for screener_id in STOCK_SCREENERS:
        if len(symbols) >= limit:
            break
        try:
            response = session.get(
                (
                    "https://query1.finance.yahoo.com/v1/finance/screener/"
                    f"predefined/saved?count={max(limit, 12)}&scrIds={screener_id}"
                ),
                timeout=4,
                headers=headers,
            )
            if response.status_code != 200:
                continue
            payload = response.json() or {}
        except Exception:
            continue

        screener_results = (((payload.get("finance") or {}).get("result")) or [])
        if not screener_results:
            continue

        quotes = screener_results[0].get("quotes") or []
        for quote in quotes:
            symbol = (quote.get("symbol") or "").strip()
            quote_type = (quote.get("quoteType") or "").strip().upper()
            if not symbol or symbol in seen or quote_type != "EQUITY":
                continue
            seen.add(symbol)
            symbols.append({
                "symbol": symbol,
                "name": (quote.get("shortName") or quote.get("longName") or symbol).strip(),
            })
            if len(symbols) >= limit:
                break

    if not symbols:
        return [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com, Inc."},
            {"symbol": "META", "name": "Meta Platforms, Inc."},
            {"symbol": "TSLA", "name": "Tesla, Inc."},
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries Limited"},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services Limited"},
            {"symbol": "7203.T", "name": "Toyota Motor Corporation"},
        ][:limit]

    return symbols[:limit]
