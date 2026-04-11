import pandas as pd

def periodic_returns(data):
    adj_close =  data['Close']
    periods = {
        "1D": 1,
        "1W": 5,
        "1M": 21,
        "6M": 126
    }
    returns = {}
    for label,period in periods.items():
        return_series = adj_close.pct_change(period)*100
        value = return_series.iloc[-1]
        returns[label] = value
    return returns
       