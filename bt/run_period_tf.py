import sys; sys.path.insert(0,'/home/claude/bt')
import sr_diag, period_levels as pl, pandas as pd, numpy as np, time
sr_diag.START = "2012-01-01"
g = sr_diag.load(); d, atr = sr_diag.daily_atr(g)
lv = pl.period_levels(g, atr); fake = pl.period_levels(g, atr, fake_shift=0.37)
for tf, W, hold in ((5, 6, 288), (15, 4, 96)):
    t0 = time.time()
    b = pl.resample(g, tf); sr_diag.W_CONFIRM = W
    df = sr_diag.simulate(b, lv, atr, hold=hold); df.to_pickle(f"/home/claude/bt/period_{tf}m.pkl")
    print(f"\n== gold {tf}-minute confirmation, 3R ==", flush=True)
    print(sr_diag.stats(df, "real levels, all"), flush=True)
    for k_ in ("W", "M", "Q", "H", "Y"): print(sr_diag.stats(df[df.kind == k_], f"  {k_} levels"), flush=True)
    print(sr_diag.stats(df[df.touch == 1], "  first touch"), flush=True)
    print(sr_diag.stats(df[df.year >= 2020], "  2020-2026 only"), flush=True)
    print(df.groupby("year").R.agg(["count", "mean"]).round(2).T.to_string(), flush=True)
    fk = sr_diag.simulate(b, fake, atr, hold=hold); print(sr_diag.stats(fk, "fake levels"), flush=True)
    print("elapsed", round(time.time()-t0), flush=True)
