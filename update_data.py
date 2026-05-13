from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import akshare as ak
import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


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


# ── Real-time quote (Sina Market Center) ─────────────────────────────────────

SINA_FUTURES_URL = (
    "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "Market_Center.getHQFuturesData?page=1&sort=position&asc=0&node=zly_qh&base=futures"
)


def get_realtime_quote_sina() -> dict | None:
    """Fetch live P0 quote from Sina Market Center (same API as the browser front-end)."""
    try:
        resp = requests.get(SINA_FUTURES_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        p0 = next((item for item in data if item.get("symbol") == "P0"), None)
        if not p0 or not float(p0.get("trade") or 0):
            return None
        price = float(p0["trade"])
        prev_close = float(p0["preclose"])
        change = (price - prev_close) / prev_close if prev_close else 0
        return {
            "price": price,
            "open": float(p0["open"]),
            "high": float(p0["high"]),
            "low": float(p0["low"]),
            "volume": int(p0["volume"]),
            "prev_close": prev_close,
            "change_pct": pct(change),
            "tradedate": p0.get("tradedate", ""),
            "ticktime": p0.get("ticktime", ""),
        }
    except Exception:
        return None


# ── Daily snapshot ────────────────────────────────────────────────────────────

def daily_snapshot(export, realtime: dict | None = None) -> dict:
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


# ── Step 1: Fetch news with DeepSeek function-calling ─────────────────────────

def fetch_news_summary(api_key: str, snapshot: dict) -> str:
    """
    Let DeepSeek autonomously search for recent palm oil news using the
    web_search tool and return a Chinese plain-text summary.
    """
    tool_def = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "搜索互联网，获取最新新闻、价格资讯和市场分析",
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
                "你是专业的商品期货市场信息员，擅长搜集和总结影响棕榈油期货价格的最新资讯。"
                "请主动调用 web_search 查找信息，不要凭空编造新闻。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"当前分析日期：{latest_date}。\n"
                "请搜索以下几个方向的最新信息，然后用中文给出 4–6 条舆情要点，"
                "每条说明事件内容及其对大连棕榈油期货价格的影响方向（利多/利空/中性）：\n"
                "1. 棕榈油期货 大连 最新\n"
                "2. 马来西亚 印度尼西亚 棕榈油 产量 出口\n"
                "3. 中国棕榈油 进口 需求\n"
                "4. 植物油脂 豆油 菜油 价格\n"
                "5. 棕榈油 政策 关税 补贴"
            ),
        },
    ]

    for _round in range(8):  # model may search multiple times
        try:
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
                    "tool_choice": "auto",
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]
            messages.append(msg)

            if choice["finish_reason"] == "tool_calls":
                for tc in msg.get("tool_calls", []):
                    fn_args = json.loads(tc["function"]["arguments"])
                    query = fn_args.get("query", "棕榈油最新消息")
                    print(f"  [web_search] {query}")
                    search_text = web_search(query)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": search_text,
                        }
                    )
            else:
                return msg.get("content", "")

        except Exception as exc:
            return f"新闻搜索异常: {exc}"

    return "新闻搜索超过最大轮次"


# ── Step 2: Technical + fundamental analysis → JSON ───────────────────────────

def normalize_ai_analysis(parsed: dict, snapshot: dict) -> dict:
    def to_list(val):
        if isinstance(val, str):
            return [val] if val else []
        return [str(x) for x in val] if isinstance(val, list) else []

    watch_levels = parsed.get("watch_levels", {})
    if not isinstance(watch_levels, dict):
        watch_levels = {}
    support = watch_levels.get("support", snapshot["low20"])
    resistance = watch_levels.get("resistance", snapshot["high20"])

    return {
        "summary": str(parsed.get("summary", "暂无 AI 摘要。")),
        "bias": str(parsed.get("bias", "未判断")),
        "analysis": to_list(parsed.get("analysis")),
        "news_impact": to_list(parsed.get("news_impact")),
        "watch_levels": {
            "support": float(support),
            "resistance": float(resistance),
        },
        "risk_note": str(parsed.get("risk_note", "本分析仅供行情研究，不构成投资建议。")),
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
        "news_impact": [],
        "watch_levels": {"support": snapshot["low20"], "resistance": snapshot["high20"]},
        "risk_note": "本分析仅供行情研究，不构成投资建议。",
    }


def generate_ai_analysis(snapshot: dict, news_summary: str = "") -> dict:
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

    news_block = (
        f"\n\n【近期市场舆情摘要（来自网络实时搜索）】\n{news_summary}\n"
        if news_summary else ""
    )

    prompt_content = (
        "请基于以下大连商品交易所棕榈油 P0 连续合约日线数据及市场舆情做综合中文分析。"
        f"{realtime_instruction}"
        f"{news_block}"
        "要求：\n"
        "1) 结合技术面和舆情/基本面给出综合判断；\n"
        "2) bias 字段给出偏多/震荡/偏空；\n"
        "3) analysis 数组：技术面要点（趋势、均线、RSI、量能、支撑压力）；\n"
        "4) news_impact 数组：每条针对一个新闻/基本面要点，说明对价格的影响（利多/利空/中性）；\n"
        "5) watch_levels 包含数字 support 和 resistance；\n"
        "6) 强调不构成投资建议；\n"
        "7) 只输出 JSON，字段：summary, bias, analysis, news_impact, watch_levels, risk_note。\n"
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
                    "content": "你是谨慎的中文期货技术面和基本面综合分析助手，只基于用户给出的数据与舆情作答。",
                },
                {"role": "user", "content": prompt_content},
            ],
            "temperature": 0.2,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        },
        timeout=90,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
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
        }
    )
    return parsed


# ── Night session live bar (only during 21:00–23:59 Beijing) ─────────────────

def get_live_bar(last_daily_date: str) -> dict | None:
    """Fetch night session minute data and return a preliminary next-day bar."""
    cst = timezone(timedelta(hours=8))
    now_cst = datetime.now(cst)
    if not (21 <= now_cst.hour <= 23):
        return None
    try:
        df = ak.futures_zh_minute_sina(symbol="P0", period="60")
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


# ── Main ─────────────────────────────────────────────────────────────────────

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
        "live_bar": get_live_bar(str(latest["date"])),
    }
    (DATA_DIR / "source_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if should_run_ai_analysis():
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

        # Real-time quote
        realtime = get_realtime_quote_sina()
        if realtime:
            print(f"Real-time quote: {realtime['price']} @ {realtime['tradedate']} {realtime['ticktime']}")
        else:
            print("Real-time quote: unavailable, using daily close only")

        snapshot = daily_snapshot(export, realtime)

        # Step 1 – news via web search
        news_summary = ""
        if api_key:
            print("Fetching market news via DeepSeek web search...")
            news_summary = fetch_news_summary(api_key, snapshot)
            preview = news_summary[:120].replace("\n", " ")
            print(f"News summary preview: {preview}...")

        # Step 2 – full analysis
        try:
            ai_analysis = generate_ai_analysis(snapshot, news_summary)
        except Exception as exc:  # noqa: BLE001
            ai_analysis = fallback_ai_analysis(snapshot, f"{type(exc).__name__}: {exc}")

        (DATA_DIR / "ai_analysis.json").write_text(
            json.dumps(ai_analysis, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"AI analysis: {ai_analysis['status']}")
    else:
        print("AI analysis: skipped; set RUN_AI_ANALYSIS=true to generate")

    print(f"Updated {output}")
    print(f"Rows: {len(export)}")
    print(f"Latest: {latest['date']} close={latest['close']}")


if __name__ == "__main__":
    main()
