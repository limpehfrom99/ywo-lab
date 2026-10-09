"""Diagnostic for 21a: the band's 10:00 entries always match the opening candle, so how does the band do when it may
only enter from 10:30 on (a different bet from the live rule)? Same rules otherwise; reported, not a new tuned rule."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from lab import opening_candle
from ftmo_sim import challenge, funded
from news import load_calendar, fed_days
from noise_band import run
out = pd.read_pickle("/home/claude/data/noise_band_out.pkl")
fed = set(pd.to_datetime(list(fed_days(load_calendar("/home/claude/news/news_usd.csv")))))
oc = {}
for name, pat, comm in (("US100.cash", "US100.cash_M30", 0.0), ("TSLA", "TSLA_M30", 0.00002)):
    d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0])
    oc[name] = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01", skip_days=fed)
for sym, comm in (("US100.cash", 0.0), ("US500.cash", 0.0), ("TSLA", 0.00002)):
    _, _, _, days, O, C, VW, SP = out[sym]
    raw, lev, tr = run(days, O, C, VW, SP, comm=comm, first_entry=1)
    x = raw.dropna(); x = x[x.index >= "2022-01-01"]
    h1, h2 = x.iloc[:len(x)//2], x.iloc[len(x)//2:]
    yr = x.groupby(x.index.year).sum()
    line = (f"{sym} band, entries from 10:30 only: {len(tr)} trades, {x.mean()*1e4:+.2f} bp/day at 1x, Sharpe {x.mean()/x.std()*np.sqrt(252):+.2f}, "
            f"t {x.mean()/x.std()*np.sqrt(len(x)):+.1f}, halves {h1.mean()*1e4:+.2f}/{h2.mean()*1e4:+.2f} bp, years " + " ".join(f"{y%100}:{v*100:+.1f}%" for y,v in yr.items()))
    if sym in oc:
        o = oc[sym].R; cm = x.index.intersection(o.index)
        line += f", corr with opening candle {x.reindex(cm).corr(o.reindex(cm)):.2f}"
    print(line)
# all-entries version halves for the log
for sym in ("US100.cash", "US500.cash", "TSLA"):
    x = out[sym][0].dropna(); x = x[x.index >= "2022-01-01"]
    print(f"{sym} as published, 2022-2026: halves {x.iloc[:len(x)//2].mean()*1e4:+.2f}/{x.iloc[len(x)//2:].mean()*1e4:+.2f} bp/day, worst day at 1x {x.min()*100:+.2f}%")
