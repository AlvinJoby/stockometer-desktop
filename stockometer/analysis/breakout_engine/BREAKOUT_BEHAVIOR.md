# Breakout Behavior

This module is a lightweight historical study of how a stock behaved after prior breakout and breakdown signals.

## Broad idea

The goal is not to predict the future with certainty. It answers a narrower question:

"When this stock has broken above resistance or below support in the recent past, did that move usually continue or fail?"

## How signals are found

For each day in the lookback sample, the engine checks:

1. The prior 20-session high and low, excluding the current bar.
2. The 14-session ATR, which acts as a volatility filter.
3. The average volume over the prior 20 sessions.

A signal is only counted when price moves beyond the prior range by more than:

- a small fixed percentage buffer, and
- an ATR-based volatility buffer

This reduces false signals caused by tiny moves above resistance or below support.

Volume must also be above the recent average by a modest amount. That keeps the model closer to "real" breakouts instead of random drift.

## How outcomes are judged

After a signal appears, the engine looks forward 10 trading sessions.

- For a breakout, positive follow-through is good.
- For a breakdown, negative follow-through is good, so returns are direction-adjusted.

The move is then compared with ATR at the signal date:

- `success`: follow-through was at least about 1 ATR in the expected direction
- `failure`: price moved at least about 0.75 ATR against the signal
- `neutral`: anything in between

This makes the result relative to the stock's own volatility rather than using one fixed percentage for every stock.

## What the summary means

- `total`: number of valid historical signals found
- `success_rate`: share of signals that followed through
- `failure_rate`: share of signals that failed
- `avg_return`: average direction-adjusted return after the holding window
- `avg_confidence`: average trigger quality score based on breakout distance and volume expansion

## Important limitations

- This is a historical behavior study, not a trading system.
- It does not model slippage, gaps, position sizing, or risk management.
- It uses daily candles only.
- Thinly traded symbols or symbols with very short history may not produce meaningful output.

## Practical interpretation

Use this section as a context tool:

- high success rate + positive average return: breakouts have historically had decent follow-through
- mixed success rate + near-zero average return: signals have been noisy
- high failure rate or negative average return: breakout-style signals have not been reliable recently
