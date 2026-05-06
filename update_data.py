from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import akshare as ak


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


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

    print(f"Updated {output}")
    print(f"Rows: {len(export)}")
    print(f"Latest: {latest['date']} close={latest['close']}")


if __name__ == "__main__":
    main()
