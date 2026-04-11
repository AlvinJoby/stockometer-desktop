import pandas as pd
from analysis.ma_indicator import calculate_ema,custom_ema

def calculate_macd(data):
    calculate_ema(data,12)
    calculate_ema(data,26)

    data['macd_indicator'] = data['ema_12'] - data['ema_26']

    custom_ema(data,9,'macd_indicator','macd_ema')

    data['macd_histogram'] = data['macd_indicator'] - data['macd_ema']

    return data


