"""WeChat push notifier via Server 酱 (sctapi.ftqq.com).

Runs after the "Update palm oil data" workflow completes successfully.
Detects notify-worthy events by diffing the current AI/meta files against
the last recorded state:

  1. New AI analysis (ai.generated_at_utc changed)
  2. Bias flip (previous vs current bias sign flipped)
  3. Level break (last price crossed above resistance or below support)

For each event a POST goes to https://sctapi.ftqq.com/{SENDKEY}.send. If
WECHAT_SENDKEY is empty we log "skip" and STILL update the state file so
we don't stack unsent notifications on the next run.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

AI_FILE = DATA_DIR / "ai_analysis.json"
META_FILE = DATA_DIR / "source_meta.json"
STATE_FILE = DATA_DIR / "notify_state.json"

SERVER_CHAN_URL = "https://sctapi.ftqq.com/{key}.send"


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


# ── Event extraction ─────────────────────────────────────────────────────────

def current_price(ai: dict, meta: dict) -> float | None:
    """Prefer the AI's realtime price snapshot (matches the levels it set);
    fall back to source_meta's latest_close."""
    price = _to_float(ai.get("realtime_price"))
    if price is not None:
        return price
    return _to_float(meta.get("latest_close"))


def build_events(prev_state: dict, ai: dict, meta: dict) -> list[dict]:
    events: list[dict] = []

    # 1) New AI analysis
    prev_gen = prev_state.get("ai_generated_at_utc")
    curr_gen = ai.get("generated_at_utc")
    if curr_gen and curr_gen != prev_gen:
        events.append({
            "kind": "new_ai",
            "title": f"[棕榈油] 新AI分析 · 偏向 {ai.get('bias', '?')}",
            "desp": (
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
                f"[棕榈油] 方向反转: {prev_state.get('bias')} → {ai.get('bias')}"
            ),
            "desp": (
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
            "title": f"[棕榈油] 关键位破位 · {break_desc}",
            "desp": (
                f"**破位**: {break_desc}\n\n"
                f"**当前偏向**: {ai.get('bias', '?')}\n\n"
                f"**支撑/压力**: {support} / {resistance}"
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

def build_next_state(ai: dict, meta: dict) -> dict:
    watch = ai.get("watch_levels") or {}
    return {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ai_generated_at_utc": ai.get("generated_at_utc"),
        "bias": ai.get("bias"),
        "last_price": current_price(ai, meta),
        "resistance": _to_float(watch.get("resistance")),
        "support": _to_float(watch.get("support")),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ai = load_json(AI_FILE)
    meta = load_json(META_FILE)
    prev_state = load_json(STATE_FILE)

    events = build_events(prev_state, ai, meta)
    sendkey = os.getenv("WECHAT_SENDKEY", "").strip()

    if not events:
        print("[notify] no events to send")
    elif not sendkey:
        print(f"[notify] skip: WECHAT_SENDKEY not set ({len(events)} event(s) would have fired)")
    else:
        for evt in events:
            ok = send_wechat(sendkey, evt["title"], evt["desp"])
            print(f"[notify] {evt['kind']}: {'sent' if ok else 'failed'}")

    # Always write the next state, even when we skipped or had no events —
    # otherwise a missing SENDKEY would cause the next run to re-detect the
    # same events forever.
    next_state = build_next_state(ai, meta)
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
