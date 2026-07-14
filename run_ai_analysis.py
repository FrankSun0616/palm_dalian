from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from update_data import (
    DATA_DIR,
    PROFILES,
    _load_json,
    archive_ai_history,
    build_contract_bridge,
    compute_ai_accuracy,
    daily_snapshot,
    fallback_ai_analysis,
    fetch_sina_market_board,
    generate_ai_analysis,
    news_snapshot_to_text,
    normalize_sina_quote,
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


def fetch_live_market_input(symbol: str, attempts: int = 2) -> tuple[dict, dict | None]:
    """Fetch the quote immediately before AI inference.

    Cached quotes are deliberately not returned here: a failed live request
    must block AI execution instead of silently presenting old data as live.
    """
    errors: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            board = fetch_sina_market_board(symbol)
            quote = normalize_sina_quote(
                next(
                    (
                        item for item in board
                        if str(item.get("symbol") or "").upper() == symbol
                    ),
                    None,
                )
            )
            if not quote:
                raise RuntimeError(f"{symbol} quote missing from Sina board")
            fetched_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
            quote.update(
                {
                    "source": "Sina Market Center live request",
                    "fetched_at_utc": fetched_at_utc,
                    "input_status": "live",
                }
            )
            bridge = build_contract_bridge(symbol, board, fetched_at_utc)
            return quote, bridge
        except Exception as exc:  # noqa: BLE001
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            if attempt < attempts:
                time.sleep(1)
    raise RuntimeError("; ".join(errors))


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
    cached_quote_available = cached_realtime_quote(meta, bridge) is not None
    realtime = None
    live_bridge = None
    live_error = None
    try:
        realtime, live_bridge = fetch_live_market_input(symbol)
    except Exception as exc:  # noqa: BLE001
        live_error = f"{type(exc).__name__}: {exc}"
        print(f"[{symbol}] live quote unavailable; AI will be blocked: {live_error}", flush=True)

    snapshot = daily_snapshot(
        frame,
        realtime=realtime,
        intraday=intraday,
        contract_bridge=live_bridge or bridge,
        model_validation=model_validation,
    )
    snapshot["realtime_required_for_ai"] = True
    snapshot["input_freshness"] = {
        "realtime_fetch_status": "live" if realtime else "unavailable",
        "realtime_fetched_at_utc": (realtime or {}).get("fetched_at_utc"),
        "realtime_market_trading_day": (realtime or {}).get("tradedate"),
        "realtime_market_tick_time": (realtime or {}).get("ticktime"),
        "realtime_source": (realtime or {}).get("source"),
        "realtime_fetch_error": live_error,
        "cached_realtime_available_but_not_used": cached_quote_available,
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
    freshness = snapshot["input_freshness"]
    live_ready = freshness.get("realtime_fetch_status") == "live"
    if live_ready:
        realtime = snapshot["realtime"]
        print(
            f"[{symbol}] live quote {realtime['price']} @ "
            f"{realtime['tradedate']} {realtime['ticktime']} "
            f"(fetched {realtime['fetched_at_utc']})",
            flush=True,
        )
        print(f"[{symbol}] live-quote V4-Pro analysis start", flush=True)
        try:
            analysis = generate_ai_analysis(
                snapshot,
                news_summary,
                profile_name=profile["name"],
                symbol=symbol,
            )
        except Exception as exc:  # noqa: BLE001
            analysis = fallback_ai_analysis(snapshot, f"{type(exc).__name__}: {exc}")
    else:
        analysis = fallback_ai_analysis(
            snapshot,
            "AI 已阻止：调用前未取得实时盘口，缓存报价未用于本次分析。",
        )

    analysis.setdefault("symbol", symbol)
    analysis.setdefault("instrument_name", profile["name"])
    analysis["analysis_pipeline"] = "live-quote-plus-cached-bars-v2"
    analysis["input_freshness"] = freshness
    analysis["realtime_input"] = {
        "status": freshness.get("realtime_fetch_status"),
        "fetched_at_utc": freshness.get("realtime_fetched_at_utc"),
        "market_trading_day": freshness.get("realtime_market_trading_day"),
        "market_tick_time": freshness.get("realtime_market_tick_time"),
        "source": freshness.get("realtime_source"),
        "cached_quote_used": False,
    }
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
        f"[{symbol}] live-input AI analysis: {analysis.get('status')} "
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
                print(f"[{symbol}] live-input AI pipeline failed: {type(exc).__name__}: {exc}")
    if failed:
        raise RuntimeError(f"AI analysis failed before writing results: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
