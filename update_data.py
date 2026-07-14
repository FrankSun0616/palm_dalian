from __future__ import annotations

import json
import os
import html
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

try:
    import akshare as ak
except ModuleNotFoundError:
    # The dedicated AI workflow only reads cached files and intentionally
    # installs no AKShare dependency.
    ak = None
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DEEPSEEK_MODEL = "deepseek-v4-pro"
DEEPSEEK_THINKING = {"type": "enabled"}
DEEPSEEK_REASONING_EFFORT = "high"
DAILY_FETCH_TIMEOUT_SECONDS = max(10, int(os.getenv("DAILY_FETCH_TIMEOUT_SECONDS", "30")))


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
AI_ACCURACY_HORIZON_BARS = 4
AI_ACCURACY_METHOD = "fixed_4_completed_1h_bars_v2"
AI_ACCURACY_WINDOW = 20
AI_ACCURACY_MOVE_THRESHOLD = 0.005  # 0.5%
AI_ACCURACY_LOW_THRESHOLD = 0.40
AI_ACCURACY_LOW_MIN_EVAL = 10
BEIJING_TZ = ZoneInfo("Asia/Shanghai")


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
        "model": ai_analysis.get("model"),
        "integrity_score": _num((ai_analysis.get("integrity") or {}).get("score")),
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


