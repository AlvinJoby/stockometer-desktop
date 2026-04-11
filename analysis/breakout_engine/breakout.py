import pandas as pd


LOOKBACK = 20
ATR_WINDOW = 14
HOLDING_DAYS = 10
MIN_GAP = 7
MIN_BUFFER_PCT = 0.003
ATR_BREAKOUT_MULTIPLIER = 0.35
VOLUME_CONFIRMATION_RATIO = 1.1
SUCCESS_ATR_MULTIPLIER = 1.0
FAILURE_ATR_MULTIPLIER = 0.75
MAX_HISTORY = 1900 


def _prepare_frame(df):
    required = ["Open", "High", "Low", "Close", "Volume"]
    clean = df.copy()
    for column in required:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")

    clean = clean.dropna(subset=required)
    if clean.empty:
        return clean

    prev_close = clean["Close"].shift(1)
    true_range = pd.concat(
        [
            clean["High"] - clean["Low"],
            (clean["High"] - prev_close).abs(),
            (clean["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    clean["atr"] = true_range.rolling(ATR_WINDOW).mean()
    clean["prior_high"] = clean["High"].shift(1).rolling(LOOKBACK).max()
    clean["prior_low"] = clean["Low"].shift(1).rolling(LOOKBACK).min()
    clean["avg_volume"] = clean["Volume"].shift(1).rolling(LOOKBACK).mean()
    return clean


def _event_confidence(close, level, atr, volume, avg_volume):
    breakout_distance = 0 if pd.isna(atr) or atr <= 0 else max(close - level, 0) / atr
    volume_ratio = 1 if pd.isna(avg_volume) or avg_volume <= 0 else volume / avg_volume
    confidence = (0.7 * breakout_distance) + (0.3 * max(volume_ratio - 1, 0))
    return round(min(max(confidence, 0), 3), 2)


def breakout_engine(df, lookback=LOOKBACK):
    if len(df) < max(lookback + 1, ATR_WINDOW + 1):
        return {"signal": "range", "level": None, "confidence": 0}

    enriched = _prepare_frame(df.tail(max(lookback + ATR_WINDOW + 5, 40)))
    row = enriched.iloc[-1]

    if pd.isna(row["prior_high"]) or pd.isna(row["prior_low"]):
        return {"signal": "range", "level": None, "confidence": 0}

    atr = row["atr"]
    close = row["Close"]
    volume = row["Volume"]
    avg_volume = row["avg_volume"]
    prior_high = row["prior_high"]
    prior_low = row["prior_low"]

    atr_value = 0 if pd.isna(atr) else float(atr)
    breakout_buffer = max(prior_high * MIN_BUFFER_PCT, atr_value * ATR_BREAKOUT_MULTIPLIER)
    breakdown_buffer = max(prior_low * MIN_BUFFER_PCT, atr_value * ATR_BREAKOUT_MULTIPLIER)
    has_volume_support = pd.isna(avg_volume) or avg_volume <= 0 or volume >= avg_volume * VOLUME_CONFIRMATION_RATIO

    if close > prior_high + breakout_buffer and has_volume_support:
        return {
            "signal": "breakout",
            "level": round(prior_high, 2),
            "confidence": _event_confidence(close, prior_high, atr, volume, avg_volume),
        }

    if close < prior_low - breakdown_buffer and has_volume_support:
        return {
            "signal": "breakdown",
            "level": round(prior_low, 2),
            "confidence": _event_confidence(prior_low, close, atr, volume, avg_volume),
        }

    return {"signal": "range", "level": None, "confidence": 0}


def get_breakout_events(df, lookback=LOOKBACK):
    events = []
    prepared = _prepare_frame(df)

    start_index = max(lookback + 1, ATR_WINDOW + 1)
    end_index = len(prepared) - HOLDING_DAYS
    for i in range(start_index, end_index):
        row = prepared.iloc[i]
        if pd.isna(row["prior_high"]) or pd.isna(row["prior_low"]) or pd.isna(row["atr"]):
            continue

        sub_df = prepared.iloc[: i + 1]
        result = breakout_engine(sub_df, lookback)
        if result["signal"] in ["breakout", "breakdown"]:
            events.append(
                {
                    "index": i,
                    "type": result["signal"],
                    "level": result["level"],
                    "price": float(row["Close"]),
                    "atr": float(row["atr"]),
                    "confidence": result["confidence"],
                }
            )

    return events


def filter_duplicate_events(events, min_gap=MIN_GAP):
    filtered = []
    last_index = -10_000
    last_type = None

    for event in events:
        is_far_enough = event["index"] - last_index >= min_gap
        switched_direction = event["type"] != last_type
        if is_far_enough or switched_direction:
            filtered.append(event)
            last_index = event["index"]
            last_type = event["type"]

    return filtered


def evaluate_events(events, df, holding_days=HOLDING_DAYS):
    for event in events:
        idx = event["index"]
        entry = event["price"]
        exit_price = float(df["Close"].iloc[idx + holding_days])
        raw_move = (exit_price - entry) / entry
        directional_move = raw_move if event["type"] == "breakout" else -raw_move
        event["return"] = directional_move

    return events


def classify_events(events):
    for event in events:
        atr = event.get("atr", 0)
        price = event.get("price", 0)
        move = event.get("return", 0)

        if not atr or not price:
            event["outcome"] = "neutral"
            continue

        atr_pct = atr / price
        success_th = SUCCESS_ATR_MULTIPLIER * atr_pct
        failure_th = -FAILURE_ATR_MULTIPLIER * atr_pct

        if move >= success_th:
            event["outcome"] = "success"
        elif move <= failure_th:
            event["outcome"] = "failure"
        else:
            event["outcome"] = "neutral"

    return events


def summarize(events):
    total = len(events)
    if total == 0:
        return {
            "total": 0,
            "success_rate": 0,
            "failure_rate": 0,
            "median_return": 0,
            "avg_confidence": 0,
            "confidence_level": "Low Confidence",
            "confidence_note": "limited sample size",
            "low_confidence": True,
        }

    success_count = sum(1 for event in events if event["outcome"] == "success")
    failure_count = sum(1 for event in events if event["outcome"] == "failure")
    returns = [event["return"] for event in events]
    median_return = pd.Series(returns).median()
    avg_confidence = sum(event.get("confidence", 0) for event in events) / total
    if total < 20:
        confidence_level = "Low Confidence"
        confidence_note = "limited sample size"
        low_confidence = True
    elif total < 50:
        confidence_level = "Moderate Confidence"
        confidence_note = "sample size is improving"
        low_confidence = False
    else:
        confidence_level = "High Confidence"
        confidence_note = "ample sample size"
        low_confidence = False

    return {
        "total": total,
        "success_rate": round(success_count / total, 2),
        "failure_rate": round(failure_count / total, 2),
        "median_return": round(float(median_return), 4),
        "avg_confidence": round(avg_confidence, 2),
        "confidence_level": confidence_level,
        "confidence_note": confidence_note,
        "low_confidence": low_confidence,
    }


def recent_events(events, df, n=10):
    latest = events[-n:]
    output = []

    for event in latest:
        date = str(df.index[event["index"]].date())
        output.append(
            {
                "date": date,
                "type": event["type"],
                "return": round(event["return"] * 100, 2),
                "outcome": event["outcome"],
                "confidence": round(event.get("confidence", 0), 2),
            }
        )

    return output


def breakout_behavior(df):
    clean = _prepare_frame(df.tail(MAX_HISTORY))
    if clean.empty or len(clean) < max(LOOKBACK + HOLDING_DAYS + 5, 60):
        return {"summary": {"note": "Low data"}, "recent": []}

    events = get_breakout_events(clean)
    events = filter_duplicate_events(events)
    events = evaluate_events(events, clean)
    events = classify_events(events)

    if not events:
        return {"summary": {"note": "Low data"}, "recent": []}

    return {
        "summary": summarize(events),
        "recent": recent_events(events, clean),
    }
