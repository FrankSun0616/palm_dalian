from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import akshare as ak
import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


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


def daily_snapshot(export) -> dict[str, object]:
    rows = export.tail(120).to_dict(orient="records")
    closes = [float(row["close"]) for row in rows]
    volumes = [float(row["volume"]) for row in rows]
    latest = rows[-1]
    previous = rows[-2]
    change = (latest["close"] - previous["close"]) / previous["close"]
    high20 = max(float(row["high"]) for row in rows[-20:])
    low20 = min(float(row["low"]) for row in rows[-20:])
    volume_avg20 = sum(volumes[-20:]) / 20
    return {
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


def fallback_ai_analysis(snapshot: dict[str, object], reason: str) -> dict[str, object]:
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
            f"最新日线收盘 {snapshot['close']:.0f}，日涨跌 {snapshot['change_pct']}。",
            f"MA10/MA20/MA60 分别为 {snapshot['ma10']:.0f}/{snapshot['ma20']:.0f}/{snapshot['ma60']:.0f}。",
            f"20日区间支撑压力为 {snapshot['low20']:.0f}-{snapshot['high20']:.0f}。",
        ],
        "watch_levels": {
            "support": snapshot["low20"],
            "resistance": snapshot["high20"],
        },
        "risk_note": "本分析仅供行情研究，不构成投资建议。",
    }


def normalize_ai_analysis(parsed: dict[str, object], snapshot: dict[str, object]) -> dict[str, object]:
    analysis = parsed.get("analysis", [])
    if isinstance(analysis, str):
        analysis = [analysis]
    if not isinstance(analysis, list):
        analysis = []

    watch_levels = parsed.get("watch_levels", {})
    if not isinstance(watch_levels, dict):
        watch_levels = {}
    support = watch_levels.get("support", snapshot["low20"])
    resistance = watch_levels.get("resistance", snapshot["high20"])

    return {
        "summary": str(parsed.get("summary", "暂无 AI 摘要。")),
        "bias": str(parsed.get("bias", "未判断")),
        "analysis": [str(item) for item in analysis],
        "watch_levels": {
            "support": float(support),
            "resistance": float(resistance),
        },
        "risk_note": str(parsed.get("risk_note", "本分析仅供行情研究，不构成投资建议。")),
    }


def generate_ai_analysis(snapshot: dict[str, object]) -> dict[str, object]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return fallback_ai_analysis(snapshot, "DEEPSEEK_API_KEY is not configured")

    prompt = {
        "role": "user",
        "content": (
            "请基于下面的大连商品交易所棕榈油 P0 连续合约日线数据做中文行情分析。"
            "要求：1) 明确只分析日线，不要声称有逐笔盘口；2) 给出偏多/震荡/偏空判断；"
            "3) 解释趋势、均线、RSI、量能、支撑压力；4) 给出未来1-3个交易日的观察情景；"
            "5) 强调不构成投资建议；6) 只输出 JSON；"
            "7) analysis 必须是字符串数组；8) watch_levels 必须是对象，包含数字 support 和 resistance；"
            "字段为 summary,bias,analysis,watch_levels,risk_note。"
            f"\n\n数据:\n{json.dumps(snapshot, ensure_ascii=False)}"
        ),
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是谨慎的中文期货日线技术分析助手，只基于用户给出的数据分析。"},
            prompt,
        ],
        "temperature": 0.2,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = normalize_ai_analysis(json.loads(content), snapshot)
    parsed.update(
        {
            "source": "DeepSeek API",
            "model": payload["model"],
            "status": "ok",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "latest_date": snapshot["latest_date"],
        }
    )
    return parsed


def main() -> None:
    df = ak.futures_zh_daily_sina(symbol="P0")
    if df.empty:
        raise RuntimeError("AKShare returned empty P0 daily data")

    export = df[["date", "open", "high", "low", "close", "volume"]].copy()
    output = DATA_DIR / "palm_oil_p0_daily.csv"
    export.to_csv(output, index=False)

    latest = export.tail(1).iloc[0]
    meta = {
        "source": "AKShare futures_zh_daily_sina",
        "symbol": "P0",
        "market": "DCE palm oil continuous contract",
        "instrument_name": "棕榈油连续",
        "rows": int(len(export)),
        "latest_date": str(latest["date"]),
        "latest_close": float(latest["close"]),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (DATA_DIR / "source_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    snapshot = daily_snapshot(export)
    try:
        ai_analysis = generate_ai_analysis(snapshot)
    except Exception as exc:  # noqa: BLE001 - write diagnostics for the public status file.
        ai_analysis = fallback_ai_analysis(snapshot, f"{type(exc).__name__}: {exc}")
    (DATA_DIR / "ai_analysis.json").write_text(
        json.dumps(ai_analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Updated {output}")
    print(f"Rows: {len(export)}")
    print(f"Latest: {latest['date']} close={latest['close']}")
    print(f"AI analysis: {ai_analysis['status']}")


if __name__ == "__main__":
    main()
