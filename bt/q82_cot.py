"""Log #82 part 1 (+ part 4): Bernd Skorupinski's COT index as weekly rules on the 15 commodity CFDs (CFTC Disaggregated
Futures-Only, 2006-2026) and on US500/US100 (MT5 calendar CFTC non-commercial net = large speculators, contrarian).

Rules fixed in research/log.md #82 and research/drafts/q82_cot.md ("Rules as implemented") before this ran:
  signal   COT index of a group over the last N reports (q82_cot_data.cot_signal), large/small speculators inverted;
           bullish >= hi, bearish <= lo. Grid: group {comm, large, small} x N {26, 52, 157} x thresholds {80/20, 90/10}
           x hold {1, 4, 8 weeks}. Primary cell: comm, 157, 80/20, hold 4 (also 1 and 8), pooled over the 15 commodities.
           Indices: only 'large' exists (the calendar series); index primary = large, 157, 80/20, hold 4.
  timing   a report is used from the first FTMO D1 bar that opens after its release (normally Friday 15:30 New York -> the
           Sunday-evening open); reports with delayed releases (shutdowns, 2023 ION incident) give no signal.
  trade    in the bias direction at that bar's open; exit at the open of the first bar >= 7 x hold days later; no stop.
           Non-overlapping per market: a signal while a trade is open is ignored (the tradeable rule). The 'every signal week'
           mean (overlapping) is reported too.
  result   R = (side x (exit - entry) - costs) / ATR(20) of the daily bars before entry. Costs: spread x 1.2 at entry (median
           intraday spread of the entry day, zeros filled per q75_swing_common) + commission x (|entry| + |exit|) + swap for
           every 17:00 New York rollover held (today's swap sheet as % of price, x3 on the triple day; q75_swing_common.Swaps).
  baseline (a) random weeks: the same side and hold from 20 random report weeks of the same market and year; (b) always-long:
           a long with the same hold from every report week of the same market and year.
  bar      PROTOCOL rule 4 (n >= 200, both chronological halves > 0, t >= 2, mean >= +0.05R, no year < -0.3R) AND mean R above
           both baselines. If the primary passes: selection-aware permutation test over every cell (each market's weekly signal
           series circularly shifted by a random offset, >= 200 shuffles, all cells rerun, best pooled t kept -> p_best) and
           the BCa 95% lower bound of the primary's mean R.
python3 -I bt/q82_cot.py [--perm N] [--force-perm]"""
import os, sys, time, argparse
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
import numpy as np
import pandas as pd
from numba import njit
import universe as U                    # noqa: E402
import q75_swing_common as C            # noqa: E402
import q82_cot_data as Q                # noqa: E402

RES = "/home/claude/ywo-lab/results"
HOLDS = (1, 4, 8); NWIN = (26, 52, 157); THRS = ((80, 20), (90, 10)); GROUPS = ("comm", "large", "small")
DAY = 86400 * 10 ** 9
COMMODITIES = list(Q.DISAGG_MAP.values())
CODE_OF = {v: k for k, v in Q.DISAGG_MAP.items()}
INDEX_SERIES = {"US500.cash": "S&P 500", "US100.cash": "Nasdaq 100"}
PRIMARY = ("comm", 157, 80, 20)


