import pandas as pd

def companyData(ticker):
    info = ticker.info

    required_fields = [
        "longName",
        "sector",
        "marketCap",
        "trailingPE",
        "priceToBook",
        "totalRevenue",
        "netIncomeToCommon",
        "profitMargins",
        "beta",
        "fiftyTwoWeekRange",
        "currentPrice",
        "dayHigh",
        "dayLow",
        "fiftyDayAverage",
        "twoHundredDayAverage",
        "fiftyTwoWeekHigh",
        "fiftyTwoWeekLow",
        "52WeekChange",
        "averageVolume",
        "averageVolume10days",
        "volume",
        "dividendYield",
        "dividendRate",
    ]

    company_data = {field: info.get(field) for field in required_fields}

    return company_data

def format_number(value):
    if value is None:
        return "N/A"

    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000

    if value >= trillion:
        return f"{value / trillion:.2f} T"
    elif value >= billion:
        return f"{value / billion:.2f} B"
    elif value >= million:
        return f"{value / million:.2f} M"
    else:
        return f"{value:,.0f}"
