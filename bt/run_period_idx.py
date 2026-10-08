import sys; sys.path.insert(0,'/home/claude/bt')
import sr_diag, period_levels as pl, pandas as pd, numpy as np, time
for sym in ("US100", "US500", "TSLA", "AAPL"):
    b5 = pd.read_pickle(f"/home/claude/data/{sym}_m5.pkl")
    sr_diag.COMM = b5.attrs.get("comm", 0.0)
    g = b5[["open","high","low","close","sp","nyd","nym"]].copy()
    d, atr = sr_diag.daily_atr(g)
    lv = pl.period_levels(g, atr); fake = pl.period_levels(g, atr, fake_shift=0.37)
    for tf, W, hold in ((5, 6, 288), (15, 4, 96)):
        b = g if tf == 5 else pl.resample(g, 15); sr_diag.W_CONFIRM = W
        df = sr_diag.simulate(b, lv, atr, hold=hold); fk = sr_diag.simulate(b, fake, atr, hold=hold)
        print(f"{sym} {tf}m: " + sr_diag.stats(df, "real") + " | fake avgR=%+.3f n=%d" % (fk.R.mean(), len(fk)), flush=True)
        print("   per year:", df.groupby("year").R.mean().round(2).to_dict(), flush=True)
