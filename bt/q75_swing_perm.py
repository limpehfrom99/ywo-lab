"""Log #75 / #39 exit grid: selection-aware permutation test (PROTOCOL 'Robustness checks', pattern of log #70 / bt/robust_check.py C).

Triggered because two PRIMARY cells (D1 pooled by group) cleared the CANDIDATE bar: crypto D1 N20_chand2 and crypto D1 N55_chand2.
Cells = every group-pooled cell of the idea: 8 groups x 2 timeframes (D1, H4) x 14 entry/exit cells = 224 (as run in
q75_swing_trend.py, same data, segments, costs). Statistic = pooled t of R (as #70). Null = random entry bars: every symbol-cell's
real trades are replaced by the same number of trades with the same directions, entered at the next open after a random bar of the
same symbol/timeframe/segment, with the same exit rule and R unit; all 224 cells recomputed in every shuffle. 200 shuffles.
p_alone = share of shuffles whose same cell >= the real t; p_best = share whose BEST cell >= the real t; BCa 95% lower bound of the
passing cells' mean R (robust.bca_bounds, 20,000 resamples). Also: per-symbol / per-year split of the passing cells and the same
cells without the LTCUSD 2011-12 D1 history (half/double price glitches, see the q75_swing report).
Output: results/q75_swing_exitgrid_perm.csv, results/q75_swing_exitgrid_perm_trades.csv (real trades of the passing cells).
"""
import sys, os, time
import numpy as np, pandas as pd

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
import q75_swing_trend as TR  # noqa: E402
from robust import mcpt_select, bca_bounds  # noqa: E402
U = C.U
N_PERM = 200
PASSING = [("crypto", "D1", "N20_chand2"), ("crypto", "D1", "N55_chand2")]


