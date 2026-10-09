#!/usr/bin/env python3
"""Load FTMO / MT5 "Export Bars" CSV files and check their health.

Usage:
    python ftmo_data.py FILE.csv [FILE2.csv ...]

In Python:
    from ftmo_data import load_export, health
    d = load_export("TSLA_M30_....csv")   # index = server time; columns open high low close tickvol vol spread sp
    print(health(d))

`sp` is the spread in price units (SPREAD points x point size). The point size is in d.attrs["point"].
FTMO server time = New York + 7 hours all year, so New York time = index - 7h.
"""
import re
import sys

import numpy as np
import pandas as pd

SERVER_MINUS_NY_HOURS = 7


def load_export(path):
    d = pd.read_csv(path, sep="\t", dtype=str)
    d.columns = [c.strip().strip("<>").lower() for c in d.columns]
    decimals = d["open"].str.split(".").str[1].str.len().max()
    decimals = 0 if pd.isna(decimals) else int(decimals)
    for c in ["open", "high", "low", "close", "tickvol", "vol", "spread"]:
        if c in d:
            d[c] = pd.to_numeric(d[c])
        else:
            d[c] = 0.0
    when = d["date"] + " " + (d["time"] if "time" in d else "00:00:00")
    d.index = pd.to_datetime(when, format="%Y.%m.%d %H:%M:%S")
    d = d[["open", "high", "low", "close", "tickvol", "vol", "spread"]].sort_index()
    point = 10.0 ** -decimals
    d["sp"] = d["spread"] * point
    d.attrs["point"] = point
    m = re.search(r"([A-Za-z0-9.]+?)_(M1|M5|M15|M30|H1|H4|D1)_", str(path).split("/")[-1])
    d.attrs["symbol"], d.attrs["tf"] = (m.group(1), m.group(2)) if m else ("?", "?")
    return d


def load_npz(path):
    """Read a compact file written by tools/export/export_history.py (format ywo-bars-v1). Same output as load_export."""
    import json
    with np.load(path) as z:
        meta = json.loads(bytes(z["meta"]).decode())
        t = meta["t0"] + np.cumsum(z["dt"].astype(np.int64))
        o_pc, c_o = z["o_pc"].astype(np.int64), z["c_o"].astype(np.int64)
        o = np.cumsum(o_pc) + np.cumsum(c_o) - c_o
        c = o + c_o
        h = np.maximum(o, c) + z["h_x"].astype(np.int64)
        lo = np.minimum(o, c) - z["x_l"].astype(np.int64)
        point = 10.0 ** -meta["digits"]
        d = pd.DataFrame({"open": o * point, "high": h * point, "low": lo * point, "close": c * point,
                          "tickvol": z["tv"].astype(np.int64), "vol": z["rv"].astype(np.int64), "spread": z["sp"].astype(np.int64)},
                         index=pd.to_datetime(t, unit="s"))
    d[["open", "high", "low", "close"]] = d[["open", "high", "low", "close"]].round(meta["digits"])
    d = d[~d.index.duplicated()].sort_index()
    d["sp"] = d["spread"] * point
    d.attrs.update(point=point, symbol=meta["symbol"], tf=meta["tf"], server=meta.get("server", "?"))
    return d


def load_any(path):
    """load_npz for .npz files, load_export for MT5 'Export Bars' text files (.csv or .csv.gz)."""
    return load_npz(path) if str(path).endswith(".npz") else load_export(path)


def health(d):
    """Per year: bars per day, most common first bar (server time), busiest half-hour, median spread, real-volume share."""
    days = pd.Series(d.index.normalize(), index=d.index)
    per_day = d.groupby(days).size()
    first = d.index.to_series().groupby(days).min().dt.strftime("%H:%M")
    hh = d.index.strftime("%H:%M")
    rows = []
    for y in sorted(set(d.index.year)):
        sel = d.index.year == y
        dy = d[sel]
        py = per_day[per_day.index.year == y]
        fy = first[first.index.year == y]
        busiest = dy.groupby(hh[sel]).tickvol.mean().idxmax() if dy.tickvol.sum() > 0 else "-"
        sp = dy.sp[dy.sp > 0]
        rows.append({"year": y, "days": len(py), "bars/day": float(py.median()),
                     "first bar": fy.mode().iloc[0] if len(fy) else "-",
                     "busiest half-hour": busiest,
                     "median spread": round(float(sp.median()), 4) if len(sp) else None,
                     "real volume %": int((dy.vol > 0).mean() * 100)})
    return pd.DataFrame(rows).set_index("year")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pd.set_option("display.width", 200)
    for f in sys.argv[1:]:
        d = load_any(f)
        print(f"\n== {d.attrs['symbol']} {d.attrs['tf']}: {len(d):,} bars, {d.index[0]} -> {d.index[-1]}, point {d.attrs['point']}")
        print("   (FTMO stock/index files: the 9:30 New York open should show as 16:30 server time)")
        print(health(d).to_string())
