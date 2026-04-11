import pandas as pd
import config



def calculate_rsi(data):

    period = 14

    #gain=max(priceChange,0)
    #loss=max(-priceChange,0)

    data['gain'] = data["priceChange"].clip(lower=0)
    data['loss'] = (data["priceChange"].clip(upper=0)).abs()

    #calculating normal 14day avg of g/l

    data['avg_gain'] = (data['gain'].rolling(window=period)).mean()
    data['avg_loss'] = (data['loss'].rolling(window=period)).mean()

    # Wilder's formula
    
    for i in range(period+1,len(data)):

        data.loc[data.index[i], 'avg_gain'] = (data.loc[data.index[i-1], 'avg_gain'] *
                                               (period-1) + data['gain'].iloc[i])/period
    
        data.loc[data.index[i], 'avg_loss'] = (data.loc[data.index[i-1], 'avg_loss'] *
                                               (period-1) + data['loss'].iloc[i])/period
        
    #Relative Strength (RS)

    data['RS'] = data['avg_gain']/data['avg_loss']

    #RSI

    data['RSI'] = 100-(100/(1+data['RS']))


def mark_signals(data):

    data["buy_RSI"] = None
    data["sell_RSI"] = None

    for i in range(1, len(data)):

        prev_rsi = data.iloc[i-1]["RSI"]
        curr_rsi = data.iloc[i]["RSI"]

        if prev_rsi < 30 and curr_rsi > 30:
            data.loc[data.index[i], "buy_RSI"] = data.iloc[i]["Close"]

        elif prev_rsi > 70 and curr_rsi < 70:
            data.loc[data.index[i], "sell_RSI"] = data.iloc[i]["Close"]

    return data