def _parse_generated_beijing(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00") if text.endswith("Z") else text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(BEIJING_TZ).replace(tzinfo=None)


def _load_accuracy_bars(profile_dir: Path) -> list[dict[str, object]]:
    path = profile_dir / "intraday_1h.csv"
    try:
        frame = pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return []
    if "datetime" not in frame.columns or "close" not in frame.columns:
        return []
    frame = frame[["datetime", "close"]].copy()
    frame["datetime"] = pd.to_datetime(frame["datetime"], errors="coerce")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna().sort_values("datetime").drop_duplicates("datetime", keep="last")
    return [
        {"datetime": row.datetime.to_pydatetime(), "close": float(row.close)}
        for row in frame.itertuples(index=False)
    ]


def _grade_fixed_horizon(entry: dict, outcome_price: float) -> tuple[str, float] | None:
    try:
        price_at = float(entry.get("price_at"))
        price_out = float(outcome_price)
    except (TypeError, ValueError):
        return None
    if not price_at:
        return None
    move = (price_out - price_at) / price_at
    sign = int(entry.get("bias_sign") or 0)
    thr = AI_ACCURACY_MOVE_THRESHOLD
    if sign > 0:
        if move > thr:
            return "hit", move
        if move < -thr:
            return "miss", move
        return "flat", move
    if sign < 0:
        if move < -thr:
            return "hit", move
        if move > thr:
            return "miss", move
        return "flat", move
    return ("hit" if abs(move) <= thr else "miss"), move


def compute_ai_accuracy(profile_dir, current_price: float | None = None) -> dict:
    """Grade each independent AI forecast at a fixed four completed 1H-bar horizon."""
    profile_dir = Path(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    acc_path = profile_dir / "ai_accuracy.json"
    hist = _load_json(profile_dir / "ai_history.json")
    entries = hist.get("entries") if isinstance(hist, dict) else None
    if not isinstance(entries, list):
        entries = []

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bars = _load_accuracy_bars(profile_dir)
    candidates: dict[str, dict[str, object]] = {}
    pending = 0
    unmatched = 0
    eligible = 0
    for entry in entries:
        generated = _parse_generated_beijing(entry.get("generated_at_utc"))
        if generated is None or entry.get("price_at") in (None, 0):
            unmatched += 1
            continue
        start_index = next(
            (index for index, bar in enumerate(bars) if bar["datetime"] > generated),
            None,
        )
        if start_index is None:
            pending += 1
            continue
        start_time = bars[start_index]["datetime"]
        if (start_time - generated).total_seconds() > 96 * 3600:
            unmatched += 1
            continue
        target_index = start_index + AI_ACCURACY_HORIZON_BARS - 1
        if target_index >= len(bars):
            pending += 1
            continue
        eligible += 1
        key = start_time.isoformat(sep=" ")
        candidate = {
            "entry": entry,
            "generated": generated,
            "entry_bar_time": key,
            "outcome_bar_time": bars[target_index]["datetime"].isoformat(sep=" "),
            "outcome_price": float(bars[target_index]["close"]),
        }
        existing = candidates.get(key)
        if existing is None or generated > existing["generated"]:
            candidates[key] = candidate

    graded: list[dict[str, object]] = []
    for candidate in sorted(candidates.values(), key=lambda item: item["entry_bar_time"]):
        entry = candidate["entry"]
        grade = _grade_fixed_horizon(entry, candidate["outcome_price"])
        if grade is None:
            unmatched += 1
            continue
        outcome, move = grade
        graded.append({
            "bias": entry.get("bias"),
            "generated_at_utc": entry.get("generated_at_utc"),
            "price_at": entry.get("price_at"),
            "entry_bar_time": candidate["entry_bar_time"],
            "outcome_bar_time": candidate["outcome_bar_time"],
            "outcome_price": candidate["outcome_price"],
            "move_pct": round(move, 6),
            "outcome": outcome,
        })

    scored = [item for item in graded if item["outcome"] in {"hit", "miss"}]
    total_evaluated = len(scored)
    hits = sum(1 for item in scored if item["outcome"] == "hit")
    misses = sum(1 for item in scored if item["outcome"] == "miss")
    flats = sum(1 for item in graded if item["outcome"] == "flat")
    recent = scored[-AI_ACCURACY_WINDOW:]
    recent_hit_rate = (
        sum(1 for item in recent if item["outcome"] == "hit") / len(recent)
        if len(recent) >= AI_HISTORY_MIN_FOR_SCORING
        else None
    )

    warning = bool(
        recent_hit_rate is not None
        and recent_hit_rate < AI_ACCURACY_LOW_THRESHOLD
        and total_evaluated >= AI_ACCURACY_LOW_MIN_EVAL
    )

    result = {
        "updated_at_utc": now_iso,
        "evaluation_method": AI_ACCURACY_METHOD,
        "horizon_bars": AI_ACCURACY_HORIZON_BARS,
        "move_threshold": AI_ACCURACY_MOVE_THRESHOLD,
        "recent_hit_rate": round(recent_hit_rate, 4) if recent_hit_rate is not None else None,
        "total_evaluated": total_evaluated,
        "total_matured": len(graded),
        "hits": hits,
        "misses": misses,
        "neutrals": flats,
        "pending": pending,
        "duplicates_collapsed": max(0, eligible - len(candidates)),
        "unmatched": unmatched,
        "warning_low_accuracy": warning,
        "last_grade": graded[-1] if graded else None,
        "recent_grades": graded[-AI_ACCURACY_WINDOW:],
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
        "contract_prefix": "P",
        "contract_specs": {
            "multiplier": 10,
            "tick_size": 1,
            "price_unit": "元/吨",
            "tick_value": 10,
            "rule_reference": "大商所〔2026〕32号",
            "effective_from": "2026-04-10",
            "source_url": "https://www.dce.com.cn/dce/content/2026/ywggytz/18628268.html",
        },
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
        "contract_prefix": "Y",
        "contract_specs": {
            "multiplier": 10,
            "tick_size": 1,
            "price_unit": "元/吨",
            "tick_value": 10,
            "rule_reference": "大商所〔2026〕32号",
            "effective_from": "2026-04-10",
            "source_url": "https://www.dce.com.cn/dce/content/2026/ywggytz/18628268.html",
        },
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
    "Market_Center.getHQFuturesData?page=1&num=100&sort=position&asc=0&node={node}&base=futures"
)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def fetch_sina_market_board(symbol: str = "P0") -> list[dict]:
    """Return the complete commodity board used by both the live quote and
    continuous-to-tradable-contract mapping."""
    profile = PROFILES.get(symbol)
    if not profile:
        return []
    url = SINA_MARKET_URL_TMPL.format(node=profile["market_node"])
    resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []


def normalize_sina_quote(item: dict | None) -> dict | None:
    if not item:
        return None
    price = _safe_float(item.get("trade"))
    if price <= 0:
        return None
    previous_close = _safe_float(item.get("preclose"))
    previous_settlement = (
        _safe_float(item.get("presettlement"))
        or _safe_float(item.get("prevsettlement"))
    )
    reference = previous_settlement or previous_close
    change = price - reference if reference else 0.0
    change_ratio = change / reference if reference else 0.0
    return {
        "symbol": str(item.get("symbol") or ""),
        "name": str(item.get("name") or ""),
        "price": price,
        "open": _safe_float(item.get("open")),
        "high": _safe_float(item.get("high")),
        "low": _safe_float(item.get("low")),
        "volume": _safe_int(item.get("volume")),
        "open_interest": _safe_int(item.get("position")),
        "prev_close": previous_close,
        "prev_settlement": previous_settlement,
        "reference_price": reference,
        "reference_type": "previous_settlement" if previous_settlement else "previous_close",
        "change": round(change, 4),
        "change_ratio": round(change_ratio, 8),
        "change_pct": pct(change_ratio),
        "bid_price": _safe_float(item.get("bidprice1")),
        "ask_price": _safe_float(item.get("askprice1")),
        "bid_volume": _safe_int(item.get("bidvol1")),
        "ask_volume": _safe_int(item.get("askvol1")),
        "tradedate": str(item.get("tradedate") or ""),
        "ticktime": str(item.get("ticktime") or ""),
    }


def _delivery_month(contract: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"[A-Z]+(\d{2})(\d{2})", contract.upper())
    if not match:
        return None
    year = 2000 + int(match.group(1))
    month = int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return year, month


def _months_to_delivery(contract: str, trading_day: str) -> int | None:
    delivery = _delivery_month(contract)
    if not delivery:
        return None
    try:
        current = datetime.strptime(trading_day[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        current = datetime.now(timezone(timedelta(hours=8)))
    year, month = delivery
    return (year - current.year) * 12 + month - current.month


def build_contract_bridge(
    symbol: str,
    board: list[dict],
    updated_at_utc: str | None = None,
) -> dict | None:
    """Map a continuous symbol to the highest-open-interest tradable month.

    The mapping is evidence-based: specific month contracts are ranked by
    current open interest, then compared with the continuous quote. No expiry
    date is guessed; only month distance and OI migration are used for alerts.
    """
    profile = PROFILES.get(symbol)
    if not profile:
        return None
    prefix = str(profile["contract_prefix"]).upper()
    continuous = normalize_sina_quote(
        next((item for item in board if str(item.get("symbol") or "").upper() == symbol), None)
    )
    contract_pattern = re.compile(rf"^{re.escape(prefix)}\d{{4}}$")
    candidates = [
        quote
        for item in board
        if contract_pattern.fullmatch(str(item.get("symbol") or "").upper())
        for quote in [normalize_sina_quote(item)]
        if quote and quote["open_interest"] > 0
    ]
    candidates.sort(key=lambda item: (item["open_interest"], item["volume"]), reverse=True)
    if not candidates:
        return None

    main = candidates[0]
    secondary = candidates[1] if len(candidates) > 1 else None
    trading_day = str(main.get("tradedate") or (continuous or {}).get("tradedate") or "")
    months_left = _months_to_delivery(main["symbol"], trading_day)
    total_oi = sum(int(item["open_interest"]) for item in candidates)
    main_share = main["open_interest"] / total_oi if total_oi else 0.0
    secondary_ratio = (
        secondary["open_interest"] / main["open_interest"]
        if secondary and main["open_interest"] else 0.0
    )
    spread = secondary["price"] - main["price"] if secondary else None
    spread_ratio = spread / main["price"] if spread is not None and main["price"] else None

    if (months_left is not None and months_left <= 1) or secondary_ratio >= 0.85:
        roll_state = "urgent"
        roll_label = "临近换月"
        roll_reason = "主力临近交割月或次主力持仓已接近主力，执行前必须复核流动性。"
    elif (months_left is not None and months_left <= 2) or secondary_ratio >= 0.50:
        roll_state = "watch"
        roll_label = "监控移仓"
        roll_reason = "主力进入交割月前约两个月或次主力持仓超过主力一半。"
    else:
        roll_state = "stable"
        roll_label = "主力稳定"
        roll_reason = "主力持仓仍明显领先，暂未出现高强度换月信号。"

    month_pressure = 10
    if months_left is not None:
        month_pressure = 100 if months_left <= 0 else 80 if months_left == 1 else 50 if months_left == 2 else 25 if months_left == 3 else 10
    roll_score = round(max(month_pressure, secondary_ratio * 100))
    mapping_verified = bool(
        continuous
        and abs(continuous["price"] - main["price"]) <= float(profile["contract_specs"]["tick_size"])
        and continuous["open_interest"] == main["open_interest"]
    )

    return {
        "source": "Sina Market Center",
        "source_url": SINA_MARKET_URL_TMPL.format(node=profile["market_node"]),
        "symbol": symbol,
        "market": "DCE",
        "updated_at_utc": updated_at_utc or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trading_day": trading_day,
        "market_time": str(main.get("ticktime") or ""),
        "continuous": continuous,
        "main": main,
        "secondary": secondary,
        "mapping_verified": mapping_verified,
        "mapping_note": (
            f"{symbol} 当前行情与 {main['symbol']} 的价格及持仓一致。"
            if mapping_verified else
            f"{symbol} 与最高持仓合约 {main['symbol']} 未完全一致，执行前需人工复核。"
        ),
        "main_open_interest_share": round(main_share, 4),
        "secondary_open_interest_ratio": round(secondary_ratio, 4),
        "secondary_spread": round(spread, 4) if spread is not None else None,
        "secondary_spread_ratio": round(spread_ratio, 6) if spread_ratio is not None else None,
        "spread_structure": (
            "远月升水" if spread is not None and spread > 0 else
            "远月贴水" if spread is not None and spread < 0 else
            "平水"
        ),
        "months_to_delivery_month": months_left,
        "roll_state": roll_state,
        "roll_label": roll_label,
        "roll_score": roll_score,
        "roll_reason": roll_reason,
        "contract_specs": dict(profile["contract_specs"]),
        "candidates": candidates[:6],
    }


def fetch_contract_market_snapshot(symbol: str, out_dir: Path) -> tuple[dict | None, dict | None]:
    board = fetch_sina_market_board(symbol)
    realtime = normalize_sina_quote(
        next((item for item in board if str(item.get("symbol") or "").upper() == symbol), None)
    )
    bridge = build_contract_bridge(symbol, board)
    if bridge:
        (out_dir / "contract_bridge.json").write_text(
            json.dumps(bridge, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return realtime, bridge


def get_realtime_quote_sina(symbol: str = "P0") -> dict | None:
    """Compatibility wrapper for callers that only need the live quote."""
    try:
        board = fetch_sina_market_board(symbol)
        return normalize_sina_quote(
            next((item for item in board if str(item.get("symbol") or "").upper() == symbol), None)
        )
    except Exception:
        return None


# ── Daily snapshot ────────────────────────────────────────────────────────────

def daily_snapshot(
    export,
    realtime: dict | None = None,
    intraday: dict | None = None,
    contract_bridge: dict | None = None,
    model_validation: dict | None = None,
) -> dict:
    generated_utc = datetime.now(timezone.utc)
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
        "analysis_as_of_utc": generated_utc.isoformat(timespec="seconds"),
        "analysis_as_of_beijing": generated_utc.astimezone(BEIJING_TZ).isoformat(timespec="seconds"),
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
        analysis_date = generated_utc.astimezone(BEIJING_TZ).date()
        try:
            quote_label_date = datetime.fromisoformat(str(realtime["tradedate"])).date()
        except (KeyError, TypeError, ValueError):
            quote_label_date = None
        future_label = bool(quote_label_date and quote_label_date > analysis_date)
        snap["realtime_trading_day_label"] = realtime.get("tradedate")
        snap["realtime_tick_time"] = realtime.get("ticktime")
        snap["realtime_label_is_future"] = future_label
        if future_label:
            snap["realtime_note"] = (
                f"盘口交易日归属标签 {realtime['tradedate']}，最新盘口时间 {realtime['ticktime']}"
                f"（不是未来行情），当前价 {realtime['price']:.0f}，涨跌 {realtime['change_pct']}"
            )
        else:
            snap["realtime_note"] = (
                f"实时行情截至 {realtime['tradedate']} {realtime['ticktime']}，"
                f"当前价 {realtime['price']:.0f}，涨跌 {realtime['change_pct']}"
            )
    if intraday:
        snap["intraday"] = intraday
    if contract_bridge:
        snap["contract_bridge"] = contract_bridge
    if model_validation:
        snap["model_validation"] = {
            "strategy_version": model_validation.get("strategy_version"),
            "status": model_validation.get("status"),
            "status_label": model_validation.get("status_label"),
            "holdout": model_validation.get("holdout"),
            "limitations": model_validation.get("limitations"),
        }
    return snap


# ── Fixed-rule model validation (strict next-open execution) ─────────────────

MODEL_STRATEGY_VERSION = "daily-trend-breakout-pullback-v1"
MODEL_HOLDOUT_FRACTION = 0.30
MODEL_MAX_HOLDING_BARS = 12
MODEL_STOP_ATR = 1.25
MODEL_TARGET_R = 2.0
MODEL_SLIPPAGE_POINTS_PER_SIDE = 2.0
MODEL_FEE_YUAN_PER_SIDE = 3.0


def _round_price(value: float, tick_size: float) -> float:
    return round(value / tick_size) * tick_size


def _resolve_trade_bar(
    direction_sign: int,
    bar_open: float,
    bar_high: float,
    bar_low: float,
    stop_price: float,
    target_price: float,
) -> tuple[float, str, bool] | None:
    """Resolve one OHLC bar without assuming an unknowable intrabar path."""
    if direction_sign > 0:
        if bar_open <= stop_price:
            return bar_open, "gap_stop", False
        if bar_open >= target_price:
            return target_price, "gap_target", False
        stop_hit = bar_low <= stop_price
        target_hit = bar_high >= target_price
    else:
        if bar_open >= stop_price:
            return bar_open, "gap_stop", False
        if bar_open <= target_price:
            return target_price, "gap_target", False
        stop_hit = bar_high >= stop_price
        target_hit = bar_low <= target_price
    if stop_hit and target_hit:
        return stop_price, "stop_same_bar", True
    if stop_hit:
        return stop_price, "stop", False
    if target_hit:
        return target_price, "target", False
    return None


def _trade_metrics(trades: list[dict]) -> dict:
    if not trades:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": None,
            "expectancy_r": None,
            "profit_factor": None,
            "max_drawdown_r": None,
            "average_holding_bars": None,
            "long_trades": 0,
            "short_trades": 0,
            "stop_rate": None,
            "target_rate": None,
        }

    results = [float(item["net_r"]) for item in trades]
    wins = sum(value > 0 for value in results)
    losses = sum(value <= 0 for value in results)
    gross_profit = sum(value for value in results if value > 0)
    gross_loss = -sum(value for value in results if value < 0)
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in results:
        equity += value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)
    count = len(trades)
    return {
        "trades": count,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / count, 4),
        "expectancy_r": round(sum(results) / count, 4),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "max_drawdown_r": round(max_drawdown, 4),
        "average_holding_bars": round(sum(int(item["holding_bars"]) for item in trades) / count, 2),
        "long_trades": sum(item["direction"] == "long" for item in trades),
        "short_trades": sum(item["direction"] == "short" for item in trades),
        "stop_rate": round(sum(item["exit_reason"] in {"stop", "gap_stop", "stop_same_bar"} for item in trades) / count, 4),
        "target_rate": round(sum(item["exit_reason"] in {"target", "gap_target"} for item in trades) / count, 4),
        "net_r_total": round(sum(results), 4),
        "best_trade_r": round(max(results), 4),
        "worst_trade_r": round(min(results), 4),
    }


def build_model_validation(export, symbol: str) -> dict:
    """Run one fixed, non-optimized daily model with a chronological holdout.

    A signal can only use the completed close at index t and is filled at the
    next bar's open. Same-bar stop/target collisions are resolved as a stop,
    and adverse opening gaps fill at the open. These rules deliberately bias
    results toward caution instead of flattering the strategy.
    """
    profile = PROFILES[symbol]
    specs = profile["contract_specs"]
    tick_size = float(specs["tick_size"])
    multiplier = float(specs["multiplier"])
    frame = export.copy().reset_index(drop=True)
    frame["date"] = frame["date"].astype(str)
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    close = frame["close"]
    frame["ema20"] = close.ewm(span=20, adjust=False).mean()
    frame["ema60"] = close.ewm(span=60, adjust=False).mean()
    delta = close.diff()
    average_gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    average_loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    relative_strength = average_gain / average_loss.replace(0, pd.NA)
    frame["rsi14"] = 100 - 100 / (1 + relative_strength)
    frame.loc[average_loss.eq(0), "rsi14"] = 100.0

    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["atr14"] = true_range.rolling(14, min_periods=14).mean()
    prior_high20 = frame["high"].rolling(20).max().shift(1)
    prior_low20 = frame["low"].rolling(20).min().shift(1)
    pullback_long = (close > frame["ema20"]) & (close.shift(1) <= frame["ema20"].shift(1))
    pullback_short = (close < frame["ema20"]) & (close.shift(1) >= frame["ema20"].shift(1))
    trend_long = (
        (close > frame["ema60"])
        & (frame["ema20"] > frame["ema60"])
        & (frame["ema20"] > frame["ema20"].shift(5))
    )
    trend_short = (
        (close < frame["ema60"])
        & (frame["ema20"] < frame["ema60"])
        & (frame["ema20"] < frame["ema20"].shift(5))
    )
    signal = pd.Series(0, index=frame.index, dtype="int64")
    signal.loc[
        trend_long
        & ((close > prior_high20) | pullback_long)
        & frame["rsi14"].between(45, 75)
    ] = 1
    signal.loc[
        trend_short
        & ((close < prior_low20) | pullback_short)
        & frame["rsi14"].between(25, 55)
    ] = -1
    frame["signal"] = signal

    split_index = max(61, min(len(frame) - 2, int(len(frame) * (1 - MODEL_HOLDOUT_FRACTION))))
    split_date = str(frame.iloc[split_index]["date"])
    round_trip_cost_points = (
        MODEL_SLIPPAGE_POINTS_PER_SIDE * 2
        + (MODEL_FEE_YUAN_PER_SIDE * 2 / multiplier)
    )
    trades: list[dict] = []
    same_bar_collisions = 0
    cursor = 60
    while cursor < len(frame) - 1:
        direction_sign = int(frame.iloc[cursor]["signal"])
        signal_atr = _safe_float(frame.iloc[cursor]["atr14"])
        if direction_sign == 0 or signal_atr <= 0:
            cursor += 1
            continue

        entry_index = cursor + 1
        entry_price = float(frame.iloc[entry_index]["open"])
        risk_points = max(signal_atr * MODEL_STOP_ATR, tick_size * 8)
        stop_price = _round_price(entry_price - direction_sign * risk_points, tick_size)
        risk_points = abs(entry_price - stop_price)
        if risk_points <= 0:
            cursor += 1
            continue
        target_price = _round_price(
            entry_price + direction_sign * MODEL_TARGET_R * risk_points,
            tick_size,
        )

        last_exit_index = min(entry_index + MODEL_MAX_HOLDING_BARS - 1, len(frame) - 1)
        exit_index = last_exit_index
        exit_price = float(frame.iloc[exit_index]["close"])
        exit_reason = "time_exit"
        for bar_index in range(entry_index, last_exit_index + 1):
            bar = frame.iloc[bar_index]
            resolution = _resolve_trade_bar(
                direction_sign,
                float(bar["open"]),
                float(bar["high"]),
                float(bar["low"]),
                stop_price,
                target_price,
            )
            if resolution:
                exit_price, exit_reason, same_bar_collision = resolution
                exit_index = bar_index
                if same_bar_collision:
                    same_bar_collisions += 1
                break

        gross_points = direction_sign * (exit_price - entry_price)
        gross_r = gross_points / risk_points
        net_r = (gross_points - round_trip_cost_points) / risk_points
        trades.append(
            {
                "signal_index": cursor,
                "entry_index": entry_index,
                "exit_index": exit_index,
                "signal_date": str(frame.iloc[cursor]["date"]),
                "entry_date": str(frame.iloc[entry_index]["date"]),
                "exit_date": str(frame.iloc[exit_index]["date"]),
                "direction": "long" if direction_sign > 0 else "short",
                "entry_price": round(entry_price, 2),
                "stop_price": round(stop_price, 2),
                "target_price": round(target_price, 2),
                "exit_price": round(exit_price, 2),
                "exit_reason": exit_reason,
                "holding_bars": exit_index - entry_index + 1,
                "initial_risk_points": round(risk_points, 2),
                "gross_r": round(gross_r, 4),
                "net_r": round(net_r, 4),
                "sample": "holdout" if cursor >= split_index else "reference",
            }
        )
        cursor = max(exit_index, cursor + 1)

    reference_trades = [item for item in trades if item["sample"] == "reference"]
    holdout_trades = [item for item in trades if item["sample"] == "holdout"]
    holdout = _trade_metrics(holdout_trades)
    holdout_pf = holdout.get("profit_factor")
    holdout_exp = holdout.get("expectancy_r")
    if holdout["trades"] < 30:
        status, status_label = "insufficient", "样本不足"
    elif holdout_exp is None or holdout_exp <= 0 or holdout_pf is None or holdout_pf < 1:
        status, status_label = "rejected", "样本外无优势"
    elif holdout_pf < 1.20 or holdout_exp < 0.10:
        status, status_label = "unproven", "优势尚未证实"
    else:
        status, status_label = "positive", "样本外正优势"

    no_overlap = all(
        trades[index]["entry_index"] > trades[index - 1]["exit_index"]
        for index in range(1, len(trades))
    )
    entry_after_signal = all(
        item["entry_index"] == item["signal_index"] + 1 for item in trades
    )
    return {
        "source": "local deterministic backtest",
        "symbol": symbol,
        "market": f"DCE {profile['name']} continuous history",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "strategy_version": MODEL_STRATEGY_VERSION,
        "status": status,
        "status_label": status_label,
        "sample_period": {
            "start": str(frame.iloc[0]["date"]),
            "end": str(frame.iloc[-1]["date"]),
            "rows": int(len(frame)),
            "holdout_start": split_date,
            "holdout_fraction": MODEL_HOLDOUT_FRACTION,
        },
        "methodology": {
            "signal_timing": "仅使用当日收盘后可知的EMA20/EMA60、RSI14、ATR14及前20日高低点",
            "entry_timing": "信号后下一交易日开盘成交",
            "entry_rule": "EMA20与EMA60同向时，20日突破或回踩EMA20重新收复/跌破",
            "exit_rule": f"{MODEL_STOP_ATR:.2f} ATR止损、{MODEL_TARGET_R:.1f}R目标、最多持有{MODEL_MAX_HOLDING_BARS}根日线",
            "collision_policy": "同一根K线同时触及止损和止盈时按止损成交",
            "gap_policy": "不利跳空越过止损时按开盘价成交；有利跳空按原目标价成交",
            "cost_assumption": (
                f"单边滑点{MODEL_SLIPPAGE_POINTS_PER_SIDE:.0f}点 + "
                f"单边手续费假设{MODEL_FEE_YUAN_PER_SIDE:.0f}元/手"
            ),
            "parameter_search": "无；参数固定，未按样本外结果优化",
        },
        "all": _trade_metrics(trades),
        "reference": _trade_metrics(reference_trades),
        "holdout": holdout,
        "integrity": {
            "entry_after_signal": entry_after_signal,
            "no_overlapping_positions": no_overlap,
            "same_bar_conservative": True,
            "same_bar_collision_count": same_bar_collisions,
            "chronological_split": True,
        },
        "latest_signal": (
            "long" if int(frame.iloc[-1]["signal"]) > 0 else
            "short" if int(frame.iloc[-1]["signal"]) < 0 else
            "flat"
        ),
        "recent_trades": trades[-12:],
        "limitations": [
            "连续合约历史可能包含换月跳空，不能替代具体月份合约回测。",
            "样本外仅为一次时间切分，不等于未来收益保证。",
            "未模拟涨跌停、排队成交、盘口冲击、保证金变化和税费差异。",
            "该日线基准模型不等同于网页中的1小时/4小时日内执行计划。",
        ],
    }


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
                    "model": DEEPSEEK_MODEL,
                    "messages": messages,
                    "tools": tool_def,
                    "tool_choice": tool_choice,
                    "thinking": DEEPSEEK_THINKING,
                    "reasoning_effort": DEEPSEEK_REASONING_EFFORT,
                    "max_tokens": 12000,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]
            # Thinking content is output-only and must not be sent back in the
            # next tool-calling round.
            messages.append({key: value for key, value in msg.items() if key != "reasoning_content"})

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
    normalization_warnings: list[str] = []

    def safe_float(value: object, fallback: float, label: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            normalization_warnings.append(label)
            return float(fallback)

    support = safe_float(watch_levels.get("support"), snapshot["low20"], "support")
    resistance = safe_float(watch_levels.get("resistance"), snapshot["high20"], "resistance")
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
        "watch_levels":  {"support": support, "resistance": resistance},
        "normalization_warnings": normalization_warnings,
        "risk_note":     str(parsed.get("risk_note", "本分析仅供行情研究，不构成投资建议。")),
    }


def audit_ai_analysis(ai_analysis: dict, snapshot: dict) -> dict:
    """Check free-text AI claims against deterministic market facts.

    The audit never rewrites prose. It can repair unsafe numeric watch levels,
    and the frontend uses execution_allowed to decide whether AI may enter the
    strategy and key-level layers.
    """
    issues: list[dict[str, str]] = []
    score = 100

    def add_issue(code: str, severity: str, message: str, penalty: int) -> None:
        nonlocal score
        if any(item["code"] == code for item in issues):
            return
        issues.append({"code": code, "severity": severity, "message": message})
        score = max(0, score - penalty)

    realtime = snapshot.get("realtime") if isinstance(snapshot.get("realtime"), dict) else {}
    input_freshness = (
        snapshot.get("input_freshness")
        if isinstance(snapshot.get("input_freshness"), dict)
        else {}
    )
    realtime_fetch_status = str(input_freshness.get("realtime_fetch_status") or "")
    if snapshot.get("realtime_required_for_ai") and realtime_fetch_status != "live":
        add_issue(
            "missing_live_quote_input",
            "high",
            "本次分析未取得调用前实时盘口，禁止进入执行层。",
            100,
        )
    current_price = realtime.get("price", snapshot.get("close"))
    try:
        current_price = float(current_price)
    except (TypeError, ValueError):
        current_price = None

    watch = ai_analysis.get("watch_levels")
    if not isinstance(watch, dict):
        watch = {}
    try:
        support = float(watch.get("support"))
        resistance = float(watch.get("resistance"))
    except (TypeError, ValueError):
        support = float(snapshot["low20"])
        resistance = float(snapshot["high20"])
        add_issue("invalid_watch_levels", "high", "AI 支撑/压力不是有效数字，已改用确定性区间。", 40)
    if ai_analysis.get("normalization_warnings"):
        add_issue("invalid_watch_levels", "high", "AI 支撑/压力不是有效数字，已改用确定性区间。", 40)
    if support >= resistance:
        support = float(snapshot["low20"])
        resistance = float(snapshot["high20"])
        add_issue("reversed_watch_levels", "high", "AI 支撑不低于压力，已改用确定性区间。", 40)
    ai_analysis["watch_levels"] = {"support": support, "resistance": resistance}

    summary = str(ai_analysis.get("summary") or "")
    analysis = ai_analysis.get("analysis") if isinstance(ai_analysis.get("analysis"), list) else []
    text = "\n".join([summary, *[str(item) for item in analysis]])
    if realtime_fetch_status == "live" and current_price is not None:
        rounded_price = round(current_price)
        price_markers = {
            str(rounded_price),
            f"{rounded_price:,}",
            f"{current_price:.1f}",
            f"{current_price:,.1f}",
        }
        analysis_text = "\n".join(str(item) for item in analysis)
        if not any(marker in summary for marker in price_markers):
            add_issue(
                "summary_missing_live_price",
                "high",
                f"摘要未明确引用本次实时价 {current_price:g}。",
                35,
            )
        if not any(marker in analysis_text for marker in price_markers):
            add_issue(
                "analysis_missing_live_price",
                "high",
                f"技术分析未明确引用本次实时价 {current_price:g}。",
                35,
            )
    sentences = [item.strip() for item in re.split(r"[。！？；\n]+", text) if item.strip()]
    rsi_value = snapshot.get("rsi14")
    try:
        rsi_value = float(rsi_value)
    except (TypeError, ValueError):
        rsi_value = None
    if rsi_value is not None:
        def affirmative_daily_rsi_claim(sentence: str, term: str) -> bool:
            if "日线" not in sentence or "RSI" not in sentence.upper() or term not in sentence:
                return False
            negated = re.search(rf"(?:未|无|不|没有|非).{{0,6}}{term}", sentence)
            paired_negation = re.search(r"(?:未|无|不|没有|非).{0,6}(?:超买|超卖).{0,4}(?:或|和|及).{0,4}(?:超买|超卖)", sentence)
            return not negated and not paired_negation

        overbought_claim = any(affirmative_daily_rsi_claim(sentence, "超买") for sentence in sentences)
        oversold_claim = any(affirmative_daily_rsi_claim(sentence, "超卖") for sentence in sentences)
        if overbought_claim and rsi_value < 70:
            add_issue("false_rsi_overbought", "high", f"文本声称 RSI 超买，但日线 RSI 为 {rsi_value:.1f}。", 35)
        if oversold_claim and rsi_value > 30:
            add_issue("false_rsi_oversold", "high", f"文本声称 RSI 超卖，但日线 RSI 为 {rsi_value:.1f}。", 35)

    trading_day_label = str(snapshot.get("realtime_trading_day_label") or "")
    if snapshot.get("realtime_label_is_future") and trading_day_label:
        future_time_claim = any(
            trading_day_label in sentence
            and any(term in sentence for term in ("截至", "收盘"))
            and not any(term in sentence for term in ("归属标签", "不是未来", "不代表未来"))
            for sentence in sentences
        )
        if future_time_claim:
            add_issue(
                "future_trade_label_as_clock",
                "high",
                f"文本把交易日归属标签 {trading_day_label} 当作真实未来时刻。",
                40,
            )

    def boll_position(meta: object) -> str | None:
        if not isinstance(meta, dict) or current_price is None:
            return None
        boll = meta.get("bollinger")
        if not isinstance(boll, dict):
            return None
        try:
            upper = float(boll["upper"])
            middle = float(boll["mid"])
            lower = float(boll["lower"])
        except (KeyError, TypeError, ValueError):
            return None
        if current_price > upper:
            return "上轨上方"
        if current_price >= middle:
            return "中轨上方"
        if current_price >= lower:
            return "中轨下方"
        return "下轨下方"

    intraday = snapshot.get("intraday") if isinstance(snapshot.get("intraday"), dict) else {}
    expected_positions = {
        "1小时": boll_position(intraday.get("one_hour")),
        "4小时": boll_position(intraday.get("four_hour")),
    }
    position_terms = ("上轨上方", "中轨上方", "中轨下方", "下轨下方")
    for label, expected in expected_positions.items():
        if not expected:
            continue
        aliases = (label, "1H" if label == "1小时" else "4H")
        clauses = [
            clause.strip()
            for sentence in sentences
            for clause in re.split(r"[，,、]+", sentence)
            if clause.strip()
        ]
        claims = {
            term
            for clause in clauses
            if any(alias.lower() in clause.lower() for alias in aliases)
            for term in position_terms
            if term in clause
        }
        if claims and expected not in claims:
            add_issue(
                f"{label}_boll_mismatch",
                "high",
                f"文本的{label}布林位置与确定性计算不一致，当前应为{expected}。",
                30,
            )

    strategy = ai_analysis.get("intraday_strategy")
    required_strategy = ("bias", "entry", "stop", "take_profit", "invalidation")
    missing = [
        key for key in required_strategy
        if not isinstance(strategy, dict)
        or not str(strategy.get(key) or "").strip()
        or str(strategy.get(key)).startswith("未给出")
    ]
    if missing:
        add_issue("incomplete_strategy", "medium", f"AI 策略缺少字段：{', '.join(missing)}。", 20)

    frame = ai_analysis.get("decision_frame") if isinstance(ai_analysis.get("decision_frame"), dict) else {}
    try:
        evidence_confidence = max(0, min(100, int(float(frame.get("confidence", 0)))))
    except (TypeError, ValueError):
        evidence_confidence = 0
    if evidence_confidence < 50:
        add_issue("low_evidence_confidence", "medium", f"AI 自评证据强度仅 {evidence_confidence}/100。", 15)

    score = max(0, min(100, score))
    has_high_issue = any(item["severity"] == "high" for item in issues)
    execution_allowed = score >= 75 and evidence_confidence >= 50 and not has_high_issue
    if execution_allowed and score >= 90:
        status = "passed"
        label = "通过"
    elif has_high_issue or score < 60:
        status = "blocked"
        label = "规则接管"
    else:
        status = "caution"
        label = "仅供参考"
    return {
        "version": "deterministic-integrity-v2",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "score": score,
        "status": status,
        "label": label,
        "execution_allowed": execution_allowed,
        "evidence_confidence": evidence_confidence,
        "issues": issues,
        "facts": {
            "realtime_price": current_price,
            "realtime_fetch_status": realtime_fetch_status or None,
            "realtime_fetched_at_utc": input_freshness.get("realtime_fetched_at_utc"),
            "realtime_market_tick_time": input_freshness.get("realtime_market_tick_time"),
            "daily_rsi14": rsi_value,
            "one_hour_boll_position": expected_positions["1小时"],
            "four_hour_boll_position": expected_positions["4小时"],
            "realtime_trading_day_label": trading_day_label or None,
            "realtime_label_is_future": bool(snapshot.get("realtime_label_is_future")),
        },
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
        "model": DEEPSEEK_MODEL,
        "thinking_mode": "enabled",
        "reasoning_effort": DEEPSEEK_REASONING_EFFORT,
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
        "integrity": {
            "version": "deterministic-integrity-v1",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "score": 0,
            "status": "blocked",
            "label": "规则接管",
            "execution_allowed": False,
            "evidence_confidence": 0,
            "issues": [{"code": "ai_unavailable", "severity": "high", "message": reason}],
            "facts": {},
        },
        "risk_note": "本分析仅供行情研究，不构成投资建议。",
    }


def generate_ai_analysis(snapshot: dict, news_summary: str = "", profile_name: str = "棕榈油", symbol: str = "P0") -> dict:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return fallback_ai_analysis(snapshot, "DEEPSEEK_API_KEY is not configured")

    has_realtime = bool(snapshot.get("realtime"))
    input_freshness = (
        snapshot.get("input_freshness")
        if isinstance(snapshot.get("input_freshness"), dict)
        else {}
    )
    realtime_fetch_status = str(input_freshness.get("realtime_fetch_status") or "")
    realtime_instruction = (
        "数据中包含字段 realtime（本次 AI 调用前即时抓取的最新可用盘口）。"
        "必须在 summary 和至少一条 analysis 中明确写出 realtime.price、盘口 ticktime 和涨跌幅，"
        "并以该价格作为入场区间、止损、目标位及布林位置判断的当前基准；"
        "不得用日线 close 或小时线 close 替代当前价。"
        "realtime.tradedate 是大商所交易日归属标签，不一定是实际日历时刻；"
        "当 realtime_label_is_future=true 时，必须明确写成交易日归属标签，禁止使用‘截至该未来日期’或‘该未来日期收盘’。"
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
    contract_instruction = (
        "数据中包含 contract_bridge。请明确写出当前连续合约映射到的实际主力月份、"
        "次主力价差、持仓比和换月状态；如果 mapping_verified=false，必须把人工复核列为不交易条件。"
        if snapshot.get("contract_bridge") else
        "数据中无主力月份映射，必须提醒用户下单前自行核对具体月份合约。"
    )
    validation_instruction = (
        "数据中包含 model_validation，这是固定日线基准模型的历史样本外结果。"
        "它不等同于当前日内方案；如果状态不是 positive，必须明确说明历史优势未被证实，"
        "不得把命中率、胜率或历史结果包装成未来概率。"
        if snapshot.get("model_validation") else
        "数据中无策略验证结果，不得声称策略已经回测或验证。"
    )
    freshness_instruction = (
        "数据中包含 input_freshness。只有 realtime_fetch_status=live 的 realtime 才可称为本次实时输入；"
        "必须核对各数据时间，超过10分钟的小时线、日线或新闻要明确标注延迟，"
        "不得把缓存 K 线或历史收盘描述成刚刚成交的实时盘口。"
        if snapshot.get("input_freshness") else
        "如果无法确认采样时间，必须把数据时效列为限制。"
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
        f"{realtime_instruction}{intraday_instruction}{contract_instruction}{validation_instruction}{freshness_instruction}"
        f"{news_block}"
        "要求：\n"
        f"0) 本次分析基准时刻为 UTC {snapshot.get('analysis_as_of_utc')}、北京时间 {snapshot.get('analysis_as_of_beijing')}。"
        "所有‘今晚/明日/即将’必须相对该时刻成立；已经发生的报告或事件必须使用过去时，不能继续写成报告前或即将公布；\n"
        "1) 先给日内短线判断（结合 1H + 4H），再给日线级别背景，不能只做中长期分析；\n"
        "2) bias 字段给出偏多/震荡/偏空；\n"
        "3) analysis 数组：6–8 条技术面要点，必须包含 **1小时布林、4小时布林、日线布林/均线、实时价位置、趋势、量能、支撑压力**，每条 2–3 句；\n"
        "4) intraday_strategy 对象：必须包含 bias, entry, stop, take_profit, invalidation, notes 六个字段，给出以 1小时 + 4小时 尺度为主的日内策略，明确说明适用哪个交易时段（早盘 09:00-11:30 / 午盘 13:30-15:00 / 夜盘 21:00-23:00）；\n"
        f"{news_instructions}"
        "6) watch_levels 包含数字 support 和 resistance；\n"
        "7) decision_frame 对象必须包含：confidence(0-100，表示证据强度而非胜率)、regime、edge、no_trade_condition、long_case、short_case、event_risks、data_limits。"
        "long_case 和 short_case 都必须包含 trigger, entry_zone, stop, targets, invalidation, risk_reward；如果首目标盈亏比低于1.5，必须明确写入 no_trade_condition，不得硬给方向；\n"
        "8) P0/Y0 是连续合约分析口径，不是可直接下单的具体月份合约。结合 contract_bridge 核对主力月份、换月价差与流动性，但仍提醒下单软件二次确认；\n"
        "9) 舆情只能引用给定搜索结果，区分事实、市场预期和你的推断；禁止编造数字、发布时间或来源；\n"
        "10) 强调不构成投资建议；\n"
        "11) 只输出 JSON；字段：summary, bias, analysis, intraday_strategy, decision_frame, news_impact, news_articles, watch_levels, risk_note。\n"
        f"\n数据:\n{json.dumps(snapshot, ensure_ascii=False)}"
    )

    api_started = time.monotonic()
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是机构级中文油脂期货风险分析助手。先验证数据时效和证据，再讨论方向；"
                        "不确定时明确观望，不把连续合约当作可直接下单的具体月份合约，"
                        "不编造新闻、价格、胜率或概率，只基于用户给出的行情和舆情作答。"
                        "大商所 tradedate 是交易日归属标签；未来日期标签绝不代表未来行情。"
                    ),
                },
                {"role": "user", "content": prompt_content},
            ],
            "thinking": DEEPSEEK_THINKING,
            "reasoning_effort": DEEPSEEK_REASONING_EFFORT,
            "max_tokens": 16000,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    resp.raise_for_status()
    resp_json = resp.json()
    api_latency_seconds = round(time.monotonic() - api_started, 1)
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
            "model": DEEPSEEK_MODEL,
            "thinking_mode": "enabled",
            "reasoning_effort": DEEPSEEK_REASONING_EFFORT,
            "status": "ok",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "latest_date": snapshot["latest_date"],
            "realtime_price": snapshot["realtime"]["price"] if has_realtime else None,
            "realtime_note": snapshot.get("realtime_note"),
            "realtime_input": {
                "status": realtime_fetch_status or ("present" if has_realtime else "unavailable"),
                "fetched_at_utc": (snapshot.get("realtime") or {}).get("fetched_at_utc"),
                "market_trading_day": (snapshot.get("realtime") or {}).get("tradedate"),
                "market_tick_time": (snapshot.get("realtime") or {}).get("ticktime"),
                "source": (snapshot.get("realtime") or {}).get("source"),
            },
            "news_summary": news_summary,
            "symbol": symbol,
            "instrument_name": profile_name,
            "api_latency_seconds": api_latency_seconds,
            "token_usage": resp_json.get("usage") or {},
        }
    )
    parsed["integrity"] = audit_ai_analysis(parsed, snapshot)
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

