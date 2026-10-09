"""Ideas 10 + 11.
10. Crypto weekend effect, BTCUSD (FTMO M30 export 2020-08..2026-10; daily-only bars possible before 2021-09 like the
    indices — checked below). Weekend = Friday 21:00 UTC -> Monday 00:00 UTC. Measures: weekend return vs weekday
    return (in ATR); Monday breakout of the weekend range (buy above the weekend high / sell below the low at the first
    30-min close beyond it on Monday, stop at the range midpoint, exit at Monday 23:30 UTC). Costs 0.0325%/side + spread.
11. Gold hour-of-day drift: mean close-to-close return by NY hour, 2012-2026, per year; an hour qualifies if the sign is
    the same in >= 10 of 14 full years. Always-on rule for any qualifying hour, costs = spread + commission per trade.
"""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/bt'); sys.path.insert(0,'/home/claude/lab')
from ftmo_data import load_export
from smc_data import finish
import sr_diag
from gold_m1 import COMM as GCOMM

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))

# ---------- 10. BTC
f = glob.glob("/home/claude/data/assets/BTCUSD_M30_*.csv")[0]
x = load_export(f); x.index = x.index - pd.Timedelta(hours=7)
x.index = x.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)
x = x[~x.index.isna()][["open","high","low","close","sp"]]
b = finish(x, 0.000325)                     # commission per side
per_day = b.groupby(b.index.normalize()).size()
print("BTC bars/day by year:", per_day.groupby(per_day.index.year).mean().round(1).to_dict())
b = b[b.index >= "2021-09-14"]              # intraday bars only
d = b.groupby(b.index.normalize()).agg(o=("open","first"), c=("close","last"), h=("high","max"), l=("low","min"))
pc = d.c.shift(1); tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1); atr = tr.rolling(14).mean().shift(1)
rows = []
for day in d.index:
    if day.weekday() != 4 or not np.isfinite(atr.get(day, np.nan)): continue
    fri = b[(b.index >= day + pd.Timedelta(hours=21)) & (b.index < day + pd.Timedelta(hours=21, minutes=30))]
    mon = b[(b.index >= day + pd.Timedelta(days=3)) & (b.index < day + pd.Timedelta(days=3, minutes=30))]
    if len(fri) == 0 or len(mon) == 0: continue
    wk = b[(b.index > day + pd.Timedelta(hours=21)) & (b.index < day + pd.Timedelta(days=3))]
    rows.append(dict(day=day, year=day.year, ret=(mon.close.iloc[0] - fri.close.iloc[0]) / atr[day], wh=wk.high.max(), wl=wk.low.min(), A=atr[day]))
w = pd.DataFrame(rows)
wd = ((d.c - d.o) / atr).dropna(); wd = wd[wd.index.weekday < 5]
print(f"\n10 BTC weekend return (Fri 21:00 -> Mon 00:00 UTC, ATR units): n={len(w)} avg={w.ret.mean():+.3f} t={t(w.ret):+.1f} up={np.mean(w.ret>0):.0%}  | weekday day return avg={wd.mean():+.3f} (n={len(wd)})")
print("   per year:", w.groupby("year").ret.mean().round(2).to_dict())
# Monday breakout of the weekend range
rows = []
for r in w.itertuples():
    mon = b[(b.index >= r.day + pd.Timedelta(days=3)) & (b.index < r.day + pd.Timedelta(days=4))]
    if len(mon) < 10: continue
    mid = (r.wh + r.wl) / 2; px = None
    for i in range(len(mon)):
        c = mon.close.iloc[i]
        if c > r.wh: side = 1; e = c + mon.sp.iloc[i] / 2; stop = mid; break
        if c < r.wl: side = -1; e = c - mon.sp.iloc[i] / 2; stop = mid; break
    else: continue
    risk = abs(e - stop)
    for q in range(i + 1, len(mon)):
        if (side == 1 and mon.low.iloc[q] <= stop) or (side == -1 and mon.high.iloc[q] >= stop): px = stop; why = "stop"; break
    if px is None: px = mon.close.iloc[-1]; why = "time"
    cost = mon.sp.iloc[i] / 2 + 0.000325 * e * 2
    rows.append(dict(year=r.day.year, R=(side * (px - e) - cost) / risk, why=why, risk_atr=risk / r.A))
br = pd.DataFrame(rows)
print(f"   Monday breakout of the weekend range (stop at range mid, exit Monday close): n={len(br)} avgR={br.R.mean():+.3f} t={t(br.R):+.1f} win={np.mean(br.R>0):.0%} stop={np.mean(br.why=='stop'):.0%}")
print("   per year:", br.groupby("year").R.mean().round(2).to_dict())

# ---------- 11. gold hour-of-day
sr_diag.START = "2012-01-01"; g = sr_diag.load()
h = g[["open","close","sp"]].resample("1h").agg({"open":"first","close":"last","sp":"mean"}).dropna()
ny = h.index.tz_localize("UTC").tz_convert("America/New_York"); h["hr"] = ny.hour; h["year"] = h.index.year
h["ret"] = (h.close - h.open) / h.open * 1e4         # basis points
tab = h[h.year <= 2025].pivot_table(index="hr", columns="year", values="ret", aggfunc="mean")
sign_ok = ((tab > 0).sum(axis=1) >= 10) | ((tab < 0).sum(axis=1) >= 10)
allm = h.groupby("hr").ret.mean(); cost_bp = ((h.sp / h.open * 1e4) + 2 * GCOMM * 1e4).groupby(h.hr).mean()
print("\n11 gold hour-of-day (NY hour): mean return bp/hour, years with same sign (of 14), round-trip cost bp")
for hr in range(24):
    if hr not in tab.index: continue
    pos = int((tab.loc[hr] > 0).sum()); neg = int((tab.loc[hr] < 0).sum())
    flag = " <-- qualifies" if sign_ok.get(hr, False) else ""
    print(f"   {hr:02d}:00  {allm[hr]:+.2f} bp  +{pos}/-{neg}  cost {cost_bp[hr]:.2f} bp{flag}")
q = [hr for hr in tab.index if sign_ok.get(hr, False)]
for hr in q:
    s = h[h.hr == hr]; net = s.ret - (s.sp / s.open * 1e4 + 2 * GCOMM * 1e4) * np.sign(allm[hr]) * np.sign(allm[hr])
    sgn = np.sign(allm[hr]); netr = sgn * s.ret - (s.sp / s.open * 1e4 + 2 * GCOMM * 1e4)
    print(f"   always-on {'long' if sgn>0 else 'short'} at {hr:02d}:00 NY: n={len(s)} net {netr.mean():+.2f} bp/trade t={t(netr):+.1f}; per year:", netr.groupby(s.year).mean().round(1).to_dict())
