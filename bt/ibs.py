"""IBS mean reversion with a stop, for FTMO sizing. Long when IBS < 0.2 and close > 200-SMA; short when IBS > 0.8 and close < 200-SMA.
Entry at the close (+ half spread); stop = entry -/+ 2 x ATR(14) (checked on daily lows/highs, gap fills at the open);
exit at the first close beyond the previous day's high (low for shorts) or after 5 days. R per planned risk (2 ATR). Swap 0.01%/night."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from daily_ideas import daily_from_export

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))
def run(d, comm=0.0, swap=0.0001, stop_atr=2.0, max_days=5, ibs_lo=0.2):
    c, h, l, o = d.c, d.h, d.l, d.o; sma = c.rolling(200).mean(); ibs = (c - l) / (h - l).replace(0, np.nan); rows = []; i = 200
    while i < len(d) - 1:
        side = 1 if (ibs.iloc[i] < ibs_lo and c.iloc[i] > sma.iloc[i]) else (-1 if (ibs.iloc[i] > 1 - ibs_lo and c.iloc[i] < sma.iloc[i]) else 0)
        if side == 0: i += 1; continue
        e = c.iloc[i] + side * d.sp.iloc[i] / 2; risk = stop_atr * d.atr.iloc[i]; stop = e - side * risk; px = None
        for q in range(i + 1, min(i + 1 + max_days, len(d))):
            if side == 1 and l.iloc[q] <= stop: px = min(stop, o.iloc[q]); why = "stop"; break
            if side == -1 and h.iloc[q] >= stop: px = max(stop, o.iloc[q]); why = "stop"; break
            if (side == 1 and c.iloc[q] > h.iloc[q-1]) or (side == -1 and c.iloc[q] < l.iloc[q-1]) or q == min(i + max_days, len(d) - 1): px = c.iloc[q]; why = "exit"; break
        nights = (d.index[q] - d.index[i]).days
        rows.append(dict(day=d.index[i], year=d.index[i].year, side=side, R=(side * (px - e) - d.sp.iloc[q] / 2 - comm * e * 2 - swap * e * nights) / risk, why=why, stop_pct=risk / e * 100, exit_day=d.index[q]))
        i = q + 1
    return pd.DataFrame(rows).set_index("day")

if __name__ == "__main__":
    out = {}
    for name, comm in (("US100.cash", 0.0), ("US500.cash", 0.0), ("AAPL", 0.00002), ("TSLA", 0.00002)):
        d = daily_from_export(name); r = run(d, comm); out[name] = r
        by = r.groupby("year").R.mean().round(2); h = len(r) // 2
        print(f"{name:11s} n={len(r)} avgR={r.R.mean():+.3f} t={t(r.R):+.1f} win={np.mean(r.R>0):.0%} halves {r.R.iloc[:h].mean():+.3f}/{r.R.iloc[h:].mean():+.3f} last60 {r.R.iloc[-60:].mean():+.3f} longs {r.R[r.side==1].mean():+.3f} (n={int((r.side==1).sum())}) shorts {r.R[r.side==-1].mean():+.3f} stops {np.mean(r.why=='stop'):.0%} stop%% median {r.stop_pct.median():.2f}")
        print("   per year:", by.to_dict())
        for k in (0.1, 0.3): rr = run(d, comm, ibs_lo=k); print(f"   IBS threshold {k}: n={len(rr)} avgR={rr.R.mean():+.3f} t={t(rr.R):+.1f}")
        rr = run(d, comm, stop_atr=1.0); print(f"   stop 1 ATR: n={len(rr)} avgR={rr.R.mean():+.3f} t={t(rr.R):+.1f} stops {np.mean(rr.why=='stop'):.0%}")
    pd.to_pickle(out, "/home/claude/bt/ibs_trades.pkl")
