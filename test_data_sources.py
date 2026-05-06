from __future__ import annotations

import os
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def ok(name: str, **details: object) -> dict[str, object]:
    return {"method": name, "valid": True, **details}


def fail(name: str, error: BaseException) -> dict[str, object]:
    return {
        "method": name,
        "valid": False,
        "error": f"{type(error).__name__}: {error}",
    }


def summarize_df(df: pd.DataFrame) -> dict[str, object]:
    if df is None or df.empty:
        raise ValueError("empty dataframe")

    date_col = "date" if "date" in df.columns else df.columns[0]
    last = df.tail(1).iloc[0].to_dict()
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "latest_date": str(last.get(date_col)),
        "latest_close": str(last.get("close", last.get("收盘价", ""))),
        "sample_tail": df.tail(3).to_dict(orient="records"),
    }


def test_akshare_daily() -> dict[str, object]:
    import akshare as ak

    df = ak.futures_zh_daily_sina(symbol="P0")
    summary = summarize_df(df)

    export = df.rename(
        columns={
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        }
    )
    export = export[["date", "open", "high", "low", "close", "volume"]]
    out = DATA_DIR / "palm_oil_p0_daily.csv"
    export.to_csv(out, index=False)

    return ok("AKShare futures_zh_daily_sina(P0)", output=str(out), **summary)


def test_akshare_spot() -> dict[str, object]:
    import akshare as ak

    # AKShare has changed this API over time, so test a few documented/common forms.
    attempts = [
        ("market=CF, symbol=P0", lambda: ak.futures_zh_spot(symbol="P0", market="CF")),
        ("market=CF, symbol=P2609", lambda: ak.futures_zh_spot(symbol="P2609", market="CF")),
        ("market=DC, symbol=P0", lambda: ak.futures_zh_spot(symbol="P0", market="DC")),
    ]
    errors = []
    for label, fn in attempts:
        try:
            df = fn()
            summary = summarize_df(df)
            return ok(f"AKShare futures_zh_spot({label})", **summary)
        except Exception as exc:  # noqa: BLE001 - this is a source probe.
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
    raise RuntimeError(" | ".join(errors))


def test_tushare_daily_without_token() -> dict[str, object]:
    import tushare as ts

    token = os.getenv("TUSHARE_TOKEN", "")
    if token:
        ts.set_token(token)
        pro = ts.pro_api()
    else:
        pro = ts.pro_api()

    df = pro.fut_daily(ts_code="P.DCE")
    return ok("Tushare fut_daily(P.DCE)", token_present=bool(token), **summarize_df(df))


def test_dce_portal() -> dict[str, object]:
    url = "https://extportal.dce.com.cn/file/pc/index.html"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return ok(
        "DCE official portal",
        status_code=resp.status_code,
        content_type=resp.headers.get("content-type", ""),
        bytes=len(resp.content),
    )


def test_sina_quote_page() -> dict[str, object]:
    url = "https://finance.sina.com.cn/futures/quotes/P0.shtml"
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    text = resp.text
    return ok(
        "Sina futures quote page P0",
        status_code=resp.status_code,
        bytes=len(resp.content),
        contains_palm=("棕榈" in text or "P0" in text),
    )


TESTS = [
    test_akshare_daily,
    test_akshare_spot,
    test_tushare_daily_without_token,
    test_dce_portal,
    test_sina_quote_page,
]


def main() -> None:
    print(f"Run time: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Output folder: {DATA_DIR}")
    print()
    for test in TESTS:
        name = test.__name__
        print(f"=== {name} ===")
        try:
            result = test()
        except Exception as exc:  # noqa: BLE001 - command-line diagnostics.
            result = fail(name, exc)
            if os.getenv("VERBOSE_ERRORS"):
                traceback.print_exc()
        print(pd.Series(result).to_string())
        print()


if __name__ == "__main__":
    main()
