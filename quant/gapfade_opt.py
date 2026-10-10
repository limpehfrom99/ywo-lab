"""Log #73: optimising the index gap fade honestly (pre-registered in research/log.md #73).
128-cell grid on the 9 selection indices; walk-forward choice by year; permutation test of the whole procedure (grid + walk-forward
+ full-sample best); CSCV; slippage; timeframes M1-H1; descriptive splits.
python3 quant/gapfade_opt.py [n_perm]   -> results/gapfade_opt_*.csv and results/gapfade_opt_trades.csv.gz"""
import os, sys, time, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "bt"))
import universe as U, intraday as ID, permute as P
from sessions import Session
from run_battery import intraday_frame
import robust as RB

MAIN = {"GER40.cash": "eu_cash", "EU50.cash": "eu_cash", "FRA40.cash": "eu_cash", "SPN35.cash": "eu_cash", "N25.cash": "eu_cash",
        "US100.cash": "us_cash", "US500.cash": "us_cash", "US30.cash": "us_cash", "US2000.cash": "us_cash"}
GAPS = (0.75, 1.0, 1.25, 1.5); STOPS = ("gap", 0.5, 1.0, 1.5); TGTS = ("close", "none"); EXITS = ("close", "3h"); ENTRIES = ("open", "15m")
DIMS = (GAPS, STOPS, TGTS, EXITS, ENTRIES)
CELLS = list(itertools.product(*DIMS))
BASE = (1.0, "gap", "close", "close", "open")
TEST_YEARS = (2023, 2024, 2025, 2026)
OUT = os.path.join(ROOT, "results")


def cell_arrays(S, comm, cell, slip_atr=0.0):
    """-> (day index array, R array, direction array) for one cell on one session matrix."""
    g_min, stop_m, tgt_m, exit_m, ent_m = cell
    n, K = S.C.shape
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (S.open - S.prev_close) / S.atr
    ok = np.isfinite(g) & (np.abs(g) >= g_min)
    sg = np.sign(np.nan_to_num(g)).astype(int); size = np.abs(S.open - S.prev_close)
    d = -sg
    stop = S.open + sg * size if stop_m == "gap" else S.open + sg * float(stop_m) * S.atr
    tgt = S.prev_close if tgt_m == "close" else None
    exit_col = None if exit_m == "close" else np.minimum(S.first + S.cols(180) - 1, K - 1)
    i = np.arange(n)
    if ent_m == "open":
        e_col = np.where(ok, S.first, -1); e_px = S.open.copy()
    else:
        c15 = S.first + S.cols(15)                                     # first column after the first 15 minutes
        cols = np.arange(K)[None, :]
        w = (cols >= S.first[:, None]) & (cols < c15[:, None])
        long = (d == 1)[:, None]
        hit_stop = (np.where(long, S.L <= stop[:, None], S.H >= stop[:, None]) & w).any(1)
        hit_tgt = (np.where(long, S.H >= tgt[:, None], S.L <= tgt[:, None]) & w).any(1) if tgt is not None else np.zeros(n, bool)
        cc = np.minimum(c15, K - 1)
        e_px = S.O[i, cc]
        side_ok = np.where(d == 1, e_px > stop, e_px < stop)
        if tgt is not None: side_ok &= np.where(d == 1, e_px < tgt, e_px > tgt)
        ok = ok & ~hit_stop & ~hit_tgt & side_ok & (c15 < K)
        e_col = np.where(ok, cc, -1)
    R = ID.simulate(S, e_col, e_px, np.where(ok, d, 0), stop, tgt, exit_col, comm, 1.2, False)[0]
    if slip_atr:
        with np.errstate(invalid="ignore", divide="ignore"):
            R = R - slip_atr * S.atr / np.abs(e_px - stop)
    m = np.isfinite(R) & ok
    return i[m], R[m], d[m]


