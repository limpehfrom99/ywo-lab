"""Log #64 (backlog #54): Bernd Skorupinski's seasonal windows (rn058: "JPY sell from 1 Sep, 15 of 15 years"), walk-forward.
Rules fixed before running (research/log.md #64 pre-registration):
  Markets: 28 forex pairs (FTMO D1 2000-2026) + gold, silver (D1 2004/2008+). Windows: start on calendar days 1, 6, 11, ... of the
  year (73 starts), length 10, 20 or 30 trading days; entry at the close of the first trading day on/after the start, exit at the
  close L trading days later.
  Selection for test year Y (2015..2026): the same window in each of the 15 years before Y (>= 12 of them with data); select if
  >= 80% of those years went the same way; trade that direction in Y. Nothing about Y is used.
  Result per trade in ATR(20) units at entry, after costs: spread at entry and exit (median FTMO M15 spread that year x 1.2, else
  D1 spread x 2) and swap for every night held (today's swap sheet from symbol_specs.csv, triple on Wednesdays).
  Baseline: the same pair, direction and length from 20 random start days of the same test year; edge = rule - baseline.
  Overlap: also reported with only non-overlapping windows (per pair and year, in start order, skip a window that overlaps a
  window already taken).
  Pass bar: non-overlapping edge >= +0.10 ATR per trade, t >= 2, edge > 0 in both halves (2015-20 / 2021-26), and > 0 on >= 60%
  of the markets.  python3 bt/seasonal_fx.py"""
import os, sys, time, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "quant"))
import universe as U
sys.path.insert(0, os.path.join(ROOT, "lab"))
from ftmo_data import load_any

STARTS = list(range(1, 366, 5)); LENS = (10, 20, 30); YEARS = range(2015, 2027); LOOK = 15


def spread_by_year(sym, cat):
    if (sym, "M15") in cat: p = cat[(sym, "M15")]
    elif (sym, "M5") in cat: p = cat[(sym, "M5")]
    else: return {}
    d = load_any(p); s = d.sp[d.sp > 0]
    return (s.groupby(s.index.year).median() * 1.2).to_dict()


def main():
    cat = U.catalog(); spec = U.specs(); rng = np.random.default_rng(54); t0 = time.time()
    syms = sorted(s for s, tf in cat if tf == "D1" and (U.group_of(s) == "forex" or s in ("XAUUSD", "XAGUSD")))
    trades = []
    for sym in syms:
        D = load_any(cat[(sym, "D1")])[["open", "high", "low", "close", "sp"]]
        D = D[D.index.weekday < 5]; D = D[~D.index.duplicated()].sort_index()
        c = D.close.values; dates = D.index; n = len(c)
        pc = np.r_[c[0], c[:-1]]
        tr = np.maximum(D.high.values - D.low.values, np.maximum(np.abs(D.high.values - pc), np.abs(D.low.values - pc)))
        atr = pd.Series(tr).rolling(20).mean().values
        spy = spread_by_year(sym, cat); d1sp = D.sp.values * 2.0
        doy = dates.dayofyear.values; yr = dates.year.values
        # index of the first trading day on/after each (year, start day)
        first_idx = {}
        for y in np.unique(yr):
            ii = np.flatnonzero(yr == y); dd = doy[ii]
            for s in STARTS:
                k = np.searchsorted(dd, s)
                if k < len(ii): first_idx[(y, s)] = ii[k]

        def ret(i, L):
            j = i + L
            return (c[j] - c[i]) if j < n else np.nan

        def cost(i, j, side):
            sp_i = spy.get(dates[i].year, d1sp[i]); sp_j = spy.get(dates[j].year, d1sp[j])
            nights = 0; w = 0
            for k in range(i, j):                                  # nights between consecutive trading days
                gap = (dates[k + 1] - dates[k]).days
                nights += gap; w += 2 if dates[k].weekday() == 2 else 0       # Wednesday rollover counts 3 nights
            sw = U.swap_per_night(sym, c[i], side, spec if len(spec) else None) * (nights + w)
            return (sp_i + sp_j) / 2 + sw                           # half spread in, half out ~ one spread; + swap

        hist = {}
        for (y, s), i in first_idx.items():
            for L in LENS: hist[(y, s, L)] = ret(i, L)
        for Y in YEARS:
            for s in STARTS:
                if (Y, s) not in first_idx: continue
                i = first_idx[(Y, s)]
                for L in LENS:
                    j = i + L
                    if j >= n or not np.isfinite(atr[i]) or atr[i] <= 0: continue
                    past = [hist.get((y, s, L), np.nan) for y in range(Y - LOOK, Y)]
                    past = np.array([p for p in past if np.isfinite(p)])
                    if len(past) < 12: continue
                    up = (past > 0).mean(); dn = (past < 0).mean()
                    if max(up, dn) < 0.8: continue
                    side = 1 if up >= 0.8 else -1
                    R = (side * (c[j] - c[i]) - cost(i, j, side)) / atr[i]
                    base = []
                    for _ in range(20):                             # random start day in the same year, same side and length
                        ii = np.flatnonzero(yr == Y); k = int(rng.choice(ii[ii + L < n])) if (ii + L < n).any() else None
                        if k is None or not np.isfinite(atr[k]) or atr[k] <= 0: continue
                        base.append((side * (c[k + L] - c[k]) - cost(k, k + L, side)) / atr[k])
                    trades.append(dict(symbol=sym, group=U.group_of(sym), year=Y, start=s, L=L, side=side, hit=max(up, dn),
                                       entry=dates[i], exit=dates[j], R=R, base=np.mean(base) if base else np.nan))
        print(f"{sym}: {sum(1 for t in trades if t['symbol'] == sym)} windows traded ({time.time() - t0:.0f}s)", flush=True)
    T = pd.DataFrame(trades); T["edge"] = T.R - T.base
    T.to_csv(os.path.join(ROOT, "results", "seasonal_fx_trades.csv"), index=False)
    # non-overlapping: per symbol and year, in start order, skip windows overlapping a taken one
    keep = []
    for (sym, Y), g in T.sort_values(["symbol", "year", "entry", "L"]).groupby(["symbol", "year"]):
        last = None
        for idx, r in g.iterrows():
            if last is None or r.entry > last: keep.append(idx); last = r.exit
    NO = T.loc[keep]

    def summ(x, lab):
        t = x.edge.mean() / x.edge.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan
        h1 = x[x.year <= 2020].edge.mean(); h2 = x[x.year >= 2021].edge.mean()
        pos = (x.groupby("symbol").edge.mean() > 0).mean()
        print(f"{lab:34s} n={len(x):6d} rule {x.R.mean():+.3f} ATR | random {x.base.mean():+.3f} | edge {x.edge.mean():+.3f} (t {t:+.2f}) | "
              f"2015-20 {h1:+.3f} / 2021-26 {h2:+.3f} | markets with edge > 0: {pos:.0%} | win {(x.R > 0).mean():.0%}", flush=True)
    print()
    summ(T, "all selected windows")
    summ(NO, "non-overlapping")
    for L in LENS: summ(NO[NO.L == L], f"  non-overlapping, {L} days")
    for g, x in NO.groupby("group"): summ(x, f"  non-overlapping, {g}")
    summ(NO[NO.hit >= 0.93], "  non-overlapping, hit >= 93% (14-15/15)")
    jpy = NO[NO.symbol.str.endswith("JPY") & (NO.start.isin([241, 246])) ]
    if len(jpy): summ(jpy, "  JPY crosses, windows from ~1 Sep")
    print(NO.groupby("symbol").edge.agg(["mean", "size"]).round(3).sort_values("mean").to_string())
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
