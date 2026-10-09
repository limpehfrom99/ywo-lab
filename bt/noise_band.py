"""Idea 21a. "Beat the Market" noise-band intraday momentum (Zarattini, Aziz & Barbon 2024, SPY 2007-2024:
Sharpe 1.33, 19.6%/yr net, 7,668 trades). Rules fixed from the paper before running:

  sigma(t, k)  = mean over the previous 14 full sessions of |close at mark k / 9:30 open - 1|
  UB(t, k)     = max(open 9:30, prior 16:00 close) x (1 + sigma);  LB = min(open, prior close) x (1 - sigma)
  marks        = 10:00, 10:30, ..., 15:30 New York (bar closes of the 30-min bars); flat at 16:00
  exposure     = +1 if price > max(UB, VWAP); -1 if price < min(LB, VWAP); else 0   (evaluated at each mark;
                 equivalent to entering on a band break with a trailing stop at max(UB, VWAP) / min(LB, VWAP))
  sizing       = paper: notional = equity x min(4, 2% / std of the last 14 daily returns)
  costs        = FTMO bar spread (half per side at each change of exposure) + commission per side
VWAP is built from the 30-min bars (typical price x tick volume) - an approximation of the paper's 1-min VWAP.
Data: FTMO M30 exports (intraday from mid-2021). The paper's sample ends April 2024, so May 2024 onward is
out of sample for the rule itself.
Baselines: (1) coin flip - same entry and exit times, random side (500 draws); (2) the live opening-candle
rule's daily results on the same days (correlation, and does the band add anything beyond it).
"""
import sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab")
from ftmo_data import load_export

def rth_bars(sym, tf="M30"):
    d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_{tf}_*.csv")[0])
    ny = d.index - pd.Timedelta(hours=7)
    d = d.copy(); d["nyd"] = ny.normalize(); d["nyt"] = ny.strftime("%H:%M")
    return d

