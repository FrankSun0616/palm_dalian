"""Ask-DeepSeek backend for the AI Q&A feature (F2).

Reads env vars:
  DEEPSEEK_API_KEY — DeepSeek Chat API key
  SYMBOL           — "P0" or "Y0"
  QUESTION         — the user's Chinese question (verbatim)

Loads the latest market snapshot files under data/{sym_lower}/ and asks
DeepSeek to answer using ONLY that context. Writes the answer to
data/{sym_lower}/ask_response.json.

Contract with the front-end / ask.yml workflow: the response file is
overwritten fresh every run. Nothing is appended, no history is kept —
each Q&A is a one-shot standalone request.
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
DEEPSEEK_MODEL = "deepseek-v4-pro"
DEEPSEEK_THINKING = {"type": "enabled"}
DEEPSEEK_REASONING_EFFORT = "high"


PROFILES: dict[str, dict] = {
    "P0": {"name": "棕榈油", "dir": "p0"},
    "Y0": {"name": "豆油",   "dir": "y0"},
}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_response(profile_dir: Path, payload: dict) -> None:
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "ask_response.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_context(profile_dir: Path) -> dict:
    """Assemble a compact JSON blob DeepSeek can read. Only pass the fields
    the model actually needs to answer — the full ai_analysis + intraday +
    source_meta would blow through the token limit and dilute focus."""
    ai = load_json(profile_dir / "ai_analysis.json")
    meta = load_json(profile_dir / "source_meta.json")
    intraday = load_json(profile_dir / "intraday_meta.json")

    def _pick(src: dict, keys: list[str]) -> dict:
        return {k: src.get(k) for k in keys if k in src}

    trimmed_intraday = {}
    for label in ("one_hour", "two_hour"):
        block = intraday.get(label) or {}
        if not isinstance(block, dict):
            continue
        trimmed_intraday[label] = _pick(block, [
            "label", "latest_time", "open", "high", "low", "close",
            "change_pct", "volume", "rsi14", "bollinger", "high20", "low20",
        ])

    return {
        "source_meta": _pick(meta, [
            "symbol", "market", "instrument_name",
            "latest_date", "latest_close", "updated_at_utc",
            "latest_open_interest", "oi_change", "oi_change_pct",
            "live_bar",
        ]),
        "ai_analysis": _pick(ai, [
            "generated_at_utc", "summary", "bias", "analysis",
            "intraday_strategy", "news_impact", "watch_levels",
            "realtime_price", "realtime_note", "risk_note",
        ]),
        "intraday": trimmed_intraday,
    }


def ask_deepseek(api_key: str, symbol: str, name: str, question: str, context: dict) -> str:
    system_msg = (
        f"你是大连商品交易所{name}({symbol})看盘助手，"
        "只基于用户提供的市场数据回答。回答简洁、中文、100-400字。"
    )
    user_msg = (
        f"【市场数据】\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        f"问题: {question}"
    )
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "thinking": DEEPSEEK_THINKING,
            "reasoning_effort": DEEPSEEK_REASONING_EFFORT,
            "max_tokens": 2400,
        },
        timeout=120,
    )
    resp.raise_for_status()
    payload = resp.json()
    choice = payload["choices"][0]
    content = (choice.get("message") or {}).get("content", "").strip()
    if not content:
        raise RuntimeError("DeepSeek returned empty answer")
    return content


def main() -> int:
    symbol = os.getenv("SYMBOL", "").strip().upper()
    question = os.getenv("QUESTION", "").strip()
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

    profile = PROFILES.get(symbol)
    if not profile:
        print(f"[ask] invalid SYMBOL {symbol!r}; expected P0 or Y0", file=sys.stderr)
        return 2
    if not question:
        print("[ask] empty QUESTION", file=sys.stderr)
        return 2

    profile_dir = DATA_DIR / profile["dir"]
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    base = {
        "asked_at_utc": now_iso,
        "question": question,
        "symbol": symbol,
        "model": DEEPSEEK_MODEL,
        "thinking_mode": "enabled",
        "reasoning_effort": DEEPSEEK_REASONING_EFFORT,
    }

    if not api_key:
        write_response(profile_dir, {
            **base,
            "answer": "",
            "status": "error",
            "error": "DEEPSEEK_API_KEY is not configured",
        })
        print("[ask] DEEPSEEK_API_KEY missing", file=sys.stderr)
        return 1

    try:
        context = build_context(profile_dir)
        answer = ask_deepseek(api_key, symbol, profile["name"], question, context)
    except Exception as exc:  # noqa: BLE001
        write_response(profile_dir, {
            **base,
            "answer": "",
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        })
        print(f"[ask] failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    write_response(profile_dir, {
        **base,
        "answer": answer,
        "status": "ok",
    })
    print(f"[ask] ok, {len(answer)} chars written to {profile_dir/'ask_response.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
