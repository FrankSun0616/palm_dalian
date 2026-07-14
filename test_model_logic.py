from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ask_deepseek as ask_backend
from run_ai_analysis import fetch_live_market_input, run_symbol
from update_data import (
    _resolve_trade_bar,
    audit_ai_analysis,
    build_contract_bridge,
    compute_ai_accuracy,
    fetch_daily_once_isolated,
    fetch_daily_with_retry,
)


def quote(symbol: str, price: float, position: int, volume: int = 100) -> dict:
    return {
        "symbol": symbol,
        "name": symbol,
        "trade": str(price),
        "open": str(price - 1),
        "high": str(price + 2),
        "low": str(price - 2),
        "preclose": "90",
        "presettlement": "98",
        "volume": str(volume),
        "position": str(position),
        "tradedate": "2026-07-13",
        "ticktime": "10:00:00",
    }


class ContractBridgeTests(unittest.TestCase):
    def test_highest_open_interest_is_mapped_and_change_uses_settlement(self) -> None:
        board = [
            quote("P0", 100, 1_000, 500),
            quote("P2701", 104, 600, 200),
            quote("P2609", 100, 1_000, 500),
            quote("P2610", 101, 50, 30),
        ]
        bridge = build_contract_bridge("P0", board, "2026-07-12T12:00:00+00:00")
        self.assertIsNotNone(bridge)
        assert bridge is not None
        self.assertEqual(bridge["main"]["symbol"], "P2609")
        self.assertEqual(bridge["secondary"]["symbol"], "P2701")
        self.assertTrue(bridge["mapping_verified"])
        self.assertEqual(bridge["secondary_spread"], 4)
        self.assertEqual(bridge["main"]["reference_type"], "previous_settlement")
        self.assertAlmostEqual(bridge["main"]["change_ratio"], 2 / 98, places=7)
        self.assertEqual(bridge["contract_specs"]["tick_size"], 1)


