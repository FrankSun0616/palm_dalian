from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from update_data import (
    DATA_DIR,
    PROFILES,
    _load_json,
    archive_ai_history,
    compute_ai_accuracy,
    daily_snapshot,
    fallback_ai_analysis,
    generate_ai_analysis,
    news_snapshot_to_text,
    sanitize_ohlc_frame,
)


def cached_realtime_quote(meta: dict, bridge: dict) -> dict | None:
    quote = meta.get("realtime_quote")
    if isinstance(quote, dict) and float(quote.get("price") or 0) > 0:
        return quote

    main = bridge.get("main") if isinstance(bridge, dict) else None
    if not isinstance(main, dict) or float(main.get("price") or 0) <= 0:
        return None
    return {
        "symbol": main.get("symbol"),
        "name": main.get("name"),
        "price": float(main["price"]),
        "open": main.get("open"),
        "high": main.get("high"),
        "low": main.get("low"),
        "previous_close": main.get("prev_close"),
        "previous_settlement": main.get("prev_settlement"),
        "reference_price": main.get("reference_price"),
        "reference_type": main.get("reference_type"),
        "change": main.get("change"),
        "change_ratio": main.get("change_ratio"),
        "change_pct": main.get("change_pct"),
        "volume": main.get("volume"),
        "open_interest": main.get("open_interest"),
        "tradedate": main.get("tradedate"),
        "ticktime": main.get("ticktime"),
        "source": "cached contract bridge",
    }


def load_cached_snapshot(symbol: str) -> tuple[dict, Path, dict]:
    profile = PROFILES[symbol]
    out_dir = DATA_DIR / profile["dir"]
    frame = pd.read_csv(out_dir / "daily.csv")
    frame = sanitize_ohlc_frame(frame, "date", f"{symbol} cached daily")
    if frame is None or frame.empty:
        raise RuntimeError(f"{symbol} cached daily data is empty")

    meta = _load_json(out_dir / "source_meta.json")
    intraday = _load_json(out_dir / "intraday_meta.json")
    bridge = _load_json(out_dir / "contract_bridge.json")
    model_validation = _load_json(out_dir / "model_validation.json")
    news = _load_json(out_dir / "news_snapshot.json")
    realtime = cached_realtime_quote(meta, bridge)

    snapshot = daily_snapshot(
        frame,
        realtime=realtime,
        intraday=intraday,
        contract_bridge=bridge,
        model_validation=model_validation,
    )
    snapshot["input_freshness"] = {
        "daily_updated_at_utc": meta.get("updated_at_utc"),
        "daily_fetch_status": meta.get("daily_fetch_status", "live"),
        "intraday_updated_at_utc": intraday.get("updated_at_utc"),
        "news_updated_at_utc": news.get("updated_at_utc"),
        "contract_bridge_updated_at_utc": bridge.get("updated_at_utc"),
    }
    return snapshot, out_dir, news


def run_symbol(symbol: str) -> dict:
    started = time.monotonic()
    snapshot, out_dir, news = load_cached_snapshot(symbol)
    profile = PROFILES[symbol]
    news_summary = news_snapshot_to_text(news)
    print(f"[{symbol}] cached-data V4-Pro analysis start", flush=True)
    try:
        analysis = generate_ai_analysis(
            snapshot,
            news_summary,
            profile_name=profile["name"],
            symbol=symbol,
        )
    except Exception as exc:  # noqa: BLE001
        analysis = fallback_ai_analysis(snapshot, f"{type(exc).__name__}: {exc}")

    analysis.setdefault("symbol", symbol)
    analysis.setdefault("instrument_name", profile["name"])
    analysis["analysis_pipeline"] = "cached-market-data-v1"
    analysis["input_freshness"] = snapshot["input_freshness"]
    (out_dir / "ai_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    realtime = snapshot.get("realtime") or {}
    current_price = float(realtime.get("price") or snapshot["close"])
    if analysis.get("status") == "ok":
        archive_ai_history(out_dir, analysis, current_price)
    accuracy = compute_ai_accuracy(out_dir, current_price)
    elapsed = round(time.monotonic() - started, 1)
    print(
        f"[{symbol}] cached-data AI analysis: {analysis.get('status')} "
        f"({elapsed:.1f}s), evaluated={accuracy.get('total_evaluated')}",
        flush=True,
    )
    return {"symbol": symbol, "status": analysis.get("status"), "elapsed": elapsed}


def main() -> int:
    requested = os.getenv("SYMBOLS", "P0,Y0")
    symbols = [
        value.strip().upper()
        for value in requested.split(",")
        if value.strip().upper() in PROFILES
    ]
    if not symbols:
        raise RuntimeError("No valid symbols requested")

    failed: list[str] = []
    with ThreadPoolExecutor(max_workers=len(symbols)) as pool:
        futures = {pool.submit(run_symbol, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                failed.append(symbol)
                print(f"[{symbol}] cached-data AI pipeline failed: {type(exc).__name__}: {exc}")
    if failed:
        raise RuntimeError(f"AI analysis failed before writing results: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
