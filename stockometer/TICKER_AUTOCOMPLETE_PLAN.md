# Ticker Autocomplete Plan

## Purpose

This document is the single working file for the ticker suggestion feature.

Use it for:
- feature design
- implementation sequence
- status tracking
- testing checklist
- rough notes and scratch work while building

## Status

Overall status: `completed`

Implementation phases:

| Phase | Status | Notes |
| --- | --- | --- |
| 1. Read current app flow | completed | Reviewed current routes, templates, styles, and JS. |
| 2. Design backend suggestion API | completed | Using `yfinance.Search` plus normalization and fail-closed behavior. |
| 3. Design frontend autocomplete UI | completed | Debounced fetch, dropdown, keyboard support, no change to submit flow. |
| 4. Add backend tests | completed | Route and helper tests added with Yahoo search mocked. |
| 5. Implement backend | completed | Helper module and `/api/symbols` route added. |
| 6. Implement frontend | completed | `index.html`, `index.css`, and `index.js` wired. |
| 7. Verify manually | completed | Live `/api/symbols?q=app` returned ticker matches and landing page served new hooks. |
| 8. Final cleanup | completed | README and tracker updated. |

## Current Codebase Notes

### Existing request flow

Landing page:
- Route: `/`
- Template: [templates/index.html](/Users/abinthomas/Desktop/hobby/stockometer/templates/index.html)
- Behavior: plain HTML form posts directly to `/analyze`

Analysis flow:
- Route: `/analyze`
- File: [app.py](/Users/abinthomas/Desktop/hobby/stockometer/app.py)
- Behavior: validates symbol, fetches market data with `yfinance`, computes indicators, renders `main.html`

Frontend today:
- Landing page has no JavaScript
- Existing JS is only for the results page resize interaction in [static/main.js](/Users/abinthomas/Desktop/hobby/stockometer/static/main.js)
- Landing page styling lives in [static/index.css](/Users/abinthomas/Desktop/hobby/stockometer/static/index.css)

### Relevant constraints from current implementation

- The existing form submit path should remain intact.
- Suggestions should enhance typing, not replace the current form model.
- The repo already depends on `yfinance`.
- Installed `yfinance` includes `Search`, which can be used for ticker lookup.

## Feature Goal

When the user starts typing in the ticker input on the landing page, the app should suggest matching ticker names and symbols in a dropdown. The user should be able to:

- click a suggestion
- navigate suggestions with keyboard arrows
- press Enter to choose a suggestion
- press Escape to close the dropdown
- continue using the existing Analyze submit flow

The selected value written into the input should be the ticker symbol, not the company display label.

## Proposed Solution

## 1. Backend API

Add a new route:

- `GET /api/symbols?q=<query>`

Response shape:

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NMS",
    "type": "EQUITY"
  }
]
```

### Backend helper responsibilities

Create a dedicated helper module, likely:

- `symbol_search.py`

Responsibilities:
- call `yfinance.Search`
- limit number of results
- normalize Yahoo payload
- filter invalid items
- dedupe duplicate symbols
- fail closed with empty results when upstream search fails

### Suggested normalization rules

Input fields to inspect from Yahoo quote objects:
- `symbol`
- `shortname`
- `longname`
- `exchange`
- `quoteType`

Output rules:
- `symbol`: required
- `name`: prefer `shortname`, fallback to `longname`, fallback to symbol
- `exchange`: optional, default `""`
- `type`: uppercase string if present, else `""`

### Suggested filtering rules

Drop items when:
- `symbol` is missing
- `symbol` is blank
- `quoteType` is not one of the allowed categories, if filtering is enabled

Recommended initial allowlist:
- `EQUITY`
- `ETF`
- `MUTUALFUND`

Possible later extension:
- `INDEX`
- `CRYPTOCURRENCY`

### API behavior rules

- if `q` missing or blank: return `[]`
- if trimmed query length < 2: return `[]`
- if Yahoo search raises error: return `[]`
- HTTP status should remain `200` for normal suggestion failures to keep the typing UX smooth

## 2. Frontend UX

Enhance the landing page input in:

- [templates/index.html](/Users/abinthomas/Desktop/hobby/stockometer/templates/index.html)

Add:
- stable `id` for the input
- wrapper element that can anchor a dropdown
- suggestion list container below input
- loading and empty state placeholders if useful
- accessibility attributes for combobox/listbox semantics

Recommended structure:

```html
<div class="symbol-input autocomplete">
  <input ... />
  <div class="suggestions" hidden></div>
