"""Idea 21c. IBS mean reversion on the Nasdaq/S&P ("2.11 Sharpe" rule, Quantitativo; QQQ since 1999), as published:
  range25 = 25-day average of (high - low);  IBS = (close - low) / (high - low)
  band    = 10-day highest high (incl. today) - 2.5 x range25
  entry   = buy at the close when close < band and IBS < 0.3
  exit    = sell at the first close above the previous day's high (no stop)
Variant (fixed in advance, from the same family): classic IBS < 0.2 entry, same exit.
Data: FTMO US100.cash / US500.cash, daily bars by FTMO trading day (server date; daily-only before 2021-09),
Dec 2017 - Oct 2026. Costs: spread US100 1.5 pts, US500 0.5 pts per round trip (the exports carry no spread before
2021), swap 0.01% of price per night held. R = P&L / ATR(14) at entry (as ideas 8 and 9).
Baseline: long for the same number of days from random entry days (unconditional drift), and the same trades'
gross P&L vs that drift.
"""
import sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab")
from ftmo_data import load_export

def daily(sym):
    x = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0])
    d = x.groupby(x.index.normalize()).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
    d = d[d.index.weekday < 5]
    pc = d.c.shift(1); tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    return d

def run(d, spread, entry_rule="published", swap=0.0001):
    h, l, c, A = d.h.values, d.l.values, d.c.values, d.atr.values
    rng25 = (d.h - d.l).rolling(25).mean().values
    hh10 = d.h.rolling(10).max().values
    ibs = ((d.c - d.l) / (d.h - d.l)).values
    rows = []; i = 30
    while i < len(d) - 1:
        if entry_rule == "published":
            sig = c[i] < hh10[i] - 2.5 * rng25[i] and ibs[i] < 0.3
        else:
            sig = ibs[i] < 0.2
        if not sig or np.isnan(A[i]):
            i += 1; continue
        e = c[i]; q = None
        for j in range(i + 1, len(d)):
            if c[j] > h[j - 1]:
                q = j; break
        if q is None:
            break
        nights = (d.index[q] - d.index[i]).days
        gross = c[q] - e
        rows.append(dict(day=d.index[i], year=d.index[i].year, days=q - i, R=(gross - spread - swap * e * nights) / A[i],
                         grossR=gross / A[i], ret=(gross - spread - swap * e * nights) / e))
        i = q + 1
    return pd.DataFrame(rows)

def drift_baseline(d, holds, swap=0.0001, spread=0.0):
    c, A = d.c.values, d.atr.values; idx = d.index; vals = []
    for hld in holds:
        r = []
        for i in range(30, len(d) - hld):
            nights = (idx[i + hld] - idx[i]).days
            r.append((c[i + hld] - c[i] - spread - swap * c[i] * nights) / A[i])
        vals.append(np.mean(r))
    return np.array(vals)

if __name__ == "__main__":
    for sym, spread_pts in (("US100.cash", 1.5), ("US500.cash", 0.5)):
        d = daily(sym)
        print(f"\n== {sym} daily {d.index[0].date()}..{d.index[-1].date()} ({len(d)} days)")
        for rule in ("published", "ibs<0.2"):
            t = run(d, spread_pts, rule)
            R = t.R; tt = R.mean() / R.std() * np.sqrt(len(R))
            base = drift_baseline(d, t.days.values, spread=spread_pts)
            yrs = t.groupby("year").R.mean()
            time_in = t.days.sum() / len(d)
            print(f"  {rule:10s}: n={len(t)} ({len(t) / (len(d) / 252):.0f}/yr), avgR {R.mean():+.3f} t {tt:+.1f} win {np.mean(R > 0):.0%}, "
                  f"avg hold {t.days.mean():.1f} days, in market {time_in:.0%} | same holds from random days {base.mean():+.3f}R "
                  f"-> edge over drift {R.mean() - base.mean():+.3f}R | halves {R.iloc[:len(R)//2].mean():+.3f}/{R.iloc[len(R)//2:].mean():+.3f} | worst trade {R.min():+.2f}R")
            print("     per year:", " ".join(f"{y % 100}:{v:+.2f}" for y, v in yrs.items()))
            ann = t.ret.sum() / (len(d) / 252)
            print(f"     at 1x notional: {ann:+.1%} a year from {time_in:.0%} time in market; worst trade {t.ret.min():+.1%}")
