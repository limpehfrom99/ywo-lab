"""Online-sourced daily rules on US100/US500 (daily from the M30 export, 2018-2026) and TSLA/AAPL (daily from M30 exports):
 RSI2  (Connors, as tested by backtrex.com): long when RSI(2) < 5 and close > 200-day SMA, exit when close > 5-day SMA or < 200-SMA;
       short mirror (RSI2 > 95, close < 200-SMA). R = P&L / daily ATR(14). Costs: spread + commission + swap 0.01%/night.
 IBS   (Quantified Strategies family): long when IBS = (close-low)/(high-low) < 0.2 and close > 200-SMA, exit when close > previous high
       (max 5 days). Short mirror with IBS > 0.8 below the 200-SMA.
 EXPIRY days (queue #16): return on the 3rd Friday of each month and on the Monday after, vs other days.
 POST-FOMC (queue #17): on FOMC days, direction of the 14:00-14:30 NY candle held to the 16:00 close (30-min bars, 2021-09+)."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from daily_ideas import daily_from_export
from index_ideas import frame
from news import load_calendar, fed_days

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))
def rsi(c, n):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); dn = (-d).clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))
def report(label, r):
    if len(r) < 10: print(f"{label}: n={len(r)}"); return
    by = r.groupby("year").R.mean(); h = len(r) // 2
    print(f"{label}: n={len(r)} avgR={r.R.mean():+.3f} t={t(r.R):+.1f} win={np.mean(r.R>0):.0%} years>0 {int((by>0).sum())}/{len(by)} halves {r.R.iloc[:h].mean():+.3f}/{r.R.iloc[h:].mean():+.3f}")

def mr(d, mode, comm=0.0, swap=0.0001):
    c = d.c; sma200 = c.rolling(200).mean(); sma5 = c.rolling(5).mean(); r2 = rsi(c, 2); ibs = (c - d.l) / (d.h - d.l).replace(0, np.nan)
    rows = []; i = 200
    while i < len(d) - 1:
        side = 0
        if mode == "rsi2":
            if r2.iloc[i] < 5 and c.iloc[i] > sma200.iloc[i]: side = 1
            elif r2.iloc[i] > 95 and c.iloc[i] < sma200.iloc[i]: side = -1
        else:
            if ibs.iloc[i] < 0.2 and c.iloc[i] > sma200.iloc[i]: side = 1
            elif ibs.iloc[i] > 0.8 and c.iloc[i] < sma200.iloc[i]: side = -1
        if side == 0: i += 1; continue
        e = c.iloc[i] + side * d.sp.iloc[i] / 2; A = d.atr.iloc[i]; px = None
        for q in range(i + 1, min(i + (30 if mode == "rsi2" else 6), len(d))):
            if mode == "rsi2":
                done = (side == 1 and (c.iloc[q] > sma5.iloc[q] or c.iloc[q] < sma200.iloc[q])) or (side == -1 and (c.iloc[q] < sma5.iloc[q] or c.iloc[q] > sma200.iloc[q]))
            else:
                done = (side == 1 and c.iloc[q] > d.h.iloc[q-1]) or (side == -1 and c.iloc[q] < d.l.iloc[q-1])
            if done or q == min(i + (30 if mode == "rsi2" else 6), len(d)) - 1: px = c.iloc[q]; break
        nights = (d.index[q] - d.index[i]).days
        rows.append(dict(year=d.index[i].year, R=(side * (px - e) - d.sp.iloc[q] / 2 - comm * e * 2 - swap * e * nights) / A))
        i = q + 1
    return pd.DataFrame(rows)

fomc = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
for sym, comm in (("US100.cash", 0.0), ("US500.cash", 0.0), ("TSLA_M30", 0.00002), ("AAPL_M30", 0.00002)):
    name = sym.replace("_M30", "")
    d = daily_from_export(name) if "cash" in sym else daily_from_export(name)
    print(f"\n==== {name} daily {d.index[0].date()}..{d.index[-1].date()} ====")
    report("RSI(2) mean reversion", mr(d, "rsi2", comm)); report("IBS mean reversion", mr(d, "ibs", comm))
    # expiry days
    third_fri = [x for x in d.index if x.weekday() == 4 and 15 <= x.day <= 21]
    ret = (d.c - d.o) / d.atr; mon_after = [d.index[d.index.get_loc(x) + 1] for x in third_fri if d.index.get_loc(x) + 1 < len(d)]
    print(f"expiry Friday day-return: n={len(third_fri)} avg {ret.reindex(third_fri).mean():+.3f} ATR | Monday after: {ret.reindex(mon_after).mean():+.3f} | all days {ret.mean():+.3f}")
    if "cash" in sym:
        g = frame(sym); rows = []
        for day, x in g.groupby("nyd"):
            if day not in fomc: continue
            b1 = x[x.nym == 840]; b2 = x[x.nym == 930]
            if len(b1) == 0 or len(b2) == 0: continue
            side = 1 if b1.close.iloc[0] > b1.open.iloc[0] else -1; e = b1.close.iloc[0] + side * b1.sp.iloc[0] / 2
            A = (x.high.max() - x.low.min()); rows.append(dict(year=day.year, R=(side * (b2.close.iloc[0] - e) - b1.sp.iloc[0] / 2) / (abs(b1.close.iloc[0] - b1.open.iloc[0]) + 1e-9)))
        r = pd.DataFrame(rows); print(f"post-FOMC 14:30 candle direction held to 16:00 (R = move / candle body): n={len(r)} avgR={r.R.mean():+.2f} win={np.mean(r.R>0):.0%} per year {r.groupby('year').R.mean().round(2).to_dict()}")