def run_grid(sessions, cells=CELLS, slip_atr=0.0):
    """-> {cell: DataFrame(day, sym, R, d)}"""
    out = {}
    for c in cells:
        parts = []
        for s, (S, comm) in sessions.items():
            ii, R, d = cell_arrays(S, comm, c, slip_atr)
            if len(R): parts.append(pd.DataFrame({"day": S.days[ii], "sym": s, "R": R, "d": d}))
        out[c] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["day", "sym", "R", "d"])
    return out


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def walk_forward(trades, min_n=100):
    """Expanding window: each test year trades the cell with the best pooled t on all earlier data. -> (OOS trades, picks)"""
    oos, picks = [], []
    for Y in TEST_YEARS:
        cut = np.datetime64(f"{Y}-01-01"); end = np.datetime64(f"{Y + 1}-01-01")
        best, bt = None, -np.inf
        for c, T in trades.items():
            tr = T.R.values[T.day.values < cut]
            if len(tr) < min_n: continue
            t = tstat(tr)
            if np.isfinite(t) and t > bt: best, bt = c, t
        if best is None: continue
        T = trades[best]; sel = (T.day.values >= cut) & (T.day.values < end)
        oos.append(T[sel].assign(year=Y, cell=str(best))); picks.append((Y, best, bt, sel.sum(), T.R.values[sel].mean() if sel.any() else np.nan))
    return (pd.concat(oos, ignore_index=True) if oos else pd.DataFrame()), picks


def summarize(trades):
    rows = []
    for c, T in trades.items():
        R = T.R.values; dd = pd.DatetimeIndex(T.day)
        yrs = pd.Series(R).groupby(dd.year).mean()
        rows.append(dict(min_gap=c[0], stop=c[1], target=c[2], exit=c[3], entry=c[4], n=len(R), avgR=R.mean() if len(R) else np.nan,
                         t=tstat(R), before2024=R[dd < "2024-01-01"].mean() if (dd < "2024-01-01").any() else np.nan,
                         from2024=R[dd >= "2024-01-01"].mean() if (dd >= "2024-01-01").any() else np.nan, win=(R > 0).mean() if len(R) else np.nan,
                         worst_year=yrs.min() if len(yrs) else np.nan, by_year=" ".join(f"{y % 100}:{v:+.2f}" for y, v in yrs.items())))
    return pd.DataFrame(rows)


def neighbours(c):
    out = []
    for k, dim in enumerate(DIMS):
        j = dim.index(c[k])
        for jj in (j - 1, j + 1):
            if 0 <= jj < len(dim):
                n = list(c); n[k] = dim[jj]; out.append(tuple(n))
    return out


def resample(d, minutes, offset_min=0):
    r = d.resample(f"{minutes}min", offset=f"{offset_min}min", label="left", closed="left")
    x = pd.DataFrame({"open": r.open.first(), "high": r.high.max(), "low": r.low.min(), "close": r.close.last(),
                      "sp": r.sp.median(), "tickvol": r.tickvol.sum()}).dropna(subset=["open"])
    return x


