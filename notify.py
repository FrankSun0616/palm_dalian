"""WeChat push notifier via Server 酱 (sctapi.ftqq.com).

Runs after the "Update palm oil data" workflow completes successfully.
Iterates every symbol in PROFILES (P0 palm oil + Y0 soybean oil) and, per
symbol, detects notify-worthy events by diffing the current AI/meta files
against the last recorded state:

  1. New AI analysis (ai.generated_at_utc changed)
  2. Bias flip (previous vs current bias sign flipped)
  3. Level break (last price crossed above resistance or below support)

State for all symbols lives in ONE top-level file (data/notify_state.json)
keyed by symbol so we don't need to duplicate file writes per profile.

For each event a POST goes to https://sctapi.ftqq.com/{SENDKEY}.send. If
WECHAT_SENDKEY is empty we log "skip" and STILL update the state file so
we don't stack unsent notifications on the next run.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

# Shared state for BOTH symbols, keyed by symbol code.
STATE_FILE = DATA_DIR / "notify_state.json"

SERVER_CHAN_URL = "https://sctapi.ftqq.com/{key}.send"


# ── Notify profiles ──────────────────────────────────────────────────────────
#
# Mirrors update_data.PROFILES but keeps notify.py self-contained (no import
# of update_data — that module pulls in akshare/requests-heavy deps we don't
# need for pushing WeChat notifications).

NOTIFY_PROFILES: dict[str, dict] = {
    "P0": {"name": "棕榈油", "dir": "p0", "emoji": "🌴"},
    "Y0": {"name": "豆油",   "dir": "y0", "emoji": "🌱"},
}


# ── Data loading (gracefully handle missing files) ───────────────────────────

def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[notify] {path.name} not found; treating as empty")
        return {}
    except json.JSONDecodeError as exc:
        print(f"[notify] {path.name} parse failed: {exc}")
        return {}


# ── Bias mapping ─────────────────────────────────────────────────────────────

# Keyword -> sign mapping for bias direction. Order matters: we scan the
# incoming bias string for the FIRST keyword present so mixed strings like
# "偏多，逢低" still resolve to +1.
_BIAS_LEXICON: list[tuple[str, int]] = [
    ("偏多", +1), ("多头", +1), ("看多", +1), ("做多", +1), ("强", +1),
    ("偏空", -1), ("空头", -1), ("看空", -1), ("做空", -1), ("弱", -1),
]


def bias_sign(bias: str | None) -> int:
    """Map a bias string to +1 (long), -1 (short), or 0 (neutral/unknown)."""
    if not bias:
        return 0
    text = str(bias)
    for keyword, sign in _BIAS_LEXICON:
        if keyword in text:
            return sign
    return 0


def bias_flipped(prev: str | None, curr: str | None) -> bool:
    """True only when sign flips from +1<->-1. Transitions through 0 do NOT
    count as a flip — the trader only cares when the model changes its mind
    outright, not when it goes to/from 震荡/未判断."""
    p, c = bias_sign(prev), bias_sign(curr)
    return p != 0 and c != 0 and p != c


# ── Level-break detection ────────────────────────────────────────────────────

def _to_float(x) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def detect_level_break(
    prev_price: float | None,
    curr_price: float | None,
    resistance: float | None,
    support: float | None,
) -> str | None:
    """Return a short human description if price crossed a level since the
    previous check, else None. Requires both prev and curr prices — a level
    that is straddled but not crossed since the last state is not a break.

    A crossing counts when prev was on one side of the level and curr is on
    the other (strict inequality on the entry side, inclusive on the arrival
    side) — this catches "closed at resistance" as well as clean breakouts.
    """
    if curr_price is None or prev_price is None:
        return None
    if resistance is not None and prev_price < resistance <= curr_price:
        return f"上破压力位 {resistance:g}（{prev_price:g} → {curr_price:g}）"
    if support is not None and prev_price > support >= curr_price:
        return f"下破支撑位 {support:g}（{prev_price:g} → {curr_price:g}）"
    return None


# ── Data-freshness monitor (F6) ──────────────────────────────────────────────

# Trading-hour thresholds are stricter than off-hours because the pipeline is
# scheduled every 5 min during market open. Times are Beijing local (UTC+8).
STALE_THRESHOLD_TRADING_SEC = 15 * 60
STALE_THRESHOLD_OFFHOURS_SEC = 6 * 3600
_BEIJING = timezone(timedelta(hours=8))


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        s = str(value)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_trading_hours(now_utc: datetime) -> bool:
    """True if now (Beijing) sits inside the day (09:00-15:00) or night
    (21:00-23:30) DCE session windows."""
    b = now_utc.astimezone(_BEIJING)
    minutes = b.hour * 60 + b.minute
    return (9 * 60 <= minutes <= 15 * 60) or (21 * 60 <= minutes <= 23 * 60 + 30)


def check_data_freshness(meta: dict, now_utc: datetime | None = None) -> dict | None:
    """Return a dict describing the staleness (elapsed_sec, threshold_sec) if
    source_meta.updated_at_utc is beyond the current-hour threshold, else None.

    Returning a dict (not a formatted string) lets the caller decide whether
    to actually push based on prev_state.data_stale_alerted."""
    if not meta:
        return None
    updated = _parse_utc(meta.get("updated_at_utc"))
    if updated is None:
        return None
    now = now_utc or datetime.now(timezone.utc)
    elapsed = (now - updated).total_seconds()
    if elapsed < 0:
        return None
    threshold = STALE_THRESHOLD_TRADING_SEC if _is_trading_hours(now) else STALE_THRESHOLD_OFFHOURS_SEC
    if elapsed <= threshold:
        return None
    return {
        "elapsed_sec": int(elapsed),
        "threshold_sec": int(threshold),
        "updated_at_utc": meta.get("updated_at_utc"),
    }


# ── Event extraction ─────────────────────────────────────────────────────────

def current_price(ai: dict, meta: dict) -> float | None:
    """Prefer the AI's realtime price snapshot (matches the levels it set);
    fall back to source_meta's latest_close."""
    price = _to_float(ai.get("realtime_price"))
    if price is not None:
        return price
    return _to_float(meta.get("latest_close"))


