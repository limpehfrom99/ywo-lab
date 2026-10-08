"""Idea 4: turn-of-the-month. Buy at the close of T-1 (second-to-last trading day of the month),
exit at the close of T+3 (third trading day of the new month) or at a stop 1 daily ATR below entry.
R = P&L / ATR (risk = 1 ATR). Costs: spread at entry+exit, commission, swap 0.01%/night approx.
Baseline: the same trade started on every other day of the month (the 'any day' 4-day hold)."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/bt'); sys.path.insert(0,'/home/claude/lab')
import sr_diag
from weekly_open import frames   # gold M1, US100/US500 M30

def run(sym, g, hold_days=4, swap=0.0001):
    d, atr = sr_diag.daily_atr(g)
    day = g.groupby("nyd").agg(o=("open","first"), h=("high","max"), l=("low","min"), c=("close","last"), sp=("sp","mean"))
    day["atr"] = atr; day = day.dropna(); days = day.index
    month = pd.Series(days.month, index=days)
    # position of each day within its month: last trading day = T
    rank_from_end = month.groupby([days.year, days.month]).cumcount(ascending=False)
    rank_from_start = month.groupby([days.year, days.month]).cumcount()
    comm = g.attrs["comm"]; rows = []
    for i in range(len(days) - hold_days - 1):
        if rank_from_end.iloc[i] != 1: continue       # T-1
        e = day.c.iloc[i] + day.sp.iloc[i] / 2; A = day.atr.iloc[i]; stop = e - A
        px = None; nights = 0
        for q in range(i + 1, i + 1 + hold_days):
            nights += (days[q] - days[q-1]).days
            if day.l.iloc[q] <= stop: px = stop; why = "stop"; break
        if px is None: px = day.c.iloc[q]; why = "time"
        cost = day.sp.iloc[q] / 2 + comm * e * 2 + swap * e * nights
        rows.append(dict(day=days[i], year=days[i].year, R=(px - e - cost) / A, why=why))
    r = pd.DataFrame(rows)
    # baseline: same trade from every day
    base = []
    for i in range(len(days) - hold_days - 1):
        e = day.c.iloc[i]; A = day.atr.iloc[i]; base.append((day.c.iloc[i + hold_days] - e) / A)
    base = np.array(base)
    print(f"\n{sym}: TOM n={len(r)} avgR={r.R.mean():+.3f} t={r.R.mean()/(r.R.std()/np.sqrt(len(r))):+.1f} win={np.mean(r.R>0):.0%}"
          f" | any-day {hold_days}-day hold (gross) avg={base.mean():+.3f}R | TOM gross-ish advantage={r.R.mean()-base.mean():+.3f}")
    print("   per year:", r.groupby("year").R.mean().round(2).to_dict())
    h = len(r)//2; print("   halves: %+.3f / %+.3f" % (r.R.iloc[:h].mean(), r.R.iloc[h:].mean()))
    return r

if __name__ == "__main__":
    for sym, g in frames():
        run(sym, g)
