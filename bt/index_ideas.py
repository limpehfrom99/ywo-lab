"""Ideas 5, 6, 7 on US100/US500 (M30 2017-2026, FTMO export; no commission; spread from export).
5. Opening-gap fade: gap = 9:30 NY open - prior day's 16:00 close. If 0.3 ATR <= |gap| <= 1.0 ATR, trade toward
   the prior close at the 9:30 open; target = prior close; stop = 1 gap beyond the open; exit at 11:00 if neither.
   R = P&L / |gap|. Baseline: same trade on every day with |gap| < 0.3 ATR (small gaps) and coin flip.
6. Overnight return: buy 15:30 bar close (=16:00 cash close) and sell at the 9:30 bar close next day (hold through the
   night; swap 0.01%/night). Intraday mirror: buy 9:30 close, sell 15:30 close. R = P&L / daily ATR.
7. Pre-FOMC drift: long from the 15:30 bar close the day before an FOMC decision to the 13:30 bar close on FOMC day
   (just before the 14:00 statement). R = P&L / ATR. Baseline: the same window on every other day.
"""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/bt'); sys.path.insert(0,'/home/claude/lab')
import sr_diag
from ftmo_data import load_export
from smc_data import finish
from news import load_calendar, fed_days

def frame(sym):
    f = glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0]
    x = load_export(f); x.index = x.index - pd.Timedelta(hours=7)
    x.index = x.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)
    x = x[~x.index.isna()][["open","high","low","close","sp"]]
    b = finish(x, 0.0); return b[["open","high","low","close","sp","nyd","nym"]].copy()

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))
def report(label, r, by="year"):
    print(f"{label}: n={len(r)} avgR={r.R.mean():+.3f} t={t(r.R):+.1f} win={np.mean(r.R>0):.0%}  halves {r.R.iloc[:len(r)//2].mean():+.3f}/{r.R.iloc[len(r)//2:].mean():+.3f}")
    print("   per year:", r.groupby(by).R.mean().round(2).to_dict())

fomc = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
for sym in ("US100.cash", "US500.cash"):
    g = frame(sym); d, atr = sr_diag.daily_atr(g)
    bars = {m: g[g.nym == m] for m in (570, 930, 810, 660)}       # 9:30, 15:30, 13:30, 11:00 bars (NY minutes)
    o930 = bars[570].set_index("nyd"); c1530 = bars[930].set_index("nyd"); c1330 = bars[810].set_index("nyd"); c1100 = bars[660].set_index("nyd")
    days = sorted(set(o930.index) & set(c1530.index)); days = pd.DatetimeIndex(days)
    print(f"\n==== {sym} {days[0].date()} .. {days[-1].date()} ({len(days)} days) ====")
    # ---- 5. gap fade
    rows = []
    for i in range(1, len(days)):
        dprev, day = days[i-1], days[i]; A = atr.get(day, np.nan)
        if not np.isfinite(A): continue
        pc = c1530.close[dprev]; op = o930.open[day]; gap = op - pc; sp = o930.sp[day]
        side = -1 if gap > 0 else 1
        entry = op + side * sp / 2; tgt = pc; stop = op - side * abs(gap); risk = abs(gap)
        # walk 9:30 .. 10:30 bars, exit at the 11:00 bar close
        seg = g[(g.nyd == day) & (g.nym >= 570) & (g.nym <= 660)]
        px = None
        for _, b in seg.iterrows():
            if side == 1 and b.low <= stop or side == -1 and b.high >= stop: px = stop; why = "stop"; break
            if side == 1 and b.high >= tgt or side == -1 and b.low <= tgt: px = tgt; why = "fill"; break
        if px is None: px = seg.close.iloc[-1]; why = "time"
        rows.append(dict(day=day, year=day.year, gap_atr=abs(gap) / A, R=(side * (px - entry) - sp / 2) / risk, why=why))
    r = pd.DataFrame(rows)
    sel = r[(r.gap_atr >= 0.3) & (r.gap_atr <= 1.0)]; small = r[r.gap_atr < 0.3]
    report("5 gap fade 0.3-1.0 ATR", sel); report("   baseline: small gaps < 0.3 ATR, same rule", small)
    print("   fill rate:", f"{np.mean(sel.why=='fill'):.0%}", " gaps > 1 ATR:", f"n={len(r[r.gap_atr>1])} avgR={r[r.gap_atr>1].R.mean():+.3f}")
    # ---- 6. overnight vs intraday
    rows = []
    for i in range(1, len(days)):
        dprev, day = days[i-1], days[i]; A = atr.get(day, np.nan)
        if not np.isfinite(A): continue
        e = c1530.close[dprev] + c1530.sp[dprev] / 2; x = o930.close[day] - o930.sp[day] / 2
        nights = (day - dprev).days
        rows.append(dict(day=day, year=day.year, R=(x - e - 0.0001 * e * nights) / A, kind="overnight"))
        e2 = o930.close[day] + o930.sp[day] / 2; x2 = c1530.close[day] - c1530.sp[day] / 2
        rows.append(dict(day=day, year=day.year, R=(x2 - e2) / A, kind="intraday"))
    r = pd.DataFrame(rows)
    report("6 overnight (15:30 -> next 9:30 close)", r[r.kind == "overnight"]); report("   intraday (9:30 -> 15:30 close)", r[r.kind == "intraday"])
    # ---- 7. pre-FOMC drift
    rows = []
    for i in range(1, len(days)):
        dprev, day = days[i-1], days[i]; A = atr.get(day, np.nan)
        if not np.isfinite(A) or day not in c1330.index: continue
        e = c1530.close[dprev] + c1530.sp[dprev] / 2; x = c1330.close[day] - c1330.sp[day] / 2
        rows.append(dict(day=day, year=day.year, R=(x - e - 0.0001 * e) / A, fomc=day in fomc))
    r = pd.DataFrame(rows)
    report("7 pre-FOMC (day-before 15:30 -> FOMC day 13:30)", r[r.fomc]); report("   baseline: every other day, same window", r[~r.fomc])
