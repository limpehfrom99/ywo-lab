"""Ideas 8 + 9 on daily bars.
8. Short-term index reversal (US100/US500 daily 2018-2026, from the M30 export: daily-only bars before 2021-09,
   aggregated 30-min after): buy at the close after 3 consecutive lower closes, exit at the first close above the
   previous close or after 5 days; stop 1.5 ATR. Mirror for shorts after 3 higher closes. R = P&L / ATR.
   Baseline: unconditional 5-day hold; coin flip = mirror average.
9. Gold trend following (daily from M1, 2012-2026): long on a close above the 20-day high, exit on a close below the
   10-day low or a stop 2 ATR(20) below entry (trailing on closes); mirror for shorts. Swap 0.01%/night. R = P&L / ATR.
"""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/bt'); sys.path.insert(0,'/home/claude/lab')
from ftmo_data import load_export
from smc_data import finish
import sr_diag

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))
def report(label, r):
    if len(r) == 0: print(label, "n=0"); return
    print(f"{label}: n={len(r)} avgR={r.R.mean():+.3f} t={t(r.R):+.1f} win={np.mean(r.R>0):.0%}  halves {r.R.iloc[:len(r)//2].mean():+.3f}/{r.R.iloc[len(r)//2:].mean():+.3f}")
    print("   per year:", r.groupby('year').R.mean().round(2).to_dict())

def daily_from_export(sym):
    f = glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0]
    x = load_export(f); x.index = x.index - pd.Timedelta(hours=7)
    x.index = x.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)
    x = x[~x.index.isna()]; b = finish(x[["open","high","low","close","sp"]], 0.0)
    d = b.groupby("nyd").agg(o=("open","first"), h=("high","max"), l=("low","min"), c=("close","last"), sp=("sp","mean"))
    pc = d.c.shift(1); tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean().shift(1); return d.dropna()

def reversal(d, n_down=3, max_hold=5, stop_atr=1.5, swap=0.0001):
    c = d.c.values; h = d.h.values; l = d.l.values; A = d.atr.values; sp = d.sp.values; idx = d.index; rows = []
    i = n_down
    while i < len(d) - 1:
        down = all(c[i-k] < c[i-k-1] for k in range(n_down)); up = all(c[i-k] > c[i-k-1] for k in range(n_down))
        if not (down or up): i += 1; continue
        side = 1 if down else -1; e = c[i] + side * sp[i] / 2; stop = e - side * stop_atr * A[i]; px = None
        for q in range(i + 1, min(i + 1 + max_hold, len(d))):
            if (side == 1 and l[q] <= stop) or (side == -1 and h[q] >= stop): px = stop; why = "stop"; break
            if (side == 1 and c[q] > c[q-1]) or (side == -1 and c[q] < c[q-1]): px = c[q]; why = "reverse"; break
        if px is None: px = c[q]; why = "time"
        nights = (idx[q] - idx[i]).days
        rows.append(dict(day=idx[i], year=idx[i].year, side=side, R=(side * (px - e) - sp[q] / 2 - swap * e * nights) / A[i], why=why))
        i = q + 1
    return pd.DataFrame(rows)

def donchian(d, n_in=20, n_out=10, stop_atr=2.0, swap=0.0001, comm=0.0):
    c = d.c.values; h = d.h.values; l = d.l.values; A = d.atr.values; sp = d.sp.values; idx = d.index; rows = []
    hi_in = pd.Series(h).rolling(n_in).max().shift(1).values; lo_in = pd.Series(l).rolling(n_in).min().shift(1).values
    hi_out = pd.Series(h).rolling(n_out).max().shift(1).values; lo_out = pd.Series(l).rolling(n_out).min().shift(1).values
    i = n_in + 1
    while i < len(d) - 1:
        if c[i] > hi_in[i]: side = 1
        elif c[i] < lo_in[i]: side = -1
        else: i += 1; continue
        e = c[i] + side * sp[i] / 2; A0 = A[i]; stop = e - side * stop_atr * A0; px = None; best = e
        for q in range(i + 1, len(d)):
            if (side == 1 and l[q] <= stop) or (side == -1 and h[q] >= stop): px = stop; why = "stop"; break
            best = max(best, c[q]) if side == 1 else min(best, c[q]); stop = best - side * stop_atr * A0 if side == 1 else best + stop_atr * A0
            if (side == 1 and c[q] < lo_out[q]) or (side == -1 and c[q] > hi_out[q]): px = c[q]; why = "channel"; break
        if px is None: px = c[-1]; q = len(d) - 1; why = "end"
        nights = (idx[q] - idx[i]).days
        rows.append(dict(day=idx[i], year=idx[i].year, side=side, R=(side * (px - e) - sp[q] / 2 - comm * e * 2 - swap * e * nights) / A0, why=why, days=q - i))
        i = q + 1
    return pd.DataFrame(rows)

if __name__ == "__main__":
    for sym in ("US100.cash", "US500.cash"):
        d = daily_from_export(sym); print(f"\n==== {sym} daily {d.index[0].date()}..{d.index[-1].date()} ({len(d)} days) ====")
        r = reversal(d); report("8 reversal after 3 down/up closes (both sides)", r)
        report("   longs after 3 down", r[r.side == 1]); report("   shorts after 3 up", r[r.side == -1])
        base = (d.c.shift(-5) - d.c) / d.atr; print(f"   baseline unconditional 5-day hold: avg {base.mean():+.3f} ATR")
    sr_diag.START = "2012-01-01"; g = sr_diag.load(); dd, atr = sr_diag.daily_atr(g)
    d = g.groupby("nyd").agg(o=("open","first"), h=("high","max"), l=("low","min"), c=("close","last"), sp=("sp","mean")); d["atr"] = atr; d = d.dropna()
    print(f"\n==== gold daily {d.index[0].date()}..{d.index[-1].date()} ====")
    r = donchian(d, comm=0.000007); report("9 gold Donchian 20/10, 2 ATR trailing stop (both sides)", r)
    report("   longs", r[r.side == 1]); report("   shorts", r[r.side == -1]); print("   avg hold days", round(r.days.mean(), 1), "exits", r.why.value_counts().to_dict())
    for sym in ("US100.cash", "US500.cash"):
        d = daily_from_export(sym); r = donchian(d); report(f"9b {sym} Donchian 20/10 (both sides)", r); report("   longs", r[r.side == 1])
