"""Unpack the exporter's zip parts into /home/claude/data/x and check every file.

python3 -I ingest.py ZIP [ZIP ...]
Only members named like SYMBOL_TF_YYYYMMDDHHMM_YYYYMMDDHHMM.npz/.csv.gz and the exporter's info files are extracted
(flat, no paths). Then every file is loaded and summarised: bars, first/last bar, bars per day, median spread by year,
and New York-time sanity (busiest 30 minutes for US stocks/indices should be 9:30-10:00).
"""
import os, re, sys, zipfile
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "lab"))
from ftmo_data import load_any  # noqa: E402
from universe import NAME_RE, group_of  # noqa: E402

DEST = os.environ.get("YWO_DEST", "/home/claude/data/x")
INFO = {"manifest.txt", "symbol_specs.csv", "symbols_available.txt", "account.txt"}


def unpack(zips):
    os.makedirs(DEST, exist_ok=True); n = 0
    for z in zips:
        with zipfile.ZipFile(z) as f:
            for m in f.infolist():
                name = os.path.basename(m.filename)
                if m.is_dir() or not (NAME_RE.match(name) or name in INFO): continue
                with f.open(m) as src, open(os.path.join(DEST, name), "wb") as dst: dst.write(src.read())
                n += 1
    return n


def check(path):
    d = load_any(path); sym, tf = d.attrs["symbol"], d.attrs["tf"]
    ny = d.index - pd.Timedelta(hours=7)
    per_day = pd.Series(1, index=ny.normalize()).groupby(level=0).size()
    row = dict(symbol=sym, tf=tf, group=group_of(sym), bars=len(d), first=d.index[0].date(), last=d.index[-1].date(),
               bars_per_day=float(per_day.median()) if tf != "D1" else 1.0,
               spread_med=float(d.sp[d.sp > 0].median()) if (d.sp > 0).any() else np.nan)
    if tf != "D1":
        # first year with full intraday bars (median bars/day >= 60% of the last year's)
        by_year = per_day.groupby(per_day.index.year).median()
        full = by_year[by_year >= 0.6 * by_year.iloc[-1]]
        row["intraday_from"] = int(full.index[0]) if len(full) else None
        row["bars_per_day_by_year"] = " ".join(f"{y % 100:02d}:{v:.0f}" for y, v in by_year.items())
        if group_of(sym) in ("stock", "us_index") and d.tickvol.sum() > 0:
            hh = (ny.hour * 60 + ny.minute) // 30 * 30
            recent = d.index >= d.index[-1] - pd.Timedelta(days=365)
            busy = d.tickvol[recent].groupby(hh[recent]).mean().idxmax()
            row["busiest_ny"] = f"{busy // 60:02d}:{busy % 60:02d}"
    return row


def main():
    zips = sys.argv[1:]
    if zips: print(f"extracted {unpack(zips)} files into {DEST}")
    rows = []
    for p in sorted(os.listdir(DEST)):
        if NAME_RE.match(p):
            try: rows.append(check(os.path.join(DEST, p)))
            except Exception as e: rows.append(dict(symbol=p, tf="?", error=repr(e)))
    df = pd.DataFrame(rows)
    out = os.path.join(HERE, "..", "results", "data_coverage.csv"); df.to_csv(out, index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 80)
    print(df.drop(columns=[c for c in ("bars_per_day_by_year",) if c in df]).to_string(index=False))
    print(f"\n{len(df)} files, {df.symbol.nunique()} symbols -> {out}")


if __name__ == "__main__":
    main()
