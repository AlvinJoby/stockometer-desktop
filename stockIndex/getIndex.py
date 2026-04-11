EXCHANGE_TO_INDEX = {
    # 🇮🇳 India
    "NSE": "NIFTYBEES.NS",
    "NSI": "NIFTYBEES.NS",
    "BSE": "SENSEXBEES.BO",
    "BOM": "SENSEXBEES.BO",

    # 🇺🇸 USA
    "NMS": "SPY",
    "NYQ": "SPY",
    "ASE": "SPY",
    "PCX": "SPY",
    "BATS": "SPY",
    "ARCX": "SPY",

    # 🇬🇧 UK
    "LSE": "EWU",

    # 🇯🇵 Japan
    "TYO": "EWJ",

    # 🇭🇰 Hong Kong
    "HKG": "EWH",

    # 🇨🇳 China
    "SHH": "ASHR",
    "SHE": "ASHR",

    # 🇩🇪 Germany
    "FRA": "EWG",
    "GER": "EWG",

    # 🇫🇷 France
    "PAR": "EWQ",

    # 🇨🇦 Canada
    "TOR": "EWC",
    "TSX": "EWC",

    # 🇦🇺 Australia
    "ASX": "EWA",

    # 🇰🇷 Korea
    "KSC": "EWY",
    "KOSPI": "EWY",

    # 🇧🇷 Brazil
    "SAO": "EWZ",

    # 🇿🇦 South Africa
    "JNB": "EZA",

    # 🇹🇼 Taiwan
    "TAI": "EWT",
    "TPE": "EWT",

    # 🇸🇬 Singapore
    "SES": "EWS",

    # 🇲🇽 Mexico
    "MEX": "EWW",

    # 🇮🇹 Italy
    "MIL": "EWI",

    # 🇪🇸 Spain
    "MCE": "EWP",

    # 🇳🇱 Netherlands
    "AMS": "EWN",

    # 🇸🇪 Sweden
    "STO": "EWD",

    # 🇨🇭 Switzerland
    "SWX": "EWL",

    # 🇷🇺 Russia (limited usability now)
    "MCX": "ERUS",

    # 🇮🇩 Indonesia
    "JKT": "EIDO",

    # 🇲🇾 Malaysia
    "KLS": "EWM",

    # 🇹🇭 Thailand
    "BKK": "THD",

    # 🇵🇭 Philippines
    "PSE": "EPHE",

    # 🇵🇱 Poland
    "WSE": "EPOL",

    # 🇹🇷 Turkey
    "IST": "TUR",
}

US_EXCHANGES = {
    "NMS", "NYQ", "ASE", "PCX", "BATS", "ARCX"
}


SUFFIX_TO_INDEX = {
    # 🇮🇳
    ".NS": "NIFTYBEES.NS",
    ".BO": "SENSEXBEES.BO",

    # 🇬🇧
    ".L": "EWU",

    # 🇯🇵
    ".T": "EWJ",

    # 🇭🇰
    ".HK": "EWH",

    # 🇨🇳
    ".SS": "ASHR",
    ".SZ": "ASHR",

    # 🇫🇷
    ".PA": "EWQ",

    # 🇩🇪
    ".F": "EWG",

    # 🇨🇦
    ".TO": "EWC",

    # 🇦🇺
    ".AX": "EWA",

    # 🇰🇷
    ".KS": "EWY",
    ".KQ": "EWY",

    # 🇧🇷
    ".SA": "EWZ",

    # 🇿🇦
    ".JO": "EZA",

    # 🇹🇼
    ".TW": "EWT",

    # 🇸🇬
    ".SI": "EWS",

    # 🇲🇽
    ".MX": "EWW",

    # 🇮🇹
    ".MI": "EWI",

    # 🇪🇸
    ".MC": "EWP",

    # 🇳🇱
    ".AS": "EWN",

    # 🇸🇪
    ".ST": "EWD",

    # 🇨🇭
    ".SW": "EWL",

    # 🇮🇩
    ".JK": "EIDO",

    # 🇲🇾
    ".KL": "EWM",

    # 🇹🇭
    ".BK": "THD",

    # 🇵🇭
    ".PS": "EPHE",
}


INDEX_DISPLAY_NAMES = {
    "SPY": "S&P 500 (ETF)",
    "NIFTYBEES.NS": "NIFTY 50 (ETF)",
    "SENSEXBEES.BO": "SENSEX (ETF)",

    "EWU": "UK Market (ETF)",
    "EWJ": "Japan Market (ETF)",
    "EWH": "Hong Kong Market (ETF)",
    "ASHR": "China Market (ETF)",
    "EWG": "Germany Market (ETF)",
    "EWQ": "France Market (ETF)",
    "EWC": "Canada Market (ETF)",
    "EWA": "Australia Market (ETF)",
    "EWY": "Korea Market (ETF)",
    "EWZ": "Brazil Market (ETF)",
    "EZA": "South Africa Market (ETF)",

    "EWT": "Taiwan Market (ETF)",
    "EWS": "Singapore Market (ETF)",
    "EWW": "Mexico Market (ETF)",
    "EWI": "Italy Market (ETF)",
    "EWP": "Spain Market (ETF)",
    "EWN": "Netherlands Market (ETF)",
    "EWD": "Sweden Market (ETF)",
    "EWL": "Switzerland Market (ETF)",

    "EIDO": "Indonesia Market (ETF)",
    "EWM": "Malaysia Market (ETF)",
    "THD": "Thailand Market (ETF)",
    "EPHE": "Philippines Market (ETF)",
    "EPOL": "Poland Market (ETF)",
    "TUR": "Turkey Market (ETF)",

    "ERUS": "Russia Market (ETF)",
}


def get_index(exchange: str, symbol: str = None) -> str:
    normalized_exchange = (exchange or "").upper().strip()

    if normalized_exchange:
        index = EXCHANGE_TO_INDEX.get(normalized_exchange)

        if not index and normalized_exchange in US_EXCHANGES:
            return "SPY"

        if index:
            return index

    normalized_symbol = (symbol or "").upper().strip()

    for suffix, index in SUFFIX_TO_INDEX.items():
        if normalized_symbol.endswith(suffix):
            return index

    return None


def get_index_display_name(index_ticker: str) -> str:
    if not index_ticker:
        return None

    return INDEX_DISPLAY_NAMES.get(index_ticker, index_ticker)