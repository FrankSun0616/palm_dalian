from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"{path}: root must be an object"
    return value


def parse_utc(value: object, label: str) -> datetime:
    assert isinstance(value, str) and value, f"{label}: missing timestamp"
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def validate_ohlc(path: Path, time_field: str, minimum_rows: int) -> list[dict[str, str]]:
    fields, rows = read_csv(path)
    required = {time_field, "open", "high", "low", "close", "volume"}
    assert required.issubset(fields), f"{path}: missing {sorted(required - set(fields))}"
    assert len(rows) >= minimum_rows, f"{path}: only {len(rows)} rows"
    labels = [row[time_field] for row in rows]
    assert labels == sorted(labels), f"{path}: {time_field} is not sorted"
    assert len(labels) == len(set(labels)), f"{path}: duplicate {time_field} values"
    for index, row in enumerate(rows):
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        volume = float(row["volume"])
        assert high >= max(open_price, close), f"{path}:{index + 2}: high below body"
        assert low <= min(open_price, close), f"{path}:{index + 2}: low above body"
        assert high >= low, f"{path}:{index + 2}: inverted range"
        assert volume >= 0, f"{path}:{index + 2}: negative volume"
    return rows


def validate_symbol(symbol: str) -> None:
    directory = ROOT / "data" / symbol.lower()
    daily_rows = validate_ohlc(directory / "daily.csv", "date", 200)
    for filename in ("intraday_1h.csv", "intraday_2h.csv", "intraday_4h.csv"):
        validate_ohlc(directory / filename, "datetime", 20)

    source = read_json(directory / "source_meta.json")
    assert source.get("symbol") == symbol, f"{symbol}: source symbol mismatch"
    assert "DCE" in str(source.get("market", "")), f"{symbol}: market is not DCE"
    assert source.get("latest_date") == daily_rows[-1]["date"], f"{symbol}: latest date mismatch"
    parse_utc(source.get("updated_at_utc"), f"{symbol} source updated_at_utc")

    intraday = read_json(directory / "intraday_meta.json")
    assert intraday.get("symbol") == symbol, f"{symbol}: intraday symbol mismatch"
    parse_utc(intraday.get("updated_at_utc"), f"{symbol} intraday updated_at_utc")
    for key in ("one_hour", "two_hour", "four_hour"):
        block = intraday.get(key)
        assert isinstance(block, dict), f"{symbol}: missing {key}"
        boll = block.get("bollinger")
        assert isinstance(boll, dict), f"{symbol}: missing {key}.bollinger"
        lower = float(boll["lower"])
        middle = float(boll["mid"])
        upper = float(boll["upper"])
        assert lower <= middle <= upper, f"{symbol}: invalid {key} bollinger order"

    ai = read_json(directory / "ai_analysis.json")
    assert ai.get("status") in {"ok", "fallback"}, f"{symbol}: invalid AI status"
    parse_utc(ai.get("generated_at_utc"), f"{symbol} AI generated_at_utc")
    assert isinstance(ai.get("analysis"), list), f"{symbol}: AI analysis must be a list"
    assert isinstance(ai.get("watch_levels"), dict), f"{symbol}: AI watch levels missing"

    news = read_json(directory / "news_snapshot.json")
    parse_utc(news.get("updated_at_utc"), f"{symbol} news updated_at_utc")
    assert isinstance(news.get("articles"), list), f"{symbol}: news articles must be a list"

    bridge = read_json(directory / "contract_bridge.json")
    assert bridge.get("symbol") == symbol, f"{symbol}: contract bridge symbol mismatch"
    assert bridge.get("market") == "DCE", f"{symbol}: contract bridge is not DCE"
    parse_utc(bridge.get("updated_at_utc"), f"{symbol} bridge updated_at_utc")
    prefix = symbol.removesuffix("0")
    main = bridge.get("main")
    secondary = bridge.get("secondary")
    assert isinstance(main, dict), f"{symbol}: main contract missing"
    assert re.fullmatch(rf"{prefix}\d{{4}}", str(main.get("symbol", ""))), f"{symbol}: invalid main contract"
    assert float(main.get("price", 0)) > 0, f"{symbol}: invalid main price"
    assert int(main.get("open_interest", 0)) > 0, f"{symbol}: invalid main open interest"
    assert main.get("reference_type") == "previous_settlement", f"{symbol}: live change must use previous settlement"
    assert isinstance(secondary, dict), f"{symbol}: secondary contract missing"
    assert 0 <= float(bridge.get("secondary_open_interest_ratio", -1)), f"{symbol}: invalid secondary OI ratio"
    assert bridge.get("roll_state") in {"stable", "watch", "urgent"}, f"{symbol}: invalid roll state"
    specs = bridge.get("contract_specs")
    assert isinstance(specs, dict), f"{symbol}: contract specs missing"
    assert float(specs.get("multiplier", 0)) == 10, f"{symbol}: contract multiplier mismatch"
    assert float(specs.get("tick_size", 0)) == 1, f"{symbol}: post-2026 tick size mismatch"
    assert source.get("main_contract") == main.get("symbol"), f"{symbol}: source/main mapping mismatch"

    model = read_json(directory / "model_validation.json")
    assert model.get("symbol") == symbol, f"{symbol}: model symbol mismatch"
    assert model.get("status") in {"positive", "unproven", "rejected", "insufficient"}, f"{symbol}: invalid model status"
    parse_utc(model.get("generated_at_utc"), f"{symbol} model generated_at_utc")
    holdout = model.get("holdout")
    assert isinstance(holdout, dict), f"{symbol}: holdout metrics missing"
    assert int(holdout.get("trades", 0)) >= 30, f"{symbol}: holdout sample too small"
    integrity = model.get("integrity")
    assert isinstance(integrity, dict), f"{symbol}: model integrity missing"
    for key in ("entry_after_signal", "no_overlapping_positions", "same_bar_conservative", "chronological_split"):
        assert integrity.get(key) is True, f"{symbol}: model integrity failed: {key}"
    recent_trades = model.get("recent_trades")
    assert isinstance(recent_trades, list) and recent_trades, f"{symbol}: recent model trades missing"
    for trade in recent_trades:
        assert int(trade["entry_index"]) == int(trade["signal_index"]) + 1, f"{symbol}: lookahead entry detected"


