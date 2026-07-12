from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from update_data import (
    _resolve_trade_bar,
    audit_ai_analysis,
    build_contract_bridge,
    compute_ai_accuracy,
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


if __name__ == "__main__":
    unittest.main()
