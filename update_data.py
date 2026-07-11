from __future__ import annotations

import json
import os
import html
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import akshare as ak
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


# ── AI history / accuracy helpers ────────────────────────────────────────────

# Kept in sync with notify.bias_sign — duplicated here to avoid importing
# notify.py (which is a lightweight standalone script) from the data pipeline.
_BIAS_LEXICON: list[tuple[str, int]] = [
    ("偏多", +1), ("多头", +1), ("看多", +1), ("做多", +1), ("强", +1),
    ("偏空", -1), ("空头", -1), ("看空", -1), ("做空", -1), ("弱", -1),
]


def _bias_sign(bias: str | None) -> int:
    """+1 for long, -1 for short, 0 for neutral/unknown. Matches notify.bias_sign."""
    if not bias:
        return 0
    text = str(bias)
    for keyword, sign in _BIAS_LEXICON:
        if keyword in text:
            return sign
    return 0


AI_HISTORY_MAX = 100
AI_HISTORY_MIN_FOR_SCORING = 5
AI_ACCURACY_ELAPSED_DAYS = 3
AI_ACCURACY_WINDOW = 20
AI_ACCURACY_MOVE_THRESHOLD = 0.005  # 0.5%
AI_ACCURACY_LOW_THRESHOLD = 0.40
AI_ACCURACY_LOW_MIN_EVAL = 10


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def archive_ai_history(profile_dir, ai_analysis: dict, current_price: float) -> None:
    """Append a compact record of this AI analysis to
    data/{profile_dir}/ai_history.json (list, trimmed to last 100)."""
    profile_dir = Path(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    hist_path = profile_dir / "ai_history.json"

    watch = ai_analysis.get("watch_levels") or {}
    support = watch.get("support")
    resistance = watch.get("resistance")

    def _num(x):
        try:
            if x is None:
                return None
            return float(x)
        except (TypeError, ValueError):
            return None

    bias = str(ai_analysis.get("bias") or "")
    entry = {
        "generated_at_utc": ai_analysis.get("generated_at_utc")
            or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bias": bias,
        "bias_sign": _bias_sign(bias),
        "price_at": _num(current_price),
        "resistance": _num(resistance),
        "support": _num(support),
    }

    existing = _load_json(hist_path)
    entries = existing.get("entries") if isinstance(existing, dict) else None
    if not isinstance(entries, list):
        entries = []
    entries.append(entry)
    if len(entries) > AI_HISTORY_MAX:
        entries = entries[-AI_HISTORY_MAX:]

    hist_path.write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _grade_entry(entry: dict, current_price: float) -> str | None:
    """Return 'hit'|'miss'|'neutral' if this entry has enough elapsed time and
    can be graded against current_price, else None."""
    gen = entry.get("generated_at_utc")
    price_at = entry.get("price_at")
    if not gen or price_at in (None, 0):
        return None
    try:
        gen_dt = datetime.fromisoformat(gen.replace("Z", "+00:00") if gen.endswith("Z") else gen)
    except ValueError:
        return None
    if gen_dt.tzinfo is None:
        gen_dt = gen_dt.replace(tzinfo=timezone.utc)
    elapsed_days = (datetime.now(timezone.utc) - gen_dt).total_seconds() / 86400.0
    if elapsed_days < AI_ACCURACY_ELAPSED_DAYS:
        return None
    try:
        pa = float(price_at)
        cp = float(current_price)
    except (TypeError, ValueError):
        return None
    move = (cp - pa) / pa
    sign = int(entry.get("bias_sign") or 0)
    thr = AI_ACCURACY_MOVE_THRESHOLD
    if sign > 0:
        if move > thr:
            return "hit"
        if move < -thr:
            return "miss"
        return "neutral"
    if sign < 0:
        if move < -thr:
            return "hit"
        if move > thr:
            return "miss"
        return "neutral"
    # neutral bias: hit if move stays inside ±thr, miss if big move
    return "hit" if abs(move) <= thr else "miss"


def compute_ai_accuracy(profile_dir, current_price: float) -> dict:
    """Grade past AI entries in ai_history.json against current_price and
    write data/{profile_dir}/ai_accuracy.json. Returns the written dict."""
    profile_dir = Path(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    acc_path = profile_dir / "ai_accuracy.json"
    hist = _load_json(profile_dir / "ai_history.json")
    entries = hist.get("entries") if isinstance(hist, dict) else None
    if not isinstance(entries, list):
        entries = []

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if len(entries) < AI_HISTORY_MIN_FOR_SCORING:
        result = {
            "updated_at_utc": now_iso,
            "recent_hit_rate": None,
            "total_evaluated": 0,
            "hits": 0,
            "misses": 0,
            "neutrals": 0,
            "warning_low_accuracy": False,
            "last_grade": None,
        }
        acc_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    graded: list[dict] = []
    for e in entries:
        outcome = _grade_entry(e, current_price)
        if outcome is None:
            continue
        graded.append({
            "bias": e.get("bias"),
            "generated_at_utc": e.get("generated_at_utc"),
            "price_at": e.get("price_at"),
            "current_price": float(current_price),
            "outcome": outcome,
        })

    total_evaluated = len(graded)
    hits = sum(1 for g in graded if g["outcome"] == "hit")
    misses = sum(1 for g in graded if g["outcome"] == "miss")
    neutrals = sum(1 for g in graded if g["outcome"] == "neutral")

    recent = graded[-AI_ACCURACY_WINDOW:]
    if len(recent) >= AI_HISTORY_MIN_FOR_SCORING:
        recent_hit_rate = sum(1 for g in recent if g["outcome"] == "hit") / len(recent)
    else:
        recent_hit_rate = None

    warning = bool(
        recent_hit_rate is not None
        and recent_hit_rate < AI_ACCURACY_LOW_THRESHOLD
        and total_evaluated >= AI_ACCURACY_LOW_MIN_EVAL
    )

    result = {
        "updated_at_utc": now_iso,
        "recent_hit_rate": round(recent_hit_rate, 4) if recent_hit_rate is not None else None,
        "total_evaluated": total_evaluated,
        "hits": hits,
        "misses": misses,
        "neutrals": neutrals,
        "warning_low_accuracy": warning,
        "last_grade": graded[-1] if graded else None,
    }
    acc_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


# ── F4: Overseas overnight snapshot ─────────────────────────────────────────
#
# Writes a single shared data/overseas.json used by BOTH the P0 and Y0 front
# pages. Best-effort — a per-symbol failure or a total-network failure just
# omits that symbol, never fails the pipeline.

# akshare returns rows keyed by 名称 (Chinese name); we map code → cn_name so
# a single realtime call covers all three tickers. Keeping this hardcoded
# avoids paying for ak.futures_hq_subscribe_exchange_symbol() at runtime.
_OVERSEAS_SPEC = [
    ("FCPO",        "FCPO", "马棕油",       "马来棕榈油"),
    ("SOYBEAN_OIL", "BO",   "CBOT-黄豆油",  "CBOT 豆油"),
    ("BRENT",       "OIL",  "布伦特原油",   "布伦特原油"),
]


def fetch_overseas_snapshot(out_dir: Path = DATA_DIR) -> dict:
    result = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "symbols": {},
    }
    codes = [row[1] for row in _OVERSEAS_SPEC]
    df = None
    try:
        df = ak.futures_foreign_commodity_realtime(symbol=codes)
    except Exception as exc:  # noqa: BLE001
        print(f"[overseas] akshare fetch failed (soft-skip): {type(exc).__name__}: {exc}")

    if df is not None and not df.empty:
        for key, _code, cn_name, display in _OVERSEAS_SPEC:
            try:
                match = df[df["名称"] == cn_name]
                if match.empty:
                    continue
                row = match.iloc[0]
                price = float(row["最新价"])
                prev_close = float(row["昨日结算价"])
                if not price:
                    continue
                change = price - prev_close
                change_pct = (change / prev_close) if prev_close else 0
                result["symbols"][key] = {
                    "name": display,
                    "price": round(price, 4),
                    "change": round(change, 4),
                    "change_pct": pct(change_pct),
                    "source": "AKShare futures_foreign_commodity_realtime",
                }
            except Exception as exc:  # noqa: BLE001
                print(f"[overseas] parse {key} failed (soft-skip): {type(exc).__name__}: {exc}")

    # Fallback: try Yahoo Finance for BO=F and BZ=F if akshare gave us nothing
    # for those keys. FCPO is not on Yahoo, so we accept a possible omission.
    yahoo_map = {"SOYBEAN_OIL": ("BO=F", "CBOT 豆油"), "BRENT": ("BZ=F", "布伦特原油")}
    for key, (ticker, display) in yahoo_map.items():
        if key in result["symbols"]:
            continue
        try:
            resp = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            resp.raise_for_status()
            payload = resp.json()
            chart = (payload.get("chart") or {}).get("result") or []
            if not chart:
                continue
            meta_y = chart[0].get("meta") or {}
            price = float(meta_y.get("regularMarketPrice") or 0)
            prev_close = float(
                meta_y.get("chartPreviousClose")
                or meta_y.get("previousClose")
                or 0
            )
            if not price:
                continue
            change = price - prev_close
            change_pct = (change / prev_close) if prev_close else 0
            result["symbols"][key] = {
                "name": display,
                "price": round(price, 4),
                "change": round(change, 4),
                "change_pct": pct(change_pct),
                "source": f"Yahoo Finance {ticker}",
            }
        except Exception as exc:  # noqa: BLE001
            print(f"[overseas] yahoo {ticker} failed (soft-skip): {type(exc).__name__}: {exc}")

    out_dir.mkdir(exist_ok=True, parents=True)
    (out_dir / "overseas.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[overseas] wrote {len(result['symbols'])} symbol(s): {list(result['symbols'].keys())}")
    return result


# ── Profiles: per-symbol pipeline config ─────────────────────────────────────
#
# Each profile drives one full pipeline run (daily CSV, intraday bundle, news
# snapshot, realtime quote, AI analysis). All output files land under
# DATA_DIR / profile["dir"] so P0 and Y0 don't stomp on each other.

PROFILES: dict[str, dict] = {
    "P0": {
        "name": "棕榈油",
        "market_node": "zly_qh",  # Sina Market_Center node for realtime quote
        "dir": "p0",
        "news_queries": [
            # 棕榈油核心
            "棕榈油 期货 今日 马来西亚 印尼 出口 库存",
            "大连 棕榈油 P0 期货 今日 走势",
            "palm oil futures Malaysia Indonesia export stock today",
            "MPOB monthly palm oil production stock",
            # 印尼大宗商品 / 政策
            "印尼 大宗商品 出口 政策 关税 棕榈油",
            "Indonesia commodity export policy palm oil tariff",
            "Indonesia state-backed agency raw material export",
            "Indonesia Danantara raw materials commodity",
            "印尼 国营 大宗商品 原材料 出口 机构",
            "Indonesia nickel coal mineral export ban quota",
            # 印度（最大买家）
            "印度 棕榈油 进口 需求",
            "India palm oil import demand vegetable oil",
            # 能源 / 生物柴油（替代品需求）
            "原油 价格 布伦特 WTI 走势",
            "crude oil Brent WTI price biodiesel demand",
            # 替代油脂
            "豆油 菜油 葵花油 国际 价格 走势",
            "soybean oil rapeseed sunflower oil price",
            # 天气
            "厄尔尼诺 拉尼娜 东南亚 棕榈 干旱",
            "El Nino La Nina Southeast Asia palm oil weather",
            # 汇率
            "马来 林吉特 印尼 卢比 美元 走势",
        ],
    },
    "Y0": {
        "name": "豆油",
        "market_node": "dy_qh",
        "dir": "y0",
        "news_queries": [
            "豆油 期货 大连 走势 今日",
            "大商所 豆油 Y2609 主力 走势",
            "soybean oil futures DCE price",
            "CBOT 大豆 期货 走势",
            "USDA 大豆 报告 出口 库存",
            "阿根廷 巴西 大豆 产量 天气",
            "中国 大豆 进口 需求",
            "China soybean import demand",
            "中美 贸易 关税 大豆",
            "US-China trade soybean tariff",
            "印度 豆油 进口 需求",
            "India soybean oil demand",
            "植物油脂 联动 豆油 棕榈油",
            "原油 布伦特 WTI 走势",
            "El Nino La Nina 天气 大豆 影响",
        ],
    },
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.2f}%"


def ma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    seed = changes[:period]
    avg_gain = sum(max(item, 0) for item in seed) / period
    avg_loss = sum(max(-item, 0) for item in seed) / period
    for item in changes[period:]:
        avg_gain = (avg_gain * (period - 1) + max(item, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-item, 0)) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    avg = mean(values)
    return (sum((item - avg) ** 2 for item in values) / len(values)) ** 0.5


def bollinger_from_closes(closes: list[float], period: int = 20, width: float = 2.0) -> dict[str, float | str]:
    window = closes[-period:] if len(closes) >= period else closes
    mid = mean(window)
    sd = stddev(window)
    upper = mid + width * sd
    lower = mid - width * sd
    close = closes[-1]
    band_width = (upper - lower) / mid if mid else 0
    if close > upper:
        position = "突破上轨"
    elif close < lower:
        position = "跌破下轨"
    elif close >= mid:
        position = "中轨上方"
    else:
        position = "中轨下方"
    return {
        "period": period,
        "close": round(close, 2),
        "upper": round(upper, 2),
        "mid": round(mid, 2),
        "lower": round(lower, 2),
        "band_width": round(band_width, 4),
        "position": position,
    }


def sanitize_ohlc_frame(df, time_column: str, label: str):
    """Remove malformed bars before they reach indicators or deployed CSVs."""
    if df is None or df.empty:
        return df
    out = df.copy()
    required_numeric = ["open", "high", "low", "close", "volume"]
    for column in required_numeric:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=[time_column, *required_numeric])
    valid = (
        (out["high"] >= out[["open", "close"]].max(axis=1))
        & (out["low"] <= out[["open", "close"]].min(axis=1))
        & (out["high"] >= out["low"])
        & (out["volume"] >= 0)
    )
    removed_invalid = int((~valid).sum())
    out = out.loc[valid].copy()
    before_dedup = len(out)
    out[time_column] = out[time_column].astype(str)
    out = out.sort_values(time_column).drop_duplicates(time_column, keep="last")
    removed_duplicates = before_dedup - len(out)
    if removed_invalid or removed_duplicates:
        print(
            f"[{label}] sanitized bars: invalid={removed_invalid}, "
            f"duplicates={removed_duplicates}"
        )
    return out


