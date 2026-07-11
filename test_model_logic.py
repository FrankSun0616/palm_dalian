from __future__ import annotations

import unittest

from update_data import _resolve_trade_bar, build_contract_bridge


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


if __name__ == "__main__":
    unittest.main()
