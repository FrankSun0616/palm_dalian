# Data Sources and Trust Boundaries

## DCE continuous series

- Daily: AKShare `futures_zh_daily_sina(symbol="P0")` and `symbol="Y0"`.
- Intraday: AKShare `futures_zh_minute_sina` with 60, 120 and 240 minute periods.
- Browser quote: Sina Market Center nodes `zly_qh` for P0 and `dy_qh` for Y0.

The generated `data/p0/source_meta.json` and `data/y0/source_meta.json` record source, symbol, market, latest date and backend update times. The page separately displays browser quote time, backend snapshot time, news time and AI time.

## Related markets

`data/overseas.json` contains the available FCPO, CBOT soybean oil and Brent references. These are context signals with different trading hours and contract conventions, not direct substitutes for DCE prices.

## News

News is collected from multiple public search/RSS sources covering China oilseeds, Malaysia, Indonesia, India, biofuel policy, crude oil, weather, tariffs and major crop reports. Titles and links remain source-attributed. Search coverage can be delayed or incomplete.

## Important limitations

- P0/Y0 are continuous analysis series, not tradable delivery-month symbols.
- Sina/AKShare are practical public sources but are not an exchange-certified low-latency market-data feed.
- A future-looking date can be the DCE trading-day label assigned to the preceding night session.
- GitHub Actions scheduling is best-effort and can be delayed.
- DeepSeek V4-Pro output is secondary analysis. The page marks stale AI and falls back to deterministic rules.

AI text also passes a deterministic integrity audit. Claims about RSI and 1H/4H Bollinger position are checked against the supplied market snapshot, invalid support/resistance values are replaced, and low-confidence or contradictory output is kept out of the execution layer. Historical AI direction is evaluated at a fixed four-completed-1H-bar horizon with overlapping decision windows collapsed.

For exchange-grade execution, replace the public quote path with a licensed feed and map continuous-series analysis to the actual liquid delivery-month contract.