def session_matrix(d, step=30, open_t="09:30", n_marks=13, first_bar=None):
    """One row per day with a complete regular session. Columns: open (first bar open), close_k at each mark
    (k=1..13 -> 10:00..16:00), VWAP at each mark, spread at each mark."""
    times = pd.date_range("2000-01-01 " + open_t, periods=n_marks * (30 // step), freq=f"{step}min").strftime("%H:%M")
    s = d[d.nyt.isin(times)]
    rows = {}
    for day, b in s.groupby("nyd"):
        if len(b) != len(times):
            continue
        b = b.sort_index()
        tp = (b.high + b.low + b.close) / 3
        v = b.tickvol.replace(0, 1)
        vwap = (tp * v).cumsum() / v.cumsum()
        k = np.arange(30 // step - 1, len(b), 30 // step)       # bar index that closes at each half-hour mark
        rows[day] = dict(o=b.open.iloc[0], c=b.close.values[k], vw=vwap.values[k], sp=b.sp.values[k],
                         hi=b.high.max(), lo=b.low.min())
    days = sorted(rows)
    O = np.array([rows[x]["o"] for x in days]); C = np.vstack([rows[x]["c"] for x in days])
    VW = np.vstack([rows[x]["vw"] for x in days]); SP = np.vstack([rows[x]["sp"] for x in days])
    return pd.DatetimeIndex(days), O, C, VW, SP

def run(days, O, C, VW, SP, comm=0.0, lookback=14, vm=1.0, use_vwap=True, seed_flip=None, first_entry=0):
    """Returns per-day raw return at 1x notional (after costs), per-day sizing multiple, and a trade list."""
    n, K = C.shape                                    # K marks; last mark (16:00) is the forced exit
    move = np.abs(C / O[:, None] - 1)
    sig = pd.DataFrame(move).rolling(lookback).mean().shift(1).values * vm
    prev_c = np.r_[np.nan, C[:-1, -1]]
    dret = np.r_[np.nan, C[1:, -1] / C[:-1, -1] - 1]
    vol14 = pd.Series(dret).rolling(14).std().shift(1).values   # uses days up to yesterday
    lev = np.minimum(4.0, 0.02 / vol14)
    rng = np.random.default_rng(seed_flip) if seed_flip is not None else None
    day_ret = np.full(n, np.nan); trades = []
    for t in range(n):
        if np.isnan(sig[t, 0]) or np.isnan(prev_c[t]) or np.isnan(lev[t]):
            continue
        ub = max(O[t], prev_c[t]) * (1 + sig[t]); lb = min(O[t], prev_c[t]) * (1 - sig[t])
        pos, entry, eside, ek, r = 0, None, 0, None, 0.0
        flip = 0
        for k in range(K):
            p = C[t, k]
            if k == K - 1:
                tgt = 0
            elif k < first_entry:
                tgt = 0
            elif use_vwap:
                tgt = 1 if p > max(ub[k], VW[t, k]) else (-1 if p < min(lb[k], VW[t, k]) else 0)
            else:                                     # opposite-band stop variant: hold until the other band
                tgt = 1 if p > ub[k] else (-1 if p < lb[k] else pos)
            if tgt != pos:
                cost_side = SP[t, k] / 2 / p + comm
                if pos != 0:                          # close the open position
                    side = pos * (flip if rng is not None else 1)
                    g = side * (p / entry - 1) - cost_side
                    r += g
                    trades.append((days[t], ek, k, side, g))
                if tgt != 0:
                    pos, entry, ek = tgt, p, k
                    flip = rng.choice([-1, 1]) if rng is not None else 1
                    r -= cost_side
                else:
                    pos = 0
        day_ret[t] = r
    tr = pd.DataFrame(trades, columns=["day", "k_in", "k_out", "side", "ret"])
    return pd.Series(day_ret, index=days), pd.Series(lev, index=days), tr

def summarize(name, raw, lev, tr, split="2024-05-01"):
    ok = raw.dropna(); L = lev.reindex(ok.index)
    dyn = ok * L
    def st(x):
        ann = x.mean() * 252; vol = x.std() * np.sqrt(252); eq = (1 + x).cumprod(); dd = (eq / eq.cummax() - 1).min()
        return f"ann {ann:+.1%} vol {vol:.1%} Sharpe {ann / vol:+.2f} maxDD {dd:.1%} t {x.mean() / x.std() * np.sqrt(len(x)):+.1f}"
    print(f"\n== {name}: {len(ok)} days {ok.index[0].date()}..{ok.index[-1].date()}, {len(tr)} trades "
          f"({len(tr) / len(ok):.1f}/day), trade win {np.mean(tr.ret > 0):.0%}, avg trade {tr.ret.mean() * 1e4:+.1f} bp")
    print("   1x notional :", st(ok))
    print("   paper sizing:", st(dyn), f"(avg leverage {L.mean():.1f})")
    pre, post = dyn[dyn.index < split], dyn[dyn.index >= split]
    print(f"   paper sizing, before {split} (in the paper's sample): {pre.mean() * 252:+.1%}/yr Sharpe {pre.mean() / pre.std() * np.sqrt(252):+.2f}"
          f" | after (out of sample): {post.mean() * 252:+.1%}/yr Sharpe {post.mean() / post.std() * np.sqrt(252):+.2f}")
    yr = dyn.groupby(dyn.index.year).agg(["sum", "count"])
    print("   per year (paper sizing, sum of daily %):", {y: f"{v * 100:+.1f}%" for y, v in yr["sum"].items()})
    first = tr[tr.k_in == 0].ret; later = tr[tr.k_in > 0].ret
    print(f"   trades opened at 10:00: {len(first)} avg {first.mean() * 1e4:+.1f} bp | opened later: {len(later)} avg {later.mean() * 1e4:+.1f} bp")
    return dyn

if __name__ == "__main__":
    out = {}
    for sym, comm in (("US100.cash", 0.0), ("US500.cash", 0.0), ("TSLA", 0.00002)):
        d = rth_bars(sym)
        d = d[d.index >= "2021-06-01"]
        days, O, C, VW, SP = session_matrix(d)
        raw, lev, tr = run(days, O, C, VW, SP, comm=comm)
        dyn = summarize(f"{sym} noise band + VWAP (as published)", raw, lev, tr)
        out[sym] = (raw, lev, tr, days, O, C, VW, SP)
        # coin flip: same entry/exit marks, random side
        flips = []
        for s in range(200):
            r2, _, _ = run(days, O, C, VW, SP, comm=comm, seed_flip=s)
            flips.append(r2.dropna().mean())
        flips = np.array(flips)
        print(f"   coin flip, same times (200 draws): mean {flips.mean() * 1e4:+.2f} bp/day at 1x, 95% range "
              f"{np.percentile(flips, 2.5) * 1e4:+.2f}..{np.percentile(flips, 97.5) * 1e4:+.2f}; real {raw.dropna().mean() * 1e4:+.2f}"
              f" -> beats {np.mean(flips < raw.dropna().mean()):.0%} of draws")
        # variants (fixed list, all reported)
        r3, l3, t3 = run(days, O, C, VW, SP, comm=comm, use_vwap=False)
        x = r3.dropna(); print(f"   variant opposite-band stop (no VWAP): {x.mean() * 252:+.1%}/yr at 1x, Sharpe {x.mean() / x.std() * np.sqrt(252):+.2f}")
        for vm in (0.75, 1.25, 1.5):
            r4, _, _ = run(days, O, C, VW, SP, comm=comm, vm=vm)
            x = r4.dropna(); print(f"   variant band x{vm}: {x.mean() * 252:+.1%}/yr at 1x, Sharpe {x.mean() / x.std() * np.sqrt(252):+.2f}")
        SP2 = SP * 2
        r5, _, _ = run(days, O, C, VW, SP2, comm=comm)
        x = r5.dropna(); print(f"   double spread: {x.mean() * 252:+.1%}/yr at 1x, Sharpe {x.mean() / x.std() * np.sqrt(252):+.2f}")
    pd.to_pickle(out, "/home/claude/data/noise_band_out.pkl")
