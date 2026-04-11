# Market Status Badge

This file documents how the navbar market-status indicator is built in `stockometer`.

## Where It Lives

- Backend logic: `app.py`
- Navbar markup: `templates/main.html`
- Badge styling: `static/main.css`

## How It Works

1. `app.py` reads the stock exchange from `ticker.info["exchange"]`.
2. `_market_status(exchange)` maps that exchange to:
   - a timezone
   - a local market open time
   - a local market close time
3. The server gets the current local market time with `pandas.Timestamp.now(tz=...)`.
4. The badge is marked open only when:
   - the local day is Monday to Friday
   - the local time is between open and close
5. The result is passed into `main.html` as:
   - `market_status.is_open`
   - `market_status.label`

## Current Labels

- Open market: `LIVE`
- Closed market: `MARKET'S NOT LIVE`

The colored dot is handled in CSS with `::before`, not in the rendered text.

## Exchanges Covered

- India:
  - `NSE`, `NSI`
  - `BSE`, `BOM`
- United States:
  - `NMS`, `NYQ`, `ASE`, `PCX`
- Other mapped exchanges:
  - `LSE`
  - `HKG`
  - `TYO`

## Current Market Hours Used

- India: `09:15` to `15:30` in `Asia/Kolkata`
- US: `09:30` to `16:00` in `America/New_York`
- London: `08:00` to `16:30` in `Europe/London`
- Hong Kong: `09:30` to `16:00` in `Asia/Hong_Kong`
- Tokyo: `09:00` to `15:00` in `Asia/Tokyo`

## Notes

- This is a simple exchange-hours check.
- It does not currently account for:
  - exchange holidays
  - lunch breaks in some markets
  - special sessions / half-days
  - pre-market or after-hours trading

If higher accuracy is needed later, the next step should be adding exchange holiday calendars per market.