# ------------------------------------------------------------------------------------------------------------ prices
def price_table(sym, release_ns, cat):
    """Outcome of a trade entered at the first D1 bar opening after each release, for every hold: dict of arrays."""
    intra, tf, rel = C.load_intraday(sym, cat)
    d = C.load_d1(sym, cat, intra=intra, rel=rel)
    del intra
    t = C.ns(d.index); O = d.open.values; Hh = d.high.values; L = d.low.values; Cl = d.close.values; sp = d.sp.values
    n = len(t)
    pc = np.r_[np.nan, Cl[:-1]]
    tr = np.fmax(Hh - L, np.fmax(np.abs(Hh - pc), np.abs(L - pc)))
    atr = pd.Series(tr).rolling(20).mean().shift(1).values
    sw = C.Swaps(sym, t[0], t[-1], p_ref=Cl[-1]); comm = U.commission_of(sym)
    holes = np.r_[0, np.cumsum(np.diff(t) > 10 * DAY)]           # holes before bar i
    ent = np.searchsorted(t, release_ns, side="right")            # first bar that opens after the release
    ok_e = (ent < n)
    e = np.minimum(ent, n - 1)
    ok_e &= np.isfinite(atr[e]) & (atr[e] > 0)
    out = dict(sym=sym, t_ent=np.where(ok_e, t[e], -1), year=pd.DatetimeIndex(t[e] + DAY).year.values,
               first=d.index[0], last=d.index[-1], n_bars=n)
    for H in HOLDS:
        x = np.searchsorted(t, t[e] + 7 * H * DAY, side="left")
        ok = ok_e & (x < n)
        xx = np.minimum(x, n - 1)
        ok &= (holes[xx] == holes[e]) & ((t[xx] - t[e]) <= (7 * H + 7) * DAY)
        en, ex = O[e], O[xx]
        nights = sw.nights(t[e], t[xx])
        base = sp[e] * 1.2 + comm * (np.abs(en) + np.abs(ex))
        cl = base + sw.per_night(np.ones(len(e)), en) * nights
        cs = base + sw.per_night(-np.ones(len(e)), en) * nights
        out[f"ok{H}"] = ok
        out[f"t_ex{H}"] = np.where(ok, t[xx], -1)
        out[f"RL{H}"] = np.where(ok, (ex - en - cl) / atr[e], np.nan)
        out[f"RS{H}"] = np.where(ok, (en - ex - cs) / atr[e], np.nan)
        out[f"cost{H}"] = np.where(ok, (cl + cs) / 2 / atr[e], np.nan)
        out[f"swapL{H}"] = np.where(ok, sw.per_night(np.ones(len(e)), en) * nights / atr[e], np.nan)
        out[f"swapS{H}"] = np.where(ok, sw.per_night(-np.ones(len(e)), en) * nights / atr[e], np.nan)
    return out


# ------------------------------------------------------------------------------------------------------------ markets
def market_weeks(sym, cat):
    """Weekly signal inputs for one market: DataFrame indexed by week (release order) with release (ns), asof, skip, and the
    signal columns for every (group, N, thr); plus the price table."""
    if sym in INDEX_SERIES:
        A = Q.calendar_release_asof(INDEX_SERIES[sym])
        W = pd.DataFrame({"asof": A["asof"].values, "release": A.index.values, "skip": A["skip"].values})
        vals = pd.Series(A["value"].values)
        for N in NWIN:
            for hi, lo in THRS:
                s = Q.series_signal(vals, N, hi, lo, contrarian=True)
                W[f"large_{N}_{hi}"] = np.where(W.skip.values, 0, s.side.values)
                if (N, hi) == (157, 80): W["idx_large_157"] = s.bias_idx.values
    else:
        rep = Q.market_report(CODE_OF[sym]); S = Q.release_schedule()
        W = pd.DataFrame({"asof": rep.index, "release": S.loc[rep.index, "release"].values, "skip": S.loc[rep.index, "skip"].values})
        for g in GROUPS:
            for N in NWIN:
                for hi, lo in THRS:
                    s = Q.cot_signal(rep, g, N, hi, lo)
                    W[f"{g}_{N}_{hi}"] = np.where(W.skip.values, 0, s.side.values)
                    if (N, hi) == (157, 80): W[f"idx_{g}_157"] = s.bias_idx.values
    rel_ns = pd.DatetimeIndex(W.release.values).values.astype("datetime64[ns]").view("i8")
    P = price_table(sym, rel_ns, cat)
    W["t_ent"] = P["t_ent"]; W["year"] = P["year"]
    for H in HOLDS:
        for k in ("ok", "t_ex", "RL", "RS", "cost", "swapL", "swapS"): W[f"{k}{H}"] = P[f"{k}{H}"]
    W.attrs.update(sym=sym, first=P["first"], last=P["last"], n_bars=P["n_bars"])
    return W


def cell_names(sym):
    gs = ("large",) if sym in INDEX_SERIES else GROUPS
    return [(g, N, hi, lo) for g in gs for N in NWIN for hi, lo in THRS]


# ------------------------------------------------------------------------------------------------------------ trades
@njit(cache=True)
def nonoverlap(side, ok, t_ent, t_ex):
    n = len(side); out = np.empty(n, np.int64); k = 0; free = -1
    for w in range(n):
        if side[w] != 0 and ok[w] and t_ent[w] >= free:
            out[k] = w; k += 1; free = t_ex[w]
    return out[:k]