def fetch_daily_once_isolated(symbol: str, timeout_seconds: int = DAILY_FETCH_TIMEOUT_SECONDS):
    """Run AKShare in a child process so a stuck network call can be killed."""
    helper = ROOT / "fetch_daily_once.py"
    with tempfile.TemporaryDirectory(prefix=f"palm-{symbol.lower()}-") as tmp:
        output = Path(tmp) / "daily.csv"
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(helper),
                    "--symbol",
                    symbol,
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"AKShare {symbol} daily fetch exceeded {timeout_seconds}s hard timeout"
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "child process failed").strip()[-600:]
            raise RuntimeError(f"AKShare {symbol} child failed: {detail}")
        if not output.exists():
            raise RuntimeError(f"AKShare {symbol} child produced no CSV")
        frame = pd.read_csv(output)
        if frame.empty:
            raise RuntimeError(f"AKShare {symbol} child produced an empty CSV")
        return frame


def fetch_daily_with_retry(symbol: str = "P0", attempts: int = 2, backoff: int = 5):
    """Fetch daily bars with bounded retries, then retain the last good cache."""
    last_exc: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            df = fetch_daily_once_isolated(symbol)
            if df is not None and not df.empty:
                df.attrs["fetch_status"] = "live"
                if i > 1:
                    print(f"Daily fetch succeeded on attempt {i}/{attempts}")
                return df
            last_exc = RuntimeError("empty dataframe")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"Daily fetch attempt {i}/{attempts} failed: {type(exc).__name__}: {exc}")
        if i < attempts:
            wait = backoff * i
            print(f"  retrying in {wait}s...")
            time.sleep(wait)

    profile = PROFILES.get(symbol) or {}
    cached_path = DATA_DIR / str(profile.get("dir") or symbol.lower()) / "daily.csv"
    if cached_path.exists():
        cached = pd.read_csv(cached_path)
        if not cached.empty:
            cached.attrs["fetch_status"] = "stale_fallback"
            cached.attrs["fetch_error"] = str(last_exc)
            print(
                f"[{symbol}] daily fetch exhausted after {attempts} bounded attempts; "
                f"keeping cached {cached_path.name}"
            )
            return cached
    raise RuntimeError(
        f"AKShare futures_zh_daily_sina failed after {attempts} bounded attempts: {last_exc}"
    )


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
    profile_started = time.monotonic()
    profile = PROFILES[symbol]
    name = profile["name"]
    out_dir = DATA_DIR / profile["dir"]
    out_dir.mkdir(exist_ok=True, parents=True)
    print(f"[{symbol}] pipeline start", flush=True)

    df = fetch_daily_with_retry(symbol=symbol)
    if df.empty:
        raise RuntimeError(f"AKShare returned empty {symbol} daily data")
    daily_fetch_status = str(df.attrs.get("fetch_status") or "live")
    daily_fetch_error = str(df.attrs.get("fetch_error") or "")

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

    model_validation = build_model_validation(export, symbol)
    (out_dir / "model_validation.json").write_text(
        json.dumps(model_validation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

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
        existing_bridge = _load_json(out_dir / "contract_bridge.json")
        bridge_fallback = existing_bridge if existing_bridge.get("symbol") == symbol else None
        f_market = pool.submit(
            _safe,
            lambda: fetch_contract_market_snapshot(symbol=symbol, out_dir=out_dir),
            (None, bridge_fallback),
            "Realtime contract board fetch",
        )
        intraday = f_intraday.result()
        news_snapshot = f_news.result()
        realtime, contract_bridge = f_market.result()

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
        "contract_bridge_updated_at_utc": (contract_bridge or {}).get("updated_at_utc"),
        "main_contract": ((contract_bridge or {}).get("main") or {}).get("symbol"),
        "model_validation_status": model_validation.get("status"),
        "model_validation_generated_at_utc": model_validation.get("generated_at_utc"),
        "daily_fetch_status": daily_fetch_status,
        "daily_fetch_error": daily_fetch_error or None,
        "realtime_quote": realtime,
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

        snapshot = daily_snapshot(
            export,
            realtime,
            intraday,
            contract_bridge=contract_bridge,
            model_validation=model_validation,
        )

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
        ai_started = time.monotonic()
        print(f"[{symbol}] DeepSeek analysis start", flush=True)
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
        print(
            f"[{symbol}] AI analysis: {ai_analysis['status']} "
            f"({time.monotonic() - ai_started:.1f}s)",
            flush=True,
        )

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
    if contract_bridge:
        print(
            f"[{symbol}] Contract mapping: {symbol} -> "
            f"{contract_bridge['main']['symbol']} ({contract_bridge['roll_label']})"
        )
    holdout = model_validation["holdout"]
    print(
        f"[{symbol}] Model holdout: {model_validation['status_label']} "
        f"trades={holdout['trades']} expectancy={holdout['expectancy_r']}R "
        f"PF={holdout['profit_factor']}"
    )
    print(f"[{symbol}] pipeline complete ({time.monotonic() - profile_started:.1f}s)", flush=True)


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