def main():
    cat = U.catalog(); t0 = time.time()
    cells = [(f"N{N}_{name}", kind, k, tm) for N in (20, 55) for name, kind, k, tm in TR.GRID_EXITS]
    real = {}                     # (group, tf, cell) -> [n, s, ss]
    null = {}                     # (group, tf, cell) -> arrays (N_PERM,) n, s, ss
    keep = []
    rng_seed = 75039
    for si, sym in enumerate(C.symbols(cat)):
        grp = U.group_of(sym); comm = U.commission_of(sym)
        intra, btf, rel = C.load_intraday(sym, cat)
        d1 = C.load_d1(sym, cat, intra, rel)
        frames = {}
        if d1 is not None and len(d1) > 300: frames["D1"] = d1
        if intra is not None: frames["H4"] = C.resample(intra, "H4")
        del intra
        tmin = min(C.ns(f.index)[0] for f in frames.values()); tmax = max(C.ns(f.index)[-1] for f in frames.values())
        p_ref = max(frames.values(), key=lambda f: f.index[-1]).close.iloc[-1]
        sw = C.Swaps(sym, tmin, tmax, p_ref)
        for tf, x in frames.items():
            if len(x) < 300: continue
            for sa, sb in C.segments(C.ns(x.index)):
                if sb - sa < 200: continue
                xs = x.iloc[sa:sb]
                I = TR.indicators(xs); t = C.ns(xs.index); sp = xs.sp.values.astype(float)
                args = (I["o"], I["h"], I["l"], I["c"])
                for cell, kind, k, tm in cells:
                    N = int(cell[1:3])
                    S_i, E_i, X_i, D, EP, XP, AT, HW = TR.run_rule(*args, I[f"sig{N}"], I["atr"], I["ll10"], I["hh10"], I["sma50"], 60, kind, k, tm)
                    if len(E_i) == 0: continue
                    R = TR.costs_R(I, sp, t, sw, comm, E_i, X_i, HW, D, EP, XP, 2.0 * AT)
                    key = (grp, tf, cell)
                    r = real.setdefault(key, [0, 0.0, 0.0]); r[0] += len(R); r[1] += R.sum(); r[2] += (R ** 2).sum()
                    if (grp, tf, cell) in PASSING:
                        keep.append(pd.DataFrame(dict(symbol=sym, group=grp, tf=tf, cell=cell, t=t[E_i], side=D, R=R, hold=X_i - E_i)))
                    rng_seed += 1
                    rs = TR.run_random(*args, I["atr"], I["ll10"], I["hh10"], I["sma50"], 60, kind, k, tm, np.tile(D, N_PERM), 1, rng_seed)
                    Rr = TR.costs_R(I, sp, t, sw, comm, rs[1], rs[2], None, rs[3], rs[4], rs[5], 2.0 * rs[6])
                    shuffle = rs[7] // len(D)
                    z = null.setdefault(key, [np.zeros(N_PERM), np.zeros(N_PERM), np.zeros(N_PERM)])
                    z[0] += np.bincount(shuffle, minlength=N_PERM); z[1] += np.bincount(shuffle, Rr, N_PERM)
                    z[2] += np.bincount(shuffle, Rr ** 2, N_PERM)
        print(f"{sym} done ({si + 1}) {time.time() - t0:.0f}s", flush=True)
        del frames
    keys = sorted(real)

    def tstat(n, s, ss):
        n = np.asarray(n, float); m = s / np.maximum(n, 1); v = (ss - n * m * m) / np.maximum(n - 1, 1)
        return np.where((n > 2) & (v > 0), m / np.sqrt(np.maximum(v, 1e-300) / np.maximum(n, 1)), np.nan)

    real_t = pd.Series({"|".join(k): float(tstat(*real[k])) for k in keys})
    real_m = pd.Series({"|".join(k): real[k][1] / real[k][0] for k in keys})
    null_t = np.column_stack([tstat(*null[k]) for k in keys])
    tab = mcpt_select(real_t, null_t)
    tab["n"] = [real[k][0] for k in keys]; tab["meanR"] = real_m.values
    tab["null_mean_avg"] = [np.mean(null[k][1] / np.maximum(null[k][0], 1)) for k in keys]
    tab = tab.sort_values("real", ascending=False)
    tab.to_csv(os.path.join(C.RES, "q75_swing_exitgrid_perm.csv"), float_format="%.4g")
    best = np.nanmax(null_t, axis=1)
    print(f"\nshuffled best pooled t over {len(keys)} cells: median {np.median(best):.2f}, 95th {np.quantile(best, 0.95):.2f}, "
          f"99th {np.quantile(best, 0.99):.2f}; real best {real_t.max():.2f} ({real_t.idxmax()})")
    print(tab.head(12).round(3).to_string())
    K = pd.concat(keep, ignore_index=True) if keep else pd.DataFrame()
    if len(K):
        K.to_csv(os.path.join(C.RES, "q75_swing_exitgrid_perm_trades.csv"), index=False, float_format="%.5g")
        for (g, tf, cell), x in K.groupby(["group", "tf", "cell"]):
            b = bca_bounds(x.R.values, "mean", B=20000, rng=7)
            yr = x.groupby(pd.DatetimeIndex(x.t.values).year).R.agg(["count", "mean"])
            print(f"\n{g} {tf} {cell}: n={len(x)} mean {x.R.mean():+.3f}R  BCa 95% low {b['low'][0.025]:+.3f}  "
                  f"p_best {tab.loc['|'.join((g, tf, cell)), 'p_best']:.3f}  p_alone {tab.loc['|'.join((g, tf, cell)), 'p_alone']:.3f}")
            print("  by symbol: " + ", ".join(f"{s} {v['count']:.0f}/{v['mean']:+.3f}" for s, v in x.groupby("symbol").R.agg(["count", "mean"]).iterrows()))
            print("  by year: " + " ".join(f"{y % 100:02d}:{v['count']:.0f}/{v['mean']:+.2f}" for y, v in yr.iterrows()))
            y = x[~((x.symbol == "LTCUSD") & (pd.DatetimeIndex(x.t.values).year <= 2012))]
            print(f"  without LTCUSD 2011-12: n={len(y)} mean {y.R.mean():+.3f}R t {C.tstat(y.R.values):+.2f}; "
                  f"from 2018 only: n={(pd.DatetimeIndex(x.t.values).year >= 2018).sum()} mean {x.R[pd.DatetimeIndex(x.t.values).year >= 2018].mean():+.3f}; "
                  f"without the top 1% trades: {x.R[x.R < x.R.quantile(0.99)].mean():+.3f}")


if __name__ == "__main__":
    main()
