"""Idea 21b. ATR trailing-stop flips, the most-copied TradingView strategy scripts:
  Supertrend(ATR 10, factor 3)  - Pine ta.supertrend logic, long when direction turns up, short when it turns down.
  UT Bot (key 1, ATR 10)        - xATRTrailingStop on the close; buy when the close crosses above the stop, sell below.
  UT Bot on Heikin-Ashi closes  - the popular "UT Bot + HA" combo (signals from HA, fills on real prices).
Rules fixed before running (TradingView defaults): signal at the bar close, fill at the next bar's open,
stop-and-reverse on the opposite signal. Two modes, both reported:
  always-in    as the scripts run on TradingView (overnight + weekend holds, swap 0.01% of price per 17:00 NY)
  session-only no overnight: indices/stocks trade signals inside 9:30-16:00 NY and exit at 16:00; gold exits at
               16:55 NY (before the daily break) and re-enters only on a new signal.
R = P&L after costs / distance from the fill to the indicator's stop line at the signal bar.
Costs: half the bar spread per side + commission per side; swap as above.
Baseline: coin flip at the same entry/exit times (expected value = -costs/risk; 95% band from 200 draws).
Grid (all cells reported): 3 rules x {gold M5/M15/H1 2012-26, US100/US500 M30/H1 2021-26, TSLA/AAPL M5/M15/H1 2021-26}
x 2 modes.
"""
import sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export

SWAP = 0.0001

def ny_bars_export(sym, tf):
    d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_{tf}_*.csv")[0])
    d.index = d.index - pd.Timedelta(hours=7)                    # server -> New York (naive)
    return d[["open", "high", "low", "close", "sp"]]

def ny_bars_pickle(name):
    b = pd.read_pickle(f"/home/claude/data/{name}_m5.pkl")
    idx = b.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    x = b[["open", "high", "low", "close", "sp"]].copy(); x.index = idx
    return x[~x.index.duplicated()]

def resample(x, rule, offset=None):
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean"}
    r = x.resample(rule, label="left", closed="left", offset=offset).agg(agg)
    return r.dropna(subset=["open"])

def atr_rma(h, l, c, n):
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    a = np.full(len(c), np.nan); a[n - 1] = tr[:n].mean()
    for i in range(n, len(c)):
        a[i] = (a[i - 1] * (n - 1) + tr[i]) / n
    return a

def supertrend(h, l, c, n=10, f=3.0):
    a = atr_rma(h, l, c, n); src = (h + l) / 2
    up = src + f * a; lo = src - f * a
    d = np.zeros(len(c), int); st = np.full(len(c), np.nan)
    for i in range(1, len(c)):
        if np.isnan(a[i]):
            continue
        if not np.isnan(lo[i - 1]):
            lo[i] = lo[i] if (lo[i] > lo[i - 1] or c[i - 1] < lo[i - 1]) else lo[i - 1]
            up[i] = up[i] if (up[i] < up[i - 1] or c[i - 1] > up[i - 1]) else up[i - 1]
        if np.isnan(a[i - 1]) or np.isnan(st[i - 1]):
            d[i] = 1                                            # Pine: 1 = down-trend at start
        elif st[i - 1] == up[i - 1]:
            d[i] = -1 if c[i] > up[i] else 1
        else:
            d[i] = 1 if c[i] < lo[i] else -1
        st[i] = lo[i] if d[i] == -1 else up[i]
    side = np.where(d == -1, 1, np.where(d == 1, -1, 0))        # +1 long trend, -1 short trend
    return side, st

def utbot(h, l, c, src, key=1.0, n=10):
    a = atr_rma(h, l, c, n); loss = key * a
    stop = np.full(len(c), np.nan); side = np.zeros(len(c), int)
    for i in range(1, len(c)):
        if np.isnan(loss[i]):
            continue
        p = stop[i - 1] if not np.isnan(stop[i - 1]) else 0.0
        if src[i] > p and src[i - 1] > p:
            stop[i] = max(p, src[i] - loss[i])
        elif src[i] < p and src[i - 1] < p:
            stop[i] = min(p, src[i] + loss[i])
        elif src[i] > p:
            stop[i] = src[i] - loss[i]
        else:
            stop[i] = src[i] + loss[i]
        above = src[i] > stop[i] and src[i - 1] <= p
        below = src[i] < stop[i] and src[i - 1] >= p
        side[i] = 1 if above else (-1 if below else side[i - 1])
    return side, stop

def heikin_close(o, h, l, c):
    return (o + h + l + c) / 4

def backtest(x, side, line, comm, session=None, gold=False):
    """side[i]: desired direction after bar i closes. Fill at bar i+1 open. session: bool array, bar inside the
    tradable window; positions are closed at the close of the last in-window bar of each trading day."""
    o = x.open.values; c = x.close.values; sp = x.sp.values; t = x.index
    n = len(x); pos = 0; e = None; risk = None; ei = None; rows = []
    if session is not None:
        day = (t + pd.Timedelta(hours=7)).normalize() if gold else t.normalize()
        dnext = np.r_[day[1:], day[-1:]]
        snext = np.r_[session[1:], False]
        last = session & (~snext | (np.asarray(dnext) != np.asarray(day)))
    def close_at(i, px, why):
        nonlocal pos
        nights = count_breaks(t[ei], t[i])
        g = pos * (px - e) - sp[i] / 2 - comm * (e + px) - SWAP * e * nights
        rows.append((t[ei], t[i], pos, g / risk, risk / e, (pos * (px - e)) / risk, (sp[i] / 2 + comm * (e + px) + SWAP * e * nights) / risk, why))
        pos = 0
    for i in range(1, n - 1):
        if session is not None:
            if pos != 0 and last[i]:
                close_at(i, c[i], "session"); continue
            if not session[i] or last[i] or not session[i + 1]:
                continue                                        # no new fills outside the window
        want = side[i]
        if want != 0 and want != pos and side[i - 1] != want:  # fresh flip on this bar
            if pos != 0:
                close_at(i + 1, o[i + 1], "flip")
            r = abs(o[i + 1] - line[i])
            if not np.isfinite(r) or r <= 0:
                continue
            pos, e, risk, ei = want, o[i + 1] + want * sp[i + 1] / 2, r, i + 1
    if pos != 0:
        close_at(n - 1, c[n - 1], "end")
    return pd.DataFrame(rows, columns=["t_in", "t_out", "side", "R", "risk_pct", "grossR", "costR", "why"])

