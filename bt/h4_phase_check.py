"""#39 follow-up: #35 (4-hour breaker block, 2R) with the 4-hour grid started at each possible hour (UTC 00/01/02/03 + 4k) and on
FTMO's server clock (17:00 New York = 21:00 or 22:00 UTC). Same rule, nothing re-tuned. Gold 2012 - Oct 2026, exits on 1-minute."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc_grid import load, tstat
from data_standard_check import run_35, h4_server, AGG

t0 = time.time(); B = load(); g = B["M1"]
res = {}
for k in range(4):
    B2 = dict(B); B2["H4"] = g.resample("4h", label="left", closed="left", offset=f"{k}h").agg(AGG).dropna(); res[f"UTC grid +{k}h"] = run_35(B2)
B2 = dict(B); B2["H4"] = h4_server(g); res["FTMO server clock"] = run_35(B2)
for lab, df in res.items():
    IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
    print(f"{lab:20s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} | <2024 {df.R[IS].mean():+.3f} 2024+ {df.R[~IS].mean():+.3f} "
          f"| yrs>0 {(yr>0).sum()}/{len(yr)} worst {yr.min():+.2f} | longs {df[df.side==1].R.mean():+.3f} shorts {df[df.side==-1].R.mean():+.3f}", flush=True)
allR = pd.concat(res.values()).R
print(f"all five grids pooled: avgR {allR.mean():+.3f} over {len(allR)} trades (overlapping, not independent); done {time.time()-t0:.0f}s")
