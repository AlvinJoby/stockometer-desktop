import pandas as pd

def price_change(data):
    data["priceChange"] = data["Close"].diff()

def dailyReturns(data):
    data["dailyReturns"] = data["Close"].pct_change()*100

def daily_change(data,column):
    
    data["dailyReturns"] = data[column].pct_change()*100