def count_breaks(a, b):
    """Number of 17:00 New York roll-overs between two NY timestamps."""
    if b <= a:
        return 0
    first = a.normalize() + pd.Timedelta(hours=17)
    if a >= first:
        first += pd.Timedelta(days=1)
    return 0 if b < first else int((b - first) / pd.Timedelta(days=1)) + 1

def report(label, tr):
    if len(tr) < 30:
        print(f"{label:52s} n={len(tr)}"); return None
    R = tr.R; t = R.mean() / R.std() * np.sqrt(len(R))
    yrs = R.groupby(tr.t_in.dt.year).mean()
    rng = np.random.default_rng(0)
    flips = [(rng.choice([-1, 1], len(tr)) * tr.grossR - tr.costR).mean() for _ in range(200)]
    h1, h2 = R.iloc[: len(R) // 2].mean(), R.iloc[len(R) // 2:].mean()
    print(f"{label:52s} n={len(tr):5d} avgR {R.mean():+.3f} t {t:+.1f} win {np.mean(R > 0):.0%} halves {h1:+.2f}/{h2:+.2f} "
          f"yrs+ {int((yrs > 0).sum())}/{len(yrs)} worst yr {yrs.min():+.2f} | coin {np.mean(flips):+.3f} "
          f"[{np.percentile(flips, 2.5):+.3f},{np.percentile(flips, 97.5):+.3f}] cost/trade {tr.costR.mean():.3f}R")
    return dict(cell=label, n=len(tr), avgR=R.mean(), t=t, h1=h1, h2=h2, yrs_pos=int((yrs > 0).sum()), yrs=len(yrs),
                worst_year=yrs.min(), coin=np.mean(flips), coin_hi=np.percentile(flips, 97.5), cost=tr.costR.mean())

def session_mask(x, kind):
    h = x.index.hour + x.index.minute / 60
    if kind == "gold":
        return ~((h >= 16.9) & (h < 18.0)) & ~((x.index.weekday == 4) & (h >= 16.9))   # handled by 'last in window'
    return (h >= 9.5) & (h < 16.0)

if __name__ == "__main__":
    specs = []
    g5 = ny_bars_pickle("gold")
    specs += [("gold", "M5", g5, 0.000007), ("gold", "M15", resample(g5, "15min"), 0.000007), ("gold", "H1", resample(g5, "60min"), 0.000007)]
    for s in ("US100.cash", "US500.cash"):
        m30 = ny_bars_export(s, "M30"); m30 = m30[m30.index >= "2021-10-01"]
        specs += [(s, "M30", m30, 0.0), (s, "H1", resample(m30, "60min", offset="30min"), 0.0)]
    for s in ("TSLA", "AAPL"):
        m5 = ny_bars_pickle(s)
        specs += [(s, "M5", m5, 0.00002), (s, "M15", resample(m5, "15min"), 0.00002), (s, "H1", resample(m5, "60min", offset="30min"), 0.00002)]
    rows = []
    for sym, tf, x, comm in specs:
        x = x.dropna()
        h, l, c, o = x.high.values, x.low.values, x.close.values, x.open.values
        rules = {"Supertrend 10/3": supertrend(h, l, c), "UT Bot 1/10": utbot(h, l, c, c),
                 "UT Bot 1/10 on Heikin-Ashi": utbot(h, l, c, heikin_close(o, h, l, c))}
        if sym == "gold":
            hh = x.index.hour + x.index.minute / 60
            sess = ~((hh >= 16.9) & (hh < 18.0))
        else:
            sess = np.asarray(session_mask(x, "idx"))
        for rname, (side, line) in rules.items():
            for mode in ("always-in", "session-only"):
                tr = backtest(x, side, line, comm, session=np.asarray(sess) if mode == "session-only" else None, gold=(sym == "gold"))
                r = report(f"{sym} {tf} {rname} {mode}", tr)
                if r:
                    r.update(sym=sym, tf=tf, rule=rname, mode=mode); rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv("/home/claude/bt/atr_trail_cells.csv", index=False)
    print(f"\ncells: {len(res)}; avgR > 0: {(res.avgR > 0).sum()}; beat coin-flip 97.5% band: {(res.avgR > res.coin_hi).sum()}; "
          f"protocol bar (n>=200, t>=2, both halves > 0, avg >= +0.05R, worst year >= -0.3R): "
          f"{((res.n >= 200) & (res.t >= 2) & (res.h1 > 0) & (res.h2 > 0) & (res.avgR >= 0.05) & (res.worst_year >= -0.3)).sum()}")
    print(res.sort_values("avgR", ascending=False).head(8)[["cell", "n", "avgR", "t", "h1", "h2", "yrs_pos", "yrs", "coin"]].to_string(index=False))
