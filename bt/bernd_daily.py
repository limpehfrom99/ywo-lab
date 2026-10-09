"""Log #66: Bernd Skorupinski's Valuation Tool and True Seasonality as stand-alone daily rules on every FTMO symbol with long
daily history (rules fixed in research/log.md #66 before running; inputs from bt/bernd_bias.py).
  VAL: v (vs the synthetic dollar index; for indices and stocks also vs gold) crosses below -0.75 -> long at the next open; crosses
       above +0.75 -> short. Exit at the close 20 trading days later, or at a stop 2 x ATR(20) from the entry (gap -> open).
  SEAS: every N trading days (N = 10, 20, 30; back-to-back blocks) take the side of the 15-year seasonal average for the next
       N days, hold N days, same stop.
  Costs: FTMO spread at entry and exit (median intraday spread that year x 1.2, else D1 spread x 2) + commission + swap for every
       night held (today's swap sheet, x3 on the triple day). Result per trade in units of the stop (R = 2 ATR).
  Baseline: the same side and holding period from 20 random days of the same year (market drift and carry are not edge).
  Pass bar (same as the battery's daily rules): pooled n >= 200, edge over the baseline >= +0.05R with t >= 2, positive in both
  halves (before 2018 / from 2018 for FX and metals; before 2023 / from 2023 for the rest), on >= 60% of markets.
python3 bt/bernd_daily.py"""
import os, sys, time, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "quant"))
sys.path.insert(0, os.path.join(ROOT, "bt"))
import universe as U
import bernd_bias as BB

HOLD = 20; STOP_ATR = 2.0


def spread_year(sym):
    cat = U.catalog()
    for tf in ("M15", "M5", "M1"):
        if (sym, tf) in cat:
            d = U.load(sym, tf, cat); s = d.sp[d.sp > 0]
            return (s.groupby(s.index.year).median() * 1.2).to_dict()
    return {}


def simulate(sym, d, entries, spec, spy, rng, hold=HOLD):
    """entries: list of (i_entry, side). Returns trade rows with R and baseline."""
    O, H, L, C = (d[k].values for k in ("open", "high", "low", "close")); n = len(C); dates = d.index
    pc = np.r_[C[0], C[:-1]]
    atr = pd.Series(np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))).rolling(20).mean().shift(1).values
    comm = U.commission_of(sym); trip = U.triple_day(sym, spec if len(spec) else None); d1sp = d.sp.values * 2.0
    yrs = dates.year.values

    def one(i, side, hold):
        if i >= n - 1 or not np.isfinite(atr[i]) or atr[i] <= 0: return None
        e = O[i]; stop = e - side * STOP_ATR * atr[i]; j_end = min(i + hold - 1, n - 1); x = C[j_end]; xi = j_end
        for j in range(i, j_end + 1):
            if side == 1 and L[j] <= stop: x = min(stop, O[j]) if j > i else stop; xi = j; break
            if side == -1 and H[j] >= stop: x = max(stop, O[j]) if j > i else stop; xi = j; break
        nights = int((dates[xi] - dates[i]).days) + 2 * sum(1 for k in range(i, xi) if dates[k].weekday() == trip)
        sp = spy.get(dates[i].year, d1sp[i])
        cost = sp + comm * (abs(e) + abs(x)) + U.swap_per_night(sym, e, side, spec if len(spec) else None) * nights
        return (side * (x - e) - cost) / (STOP_ATR * atr[i])

    rows = []
    for i, side in entries:
        r = one(i, side, hold)
        if r is None: continue
        pool = np.flatnonzero(yrs == yrs[i]); pool = pool[pool < n - hold]
        base = [one(int(k), side, hold) for k in rng.choice(pool, size=min(20, len(pool)), replace=False)] if len(pool) else []
        base = [b for b in base if b is not None]
        rows.append(dict(symbol=sym, group=U.group_of(sym), day=dates[i], side=side, R=r, base=np.mean(base) if base else np.nan))
    return rows


def main():
    t0 = time.time(); rng = np.random.default_rng(65); spec = U.specs(); cat = U.catalog()
    syms = sorted(s for s, tf in cat if tf == "D1" and U.group_of(s) not in ("soft",))
    out = []
    for sym in syms:
        d = BB.d1(sym)
        if d is None or len(d) < 900: continue
        T = BB.bias_table(sym); spy = spread_year(sym)
        refs = [("val_dxy", "dxy"), ("lvl_dxy", "dxy_level")] + ([("val_gold", "gold"), ("lvl_gold", "gold_level")]
                                                                  if U.group_of(sym) in ("stock", "us_index", "index", "energy") else [])
        for col, ref in refs:
            if col not in T or T[col].notna().sum() < 250: continue
            v = T[col].values; ent = []
            for i in range(1, len(v)):
                if not (np.isfinite(v[i]) and np.isfinite(v[i - 1])): continue
                if v[i] < -0.75 <= v[i - 1]: ent.append((i, 1))
                elif v[i] > 0.75 >= v[i - 1]: ent.append((i, -1))
            out += [dict(r, rule=f"VAL_{ref}") for r in simulate(sym, d, ent, spec, spy, rng)]
        for N in (10, 20, 30):
            s = T[f"seas{N}"].values; ent = []; i = int(np.argmax(np.isfinite(s)))
            while i < len(s) - 1:
                if np.isfinite(s[i]) and s[i] != 0: ent.append((i, 1 if s[i] > 0 else -1))
                i += N
            out += [dict(r, rule=f"SEAS{N}") for r in simulate(sym, d, ent, spec, spy, rng, hold=N)]
        print(f"{sym}: {sum(1 for r in out if r['symbol'] == sym)} trades ({time.time() - t0:.0f}s)", flush=True)
    R = pd.DataFrame(out); R["edge"] = R.R - R.base
    R.to_csv(os.path.join(ROOT, "results", "bernd_daily_trades.csv"), index=False)
    t = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan
    print()
    for rule, x in R.groupby("rule"):
        cut = np.where(x.group.isin(["forex", "metal"]), x.day < "2018-01-01", x.day < "2023-01-01")
        pos = (x.groupby("symbol").edge.mean() > 0).mean()
        print(f"{rule:9s} n={len(x):6d} R {x.R.mean():+.3f} (t {t(x.R):+.2f}) | baseline {x.base.mean():+.3f} | edge {x.edge.mean():+.3f} "
              f"(t {t(x.edge.dropna()):+.2f}) | halves {x.edge[cut].mean():+.3f} / {x.edge[~cut].mean():+.3f} | markets edge>0 {pos:.0%} | "
              f"longs {x.R[x.side == 1].mean():+.3f} shorts {x.R[x.side == -1].mean():+.3f}")
        for g, y in x.groupby("group"):
            print(f"      {g:9s} n={len(y):5d} R {y.R.mean():+.3f} edge {y.edge.mean():+.3f} (t {t(y.edge.dropna()):+.2f})")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