def build_events(
    prev_state: dict,
    ai: dict,
    meta: dict,
    symbol: str,
    profile: dict,
    accuracy: dict | None = None,
    stale_info: dict | None = None,
) -> list[dict]:
    events: list[dict] = []
    emoji = profile.get("emoji", "")
    name = profile.get("name", symbol)
    tag = f"{emoji} [{name}]".strip()

    # 1) New AI analysis
    prev_gen = prev_state.get("ai_generated_at_utc")
    curr_gen = ai.get("generated_at_utc")
    if curr_gen and curr_gen != prev_gen:
        events.append({
            "kind": "new_ai",
            "title": f"{tag} 新AI分析 · 偏向 {ai.get('bias', '?')}",
            "desp": (
                f"**品种**: {name}（{symbol}）\n\n"
                f"**分析生成时间**: {curr_gen}\n\n"
                f"**偏向**: {ai.get('bias', '?')}\n\n"
                f"**摘要**: {ai.get('summary', '')}\n\n"
                f"**支撑/压力**: "
                f"{ai.get('watch_levels', {}).get('support', '?')} / "
                f"{ai.get('watch_levels', {}).get('resistance', '?')}"
            ),
        })

    # 2) Bias flip
    if bias_flipped(prev_state.get("bias"), ai.get("bias")):
        events.append({
            "kind": "bias_flip",
            "title": (
                f"{tag} 方向反转: {prev_state.get('bias')} → {ai.get('bias')}"
            ),
            "desp": (
                f"**品种**: {name}（{symbol}）\n\n"
                f"**上次偏向**: {prev_state.get('bias')}\n\n"
                f"**当前偏向**: {ai.get('bias')}\n\n"
                f"**摘要**: {ai.get('summary', '')}"
            ),
        })

    # 3) Level break
    watch = ai.get("watch_levels") or {}
    curr_price = current_price(ai, meta)
    prev_price = _to_float(prev_state.get("last_price"))
    resistance = _to_float(watch.get("resistance"))
    support = _to_float(watch.get("support"))
    break_desc = detect_level_break(prev_price, curr_price, resistance, support)
    if break_desc:
        events.append({
            "kind": "level_break",
            "title": f"{tag} 关键位破位 · {break_desc}",
            "desp": (
                f"**品种**: {name}（{symbol}）\n\n"
                f"**破位**: {break_desc}\n\n"
                f"**当前偏向**: {ai.get('bias', '?')}\n\n"
                f"**支撑/压力**: {support} / {resistance}"
            ),
        })

    # 4) F6: data-source staleness — only fire on false→true transition
    if stale_info and not bool(prev_state.get("data_stale_alerted")):
        minutes = stale_info["elapsed_sec"] // 60
        threshold_min = stale_info["threshold_sec"] // 60
        events.append({
            "kind": "data_stale",
            "title": f"⚠️ {name} 数据源异常 ({minutes} 分钟未更新)",
            "desp": (
                f"**品种**: {name}（{symbol}）\n\n"
                f"**最后更新**: {stale_info.get('updated_at_utc', '?')}\n\n"
                f"**距今**: {minutes} 分钟（阈值 {threshold_min} 分钟）\n\n"
                f"上游 AKShare/Sina 可能异常，前端数据将暂停更新。"
            ),
        })

    # 5) F7: low AI accuracy warning — only fire on false→true transition
    if accuracy and accuracy.get("warning_low_accuracy"):
        if not bool(prev_state.get("accuracy_warned")):
            hit_rate = accuracy.get("recent_hit_rate") or 0
            total_evaluated = int(accuracy.get("total_evaluated") or 0)
            hits = int(accuracy.get("hits") or 0)
            events.append({
                "kind": "accuracy_warning",
                "title": f"📉 {name} AI 命中率偏低 ({hit_rate:.0%})",
                "desp": (
                    f"近 {total_evaluated} 次评估中 {hits} 次准确。"
                    "谨慎参考 AI 判断。"
                ),
            })

    return events