def baselines(W, H):
    """Per market-year: valid week indices (for random draws) and the always-long mean."""
    ok = W[f"ok{H}"].values; yrs = W.year.values; RL = W[f"RL{H}"].values
    pools, longm = {}, {}
    for y in np.unique(yrs[ok]):
        m = np.flatnonzero(ok & (yrs == y)); pools[y] = m; longm[y] = float(np.mean(RL[m]))
    return pools, longm


def trades_for(W, cellkey, H, rng, pools, longm, overlap=False):
    side = W[cellkey].values.astype(np.int64); ok = W[f"ok{H}"].values
    t_ent = W.t_ent.values.astype(np.int64); t_ex = W[f"t_ex{H}"].values.astype(np.int64)
    idx = np.flatnonzero((side != 0) & ok) if overlap else nonoverlap(side, ok, t_ent, t_ex)
    if not len(idx): return None
    sd = side[idx]; RL = W[f"RL{H}"].values; RS = W[f"RS{H}"].values
    R = np.where(sd > 0, RL[idx], RS[idx]); yrs = W.year.values[idx]
    if overlap:
        return pd.DataFrame(dict(R=R, side=sd))
    br = np.empty(len(idx)); bl = np.empty(len(idx))
    for k, (w, s, y) in enumerate(zip(idx, sd, yrs)):
        p = pools[y]; draw = rng.choice(p, size=min(20, len(p)), replace=False)
        br[k] = np.mean(RL[draw] if s > 0 else RS[draw]); bl[k] = longm[y]
    return pd.DataFrame(dict(sym=W.attrs["sym"], asof=W["asof"].values[idx], t_ent=t_ent[idx], t_ex=t_ex[idx], year=yrs, side=sd, R=R,
                             base_rand=br, base_long=bl, cost=W[f"cost{H}"].values[idx],
                             swap=np.where(sd > 0, W[f"swapL{H}"].values[idx], W[f"swapS{H}"].values[idx])))


# ------------------------------------------------------------------------------------------------------------ stats
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def t_clustered(x, cl):
    """t of the mean with trades clustered by entry week (markets entering the same week are not independent)."""
    x = np.asarray(x, float); n = len(x)
    if n < 3: return np.nan
    e = pd.Series(x - x.mean()).groupby(np.asarray(cl)).sum().values
    se = np.sqrt(np.sum(e ** 2)) / n
    return x.mean() / se if se > 0 else np.nan