def validate_frontend() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    collector = IdCollector()
    collector.feed(html)
    duplicates = sorted({value for value in collector.ids if collector.ids.count(value) > 1})
    assert not duplicates, f"duplicate HTML ids: {duplicates}"
    required_ids = {
        "tradeGate",
        "marketRegime",
        "dataConfidence",
        "longSetupEntry",
        "shortSetupEntry",
        "posLotsRec",
        "posRR",
        "aiFreshness",
        "aiIntegrity",
        "aiIntegrityStatus",
        "priceCanvas",
        "contractMapping",
        "mainContractPrice",
        "rollRisk",
        "modelStatus",
        "modelExpectancy",
    }
    assert required_ids.issubset(collector.ids), f"missing UI ids: {sorted(required_ids - set(collector.ids))}"

    css_version = re.search(r"styles\.css\?v=([\w-]+)", html)
    js_version = re.search(r"app\.js\?v=([\w-]+)", html)
    assert css_version and js_version, "cache-busting versions are missing"
    assert css_version.group(1) == js_version.group(1), "CSS/JS cache versions differ"

    combined = html + "\n" + app
    forbidden = (
        "github_pat_",
        "ghp_",
        "PAT_KEY",
        "localStorage.setItem(\"gh_pat",
        "DEEPSEEK_API_KEY",
    )
    hits = [token for token in forbidden if token in combined]
    assert not hits, f"credential-like frontend content found: {hits}"
    assert "GH_WORKFLOW_DISPATCH_URL" in app, "direct workflow dispatch is missing"
    assert "PUBLIC_ACTIONS_TOKEN = atob(" in app, "one-click public dispatch credential is missing"
    assert 'run_ai_analysis: "true", symbols: "P0,Y0"' in app, "dual-symbol AI input is missing"
    assert "DeepSeek V4-Pro" in html, "V4-Pro identity is missing from the UI"
    assert "assessAiReliability" in app, "AI decision firewall is missing"


def validate_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "update-data.yml").read_text(encoding="utf-8")
    pipeline = (ROOT / "update_data.py").read_text(encoding="utf-8")
    ask_backend = (ROOT / "ask_deepseek.py").read_text(encoding="utf-8")
    assert 'cron: "*/5 * * * *"' in workflow, "five-minute data cron missing"
    assert 'cron: "0 */3 * * *"' in workflow, "three-hour AI cron missing"
    assert "workflow_dispatch:" in workflow, "manual dispatch missing"
    assert "run_ai_analysis" in workflow, "manual AI toggle missing"
    assert "inputs.symbols" in workflow, "manual symbol selection is missing"
    assert "test_dashboard.py" in workflow, "dashboard validation step missing"
    assert "test_model_logic.py" in workflow, "model logic unit test step missing"
    assert "ThreadPoolExecutor(max_workers=len(symbols))" in pipeline, "P0/Y0 pipeline is not parallel"
    for path, source in (("update_data.py", pipeline), ("ask_deepseek.py", ask_backend)):
        assert 'DEEPSEEK_MODEL = "deepseek-v4-pro"' in source, f"{path}: V4-Pro is not fixed"
        assert '"thinking": DEEPSEEK_THINKING' in source, f"{path}: thinking mode is missing"
        assert '"reasoning_effort": DEEPSEEK_REASONING_EFFORT' in source, f"{path}: high effort is missing"
        assert "deepseek-chat" not in source and "deepseek-reasoner" not in source, f"{path}: legacy model remains"
    assert "fixed_4_completed_1h_bars_v2" in pipeline, "fixed-horizon AI evaluation is missing"
    assert "audit_ai_analysis" in pipeline, "AI consistency audit is missing"
    assert "future_trade_label_as_clock" in pipeline, "future trading-day label guard is missing"


def main() -> None:
    validate_symbol("P0")
    validate_symbol("Y0")
    validate_frontend()
    validate_workflow()
    print("dashboard validation: OK (P0, Y0, frontend, workflow)")


if __name__ == "__main__":
    main()
