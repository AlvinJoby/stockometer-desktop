import pandas as pd

def marking_bs(data):
    prev_rsi = data['RSI'].iloc[-2]
    curr_rsi = data['RSI'].iloc[-1]

    rsi_cross_up = prev_rsi < 30 and curr_rsi > 30
    rsi_cross_down = prev_rsi > 70 and curr_rsi < 70

    uptrend = data['Close'].iloc[-1] > data['ema_20'].iloc[-1]
    downtrend = data['Close'].iloc[-1] < data['ema_20'].iloc[-1]

    buy_signal = rsi_cross_up and uptrend
    sell_signal = rsi_cross_down and downtrend

    data['signal'] = 0
    data['signal_reason'] = "No clear signal"

    if buy_signal:
        data.loc[data.index[-1],'signal'] = 1
        data.loc[data.index[-1],'signal_reason'] = "RSI oversold bounce in uptrend"

    elif sell_signal:
        data.loc[data.index[-1],'signal'] = -1
        data.loc[data.index[-1],'signal_reason'] = "RSI overbought drop in downtrend"

    return data