def stats(T):
    if T is None or not len(T): return dict(n=0)
    T = T.sort_values("t_ent"); R = T.R.values; n = len(R)
    half = n // 2
    yr = T.groupby("year").R.mean()
    wk = (T.t_ent.values // (7 * DAY))
    edge = R - T.base_rand.values; edgeL = R - T.base_long.values
    pre = T.year < 2024
    d = dict(n=n, meanR=R.mean(), t=tstat(R), t_wk=t_clustered(R, wk), win=(R > 0).mean(),
             half1=R[:half].mean() if half else np.nan, half2=R[half:].mean(),
             pre24=R[pre.values].mean() if pre.any() else np.nan, from24=R[~pre.values].mean() if (~pre).any() else np.nan,
             years_pos=f"{int((yr > 0).sum())}/{len(yr)}", worst_year=yr.min(), worst_yr=int(yr.idxmin()),
             last60=R[-60:].mean(), base_rand=T.base_rand.mean(), base_long=T.base_long.mean(),
             edge=edge.mean(), t_edge=tstat(edge), t_edge_wk=t_clustered(edge, wk), edge_long=edgeL.mean(), t_edge_long=tstat(edgeL),
             longs=int((T.side > 0).sum()), shorts=int((T.side < 0).sum()),
             R_long=R[T.side.values > 0].mean() if (T.side > 0).any() else np.nan,
             R_short=R[T.side.values < 0].mean() if (T.side < 0).any() else np.nan,
             cost=T.cost.mean(), swap=T.swap.mean(), first=str(pd.Timestamp(T.t_ent.min()).date()), last=str(pd.Timestamp(T.t_ent.max()).date()),
             by_year=" ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in yr.items()))
    d["rule4"] = bool(n >= 200 and d["t"] >= 2 and d["meanR"] >= 0.05 and d["half1"] > 0 and d["half2"] > 0 and d["worst_year"] >= -0.3)
    d["beats_both"] = bool(d["meanR"] > d["base_rand"] and d["meanR"] > d["base_long"])
    d["candidate"] = d["rule4"] and d["beats_both"]
    return d


# ------------------------------------------------------------------------------------------------------------ main
def build(cat, verbose=True):
    weeks = {}
    for sym in COMMODITIES + list(INDEX_SERIES):
        t0 = time.time(); W = market_weeks(sym, cat); weeks[sym] = W
        if verbose:
            print(f"  {sym:12s} prices {W.attrs['first'].date()}..{W.attrs['last'].date()}  report weeks {len(W)}  tradable(4w) "
                  f"{int(W.ok4.sum())}  skip {int(W.skip.sum())}  ({time.time() - t0:.0f}s)", flush=True)
    return weeks


def all_trades(weeks, seed=82):
    """Every cell x hold x market: non-overlapping trades with baselines. Returns a dict (sym, g, N, hi, H) -> DataFrame."""
    rng = np.random.default_rng(seed); out = {}
    for sym, W in weeks.items():
        for H in HOLDS:
            pools, longm = baselines(W, H)
            for g, N, hi, lo in cell_names(sym):
                T = trades_for(W, f"{g}_{N}_{hi}", H, rng, pools, longm)
                if T is not None: out[(sym, g, N, hi, H)] = T
    return out


def scopes_of(sym):
    if sym in INDEX_SERIES: return [("pooled", "us_index"), ("market", sym)]
    return [("pooled", "commodities15"), ("group", Q.MARKET_GROUP[sym]), ("market", sym)]


def cell_table(weeks, TR):
    rows = []
    keys = sorted({(g, N, hi, H) for (_, g, N, hi, H) in TR})
    for g, N, hi, H in keys:
        bucket = {}
        for sym in weeks:
            T = TR.get((sym, g, N, hi, H))
            if T is None: continue
            for sc in scopes_of(sym): bucket.setdefault(sc, []).append(T)
        for (st, sc), parts in bucket.items():
            T = pd.concat(parts, ignore_index=True)
            # 'every signal week' (overlapping) mean for the same scope
            ov = []
            for sym in weeks:
                if (st == "market" and sym != sc) or (st == "group" and Q.MARKET_GROUP.get(sym) != sc): continue
                if st == "pooled" and ((sc == "us_index") != (sym in INDEX_SERIES)): continue
                if f"{g}_{N}_{hi}" not in weeks[sym]: continue
                o = trades_for(weeks[sym], f"{g}_{N}_{hi}", H, None, None, None, overlap=True)
                if o is not None: ov.append(o)
            ovR = pd.concat(ov).R if ov else pd.Series(dtype=float)
            rows.append(dict(scope_type=st, scope=sc, group=g, N=N, thr=f"{hi}/{100 - hi}", hold=H,
                             primary=(g, N, hi) == PRIMARY[:3] or (sc in ("us_index", "US500.cash", "US100.cash") and (g, N, hi) == ("large", 157, 80)),
                             **stats(T), n_signal_weeks=len(ovR), overlap_meanR=ovR.mean() if len(ovR) else np.nan,
                             n_markets=T.sym.nunique()))
    return pd.DataFrame(rows)


def perm_test(weeks, n_perm, seed=8282):
    """Selection-aware permutation test over every pooled cell (commodities15 and us_index scopes): each market's weekly signal
    series is circularly shifted by its own random offset (>= 52 weeks from either end), the same offset for all of that market's
    cells; statistic = pooled t of R (non-overlapping trades). Returns (real Series, null array)."""
    rng = np.random.default_rng(seed)
    cells = sorted({(("us_index" if s in INDEX_SERIES else "commodities15"), g, N, hi, H)
                    for s in weeks for (g, N, hi, lo) in cell_names(s) for H in HOLDS})

    def pooled_t(shift):
        acc = {c: [] for c in cells}
        for sym, W in weeks.items():
            sc = "us_index" if sym in INDEX_SERIES else "commodities15"
            k = shift.get(sym, 0)
            for H in HOLDS:
                ok = W[f"ok{H}"].values; t_ent = W.t_ent.values.astype(np.int64); t_ex = W[f"t_ex{H}"].values.astype(np.int64)
                RL = W[f"RL{H}"].values; RS = W[f"RS{H}"].values
                for g, N, hi, lo in cell_names(sym):
                    side = np.roll(W[f"{g}_{N}_{hi}"].values.astype(np.int64), k)
                    idx = nonoverlap(side, ok, t_ent, t_ex)
                    if len(idx): acc[(sc, g, N, hi, H)].append(np.where(side[idx] > 0, RL[idx], RS[idx]))
        return np.array([tstat(np.concatenate(acc[c])) if acc[c] else np.nan for c in cells])

    real = pd.Series(pooled_t({}), index=pd.MultiIndex.from_tuples(cells, names=["scope", "group", "N", "hi", "hold"]))
    null = np.empty((n_perm, len(cells)))
    for p in range(n_perm):
        shift = {s: int(rng.integers(52, max(53, len(W) - 52))) for s, W in weeks.items()}
        null[p] = pooled_t(shift)
        if (p + 1) % 50 == 0: print(f"    perm {p + 1}/{n_perm}", flush=True)
    return real, null


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--perm", type=int, default=500); ap.add_argument("--force-perm", action="store_true")
    a = ap.parse_args()
    t0 = time.time(); cat = U.catalog()
    print("building weekly tables ...", flush=True)
    weeks = build(cat)
    TR = all_trades(weeks)
    pd.concat([T.assign(group=k[1], N=k[2], thr=f"{k[3]}/{100 - k[3]}", hold=k[4]) for k, T in TR.items()], ignore_index=True) \
        .to_csv(os.path.join(RES, "q82_cot_trades.csv.gz"), index=False, float_format="%.5g")
    cells = cell_table(weeks, TR)
    cells.to_csv(os.path.join(RES, "q82_cot_cells.csv"), index=False, float_format="%.5g")
    print(f"cells: {len(cells)} rows ({time.time() - t0:.0f}s)")
    # week tables (signals + outcomes) for later parts
    pd.concat([W.assign(sym=s) for s, W in weeks.items()], ignore_index=True).to_pickle("/tmp/claude-0/-home-claude-ywo-lab/"
                                                                                    "0f9104a2-35fd-5993-8aaf-c31d50623674/scratchpad/q82_weeks.pkl")
    show = ["scope", "group", "N", "thr", "hold", "n", "meanR", "t", "t_wk", "half1", "half2", "worst_year", "base_rand", "base_long",
            "edge", "t_edge", "rule4", "beats_both", "candidate"]
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    P = cells[(cells.scope == "commodities15") & (cells.group == "comm") & (cells.N == 157) & (cells.thr == "80/20")]
    print("\nPRIMARY (commodities15, comm, 157, 80/20):"); print(P[show].round(3).to_string(index=False))
    I = cells[(cells.scope_type == "pooled") & (cells.scope == "us_index") & (cells.N == 157) & (cells.thr == "80/20")]
    print("\nINDEX PRIMARY (large, 157, 80/20):"); print(I[show].round(3).to_string(index=False))
    passed = bool(P[P.hold == 4].candidate.iloc[0]) if len(P[P.hold == 4]) else False
    pooled = cells[cells.scope_type == "pooled"]
    print(f"\npooled cells: {len(pooled)}, rule4 {int(pooled.rule4.sum())}, candidate {int(pooled.candidate.sum())}, "
          f"positive {int((pooled.meanR > 0).sum())}")
    if passed or a.force_perm:
        print(f"\npermutation test ({a.perm} circular shifts) ...", flush=True)
        import robust
        real, null = perm_test(weeks, a.perm)
        res = robust.mcpt_select(real, null)
        res.to_csv(os.path.join(RES, "q82_cot_perm.csv"), float_format="%.5g")
        print(res.sort_values("real", ascending=False).head(10).round(3).to_string())
        Tp = pd.concat([TR[(s, "comm", 157, 80, 4)] for s in COMMODITIES if (s, "comm", 157, 80, 4) in TR])
        b = robust.bca_bounds(Tp.R.values, "mean", B=20000, rng=82)
        print(f"BCa primary mean {b['theta']:+.3f}, 95% lower bound (one-sided 2.5%) {b['low'][0.025]:+.3f}, 5% {b['low'][0.05]:+.3f}")
    else:
        print("\nprimary cell does not pass rule 4 + both baselines -> permutation test not run (pre-registered)")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
