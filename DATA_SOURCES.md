# Data Source Validation

Tested on 2026-05-06.

## Valid

- AKShare `futures_zh_daily_sina(symbol="P0")`
  - Returned 4501 daily rows.
  - Latest date: 2026-05-06.
  - Saved to `data/palm_oil_p0_daily.csv`.

- AKShare `futures_zh_spot(symbol="P0", market="CF")`
  - Returned one current quote row for `棕榈油连续`.
  - Useful for real-time display, not as clean as daily K-line history.

- Sina futures quote page `https://finance.sina.com.cn/futures/quotes/P0.shtml`
  - Page loads and contains palm oil quote content.
  - Better consumed through AKShare than scraped directly.

## Not Valid Without Credentials

- Tushare `fut_daily(ts_code="P.DCE")`
  - Failed because no Tushare Pro token is configured.
  - It should become usable after setting `TUSHARE_TOKEN`.

- `dceapi`
  - Failed because `DCE_API_KEY` and `DCE_SECRET` are not configured.

## Problematic For Direct Use

- DCE official web pages
  - Official portal is authoritative, but HTTPS failed in local Python due legacy SSL negotiation.
  - Old public day quote page returned HTTP 412.
  - Better as a paid/credentialed official source or for manual verification, not the first auto-update route.

## Recommended Route

Use AKShare daily data for the webpage:

```bash
.venv/bin/python update_data.py
```

Then serve the folder locally:

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080
```