def normalize_intraday_df(df, limit: int = 220):
    if df is None or df.empty:
        return df
    out = sanitize_ohlc_frame(df, "datetime", "intraday").tail(limit)
    out["datetime"] = out["datetime"].astype(str)
    keep = ["datetime", "open", "high", "low", "close", "volume", "hold"]
    return out[keep]


def fetch_intraday(period: str, symbol: str = "P0"):
    try:
        return normalize_intraday_df(ak.futures_zh_minute_sina(symbol=symbol, period=period))
    except Exception as exc:
        print(f"Intraday {symbol} {period}m fetch failed: {exc}")
        return None


def intraday_summary(df, label: str) -> dict[str, object] | None:
    if df is None or df.empty:
        return None
    closes = [float(item) for item in df["close"].tolist()]
    latest = df.tail(1).iloc[0]
    previous = df.tail(2).iloc[0] if len(df) >= 2 else latest
    boll = bollinger_from_closes(closes, 20, 2)
    change_pct = (float(latest["close"]) - float(previous["close"])) / float(previous["close"]) if float(previous["close"]) else 0
    recent20 = df.tail(20)
    recent30 = df.tail(30)
    numeric = df.copy()
    for column in ("open", "high", "low", "close", "volume", "hold"):
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
    previous_close = numeric["close"].shift(1)
    true_range = pd.concat(
        [
            numeric["high"] - numeric["low"],
            (numeric["high"] - previous_close).abs(),
            (numeric["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr14 = float(true_range.tail(14).mean()) if len(true_range.dropna()) >= 2 else None
    ema20_series = numeric["close"].ewm(span=20, adjust=False).mean()
    ema20 = float(ema20_series.iloc[-1])
    ema20_prev = float(ema20_series.iloc[-6]) if len(ema20_series) >= 6 else ema20
    ema20_slope_5 = (ema20 - ema20_prev) / float(latest["close"]) if float(latest["close"]) else 0
    volume_avg20 = float(numeric["volume"].tail(20).mean())
    volume_ratio20 = float(latest["volume"]) / volume_avg20 if volume_avg20 else 0
    hold_change = float(latest["hold"]) - float(previous["hold"])

    up_move = numeric["high"].diff()
    down_move = -numeric["low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr_roll = true_range.rolling(14).mean()
    plus_di = 100 * plus_dm.rolling(14).mean() / atr_roll.replace(0, pd.NA)
    minus_di = 100 * minus_dm.rolling(14).mean() / atr_roll.replace(0, pd.NA)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)
    adx14_value = dx.rolling(14).mean().iloc[-1] if len(dx) >= 28 else pd.NA
    adx14 = float(adx14_value) if pd.notna(adx14_value) else None
    return {
        "label": label,
        "latest_time": str(latest["datetime"]),
        "open": float(latest["open"]),
        "high": float(latest["high"]),
        "low": float(latest["low"]),
        "close": float(latest["close"]),
        "change_pct": pct(change_pct),
        "volume": int(latest["volume"]),
        "rsi14": round(rsi(closes, 14), 2) if len(closes) > 14 else None,
        "atr14": round(atr14, 2) if atr14 is not None else None,
        "adx14": round(adx14, 2) if adx14 is not None else None,
        "ema20": round(ema20, 2),
        "ema20_slope_5": round(ema20_slope_5, 4),
        "volume_ratio20": round(volume_ratio20, 2),
        "open_interest_change": int(hold_change),
        "bollinger": boll,
        "high20": float(recent20["high"].max()),
        "low20": float(recent20["low"].min()),
        "last_30_bars": recent30.to_dict(orient="records"),
    }


def fetch_intraday_bundle(symbol: str = "P0", out_dir: Path = DATA_DIR) -> dict[str, object]:
    h1 = fetch_intraday("60",  symbol=symbol)
    h2 = fetch_intraday("120", symbol=symbol)
    h4 = fetch_intraday("240", symbol=symbol)
    if h1 is not None and not h1.empty: h1.to_csv(out_dir / "intraday_1h.csv", index=False)
    if h2 is not None and not h2.empty: h2.to_csv(out_dir / "intraday_2h.csv", index=False)
    if h4 is not None and not h4.empty: h4.to_csv(out_dir / "intraday_4h.csv", index=False)
    bundle = {
        "source": "AKShare futures_zh_minute_sina",
        "symbol": symbol,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "one_hour":  intraday_summary(h1, "1小时"),
        "two_hour":  intraday_summary(h2, "2小时"),
        "four_hour": intraday_summary(h4, "4小时"),
    }
    (out_dir / "intraday_meta.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return bundle


# ── Real-time quote (Sina Market Center) ─────────────────────────────────────

SINA_MARKET_URL_TMPL = (
    "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "Market_Center.getHQFuturesData?page=1&sort=position&asc=0&node={node}&base=futures"
)


def get_realtime_quote_sina(symbol: str = "P0") -> dict | None:
    """Fetch live quote for `symbol` from Sina Market Center (same API as the
    browser front-end). The Sina 'node' name is looked up from PROFILES so
    each symbol hits its own commodity node (P0=zly_qh, Y0=dy_qh, ...)."""
    profile = PROFILES.get(symbol)
    if not profile:
        return None
    url = SINA_MARKET_URL_TMPL.format(node=profile["market_node"])
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        item = next((it for it in data if it.get("symbol") == symbol), None)
        if not item or not float(item.get("trade") or 0):
            return None
        price = float(item["trade"])
        prev_close = float(item["preclose"])
        change = (price - prev_close) / prev_close if prev_close else 0
        return {
            "price": price,
            "open": float(item["open"]),
            "high": float(item["high"]),
            "low": float(item["low"]),
            "volume": int(item["volume"]),
            "prev_close": prev_close,
            "change_pct": pct(change),
            "tradedate": item.get("tradedate", ""),
            "ticktime": item.get("ticktime", ""),
        }
    except Exception:
        return None


# ── Daily snapshot ────────────────────────────────────────────────────────────

def daily_snapshot(export, realtime: dict | None = None, intraday: dict | None = None) -> dict:
    rows = export.tail(120).to_dict(orient="records")
    closes = [float(row["close"]) for row in rows]
    volumes = [float(row["volume"]) for row in rows]
    latest = rows[-1]
    previous = rows[-2]
    change = (latest["close"] - previous["close"]) / previous["close"]
    high20 = max(float(row["high"]) for row in rows[-20:])
    low20 = min(float(row["low"]) for row in rows[-20:])
    volume_avg20 = sum(volumes[-20:]) / 20
    snap: dict = {
        "latest_date": str(latest["date"]),
        "open": float(latest["open"]),
        "high": float(latest["high"]),
        "low": float(latest["low"]),
        "close": float(latest["close"]),
        "change_pct": pct(change),
        "volume": int(latest["volume"]),
        "volume_ratio_20d": round(float(latest["volume"]) / volume_avg20, 2),
        "ma10": round(ma(closes, 10), 2),
        "ma20": round(ma(closes, 20), 2),
        "ma60": round(ma(closes, 60), 2),
        "rsi14": round(rsi(closes, 14), 2),
        "high20": high20,
        "low20": low20,
        "last_30_daily_bars": rows[-30:],
    }
    if realtime:
        snap["realtime"] = realtime
        snap["realtime_note"] = (
            f"实时行情截至 {realtime['tradedate']} {realtime['ticktime']}，"
            f"当前价 {realtime['price']:.0f}，涨跌 {realtime['change_pct']}"
        )
    if intraday:
        snap["intraday"] = intraday
    return snap


# ── Web search (DuckDuckGo, no API key needed) ────────────────────────────────

def web_search(query: str, max_results: int = 6) -> str:
    """Search DuckDuckGo and return formatted plain-text results."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, region="cn-zh", timelimit="m"))
        if not results:
            # Retry without time limit
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, region="cn-zh"))
        if not results:
            return "未找到相关结果"
        parts = []
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] {r['title']}\n{r['body'][:350]}\n来源: {r['href']}")
        return "\n\n".join(parts)
    except Exception as exc:
        return f"搜索失败: {exc}"


def clean_text(value: str | None) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_relevant_news(item: dict[str, str]) -> bool:
    text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
    keywords = [
        # 棕榈油本体
        "棕榈", "palm",
        # 产地与主要参与国
        "malaysia", "indonesia", "马来", "印尼", "india", "印度", "mpob",
        # 替代/联动油脂 + 大豆本体（Y0 关注）
        "油脂", "豆油", "大豆", "soybean", "soyoil", "rapeseed", "菜油", "葵花籽油", "sunflower",
        "椰子油", "coconut", "vegetable oil", "edible oil",
        # 大豆产地 / 报告（Y0 关注）
        "usda", "cbot", "argentina", "brazil", "阿根廷", "巴西",
        # 能源 / 生物柴油（影响棕榈油需求）
        "原油", "crude", "brent", "wti", "diesel", "biofuel", "biodiesel", "生物柴油",
        # 大宗商品 / 政策（state-backed agencies, raw materials, etc.）
        "大宗", "commodity", "commodities", "出口", "export", "进口", "import",
        "关税", "tariff", "tax", "补贴", "subsidy", "禁令", "ban", "配额",
        "原材料", "raw material", "raw materials", "state-backed", "state-owned",
        "国营", "国有", "管理机构", "agency", "danantara", "bumn",
        "矿产", "mineral", "镍", "nickel", "锡", "tin", "煤炭", "coal", "铜", "copper",
        # 天气（影响产量）
        "厄尔尼诺", "拉尼娜", "el nino", "el niño", "la nina", "la niña",
        "drought", "干旱", "雨季", "monsoon",
        # 期货 / 交易所
        "期货", "futures", "dce", "大连", "bursa", "fcpo",
        # 汇率（影响以美元计价的大宗商品）
        "ringgit", "rupiah", "usd", "美元", "汇率",
    ]
    return any(keyword in text for keyword in keywords)


def parse_google_news_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return ""


def fetch_google_news(query: str, max_results: int = 8) -> list[dict[str, str]]:
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query + ' when:7d')}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    )
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    results: list[dict[str, str]] = []
    for node in root.findall("./channel/item")[:max_results]:
        source_node = node.find("source")
        item = {
            "title": clean_text(node.findtext("title")),
            "url": clean_text(node.findtext("link")),
            "source": clean_text(source_node.text if source_node is not None else ""),
            "snippet": clean_text(node.findtext("description")),
            "published_at_utc": parse_google_news_date(node.findtext("pubDate")),
            "query": query,
        }
        if item["title"] and item["url"] and is_relevant_news(item):
            results.append(item)
    return results


def fetch_news_snapshot(queries: list[str], out_dir: Path = DATA_DIR) -> dict[str, object]:
    articles: list[dict[str, str]] = []

    # Fan out all Google News queries in parallel — each is an independent
    # HTTP GET, so 8 workers cuts ~30s serial down to ~4s wall clock.
    from concurrent.futures import ThreadPoolExecutor, as_completed
    seen_urls: set[str] = set()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_google_news, q): q for q in queries}
        for fut in as_completed(futures):
            q = futures[fut]
            try:
                for item in fut.result():
                    if item["url"] in seen_urls:
                        continue
                    seen_urls.add(item["url"])
                    articles.append(item)
            except Exception as exc:
                print(f"Google News snapshot failed for {q}: {exc}")

    if len(articles) < 4:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                for query in queries:
                    if len(articles) >= 12:
                        break
                    for item in ddgs.text(query, max_results=5, region="cn-zh", timelimit="w"):
                        url = item.get("href", "")
                        if not url or any(existing["url"] == url for existing in articles):
                            continue
                        article = {
                            "title": item.get("title", ""),
                            "url": url,
                            "source": url.split("/")[2] if "://" in url else "",
                            "snippet": item.get("body", ""),
                            "published_at_utc": "",
                            "query": query,
                        }
                        if is_relevant_news(article):
                            articles.append(article)
        except Exception as exc:
            print(f"DuckDuckGo news snapshot failed: {exc}")

    snapshot = {
        "source": "Google News RSS + DuckDuckGo fallback",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "articles": articles[:12],
        "status": "ok" if articles else "empty",
    }
    (out_dir / "news_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return snapshot


def news_snapshot_to_text(snapshot: dict[str, object]) -> str:
    articles = snapshot.get("articles") or []
    if not isinstance(articles, list) or not articles:
        return ""
    lines = []
    for index, item in enumerate(articles[:10], 1):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"[{index}] {item.get('title','')}\n"
            f"来源: {item.get('source','')}\n"
            f"发布时间UTC: {item.get('published_at_utc','')}\n"
            f"URL: {item.get('url','')}\n"
            f"摘要: {item.get('snippet','')}"
        )
    return "\n\n".join(lines)


# ── Step 1: Fetch news with DeepSeek function-calling ─────────────────────────

def fetch_news_raw(api_key: str, snapshot: dict, profile_name: str = "棕榈油") -> str:
    """
    DeepSeek searches the web (up to MAX_SEARCH_ROUNDS times) and returns a
    detailed plain-text digest of recent {profile_name} news WITH source URLs
    so the analysis step can build proper article cards.
    Returns "" on failure so the caller can skip the news block gracefully.
    """
    # This tool-calling loop is only a fallback; the fast path is
    # news_snapshot_to_text() which uses pre-fetched articles. Keeping it
    # short here trims worst-case runtime when the snapshot is empty.
    MAX_SEARCH_ROUNDS = 4

    tool_def = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "搜索互联网获取最新新闻、价格资讯",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"}
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    latest_date = snapshot.get("latest_date", "")
    messages: list[dict] = [
        {
            "role": "system",
            "content": (
                f"你是商品期货市场资讯员。请调用 web_search 多次搜索影响{profile_name}价格的"
                "所有相关资讯（最多 7 次搜索）。搜索方向要广泛覆盖：\n"
                f"1) {profile_name}本体——主产地产量与库存、大连主力合约盘面；\n"
                "2) 主产国政策——出口关税、禁令、配额、补贴；\n"
                "3) 主要买家需求——大宗采购、进口关税、库存变化；\n"
                "4) 原油与生物柴油——能源价格与生柴掺混政策的传导；\n"
                "5) 替代油脂——棕榈油、豆油、菜油、葵花油、椰子油的价格联动；\n"
                "6) 天气——厄尔尼诺/拉尼娜、干旱、雨季对产量的影响；\n"
                "7) 汇率——相关产油国货币与美元走势；\n"
                "8) 宏观——中国进口数据、CBOT 大豆、USDA 报告、海运费、地缘冲突。\n\n"
                "完成搜索后，请输出 8–15 条详细新闻条目（覆盖以上至少 5 个方向），"
                "每条格式严格如下（保留原始URL）：\n"
                "【标题】新闻标题\n"
                "【来源】网站/媒体名称\n"
                "【URL】原文链接\n"
                "【摘要】3–5句详细摘要，说明具体数据/事件及原因\n"
                f"【影响】利多/利空/中性，并解释对{profile_name}的传导逻辑\n"
                "---\n"
                "不要省略URL。如果搜索结果里有链接，必须原样保留。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"分析日期：{latest_date}。请广泛搜索并详细整理近期影响大连{profile_name}期货价格的"
                "所有重要新闻，不要只看本身——大宗商品政策、原油价格、生物柴油、"
                "主要买家采购、替代油脂、产区天气、相关汇率都要覆盖。"
                "每条新闻必须有具体数据（产量、价格、政策名称、百分比等）和来源URL。"
            ),
        },
    ]

    search_count = 0
    for _round in range(MAX_SEARCH_ROUNDS + 3):
        try:
            tool_choice = "none" if search_count >= MAX_SEARCH_ROUNDS else "auto"
            resp = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "tools": tool_def,
                    "tool_choice": tool_choice,
                    "temperature": 0.2,
                    "max_tokens": 5000,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]
            messages.append(msg)

            if choice["finish_reason"] == "tool_calls":
                for tc in msg.get("tool_calls", []):
                    fn_args = json.loads(tc["function"]["arguments"])
                    query = fn_args.get("query", f"{profile_name}最新消息")
                    print(f"  [web_search #{search_count + 1}] {query}")
                    search_text = web_search(query, max_results=8)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": search_text,
                        }
                    )
                    search_count += 1
            else:
                content = msg.get("content", "")
                if not content or len(content) < 50:
                    return ""
                return content

        except Exception as exc:
            print(f"  [news fetch error] {exc}")
            return ""

    return ""


# ── Step 2: Technical + fundamental analysis → JSON ───────────────────────────

def normalize_ai_analysis(parsed: dict, snapshot: dict) -> dict:
    def item_to_str(x) -> str:
        if isinstance(x, str):
            return x
        if isinstance(x, dict):
            text = x.get("news") or x.get("content") or x.get("text") or x.get("item") or ""
            impact = x.get("impact") or x.get("direction") or x.get("bias") or ""
            return f"{text}（{impact}）" if impact else text or str(x)
        return str(x)

    def to_str_list(val) -> list[str]:
        if isinstance(val, str):
            return [val] if val.strip() else []
        if isinstance(val, list):
            return [item_to_str(x) for x in val if x]
        return []

    def normalize_articles(val) -> list[dict]:
        """Keep news_articles as a list of clean dicts with known keys."""
        if not isinstance(val, list):
            return []
        result = []
        for x in val:
            if isinstance(x, dict):
                result.append({
                    "title":   str(x.get("title")   or x.get("标题")   or ""),
                    "source":  str(x.get("source")  or x.get("来源")   or x.get("media") or ""),
                    "url":     str(x.get("url")     or x.get("link")   or x.get("href")  or x.get("URL") or ""),
                    "detail":  str(x.get("detail")  or x.get("summary") or x.get("摘要") or x.get("content") or ""),
                    "impact":  str(x.get("impact")  or x.get("影响")   or x.get("direction") or "中性"),
                })
            elif isinstance(x, str) and x.strip():
                result.append({"title": x, "source": "", "url": "", "detail": "", "impact": "中性"})
        return result

    watch_levels = parsed.get("watch_levels", {})
    if not isinstance(watch_levels, dict):
        watch_levels = {}
    support = watch_levels.get("support", snapshot["low20"])
    resistance = watch_levels.get("resistance", snapshot["high20"])
    strategy = parsed.get("intraday_strategy", {})
    if not isinstance(strategy, dict):
        strategy = {}
    decision_frame = parsed.get("decision_frame", {})
    if not isinstance(decision_frame, dict):
        decision_frame = {}

    def normalize_case(value: object) -> dict[str, object]:
        case = value if isinstance(value, dict) else {}
        raw_targets = case.get("targets", [])
        if isinstance(raw_targets, (str, int, float)):
            raw_targets = [raw_targets]
        targets = [str(item) for item in raw_targets[:3]] if isinstance(raw_targets, list) else []
        return {
            "trigger": str(case.get("trigger", "等待确认")),
            "entry_zone": str(case.get("entry_zone", "未给出")),
            "stop": str(case.get("stop", "未给出")),
            "targets": targets,
            "invalidation": str(case.get("invalidation", "未给出")),
            "risk_reward": str(case.get("risk_reward", "未计算")),
        }

    try:
        confidence = max(0, min(100, int(float(decision_frame.get("confidence", 0)))))
    except (TypeError, ValueError):
        confidence = 0

    return {
        "summary":       str(parsed.get("summary", "暂无 AI 摘要。")),
        "bias":          str(parsed.get("bias", "未判断")),
        "analysis":      to_str_list(parsed.get("analysis")),
        "intraday_strategy": {
            "bias": str(strategy.get("bias", parsed.get("bias", "未判断"))),
            "entry": str(strategy.get("entry", "等待1小时/2小时K线确认后再行动")),
            "stop": str(strategy.get("stop", "未给出")),
            "take_profit": str(strategy.get("take_profit", "未给出")),
            "invalidation": str(strategy.get("invalidation", "未给出")),
            "notes": str(strategy.get("notes", "仅供研究，不构成投资建议")),
        },
        "decision_frame": {
            "confidence": confidence,
            "regime": str(decision_frame.get("regime", "未判断")),
            "edge": str(decision_frame.get("edge", "暂无明确优势")),
            "no_trade_condition": str(decision_frame.get("no_trade_condition", "数据或方向不足时观望")),
            "long_case": normalize_case(decision_frame.get("long_case")),
            "short_case": normalize_case(decision_frame.get("short_case")),
            "event_risks": to_str_list(decision_frame.get("event_risks")),
            "data_limits": to_str_list(decision_frame.get("data_limits")),
        },
        "news_impact":   to_str_list(parsed.get("news_impact")),   # short bullet strings
        "news_articles": normalize_articles(parsed.get("news_articles", [])),  # rich cards
        "watch_levels":  {"support": float(support), "resistance": float(resistance)},
        "risk_note":     str(parsed.get("risk_note", "本分析仅供行情研究，不构成投资建议。")),
    }


def fallback_ai_analysis(snapshot: dict, reason: str) -> dict:
    rt = snapshot.get("realtime")
    first_line = (
        f"实时价 {rt['price']:.0f}（{snapshot['realtime_note']}），"
        f"最新日线收盘 {snapshot['close']:.0f}，日涨跌 {snapshot['change_pct']}。"
        if rt else
        f"最新日线收盘 {snapshot['close']:.0f}，日涨跌 {snapshot['change_pct']}。"
    )
    return {
        "source": "fallback-rule-analysis",
        "model": None,
        "status": "fallback",
        "error": reason,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest_date": snapshot["latest_date"],
        "summary": "DeepSeek 未生成分析，当前显示规则分析摘要。",
        "bias": "等待AI",
        "analysis": [
            first_line,
            f"MA10/MA20/MA60 分别为 {snapshot['ma10']:.0f}/{snapshot['ma20']:.0f}/{snapshot['ma60']:.0f}。",
            f"20日区间支撑压力为 {snapshot['low20']:.0f}-{snapshot['high20']:.0f}。",
        ],
        "intraday_strategy": {
            "bias": "等待AI",
            "entry": "等待手动触发 DeepSeek 后生成1小时/2小时策略",
            "stop": "未给出",
            "take_profit": "未给出",
            "invalidation": "未给出",
            "notes": "当前为规则备用分析",
        },
        "decision_frame": {
            "confidence": 0,
            "regime": "数据不足",
            "edge": "等待 DeepSeek",
            "no_trade_condition": "AI 未生成时不把规则摘要当作独立交易依据",
            "long_case": {},
            "short_case": {},
            "event_risks": [],
            "data_limits": ["当前为备用规则分析"],
        },
        "news_impact": [],
        "news_articles": [],
        "watch_levels": {"support": snapshot["low20"], "resistance": snapshot["high20"]},
        "risk_note": "本分析仅供行情研究，不构成投资建议。",
    }


def generate_ai_analysis(snapshot: dict, news_summary: str = "", profile_name: str = "棕榈油", symbol: str = "P0") -> dict:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return fallback_ai_analysis(snapshot, "DEEPSEEK_API_KEY is not configured")

    has_realtime = bool(snapshot.get("realtime"))
    realtime_instruction = (
        "数据中包含字段 realtime（实时行情），请在分析中明确引用当前实时价格，"
        "并结合实时价与均线、支撑压力的位置关系给出判断。"
        if has_realtime else
        "数据中无实时行情，请基于最新日线收盘价分析。"
    )
    intraday_instruction = (
        "数据中包含 intraday.one_hour / two_hour / four_hour。"
        "请按 **1小时 / 4小时 / 日线** 三个核心尺度做多周期共振分析（2小时数据可作为过渡参考）。"
        "对每个尺度都要说：布林通道上/中/下轨位置、当前价在通道中的位置、带宽变化、是否突破或回归中轨。"
        "然后综合三个尺度给出适合下一个交易时段的策略。"
        "\n\n中国大商所 P0/Y0 交易时段（北京时间，工作日）：\n"
        "- 早盘 09:00–11:30\n"
        "- 午盘 13:30–15:00\n"
        "- 夜盘 21:00–23:00\n"
        "策略推荐时请指明适用哪个时段（如「今晚夜盘 21:00 开盘后关注...」）。"
        if snapshot.get("intraday") else
        "数据中无 1小时/2小时/4小时 K线，请不要声称进行了小时线分析。"
    )

    has_news = bool(news_summary and len(news_summary) > 60)
    news_block = (
        f"\n\n【近期市场舆情原始搜索结果（含来源URL）】\n{news_summary}\n"
        if has_news else ""
    )

    if has_news:
        news_instructions = (
            "4) news_impact 数组：4–8 条字符串，每条 2–4 句详细分析，"
            f"说明具体数据/事件、逻辑链条及对{profile_name}价格的影响方向（以[利多]/[利空]/[中性]开头）；\n"
            "5) news_articles 数组：从上方舆情原始结果中提取 6–10 条新闻，"
            "每条是包含以下字段的 JSON 对象：\n"
            '   {"title":"新闻标题","source":"来源媒体名","url":"原文链接（必须是http开头的完整URL）",'
            '"detail":"3–5句详细摘要，含具体数据","impact":"利多/利空/中性"}\n'
            "   URL必须原样保留搜索结果中的真实链接，不得编造；\n"
        )
    else:
        news_instructions = (
            "4) news_impact 数组：留空 []；\n"
            "5) news_articles 数组：留空 []；\n"
        )

    prompt_content = (
        f"请基于以下大连商品交易所{profile_name} {symbol} 连续合约实时行情、1小时/2小时/4小时K线、日线数据及市场舆情做综合中文分析。"
        f"{realtime_instruction}{intraday_instruction}"
        f"{news_block}"
        "要求：\n"
        "1) 先给日内短线判断（结合 1H + 4H），再给日线级别背景，不能只做中长期分析；\n"
        "2) bias 字段给出偏多/震荡/偏空；\n"
        "3) analysis 数组：6–8 条技术面要点，必须包含 **1小时布林、4小时布林、日线布林/均线、实时价位置、趋势、量能、支撑压力**，每条 2–3 句；\n"
        "4) intraday_strategy 对象：必须包含 bias, entry, stop, take_profit, invalidation, notes 六个字段，给出以 1小时 + 4小时 尺度为主的日内策略，明确说明适用哪个交易时段（早盘 09:00-11:30 / 午盘 13:30-15:00 / 夜盘 21:00-23:00）；\n"
        f"{news_instructions}"
        "6) watch_levels 包含数字 support 和 resistance；\n"
        "7) decision_frame 对象必须包含：confidence(0-100，表示证据强度而非胜率)、regime、edge、no_trade_condition、long_case、short_case、event_risks、data_limits。"
        "long_case 和 short_case 都必须包含 trigger, entry_zone, stop, targets, invalidation, risk_reward；如果首目标盈亏比低于1.5，必须明确写入 no_trade_condition，不得硬给方向；\n"
        "8) P0/Y0 是连续合约分析口径，不是可直接下单的具体月份合约。必须提醒实际执行前核对主力月份、换月价差、流动性和保证金；\n"
        "9) 舆情只能引用给定搜索结果，区分事实、市场预期和你的推断；禁止编造数字、发布时间或来源；\n"
        "10) 强调不构成投资建议；\n"
        "11) 只输出 JSON；字段：summary, bias, analysis, intraday_strategy, decision_frame, news_impact, news_articles, watch_levels, risk_note。\n"
        f"\n数据:\n{json.dumps(snapshot, ensure_ascii=False)}"
    )

    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是机构级中文油脂期货风险分析助手。先验证数据时效和证据，再讨论方向；"
                        "不确定时明确观望，不把连续合约当作可直接下单的具体月份合约，"
                        "不编造新闻、价格、胜率或概率，只基于用户给出的行情和舆情作答。"
                    ),
                },
                {"role": "user", "content": prompt_content},
            ],
            "temperature": 0.2,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    resp.raise_for_status()
    resp_json = resp.json()
    choice = resp_json["choices"][0]
    content = choice["message"]["content"]
    # Defensive: if DeepSeek truncated the response (finish_reason='length'),
    # json.loads will throw a cryptic 'Unterminated string' error. Surface a
    # cleaner error so we know to bump max_tokens rather than debug our parser.
    if choice.get("finish_reason") == "length":
        raise RuntimeError(
            f"DeepSeek output truncated at max_tokens (finish_reason=length). "
            f"Content length: {len(content)} chars. Bump max_tokens."
        )
    parsed = normalize_ai_analysis(json.loads(content), snapshot)
    parsed.update(
        {
            "source": "DeepSeek API",
            "model": "deepseek-chat",
            "status": "ok",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "latest_date": snapshot["latest_date"],
            "realtime_price": snapshot["realtime"]["price"] if has_realtime else None,
            "realtime_note": snapshot.get("realtime_note"),
            "news_summary": news_summary,
            "symbol": symbol,
            "instrument_name": profile_name,
        }
    )
    return parsed


# ── Night session live bar (only during 21:00–23:59 Beijing) ─────────────────

def get_live_bar(last_daily_date: str, symbol: str = "P0") -> dict | None:
    """Fetch night session minute data and return a preliminary next-day bar."""
    cst = timezone(timedelta(hours=8))
    now_cst = datetime.now(cst)
    if not (21 <= now_cst.hour <= 23):
        return None
    try:
        df = ak.futures_zh_minute_sina(symbol=symbol, period="60")
    except Exception:
        return None
    if df is None or df.empty:
        return None

    night_start = f"{last_daily_date} 21:00:00"
    night_end = f"{last_daily_date} 23:59:59"
    df["dt_str"] = df["datetime"].astype(str)
    night = df[(df["dt_str"] >= night_start) & (df["dt_str"] <= night_end)]
    if night.empty:
        return None

    last = datetime.strptime(last_daily_date, "%Y-%m-%d").date()
    next_day = last + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    as_of = str(night["datetime"].iloc[-1])[:16]
    return {
        "date": str(next_day),
        "open": float(night["open"].iloc[0]),
        "high": float(night["high"].max()),
        "low": float(night["low"].min()),
        "close": float(night["close"].iloc[-1]),
        "volume": int(night["volume"].sum()),
        "preliminary": True,
        "session_note": f"夜盘进行中（截至 {as_of}）",
    }


def should_run_ai_analysis() -> bool:
    return os.getenv("RUN_AI_ANALYSIS", "").strip().lower() in {"1", "true", "yes", "on"}


# ── Daily fetch with retry ───────────────────────────────────────────────────

def fetch_daily_with_retry(symbol: str = "P0", attempts: int = 4, backoff: int = 20):
    """Sina's futures API blocks GitHub Actions IPs intermittently. Retry with
    linear backoff so a single transient timeout doesn't fail the workflow."""
    import time
    last_exc: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            df = ak.futures_zh_daily_sina(symbol=symbol)
            if df is not None and not df.empty:
                if i > 1:
                    print(f"Daily fetch succeeded on attempt {i}/{attempts}")
                return df
            last_exc = RuntimeError("empty dataframe")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"Daily fetch attempt {i}/{attempts} failed: {type(exc).__name__}: {exc}")
        if i < attempts:
            wait = backoff * i  # 20s, 40s, 60s
            print(f"  retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"AKShare futures_zh_daily_sina failed after {attempts} attempts: {last_exc}")


# Candidate OI column names in AKShare's Sina daily output — order matters,
# first match wins. AKShare has used both English 'hold' (matching the minute
# feed) and Chinese '持仓' / '持仓量' across versions.
OI_COLUMN_CANDIDATES = ("hold", "open_interest", "持仓量", "持仓")


def detect_oi_column(df) -> str | None:
    """Return the name of the OI column in df, or None if not present."""
    for candidate in OI_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate
    return None


# ── Per-symbol pipeline ──────────────────────────────────────────────────────

def run_profile(symbol: str) -> None:
    """Run the full data + AI pipeline for one symbol, writing all outputs to
    DATA_DIR / PROFILES[symbol]["dir"]."""
    profile = PROFILES[symbol]
    name = profile["name"]
    out_dir = DATA_DIR / profile["dir"]
    out_dir.mkdir(exist_ok=True, parents=True)

    df = fetch_daily_with_retry(symbol=symbol)
    if df.empty:
        raise RuntimeError(f"AKShare returned empty {symbol} daily data")

    # F2: include open interest (持仓量) after volume when the daily feed has it.
    oi_col = detect_oi_column(df)
    if oi_col is not None:
        export = df[["date", "open", "high", "low", "close", "volume", oi_col]].copy()
        export = export.rename(columns={oi_col: "open_interest"})
    else:
        print(f"OI column not found in daily df; columns={list(df.columns)}")
        export = df[["date", "open", "high", "low", "close", "volume"]].copy()
    export = sanitize_ohlc_frame(export, "date", f"{symbol} daily")
    if export is None or export.empty:
        raise RuntimeError(f"{symbol} daily data is empty after OHLC validation")
    output = out_dir / "daily.csv"
    export.to_csv(output, index=False)

    # Intraday + news + realtime are best-effort AND independent of each other
    # and the daily fetch — run them in parallel. A transient Sina/DDG hiccup
    # shouldn't fail the whole workflow.
    from concurrent.futures import ThreadPoolExecutor

    def _safe(fn, fallback, label):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            print(f"[{symbol}] {label} failed (soft-skip): {type(exc).__name__}: {exc}")
            return fallback

    with ThreadPoolExecutor(max_workers=3) as pool:
        f_intraday = pool.submit(
            _safe,
            lambda: fetch_intraday_bundle(symbol=symbol, out_dir=out_dir),
            {"updated_at_utc": None, "one_hour": None, "two_hour": None, "four_hour": None},
            "Intraday fetch",
        )
        f_news = pool.submit(
            _safe,
            lambda: fetch_news_snapshot(profile["news_queries"], out_dir=out_dir),
            {"updated_at_utc": None, "articles": []},
            "News snapshot fetch",
        )
        f_realtime = pool.submit(
            _safe,
            lambda: get_realtime_quote_sina(symbol=symbol),
            None,
            "Realtime quote fetch",
        )
        intraday = f_intraday.result()
        news_snapshot = f_news.result()
        realtime = f_realtime.result()

    latest = export.tail(1).iloc[0]
    meta = {
        "source": "AKShare futures_zh_daily_sina",
        "symbol": symbol,
        "market": f"DCE {name} continuous contract",
        "instrument_name": f"{name}连续",
        "rows": int(len(export)),
        "latest_date": str(latest["date"]),
        "latest_close": float(latest["close"]),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "live_bar": get_live_bar(str(latest["date"]), symbol=symbol),
        "intraday_updated_at_utc": intraday.get("updated_at_utc"),
        "news_updated_at_utc": news_snapshot.get("updated_at_utc"),
    }

    # F2: attach open-interest fields when available.
    if oi_col is not None and len(export) >= 2:
        try:
            latest_oi = int(float(latest["open_interest"]))
            prev_oi = int(float(export.tail(2).iloc[0]["open_interest"]))
            oi_change = latest_oi - prev_oi
            oi_change_pct = (oi_change / prev_oi) if prev_oi else 0
            meta["latest_open_interest"] = latest_oi
            meta["prev_open_interest"] = prev_oi
            meta["oi_change"] = oi_change
            meta["oi_change_pct"] = pct(oi_change_pct)
        except (KeyError, ValueError, TypeError) as exc:
            print(f"[{symbol}] OI meta compute failed: {type(exc).__name__}: {exc}")
    (out_dir / "source_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if should_run_ai_analysis():
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

        # Real-time quote was already fetched in parallel above.
        if realtime:
            print(f"[{symbol}] Real-time quote: {realtime['price']} @ {realtime['tradedate']} {realtime['ticktime']}")
        else:
            print(f"[{symbol}] Real-time quote: unavailable, using daily close only")

        snapshot = daily_snapshot(export, realtime, intraday)

        # Step 1 – detailed news via web search (fallback path only)
        news_summary = news_snapshot_to_text(news_snapshot)
        if api_key and not news_summary:
            print(f"[{symbol}] Fetching market news via DeepSeek web search...")
            news_summary = fetch_news_raw(api_key, snapshot, profile_name=name)
            preview = news_summary[:150].replace("\n", " ")
            print(f"[{symbol}] News raw preview: {preview}...")
        else:
            print(f"[{symbol}] News snapshot articles: {len(news_snapshot.get('articles') or [])}")

        # Step 2 – full analysis
        try:
            ai_analysis = generate_ai_analysis(
                snapshot, news_summary, profile_name=name, symbol=symbol
            )
        except Exception as exc:  # noqa: BLE001
            ai_analysis = fallback_ai_analysis(snapshot, f"{type(exc).__name__}: {exc}")

        (out_dir / "ai_analysis.json").write_text(
            json.dumps(ai_analysis, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[{symbol}] AI analysis: {ai_analysis['status']}")

        # F3: append this analysis to the per-symbol history
        # F3+F7: re-grade the history against current price
        # Skip archiving fallback entries — they carry bias='等待AI' (bias_sign=0)
        # and would pollute the accuracy score with fake neutral outcomes.
        try:
            price_for_history = (
                float(realtime["price"]) if realtime else float(snapshot["close"])
            )
            if ai_analysis.get("status") == "ok":
                archive_ai_history(out_dir, ai_analysis, price_for_history)
            else:
                print(f"[{symbol}] AI history skipped for status={ai_analysis.get('status')}")
            acc = compute_ai_accuracy(out_dir, price_for_history)
            print(
                f"[{symbol}] AI accuracy: evaluated={acc['total_evaluated']} "
                f"hit_rate={acc['recent_hit_rate']} warn={acc['warning_low_accuracy']}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[{symbol}] AI history/accuracy failed (soft-skip): {type(exc).__name__}: {exc}")
    else:
        print(f"[{symbol}] AI analysis: skipped; set RUN_AI_ANALYSIS=true to generate")

    print(f"[{symbol}] Updated {output}")
    print(f"[{symbol}] Rows: {len(export)}")
    print(f"[{symbol}] Latest: {latest['date']} close={latest['close']}")
    print(f"[{symbol}] Intraday 1H: {bool(intraday.get('one_hour'))}, 2H: {bool(intraday.get('two_hour'))}, 4H: {bool(intraday.get('four_hour'))}")
    print(f"[{symbol}] News articles: {len(news_snapshot.get('articles') or [])}")


if __name__ == "__main__":
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed
    symbols_env = os.getenv("SYMBOLS", "P0,Y0")
    symbols = [s.strip() for s in symbols_env.split(",") if s.strip() and s.strip() in PROFILES]
    if not symbols:
        print("No valid symbols to run")
        sys.exit(1)

    # F4: shared overseas snapshot — one HTTP call to akshare covers all three
    # tickers (FCPO, CBOT-BO, Brent), same file consumed by both P0/Y0 UIs.
    # Best-effort: log & continue if akshare 429s or the runner is offline.
    try:
        fetch_overseas_snapshot(out_dir=DATA_DIR)
    except Exception as exc:  # noqa: BLE001
        print(f"[overseas] top-level fetch failed (soft-skip): {type(exc).__name__}: {exc}")

    # Run both profiles in parallel — with DeepSeek included, sequential runs
    # take ~4 min but the two profiles' Sina + AKShare + DeepSeek calls are
    # fully independent. Parallel wall time ≈ max(P0, Y0) ≈ half.
    failed: list[str] = []
    with ThreadPoolExecutor(max_workers=len(symbols)) as pool:
        futures = {pool.submit(run_profile, sym): sym for sym in symbols}
        for fut in as_completed(futures):
            sym = futures[fut]
            try:
                fut.result()
                print(f"[{sym}] pipeline done")
            except Exception as exc:  # noqa: BLE001
                print(f"[{sym}] pipeline failed: {type(exc).__name__}: {exc}")
                failed.append(sym)

    if failed:
        print(f"\n=== FAILED: {failed} ===")
        sys.exit(1)
