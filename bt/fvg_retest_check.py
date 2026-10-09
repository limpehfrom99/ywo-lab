"""Checks on the one promising cell of fvg_retest.py (1-hour, target = last pullback low): a random-timing baseline (same side,
same bracket in % of price, random minutes — removes gold's drift) and one-at-a-time neighbours of every setting."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc_grid import load, TF, tstat
from fvg_retest import run

B = load(); atr_df = B["D1"][["atr"]]
Ts = {m: {tf: TF(df, m, atr_df) for tf, df in B.items() if tf in ("M1", "M15", "H1")} for m in (False, True)}
cells = [("base (n=3, buffer 0.05 ATR, 48 bars, rr>=2, gap edge)", {}), ("fractal n=2", dict(n=2)), ("fractal n=5", dict(n=5)),
         ("stop buffer 0", dict(buf=0.0)), ("stop buffer 0.1 ATR", dict(buf=0.1)), ("window 24 bars", dict(window=24)),
         ("window 96 bars", dict(window=96)), ("rr >= 1.5", dict(min_rr=1.5)), ("rr >= 3", dict(min_rr=3.0)), ("entry at gap middle", dict(entry_mid=True))]
for lab, kw in cells:
    rows = []
    for m in (False, True):
        rows += run(Ts[m], "H1", "T1", -1 if m else 1, rand_base=10 if lab.startswith("base") else 0, **kw)
    df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "risk_pct", "side", "R_rand"]); df["t"] = pd.to_datetime(df.t)
    IS = df.t < "2024-01-01"
    extra = f" | random-timing same side {df.R_rand.mean():+.3f} (longs {df[df.side==1].R_rand.mean():+.3f}, shorts {df[df.side==-1].R_rand.mean():+.3f})" if lab.startswith("base") else ""
    print(f"{lab:52s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} | longs {df[df.side==1].R.mean():+.3f} shorts {df[df.side==-1].R.mean():+.3f} "
          f"| <2024 {df.R[IS].mean():+.3f} (n {IS.sum()}) 2024+ {df.R[~IS].mean():+.3f}{extra}", flush=True)
    if lab.startswith("base"):
        print("   by year:", " ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in df.groupby(df.t.dt.year).R.mean().items()))
        print("   2x spread: %+.3f" % (df.R - (df.R - df.R).add(0).mul(0) - 0).mean() if False else "")
