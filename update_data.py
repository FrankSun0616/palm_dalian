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


def normalize_intraday_df(df, limit: int = 220):
    if df is None or df.empty:
        return df
    out = df.copy().tail(limit)
    out["datetime"] = out["datetime"].astype(str)
    keep = ["datetime", "open", "high", "low", "close", "volume", "hold"]
    return out[keep]


def fetch_intraday(period: str):
    try:
        return normalize_intraday_df(ak.futures_zh_minute_sina(symbol="P0", period=period))
    except Exception as exc:
        print(f"Intraday {period}m fetch failed: {exc}")
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
        "bollinger": boll,
        "high20": float(recent20["high"].max()),
        "low20": float(recent20["low"].min()),
        "last_30_bars": recent30.to_dict(orient="records"),
    }


def fetch_intraday_bundle() -> dict[str, object]:
    h1 = fetch_intraday("60")
    h2 = fetch_intraday("120")
    if h1 is not None and not h1.empty:
        h1.to_csv(DATA_DIR / "intraday_1h.csv", index=False)
    if h2 is not None and not h2.empty:
        h2.to_csv(DATA_DIR / "intraday_2h.csv", index=False)
    bundle = {
        "source": "AKShare futures_zh_minute_sina",
        "symbol": "P0",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "one_hour": intraday_summary(h1, "1小时"),
        "two_hour": intraday_summary(h2, "2小时"),
    }
    (DATA_DIR / "intraday_meta.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return bundle


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
        "棕榈",
        "palm",
        "malaysia",
        "indonesia",
        "马来",
        "印尼",
        "油脂",
        "期货",
        "futures",
        "dce",
        "大连",
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


def fetch_news_snapshot() -> dict[str, object]:
    queries = [
        "棕榈油 期货 今日 马来西亚 印尼 出口 库存",
        "大连 棕榈油 P0 期货 今日 走势",
        "palm oil futures Malaysia Indonesia export stock today",
    ]
    articles: list[dict[str, str]] = []

    for query in queries:
        try:
            for item in fetch_google_news(query):
                if any(existing["url"] == item["url"] for existing in articles):
                    continue
                articles.append(item)
        except Exception as exc:
            print(f"Google News snapshot failed for {query}: {exc}")

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
    (DATA_DIR / "news_snapshot.json").write_text(
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

def fetch_news_raw(api_key: str, snapshot: dict) -> str:
    """
    DeepSeek searches the web (up to MAX_SEARCH_ROUNDS times) and returns a
    detailed plain-text digest of recent palm oil news WITH source URLs so
    the analysis step can build proper article cards.
    Returns "" on failure so the caller can skip the news block gracefully.
    """
    MAX_SEARCH_ROUNDS = 5

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
                "你是商品期货市场资讯员。请调用 web_search 多次搜索棕榈油相关最新资讯，"
                "搜索方向包括：马来西亚/印尼产量出口、中国进口需求、植物油脂联动、政策关税、"
                "大连期货盘面。最多搜索 4 次。\n"
                "完成搜索后，请输出 6–10 条详细新闻条目，每条格式严格如下（保留原始URL）：\n"
                "【标题】新闻标题\n"
                "【来源】网站/媒体名称\n"
                "【URL】原文链接\n"
                "【摘要】3–5句详细摘要，说明具体数据/事件及原因\n"
                "【影响】利多/利空/中性，并解释逻辑\n"
                "---\n"
                "不要省略URL。如果搜索结果里有链接，必须原样保留。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"分析日期：{latest_date}。请搜索并详细整理近期影响大连棕榈油期货价格的重要新闻，"
                "要求每条新闻都有具体数据（如产量数字、涨跌幅、政策名称等）和来源URL。"
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
                    "max_tokens": 3000,
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
        "news_impact": [],
        "news_articles": [],
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
    intraday_instruction = (
        "数据中包含 intraday.one_hour 和 intraday.two_hour。请把 1小时/2小时K线作为核心，"
        "重点分析布林通道上轨/中轨/下轨、当前价在通道中的位置、带宽变化、是否突破或回归中轨，"
        "并给出适合日内操作的短线策略。"
        if snapshot.get("intraday") else
        "数据中无1小时/2小时K线，请不要声称进行了小时线分析。"
    )

    has_news = bool(news_summary and len(news_summary) > 60)
    news_block = (
        f"\n\n【近期市场舆情原始搜索结果（含来源URL）】\n{news_summary}\n"
        if has_news else ""
    )

    if has_news:
        news_instructions = (
            "4) news_impact 数组：4–8 条字符串，每条 2–4 句详细分析，"
            "说明具体数据/事件、逻辑链条及对棕榈油价格的影响方向（以[利多]/[利空]/[中性]开头）；\n"
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
        "请基于以下大连商品交易所棕榈油 P0 连续合约实时行情、1小时/2小时K线、日线数据及市场舆情做综合中文分析。"
        f"{realtime_instruction}{intraday_instruction}"
        f"{news_block}"
        "要求：\n"
        "1) 先给日内短线判断，再给日线背景，不能只做中长期分析；\n"
        "2) bias 字段给出偏多/震荡/偏空；\n"
        "3) analysis 数组：6–8条技术面要点，必须包含1小时布林、2小时布林、实时价位置、趋势、量能、支撑压力，每条 2–3 句；\n"
        "4) intraday_strategy 对象：必须包含 bias, entry, stop, take_profit, invalidation, notes 六个字段，给出日内1小时/2小时级别策略；\n"
        f"{news_instructions}"
        "6) watch_levels 包含数字 support 和 resistance；\n"
        "7) 强调不构成投资建议；\n"
        "8) 只输出 JSON；字段：summary, bias, analysis, intraday_strategy, news_impact, news_articles, watch_levels, risk_note。\n"
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
            "max_tokens": 4000,
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
    intraday = fetch_intraday_bundle()
    news_snapshot = fetch_news_snapshot()

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
        "intraday_updated_at_utc": intraday.get("updated_at_utc"),
        "news_updated_at_utc": news_snapshot.get("updated_at_utc"),
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

        snapshot = daily_snapshot(export, realtime, intraday)

        # Step 1 – detailed news via web search
        news_summary = news_snapshot_to_text(news_snapshot)
        if api_key and not news_summary:
            print("Fetching market news via DeepSeek web search...")
            news_summary = fetch_news_raw(api_key, snapshot)
            preview = news_summary[:150].replace("\n", " ")
            print(f"News raw preview: {preview}...")
        else:
            print(f"News snapshot articles: {len(news_snapshot.get('articles') or [])}")

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
    print(f"Intraday 1H: {bool(intraday.get('one_hour'))}, 2H: {bool(intraday.get('two_hour'))}")
    print(f"News articles: {len(news_snapshot.get('articles') or [])}")


if __name__ == "__main__":
    main()