# ── Push ─────────────────────────────────────────────────────────────────────

def send_wechat(sendkey: str, title: str, desp: str) -> bool:
    try:
        resp = requests.post(
            SERVER_CHAN_URL.format(key=sendkey),
            data={"title": title[:64], "desp": desp[:20000]},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        code = payload.get("code")
        if code == 0:
            return True
        print(f"[notify] Server 酱 responded code={code}: {payload}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] send failed: {type(exc).__name__}: {exc}")
        return False


# ── State write ──────────────────────────────────────────────────────────────

def build_next_symbol_state(
    ai: dict,
    meta: dict,
    accuracy: dict | None = None,
    stale_info: dict | None = None,
) -> dict:
    watch = ai.get("watch_levels") or {}
    # Latch flags stay true while the condition persists; clear when it clears.
    # That's what makes the notify path fire once per false→true edge.
    return {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ai_generated_at_utc": ai.get("generated_at_utc"),
        "bias": ai.get("bias"),
        "last_price": current_price(ai, meta),
        "resistance": _to_float(watch.get("resistance")),
        "support": _to_float(watch.get("support")),
        "data_stale_alerted": bool(stale_info is not None),
        "accuracy_warned": bool(accuracy and accuracy.get("warning_low_accuracy")),
    }


def load_prev_state() -> dict:
    """Load the combined state file. Falls back to an empty dict per symbol.

    Also tolerates the legacy flat schema (pre dual-symbol) — those keys are
    mapped onto the P0 slot so the first dual-symbol run doesn't re-fire
    every P0 event."""
    raw = load_json(STATE_FILE)
    # Legacy flat schema had 'ai_generated_at_utc' at the top level.
    if raw and "ai_generated_at_utc" in raw and "P0" not in raw and "Y0" not in raw:
        return {"P0": raw}
    return raw


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    prev_state = load_prev_state()
    sendkey = os.getenv("WECHAT_SENDKEY", "").strip()

    next_state: dict = {}
    total_events = 0
    total_sent = 0

    for symbol, profile in NOTIFY_PROFILES.items():
        profile_dir = DATA_DIR / profile["dir"]
        ai = load_json(profile_dir / "ai_analysis.json")
        meta = load_json(profile_dir / "source_meta.json")
        accuracy = load_json(profile_dir / "ai_accuracy.json") or None
        stale_info = check_data_freshness(meta)

        prev_symbol_state = prev_state.get(symbol, {}) if isinstance(prev_state, dict) else {}
        events = build_events(
            prev_symbol_state, ai, meta, symbol, profile,
            accuracy=accuracy, stale_info=stale_info,
        )
        total_events += len(events)

        if not events:
            print(f"[notify] {symbol}: no events to send")
        elif not sendkey:
            print(
                f"[notify] {symbol}: skip: WECHAT_SENDKEY not set "
                f"({len(events)} event(s) would have fired)"
            )
        else:
            for evt in events:
                ok = send_wechat(sendkey, evt["title"], evt["desp"])
                if ok:
                    total_sent += 1
                print(f"[notify] {symbol} {evt['kind']}: {'sent' if ok else 'failed'}")

        next_state[symbol] = build_next_symbol_state(
            ai, meta, accuracy=accuracy, stale_info=stale_info,
        )

    if total_events == 0:
        print("[notify] no events across all symbols")
    else:
        print(f"[notify] fired {total_sent}/{total_events} event(s) across all symbols")

    # Always write the next state, even when we skipped or had no events —
    # otherwise a missing SENDKEY would cause the next run to re-detect the
    # same events forever.
    try:
        DATA_DIR.mkdir(exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(next_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[notify] state written to {STATE_FILE}")
    except OSError as exc:
        print(f"[notify] state write failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