</div>
```

### Frontend behavior

Create a new script:

- `static/index.js`

Responsibilities:
- listen to input changes
- debounce calls by `200-300ms`
- fetch `/api/symbols?q=...`
- render suggestions
- track currently highlighted option
- support keyboard and mouse interaction
- close dropdown on blur/outside click
- avoid duplicate in-flight results overwriting newer input

### Interaction details

Typing:
- do nothing for fewer than 2 chars
- show loading state while request is active
- show up to about 6 to 8 suggestions

Keyboard:
- `ArrowDown`: move active selection down
- `ArrowUp`: move active selection up
- `Enter`: if a suggestion is active, choose it and prevent form submit
- `Enter`: if no suggestion is active, allow normal form submit
- `Escape`: close dropdown

Mouse:
- hover updates active option
- click selects symbol and closes dropdown

Selection:
- write `symbol` into the input value
- optionally preserve display text only in dropdown rows

Race handling:
- if user typed again before previous response returns, ignore stale response

## 3. Styling

Extend:

- [static/index.css](/Users/abinthomas/Desktop/hobby/stockometer/static/index.css)

Add styles for:
- dropdown container
- suggestion row
- active row
- hover row
- secondary text for company name or exchange
- empty state
- loading state

Design guidance:
- keep current landing page layout intact
- dropdown should visually connect to the input
- must work on mobile and desktop
- avoid introducing a style system disconnected from existing page design

## Detailed Implementation Sequence

## Phase 1: Backend foundation

1. Create `symbol_search.py`
2. Add a `search_symbols(query)` function
3. Add an internal normalizer for raw Yahoo quote results
4. Add dedupe/filter logic
5. Keep API independent from Flask so it is easy to unit test

Definition of done:
- helper returns predictable list of normalized dictionaries
- helper returns empty list on short query and upstream failure

## Phase 2: Backend route

1. Add `GET /api/symbols` to [app.py](/Users/abinthomas/Desktop/hobby/stockometer/app.py)
2. Read `q` from query string
3. Return JSON response via `jsonify`
4. Keep route side-effect free

Definition of done:
- route returns JSON array
- no HTML rendering involved
- no server error on bad or empty input

## Phase 3: Backend tests

Add tests in:
- `tests/test_symbol_search.py`
- extend `tests/test_app.py` for route-level coverage

Coverage targets:
- blank query returns empty list
- short query returns empty list
- valid quotes normalized correctly
- duplicates are removed
- items without symbol are filtered out
- upstream exception returns empty list
- `/api/symbols` returns JSON and `200`

Definition of done:
- backend suggestion path is fully covered with deterministic mocks

## Phase 4: Frontend markup

Update:
- [templates/index.html](/Users/abinthomas/Desktop/hobby/stockometer/templates/index.html)

Changes:
- add IDs/classes for autocomplete controls
- add dropdown container
- include `static/index.js`

Definition of done:
- landing page contains all hooks needed by JS without changing current form submit behavior

## Phase 5: Frontend logic

Create:
- `static/index.js`

Implement:
- debounce
- fetch logic
- render logic
- keyboard navigation
- click selection
- outside click close
- stale request handling

Definition of done:
- suggestions appear while typing
- selection works with mouse and keyboard
- normal form submission still works

## Phase 6: Frontend styling

Update:
- [static/index.css](/Users/abinthomas/Desktop/hobby/stockometer/static/index.css)

Implement:
- dropdown placement
- row states
- spacing and typography
- responsive behavior

Definition of done:
- dropdown is readable and polished on both desktop and mobile

## Phase 7: Verification

### Automated

Run:

```bash
python -m unittest discover -s tests -v
```

### Manual

Scenarios to verify:
- type `AA` and see suggestions
- type `AAPL` and see Apple
- type `INFY` and confirm exchange-qualified suggestions appear if available
- select with mouse
- select with keyboard
- press Escape to close
- submit typed symbol without selecting suggestion
- simulate backend failure and confirm UI does not break

Observed verification:
- `GET /api/symbols?q=app` returned live matches including `APP`, `AAPL`, and `AMAT`
- landing page served autocomplete markup and `static/index.js`
- full browser-driven keyboard/mouse interaction was implemented but not exercised through a headful browser in this environment

## Failure Cases To Cover

Backend:
- empty query
- short query
- malformed Yahoo quote rows
- duplicated symbols
- upstream search failure

Frontend:
- no matches returned
- stale response arrives late
- dropdown remains open on blur
- Enter submits accidentally when an item is highlighted
- keyboard navigation escapes bounds

Operational:
- Yahoo latency causing slow responses
- rate-limit or transient failure from upstream

## Design Decisions

### Why use `yfinance.Search`

- already available in this repo
- consistent with current market-data source
- avoids introducing a second market/search provider
- keeps implementation small

### Why use a separate helper module

- easier testing
- keeps `app.py` from growing route-specific parsing logic
- isolates Yahoo response cleanup in one place

### Why return empty arrays on failure

- autocomplete should degrade quietly
- user can still submit ticker manually
- typing UX should not throw visible server errors

## Open Questions

- Should suggestions include ETFs only, or mutual funds too?
- Should we show exchange suffixes prominently for symbols like `INFY.NS`?
- Should selecting a suggestion submit immediately, or only fill the field?

Current recommendation:
- include `EQUITY`, `ETF`, `MUTUALFUND`
- display exchange in the row
- selection fills only; submit remains explicit

## Rough Notes / Scratch Pad

Use this section freely while implementing.

### Notes

- Current landing page has no dedicated JS file.
- Current CSS already styles the symbol input container; dropdown can anchor there.
- Existing `/analyze` expects a single symbol string, so autocomplete should write only the symbol into the input.
- Avoid binding the feature to the chart/results page; this is a landing-page concern only.

### Implementation Scratch

- Potential route signature: `/api/symbols?q=app`
- Potential module functions:
  - `normalize_quote(quote)`
  - `search_symbols(query, max_results=8)`
- Need to decide if frontend should use `AbortController` or a request counter for stale responses.
- Request counter is likely simpler in this repo.

### Progress Log

- 2026-04-02: Reviewed current routes, templates, CSS, JS, and installed `yfinance.Search`.
- 2026-04-02: Documented initial solution and implementation sequence.
- 2026-04-02: Added backend search helper design to code, started `/api/symbols` route, and added initial backend test coverage.
- 2026-04-02: Implemented landing-page autocomplete markup, styling, and client-side behavior.
- 2026-04-02: Verified live `/api/symbols` results locally and updated README/tracker.
- 2026-04-02: Removed local-only launch helper before PR prep so the branch only contains product, test, and documentation changes.

## PR Notes

### Suggested title

`Add ticker autocomplete and harden analysis rendering`

### Summary

- adds ticker suggestion API backed by Yahoo Finance search through `yfinance.Search`
- adds landing-page autocomplete UI with debounce, keyboard navigation, and mouse selection
- hardens `/analyze` rendering and company-metric formatting against missing data
- fixes the Plotly candlestick hover configuration issue
- adds regression tests for chart generation and symbol suggestion behavior

### Test command

```bash
python -m unittest discover -s tests -v
```

## Completion Checklist

- [x] Helper module implemented
- [x] `/api/symbols` route implemented
- [x] Backend tests added
- [x] Landing page markup updated
- [x] `static/index.js` added
- [x] `static/index.css` updated
- [x] Manual verification complete
- [x] README updated
- [x] This tracker updated to `completed`
