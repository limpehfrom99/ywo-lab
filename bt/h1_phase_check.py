"""#39 follow-up: #33 (1-hour gap retest after a break of structure, pullback-low target >= 2R) with the 1-hour grid started at :00
(as found, = FTMO's candles), :15, :30, :45. Same rule, nothing re-tuned. Gold 2012 - Oct 2026, exits on 1-minute."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc_grid import load, tstat
from data_standard_check import run_33, AGG

t0 = time.time(); B = load(); g = B["M1"]; res = {}
for k in (0, 15, 30, 45):
    B2 = dict(B); B2["H1"] = g.resample("1h", label="left", closed="left", offset=f"{k}min").agg(AGG).dropna(); res[f"1-hour grid at :{k:02d}"] = run_33(B2)
for lab, df in res.items():
    IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
    print(f"{lab:20s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} | <2024 {df.R[IS].mean():+.3f} 2024+ {df.R[~IS].mean():+.3f} "
          f"| yrs>0 {(yr>0).sum()}/{len(yr)} worst {yr.min():+.2f} | longs {df[df.side==1].R.mean():+.3f} shorts {df[df.side==-1].R.mean():+.3f}", flush=True)
allR = pd.concat(res.values()).R
print(f"all four grids pooled: avgR {allR.mean():+.3f} over {len(allR)} trades (overlapping); done {time.time()-t0:.0f}s")
