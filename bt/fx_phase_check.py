"""#48 follow-up: #35 breaker on EURUSD / GBPUSD / USDCHF with the 4-hour grid started at each hour (UTC 00/01/02/03 + 4k)
and on FTMO's server clock — the PROTOCOL check from #39. Same rule, same exits as bt/fx_cross_check.py."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc_grid import TF, tstat
import ob_strategies as O
from data_standard_check import to_server, from_server, d1_atr, AGG
from fx_cross_check import run35, COMM_FX
from ftmo_data import load_export

data = {}
for sym in ("EURUSD", "GBPUSD", "USDCHF"):
    d = load_export(glob.glob(f"/home/claude/data/fx2/{sym}_M30_*.csv")[0])
    d.index = from_server(pd.DatetimeIndex(d.index)); d = d[~d.index.isna()].sort_index()
    d = d[["open", "high", "low", "close", "sp"]].copy(); d["sp"] = d.sp * 1.2; data[sym] = d
res = {}
for grid in ("UTC +0h", "UTC +1h", "UTC +2h", "UTC +3h", "FTMO clock"):
    rows_all = []
    for sym, m30 in data.items():
        if grid == "FTMO clock":
            x = m30.copy(); x.index = to_server(m30.index); h4 = x.resample("4h", label="left", closed="left").agg(AGG).dropna()
            u = from_server(h4.index); h4 = h4[~u.isna()]; h4.index = u[~u.isna()]; h4 = h4.sort_index()
        else:
            h4 = m30.resample("4h", label="left", closed="left", offset=f"{int(grid[5])}h").agg(AGG).dropna()
        atr_df = d1_atr(m30)[["atr"]]
        Ts = {m: {"X": TF(m30, m, atr_df), "H4": TF(h4, m, atr_df)} for m in (False, True)}
        raw = {m: O.find_obs(Ts[m]["H4"]) for m in (False, True)}; N = len(Ts[False]["H4"].c)
        for m in (False, True):
            obs = O.lifetimes(raw[m], raw[not m], N)
            rows_all += [r + (sym,) for r in run35(Ts[m], obs, COMM_FX)]
    df = pd.DataFrame(rows_all, columns=["t", "R", "R_flip", "rr", "sym"]); df["t"] = pd.to_datetime(df.t); res[grid] = df
    IS = df.t < "2024-01-01"; per = df.groupby("sym").R.mean()
    print(f"{grid:11s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} | <24 {df.R[IS].mean():+.3f} 24+ {df.R[~IS].mean():+.3f} | "
          + " ".join(f"{s} {v:+.3f}" for s, v in per.items()), flush=True)
allR = pd.concat(res.values()).R
print(f"all five grids pooled: avgR {allR.mean():+.3f} (overlapping trades)")