def main():
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    t0 = time.time(); cat = U.catalog(); SS = {}
    for s, sess in MAIN.items():
        d, tf = intraday_frame(s, cat); SS[s] = (Session(d, sess), U.commission_of(s))
        print(f"{s} {tf}: {len(SS[s][0].days)} days {SS[s][0].days[0].date()}..{SS[s][0].days[-1].date()}", flush=True)
    real = run_grid(SS)
    C = summarize(real); C.to_csv(os.path.join(OUT, "gapfade_opt_cells.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(f"\n128 cells ({time.time() - t0:.0f}s); top 20 by t:"); print(C.sort_values("t", ascending=False).head(20).round(3).to_string(index=False))
    print(f"cells positive: {(C.avgR > 0).mean():.0%}; base cell: " + C[(C.min_gap == 1.0) & (C.stop == 'gap') & (C.target == 'close') & (C.exit == 'close') & (C.entry == 'open')].round(3).to_string(index=False, header=False))
    # marginal means per dimension (averaged over the other dimensions)
    for k, name in enumerate(("min_gap", "stop", "target", "exit", "entry")):
        print(f"  by {name}: " + ", ".join(f"{v}: {C[C[name].astype(str) == str(v)].avgR.mean():+.3f}" for v in DIMS[k]))
    # walk-forward
    oos, picks = walk_forward(real)
    b = real[BASE]; byears = pd.DatetimeIndex(b.day).year
    base_oos = b[np.isin(byears, TEST_YEARS)]
    print("\nwalk-forward picks (test year: cell, training t, OOS n, OOS mean R):")
    for Y, c, bt, n, m in picks: print(f"  {Y}: {c} t {bt:.2f} -> n {n}, mean {m:+.3f}  | base cell {Y}: {b.R[byears == Y].mean():+.3f} ({(byears == Y).sum()})")
    wf_mean = oos.R.mean(); print(f"walk-forward OOS: n {len(oos)}, mean {wf_mean:+.3f}, t {tstat(oos.R):.2f} | base cell same years: n {len(base_oos)}, mean {base_oos.R.mean():+.3f}, t {tstat(base_oos.R):.2f}")
    pd.DataFrame([dict(year=Y, cell=str(c), train_t=bt, oos_n=n, oos_mean=m, base_mean=b.R[byears == Y].mean()) for Y, c, bt, n, m in picks]).to_csv(
        os.path.join(OUT, "gapfade_opt_wf.csv"), index=False, float_format="%.4f")
    from collections import Counter
    most = Counter(c for _, c, _, _, _ in picks).most_common(1)[0][0]
    nb = neighbours(most); nbm = {c: real[c].R.mean() for c in nb}
    print(f"most-picked cell {most}: full-sample mean {real[most].R.mean():+.3f}; neighbours all positive: {all(v > 0 for v in nbm.values())} "
          f"(min {min(nbm.values()):+.3f})")
    best_full = C.loc[C.t.idxmax()]; best_t = best_full.t
    # CSCV over all 128 cells on daily sums
    allD = pd.DatetimeIndex(sorted(set().union(*[set(pd.DatetimeIndex(T.day)) for T in real.values()])))
    M = np.column_stack([real[c].groupby("day").R.sum().reindex(allD).fillna(0.0).values for c in CELLS])
    cs = RB.cscv_pbo(M, n_blocks=10)
    print(f"CSCV 128 cells: PBO {cs['pbo']:.0%}, IS winner {cs['is_best']:+.3f}R/day -> OOS {cs['oos_best']:+.3f} (median cell {cs['oos_median']:+.3f}), "
          f"winner loses OOS in {cs['p_oos_loss']:.0%} of splits")
    # slippage
    rows = []
    for lab, c in (("base", BASE), ("most_picked", most)):
        for sl in (0.0, 0.01, 0.02, 0.05, 0.10):
            T = run_grid(SS, [c], slip_atr=sl)[c]
            rows.append(dict(cell=lab, slip_atr=sl, n=len(T), avgR=T.R.mean(), t=tstat(T.R)))
    SL = pd.DataFrame(rows); print("\nslippage (extra cost in daily ATR per round trip):"); print(SL.round(3).to_string(index=False))
    atr_pts = {s: np.nanmedian(S.atr[pd.DatetimeIndex(S.days) >= "2025-01-01"]) for s, (S, _) in SS.items()}
    print("median daily ATR since 2025 (points): " + ", ".join(f"{s.split('.')[0]} {v:.0f}" for s, v in atr_pts.items()))
    SL.to_csv(os.path.join(OUT, "gapfade_opt_slippage.csv"), index=False, float_format="%.4f")
    # descriptive splits for base and most-picked
    for lab, c in (("base", BASE), ("most_picked", most)):
        T = real[c].copy(); dd = pd.DatetimeIndex(T.day)
        print(f"\n{lab} {c}: long (fade down gaps) {T.R[T.d == 1].mean():+.3f} ({(T.d == 1).sum()}) | short (fade up gaps) {T.R[T.d == -1].mean():+.3f} "
              f"({(T.d == -1).sum()}) | Monday {T.R[dd.weekday == 0].mean():+.3f} ({(dd.weekday == 0).sum()}) | other days {T.R[dd.weekday != 0].mean():+.3f}")
        print("  by index: " + ", ".join(f"{s.split('.')[0]} {g.R.mean():+.3f} ({len(g)})" for s, g in T.groupby("sym")))
        print("  by year: " + ", ".join(f"{y}: {g.mean():+.3f} ({len(g)})" for y, g in T.R.groupby(dd.year)))
    keep = pd.concat([real[BASE].assign(cell="base"), real[most].assign(cell="most_picked"), oos.assign(cell="wf_oos")[["day", "sym", "R", "d", "cell"]]])
    keep.to_csv(os.path.join(OUT, "gapfade_opt_trades.csv.gz"), index=False, float_format="%.6g")
    # timeframes (common period from 2022)
    rows = []
    for s, sess in MAIN.items():
        frames = {}
        if (s, "M1") in cat: frames["M1"] = U.load(s, "M1", cat)
        base_d, base_tf = intraday_frame(s, cat)
        frames[base_tf] = base_d
        off = 30 if sess == "us_cash" else 0
        src = frames.get("M1", base_d)
        for m, lab in ((15, "M15"), (30, "M30"), (60, "H1")):
            if lab not in frames: frames[lab] = resample(src, m, off if m == 60 else 0)
        for tf, d in frames.items():
            d = d[d.index >= "2021-12-20"]
            if "tickvol" not in d: d = d.assign(tickvol=1.0)
            try: S = Session(d[~d.index.duplicated()].sort_index(), sess)
            except Exception as e: print(f"  {s} {tf}: {e}"); continue
            keepd = pd.DatetimeIndex(S.days) >= "2022-01-01"
            for lab, c in (("base", BASE), ("most_picked", most)):
                ii, R, dd = cell_arrays(S, U.commission_of(s), c)
                m = keepd[ii]
                rows.append(dict(sym=s, tf=tf, cell=lab, n=int(m.sum()), sumR=R[m].sum(), avgR=R[m].mean() if m.any() else np.nan))
    TF = pd.DataFrame(rows); TF.to_csv(os.path.join(OUT, "gapfade_opt_tf.csv"), index=False, float_format="%.4f")
    g = TF.groupby(["cell", "tf"]).agg(n=("n", "sum"), sumR=("sumR", "sum")); g["avgR"] = g.sumR / g.n
    print("\ntimeframes (2022+, pooled over the indices that have each bar size):"); print(g.round(3).to_string())
    m1 = TF[TF.sym.isin(["US100.cash", "US500.cash"])].groupby(["cell", "tf"]).agg(n=("n", "sum"), sumR=("sumR", "sum")); m1["avgR"] = m1.sumR / m1.n
    print("US100 + US500 only:"); print(m1.round(3).to_string())
    print(f"\nreal done ({time.time() - t0:.0f}s); permutation test, {n_perm} shuffles of all 9 indices, all 128 cells:", flush=True)
    rng = np.random.default_rng(73); wf_perm, best_perm, basem = [], [], []
    for k in range(n_perm):
        sh = {s: (P.permute_session(S, rng), comm) for s, (S, comm) in SS.items()}
        pr = run_grid(sh)
        o, _ = walk_forward(pr)
        wf_perm.append(o.R.mean() if len(o) else np.nan)
        best_perm.append(np.nanmax([tstat(T.R.values) for T in pr.values()]))
        basem.append(pr[BASE].R.mean())
        if (k + 1) % 20 == 0:
            print(f"  {k + 1} shuffles ({time.time() - t0:.0f}s): WF OOS mean so far median {np.nanmedian(wf_perm):+.3f}, 95th {np.nanpercentile(wf_perm, 95):+.3f}; "
                  f"best t median {np.nanmedian(best_perm):.2f}", flush=True)
            pd.DataFrame(dict(wf_oos=wf_perm, best_t=best_perm, base_mean=basem)).to_csv(os.path.join(OUT, "gapfade_opt_perm.csv"), index=False)
    pd.DataFrame(dict(wf_oos=wf_perm, best_t=best_perm, base_mean=basem)).to_csv(os.path.join(OUT, "gapfade_opt_perm.csv"), index=False)
    print(f"\nwalk-forward OOS mean: real {wf_mean:+.3f} vs shuffled median {np.nanmedian(wf_perm):+.3f}, 95th {np.nanpercentile(wf_perm, 95):+.3f} -> p_WF {P.pvalue(wf_mean, wf_perm):.3f}")
    print(f"full-sample best cell t {best_t:.2f} ({tuple(best_full[['min_gap', 'stop', 'target', 'exit', 'entry']])}) vs shuffled best t median "
          f"{np.nanmedian(best_perm):.2f}, 95th {np.nanpercentile(best_perm, 95):.2f} -> p_best {P.pvalue(best_t, best_perm):.3f}")
    print(f"base cell mean {real[BASE].R.mean():+.3f} vs shuffled {np.nanmean(basem):+.3f} (95th {np.nanpercentile(basem, 95):+.3f}) -> p_alone {P.pvalue(real[BASE].R.mean(), basem):.3f}")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
