from __future__ import annotations

import argparse
from pathlib import Path

import akshare as ak


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    frame = ak.futures_zh_daily_sina(symbol=args.symbol)
    if frame is None or frame.empty:
        raise RuntimeError(f"AKShare returned no daily rows for {args.symbol}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