class LiveQuoteInputTests(unittest.TestCase):
    def test_main_analysis_fetches_quote_at_inference_time(self) -> None:
        board = [quote("P0", 100, 1_000, 500), quote("P2609", 100, 1_000, 500)]
        with patch("run_ai_analysis.fetch_sina_market_board", return_value=board):
            realtime, bridge = fetch_live_market_input("P0", attempts=1)

        self.assertEqual(realtime["price"], 100)
        self.assertEqual(realtime["input_status"], "live")
        self.assertEqual(realtime["source"], "Sina Market Center live request")
        self.assertTrue(realtime["fetched_at_utc"])
        self.assertIsNotNone(bridge)
        assert bridge is not None
        self.assertEqual(bridge["main"]["symbol"], "P2609")

    def test_qna_fetches_lightweight_live_quote(self) -> None:
        class Response:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> list[dict]:
                return [quote("Y0", 200, 2_000, 600)]

        with patch("ask_deepseek.requests.get", return_value=Response()):
            realtime = ask_backend.fetch_live_quote("Y0", "dy_qh", attempts=1)

        self.assertEqual(realtime["status"], "live")
        self.assertEqual(realtime["price"], 200)
        self.assertEqual(realtime["open_interest"], 2_000)
        self.assertTrue(realtime["fetched_at_utc"])

    def test_missing_live_quote_blocks_deepseek_instead_of_using_cache(self) -> None:
        snapshot = {
            "latest_date": "2026-07-14",
            "close": 100.0,
            "change_pct": "+1.00%",
            "ma10": 99.0,
            "ma20": 98.0,
            "ma60": 97.0,
            "low20": 90.0,
            "high20": 110.0,
            "input_freshness": {
                "realtime_fetch_status": "unavailable",
                "realtime_fetch_error": "source timeout",
                "cached_realtime_available_but_not_used": True,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            with (
                patch("run_ai_analysis.load_cached_snapshot", return_value=(snapshot, out_dir, {})),
                patch("run_ai_analysis.generate_ai_analysis") as generate,
            ):
                result = run_symbol("P0")
            written = json.loads((out_dir / "ai_analysis.json").read_text(encoding="utf-8"))

        generate.assert_not_called()
        self.assertEqual(result["status"], "fallback")
        self.assertEqual(written["realtime_input"]["status"], "unavailable")
        self.assertFalse(written["realtime_input"]["cached_quote_used"])
        self.assertIn("缓存报价未用于", written["error"])


class ConservativeFillTests(unittest.TestCase):
    def test_same_bar_stop_and_target_resolves_to_stop(self) -> None:
        result = _resolve_trade_bar(1, 100, 125, 85, 90, 120)
        self.assertEqual(result, (90, "stop_same_bar", True))

    def test_short_same_bar_stop_and_target_resolves_to_stop(self) -> None:
        result = _resolve_trade_bar(-1, 100, 115, 75, 110, 80)
        self.assertEqual(result, (110, "stop_same_bar", True))

    def test_adverse_gap_fills_at_open(self) -> None:
        result = _resolve_trade_bar(1, 85, 95, 80, 90, 120)
        self.assertEqual(result, (85, "gap_stop", False))


class DailyFetchTimeoutTests(unittest.TestCase):
    def test_isolated_daily_fetch_enforces_hard_timeout(self) -> None:
        with patch(
            "update_data.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["python"], timeout=17),
        ) as run:
            with self.assertRaisesRegex(TimeoutError, "exceeded 17s hard timeout"):
                fetch_daily_once_isolated("P0", timeout_seconds=17)
        self.assertEqual(run.call_args.kwargs["timeout"], 17)

    def test_exhausted_fetch_keeps_last_good_daily_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            profile_dir = data_dir / "p0"
            profile_dir.mkdir()
            (profile_dir / "daily.csv").write_text(
                "date,open,high,low,close,volume\n"
                "2026-07-10,9000,9100,8950,9050,100\n",
                encoding="utf-8",
            )
            with (
                patch("update_data.DATA_DIR", data_dir),
                patch("update_data.fetch_daily_once_isolated", side_effect=TimeoutError("timed out")),
            ):
                frame = fetch_daily_with_retry("P0", attempts=1, backoff=0)
        self.assertEqual(frame.attrs["fetch_status"], "stale_fallback")
        self.assertIn("timed out", frame.attrs["fetch_error"])


class AiForwardEvaluationTests(unittest.TestCase):
    def test_fixed_horizon_is_stable_and_collapses_same_window_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "intraday_1h.csv").write_text(
                "datetime,close\n"
                "2026-07-01 10:00:00,100.0\n"
                "2026-07-01 11:15:00,100.2\n"
                "2026-07-01 14:15:00,100.5\n"
                "2026-07-01 15:00:00,101.0\n"
                "2026-07-01 22:00:00,100.9\n"
                "2026-07-01 23:00:00,100.7\n"
                "2026-07-02 10:00:00,100.4\n"
                "2026-07-02 11:15:00,100.1\n"
                "2026-07-02 14:15:00,100.2\n"
                "2026-07-02 15:00:00,100.3\n",
                encoding="utf-8",
            )
            history = {
                "entries": [
                    {"generated_at_utc": "2026-07-01T01:00:00+00:00", "bias": "偏多", "bias_sign": 1, "price_at": 100},
                    {"generated_at_utc": "2026-07-01T01:30:00+00:00", "bias": "偏多", "bias_sign": 1, "price_at": 100},
                    {"generated_at_utc": "2026-07-01T07:30:00+00:00", "bias": "震荡", "bias_sign": 0, "price_at": 100},
                    {"generated_at_utc": "2026-07-02T08:00:00+00:00", "bias": "偏空", "bias_sign": -1, "price_at": 100},
                ]
            }
            (directory / "ai_history.json").write_text(json.dumps(history), encoding="utf-8")

            first = compute_ai_accuracy(directory, current_price=1)
            second = compute_ai_accuracy(directory, current_price=9999)

            self.assertEqual(first["evaluation_method"], "fixed_4_completed_1h_bars_v2")
            self.assertEqual(first["total_evaluated"], 2)
            self.assertEqual(first["hits"], 2)
            self.assertEqual(first["duplicates_collapsed"], 1)
            self.assertEqual(first["pending"], 1)
            self.assertEqual(first["recent_grades"], second["recent_grades"])


class AiIntegrityTests(unittest.TestCase):
    @staticmethod
    def snapshot() -> dict:
        return {
            "close": 100,
            "low20": 90,
            "high20": 110,
            "rsi14": 56.8,
            "realtime": {"price": 100},
            "intraday": {
                "one_hour": {"bollinger": {"upper": 105, "mid": 101, "lower": 95}},
                "four_hour": {"bollinger": {"upper": 110, "mid": 98, "lower": 90}},
            },
        }

    @staticmethod
    def analysis(summary: str) -> dict:
        return {
            "summary": summary,
            "analysis": ["1小时位于中轨下方。", "4小时位于中轨上方。"],
            "watch_levels": {"support": 95, "resistance": 105},
            "intraday_strategy": {
                "bias": "震荡",
                "entry": "等待确认",
                "stop": "94",
                "take_profit": "105",
                "invalidation": "跌破94",
            },
            "decision_frame": {"confidence": 70},
        }

    def test_false_rsi_claim_blocks_ai_from_execution_layer(self) -> None:
        analysis = self.analysis("日线 RSI 超买，短线回调风险高。")
        integrity = audit_ai_analysis(analysis, self.snapshot())
        self.assertFalse(integrity["execution_allowed"])
        self.assertEqual(integrity["status"], "blocked")
        self.assertIn("false_rsi_overbought", {item["code"] for item in integrity["issues"]})

    def test_consistent_analysis_passes(self) -> None:
        analysis = self.analysis("日线 RSI 56.8 未超买，多周期方向分化。")
        integrity = audit_ai_analysis(analysis, self.snapshot())
        self.assertTrue(integrity["execution_allowed"])
        self.assertEqual(integrity["status"], "passed")
        self.assertEqual(integrity["score"], 100)

    def test_future_trading_day_label_cannot_be_presented_as_future_close(self) -> None:
        snapshot = self.snapshot()
        snapshot["realtime_trading_day_label"] = "2026-07-13"
        snapshot["realtime_label_is_future"] = True
        analysis = self.analysis("截至2026-07-13 23:00夜盘收盘，价格维持震荡。")
        integrity = audit_ai_analysis(analysis, snapshot)
        self.assertFalse(integrity["execution_allowed"])
        self.assertIn("future_trade_label_as_clock", {item["code"] for item in integrity["issues"]})

    def test_live_input_must_be_cited_in_summary_and_analysis(self) -> None:
        snapshot = self.snapshot()
        snapshot["realtime_required_for_ai"] = True
        snapshot["input_freshness"] = {
            "realtime_fetch_status": "live",
            "realtime_fetched_at_utc": "2026-07-14T13:20:00+00:00",
            "realtime_market_tick_time": "21:20:00",
        }
        analysis = self.analysis("日线 RSI 56.8 未超买，但摘要没有引用盘口价。")
        integrity = audit_ai_analysis(analysis, snapshot)
        codes = {item["code"] for item in integrity["issues"]}
        self.assertIn("summary_missing_live_price", codes)
        self.assertIn("analysis_missing_live_price", codes)
        self.assertFalse(integrity["execution_allowed"])

    def test_fresh_live_price_citation_passes_live_input_gate(self) -> None:
        snapshot = self.snapshot()
        snapshot["realtime_required_for_ai"] = True
        snapshot["input_freshness"] = {
            "realtime_fetch_status": "live",
            "realtime_fetched_at_utc": "2026-07-14T13:20:00+00:00",
            "realtime_market_tick_time": "21:20:00",
        }
        analysis = self.analysis("实时价 100，日线 RSI 56.8 未超买，多周期方向分化。")
        analysis["analysis"].append("当前实时价 100 位于布林中轨附近。")
        integrity = audit_ai_analysis(analysis, snapshot)
        codes = {item["code"] for item in integrity["issues"]}
        self.assertNotIn("missing_live_quote_input", codes)
        self.assertNotIn("summary_missing_live_price", codes)
        self.assertNotIn("analysis_missing_live_price", codes)
        self.assertTrue(integrity["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
