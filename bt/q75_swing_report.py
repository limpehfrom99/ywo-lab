"""Log #75 'swing' ideas — aggregation: per-idea cell counts, share of cells positive, cells passing the CANDIDATE bar vs the
~2.5% expected by luck, pooled results by group x timeframe (with / without crypto; stocks with / without the second batch),
primary cells with BCa 95% lower bounds, #39 walk-forward exit choice, #37 group portfolios (daily mark-to-market R).
Reads results/q75_swing_*_{years,cells,trades}.csv; writes results/q75_swing_summary_*.csv and prints the report numbers.
"""
import sys, os
import numpy as np, pandas as pd

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
from robust import bca_bounds  # noqa: E402

R_ = C.RES
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
OUT = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); OUT.append(s)


def load(idea, kind):
    f = os.path.join(R_, f"q75_swing_{idea}_{kind}.csv")
    return pd.read_csv(f) if os.path.exists(f) else None


def cell_table(Y, by):
    """Per-cell stats (each cell = one symbol x tf x cell)."""
    return C.summarize(Y, by)


def luck_line(cells, label):
    c = cells.dropna(subset=["meanR"])
    n = len(c); pos = (c.meanR > 0).mean() if n else np.nan; passing = int(c.candidate.sum()) if n else 0
    p(f"  {label}: {n} cells, {pos:.0%} positive, median cell {c.meanR.median():+.3f}R, passing the bar {passing} "
      f"vs {0.025 * n:.1f} expected by luck" + (f" -> {', '.join(c[c.candidate].apply(lambda r: '|'.join(str(r[k]) for k in ('symbol', 'tf', 'cell') if k in r), axis=1))}" if passing else ""))
    return dict(label=label, cells=n, share_pos=pos, median=c.meanR.median(), passing=passing, by_luck=0.025 * n)


def pooled(Y, label, by=("group", "tf"), extra=None):
    rows = []
    for k, y in Y.groupby(list(by)):
        st = C.stats_from_years(y); st.pop("by_year", None)
        rows.append(dict(scope=label, **dict(zip(by, k if isinstance(k, tuple) else (k,))), **st))
    return pd.DataFrame(rows)


def show(df, cols):
    if df is None or not len(df): return
    d = df[[c for c in cols if c in df.columns]].copy()
    for c in d.columns:
        if d[c].dtype.kind == "f": d[c] = d[c].round(3)
    p(d.to_string(index=False))


COLS = ["scope", "group", "tf", "cell", "n", "meanR", "t", "win", "pre24", "from24", "years_pos", "worst_year", "base", "candidate"]


def bca_low(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 20: return np.nan
    return bca_bounds(x, "mean", B=20000, rng=1)["low"][0.025]


def main():
    luck, pools, prims = [], [], []
    # ------------------------------------------------------------------------------------------------- #32 pre-holiday
    Y = load("holiday", "years"); T = load("holiday", "trades")
    if Y is not None:
        p("\n=== #32 pre-holiday ===")
        ph = Y[Y.cell == "pre_holiday"]
        cells = cell_table(ph, ["symbol", "group", "tf", "cell"])
        luck.append(dict(idea="holiday", **luck_line(cells, "pre-holiday cells (symbols)")))
        for lab, sel in (("US indices", ph.group == "us_index"), ("stocks", ph.group == "stock"),
                         ("stocks ex 2nd batch", (ph.group == "stock") & ~ph.symbol.isin(C.SECOND_BATCH)),
                         ("other indices", ph.group == "index"), ("US500+US100", ph.symbol.isin(["US500.cash", "US100.cash"]))):
            st = C.stats_from_years(ph[sel]); st.pop("by_year", None)
            oth = Y[(Y.cell == "other_days") & Y.symbol.isin(ph[sel].symbol.unique())]
            om = oth.s.sum() / oth.n.sum() if oth.n.sum() else np.nan
            pools.append(dict(idea="holiday", scope=lab, tf="D1", cell="pre_holiday", **st, other_days_all=om))
            p(f"  pooled {lab:20s} " + C.fmt_stats(st) + f" | other days (all years) {om:+.3f}")
        # event-clustered t: mean R across symbols per event date, then t over dates
        if T is not None:
            for lab, sel in (("US indices", T.group == "us_index"), ("stocks", T.group == "stock"), ("other indices", T.group == "index")):
                ev = T[sel].groupby("day").R.mean()
                p(f"  event-clustered {lab:14s}: {len(ev)} event days, mean {ev.mean():+.3f}R, t {C.tstat(ev.values):+.2f}")
            for s in ("US500.cash", "US100.cash"):
                x = T[T.symbol == s]
                st = C.stats_from_years(ph[ph.symbol == s]); by = st.pop("by_year", "")
                prims.append(dict(idea="holiday", cell=f"{s} D1 pre-holiday", **st, by_year=by, bca_low=bca_low(x.R),
                                  other_days=Y[(Y.cell == "other_days") & (Y.symbol == s)].pipe(lambda o: o.s.sum() / o.n.sum()),
                                  m5_share=(x.src == "m5").mean()))
            x = T[T.symbol.isin(["US500.cash", "US100.cash"])]
            st = C.stats_from_years(ph[ph.symbol.isin(["US500.cash", "US100.cash"])]); by = st.pop("by_year", "")
            prims.append(dict(idea="holiday", cell="US500+US100 D1 pre-holiday", **st, by_year=by, bca_low=bca_low(x.R)))
        show(cells.sort_values("meanR", ascending=False).head(8), ["symbol", "group", "n", "meanR", "t", "pre24", "from24", "worst_year", "base", "candidate"])
    # ------------------------------------------------------------------------------------------------- #33 squeeze
    Y = load("squeeze", "years"); T = load("squeeze", "primary_trades")
    if Y is not None:
        p("\n=== #33 Bollinger squeeze ===")
        cells = cell_table(Y, ["symbol", "group", "tf", "cell"])
        luck.append(dict(idea="squeeze", **luck_line(cells, "all cells")))
        luck.append(dict(idea="squeeze", **luck_line(cells[cells.group != "crypto"], "cells ex crypto")))
        P = pooled(Y, "all"); P2 = pooled(Y[Y.group != "crypto"], "ex crypto", by=("tf",))
        P3 = pooled(Y[~Y.symbol.isin(C.SECOND_BATCH) & (Y.group == "stock")], "stocks ex 2nd batch", by=("tf",))
        P4 = pooled(Y[Y.group.isin(["us_index", "index"])], "all indices", by=("tf",))
        for d in (P, P2, P3, P4): pools.append(d.assign(idea="squeeze"))
        p("  pooled by group x tf:"); show(P, COLS)
        p("  pooled by tf, ex crypto:"); show(P2, COLS)
        p("  stocks ex 2nd batch:"); show(P3, COLS)
        p("  all indices (US + other):"); show(P4, COLS)
        for lab, sel, tsel in (("XAUUSD D1", (Y.symbol == "XAUUSD") & (Y.tf == "D1"), None), ("XAUUSD H4", (Y.symbol == "XAUUSD") & (Y.tf == "H4"), None),
                               ("indices D1 pooled", Y.group.isin(["us_index", "index"]) & (Y.tf == "D1"), None)):
            st = C.stats_from_years(Y[sel]); by = st.pop("by_year", "")
            if T is not None:
                if lab.startswith("XAUUSD"): x = T[(T.symbol == "XAUUSD") & (T.tf == lab[-2:])]
                else: x = T[(T.symbol != "XAUUSD") & (T.tf == "D1")]
                bl = bca_low(x.R)
            else: bl = np.nan
            prims.append(dict(idea="squeeze", cell=lab, **st, by_year=by, bca_low=bl))
    # ------------------------------------------------------------------------------------------------- #36 ratio
    Y = load("ratio", "years"); Cc = load("ratio", "cells"); T = load("ratio", "trades")
    if Y is not None:
        p("\n=== #36 ratio mean reversion ===")
        cells = cell_table(Y, ["symbol", "group", "tf", "cell"])
        cells = cells.merge(Cc[["pair", "tf", "beats_coin"]].rename(columns={"pair": "symbol"}), on=["symbol", "tf"], how="left")
        cells["candidate"] = cells.candidate & cells.beats_coin.fillna(False)
        luck.append(dict(idea="ratio", **luck_line(cells, "all pair cells")))
        P = pooled(Y, "all", by=("group", "tf")); pools.append(P.assign(idea="ratio"))
        if T is not None:
            co = T.groupby(["group", "tf"]).R_coin.mean().rename("coin").reset_index()
            P = P.merge(co, on=["group", "tf"], how="left")
            pc = T.groupby(["group", "tf"]).ret.mean().mul(100).rename("ret_pct").reset_index(); P = P.merge(pc, on=["group", "tf"], how="left")
        show(P, COLS + ["coin", "ret_pct"])
        show(Cc.sort_values("meanR", ascending=False), ["pair", "tf", "n", "meanR", "t", "pre24", "from24", "worst_year", "coin", "rand",
                                                         "ret_pct", "cost_pct", "pct_per_year_mean", "candidate"])
        sel = (Y.symbol == "XAUUSD/XAGUSD") & (Y.tf == "D1")
        st = C.stats_from_years(Y[sel]); by = st.pop("by_year", "")
        x = T[(T.pair == "XAUUSD/XAGUSD") & (T.tf == "D1")] if T is not None else None
        r = Cc[(Cc.pair == "XAUUSD/XAGUSD") & (Cc.tf == "D1")]
        prims.append(dict(idea="ratio", cell="XAU/XAG D1", **st, by_year=by, bca_low=bca_low(x.R) if x is not None else np.nan,
                          coin=float(r.coin.iloc[0]) if len(r) else np.nan, ret_pct=float(r.ret_pct.iloc[0]) if len(r) else np.nan,
                          pct_by_year=r.pct_by_year.iloc[0] if len(r) else ""))
    # ------------------------------------------------------------------------------------------------- #37 Clenow
    Y = load("clenow", "years"); T = load("clenow", "d1_trades")
    if Y is not None:
        p("\n=== #37 Clenow trend ===")
        cells = cell_table(Y, ["symbol", "group", "tf", "cell"])
        luck.append(dict(idea="clenow", **luck_line(cells, "all symbol cells")))
        luck.append(dict(idea="clenow", **luck_line(cells[cells.group != "crypto"], "cells ex crypto")))
        P = pooled(Y, "all"); P2 = pooled(Y[Y.group != "crypto"], "ex crypto", by=("tf",)); P3 = pooled(Y, "all incl crypto", by=("tf",))
        P4 = pooled(Y[~Y.symbol.isin(C.SECOND_BATCH) & (Y.group == "stock")], "stocks ex 2nd batch", by=("tf",))
        for d in (P, P2, P3, P4): pools.append(d.assign(idea="clenow"))
        p("  pooled per trade by group x tf:"); show(P, COLS)
        p("  pooled by tf:"); show(pd.concat([P3, P2, P4]), COLS)
        luck.append(dict(idea="clenow", **luck_line(P[P.tf == "D1"].rename(columns={"group": "symbol"}).assign(cell="group_D1"),
                                                     "D1 group cells (primary)")))
        D = load("clenow", "portfolio_daily")
        if D is not None:
            D = D.set_index(D.columns[0]); D.index = pd.to_datetime(D.index)
            D = D.reindex(pd.bdate_range(D.index.min(), D.index.max())).fillna(0.0)
            D["all"] = D.drop(columns=[c for c in D.columns if c == "all"]).sum(axis=1)
            D["all_ex_crypto"] = D[[c for c in D.columns if c not in ("all", "crypto")]].sum(axis=1)
            rows = []
            for g in D.columns:
                s = D[g]; s = s.loc[s.ne(0).idxmax():]
                yr = s.groupby(s.index.year).sum(); eq = s.cumsum(); dd = (eq.cummax() - eq).max()
                rows.append(dict(group=g, days=len(s), start=str(s.index[0].date()), R_per_year=s.sum() / (len(s) / 261),
                                 daily_t=C.tstat(s.values), sharpe=s.mean() / s.std() * np.sqrt(261) if s.std() > 0 else np.nan,
                                 pre24=s[s.index < "2024-01-01"].sum() / max((s.index < "2024-01-01").sum() / 261, 1e-9),
                                 from24=s[s.index >= "2024-01-01"].sum() / max((s.index >= "2024-01-01").sum() / 261, 1e-9),
                                 worst_year=yr.min(), worst_yr=int(yr.idxmin()), max_dd_R=dd,
                                 by_year=" ".join(f"{y % 100:02d}:{v:+.1f}" for y, v in yr.items())))
            PF = pd.DataFrame(rows); PF.to_csv(os.path.join(R_, "q75_swing_summary_clenow_portfolio.csv"), index=False, float_format="%.4g")
            p("  D1 group portfolios (daily mark-to-market, 1R = 3 ATR per position, R per year):")
            show(PF, ["group", "start", "R_per_year", "daily_t", "sharpe", "pre24", "from24", "worst_year", "worst_yr", "max_dd_R", "by_year"])
        for g, y in Y[Y.tf == "D1"].groupby("group"):
            st = C.stats_from_years(y); by = st.pop("by_year", "")
            x = T[T.group == g] if T is not None else None
            prims.append(dict(idea="clenow", cell=f"{g} D1 portfolio (per trade)", **st, by_year=by,
                              bca_low=bca_low(x.R) if x is not None else np.nan))
    # ------------------------------------------------------------------------------------------------- #39 exit grid
    Y = load("exitgrid", "years")
    if Y is not None:
        p("\n=== #39 trend exit grid ===")
        cells = cell_table(Y, ["symbol", "group", "tf", "cell"])
        luck.append(dict(idea="exitgrid", **luck_line(cells, "all symbol cells")))
        luck.append(dict(idea="exitgrid", **luck_line(cells[cells.group != "crypto"], "cells ex crypto")))
        P = pooled(Y, "group", by=("group", "tf", "cell"))
        pools.append(P.assign(idea="exitgrid"))
        luck.append(dict(idea="exitgrid", **luck_line(P[P.tf == "D1"].rename(columns={"group": "symbol"}), "D1 group-pooled cells (primary)")))
        luck.append(dict(idea="exitgrid", **luck_line(P[P.tf == "H4"].rename(columns={"group": "symbol"}), "H4 group-pooled cells")))
        Pc = pooled(Y[Y.group != "crypto"], "ex crypto", by=("tf", "cell")); pools.append(Pc.assign(idea="exitgrid"))
        p("  pooled over all groups ex crypto, per exit cell:"); show(Pc, ["scope", "tf", "cell", "n", "meanR", "t", "pre24", "from24", "worst_year", "base", "candidate"])
        p("  D1 by group (best 12 group-cells by t):"); show(P[P.tf == "D1"].sort_values("t", ascending=False).head(12), COLS)
        # walk-forward choice of exit, per group x tf x N
        wf_rows, wf_cmp = [], []
        for (g, tf), y in Y.groupby(["group", "tf"]):
            for N in ("N20", "N55"):
                yy = y[y.cell.str.startswith(N)]
                agg = yy.groupby(["cell", "year"])[["n", "s", "ss"]].sum().reset_index()
                years = sorted(agg.year.unique())
                fwd = []
                for Yr in years:
                    past = agg[(agg.year >= Yr - 3) & (agg.year < Yr)].groupby("cell")[["n", "s"]].sum()
                    past = past[past.n >= 30]
                    if not len(past) or len({*range(Yr - 3, Yr)} & set(years)) < 3: continue
                    best = (past.s / past.n).idxmax()
                    cur = agg[(agg.cell == best) & (agg.year == Yr)]
                    if len(cur): fwd.append(dict(group=g, tf=tf, N=N, year=Yr, pick=best, n=int(cur.n.sum()), s=cur.s.sum(), ss=cur.ss.sum()))
                if not fwd: continue
                F = pd.DataFrame(fwd); wf_rows.append(F)
                test_years = set(F.year)
                n, s, ss = F.n.sum(), F.s.sum(), F.ss.sum(); m = s / n; v = (ss - n * m * m) / (n - 1)
                row = dict(group=g, tf=tf, N=N, test_years=f"{min(test_years)}-{max(test_years)}", wf_n=int(n), wf_meanR=m, wf_t=m / np.sqrt(v / n))
                for cell, z in agg[agg.year.isin(test_years)].groupby("cell"):
                    row[cell.split("_", 1)[1]] = z.s.sum() / z.n.sum()
                wf_cmp.append(row)
        if wf_cmp:
            W = pd.DataFrame(wf_cmp)
            ex = [c for c in W.columns if c in ("chand2", "chand3", "chand4", "chan10", "sma50", "time20", "time60")]
            W["best_fixed"] = W[ex].max(axis=1); W["mean_fixed"] = W[ex].mean(axis=1)
            W.to_csv(os.path.join(R_, "q75_swing_summary_exitgrid_wf.csv"), index=False, float_format="%.4g")
            pd.concat(wf_rows).to_csv(os.path.join(R_, "q75_swing_summary_exitgrid_wf_picks.csv"), index=False, float_format="%.4g")
            p("  walk-forward exit choice (best mean R over the 3 previous years, per group x tf x entry) vs every fixed exit, same test years:")
            show(W, ["group", "tf", "N", "test_years", "wf_n", "wf_meanR", "wf_t"] + ex + ["best_fixed", "mean_fixed"])
            for tf in ("D1", "H4"):
                F = pd.concat(wf_rows); F = F[F.tf == tf]
                for lab, f in (("all groups", F), ("ex crypto", F[F.group != "crypto"])):
                    n, s, ss = F.n.sum(), f.s.sum(), f.ss.sum(); n = f.n.sum(); m = s / n; v = (ss - n * m * m) / (n - 1)
                    p(f"  WF pooled {tf} {lab}: n={n} mean {m:+.3f}R t {m / np.sqrt(v / n):+.2f}")
        for (g, cell), y in Y[Y.tf == "D1"].groupby(["group", "cell"]):
            st = C.stats_from_years(y); by = st.pop("by_year", "")
            prims.append(dict(idea="exitgrid", cell=f"{g} D1 {cell}", **st, by_year=by))
    # ------------------------------------------------------------------------------------------------- outputs
    L = pd.DataFrame(luck); L.to_csv(os.path.join(R_, "q75_swing_summary_luck.csv"), index=False, float_format="%.4g")
    pd.concat([x if isinstance(x, pd.DataFrame) else pd.DataFrame([x]) for x in pools], ignore_index=True).to_csv(os.path.join(R_, "q75_swing_summary_pooled.csv"), index=False, float_format="%.4g")
    PR = pd.DataFrame(prims); PR.to_csv(os.path.join(R_, "q75_swing_summary_primary.csv"), index=False, float_format="%.4g")
    p("\n=== primary cells ===")
    show(PR, ["idea", "cell", "n", "meanR", "t", "win", "pre24", "from24", "years_pos", "worst_year", "base", "bca_low", "candidate"])
    p("\n=== luck lines ===")
    show(L, ["idea", "label", "cells", "share_pos", "median", "passing", "by_luck"])


if __name__ == "__main__":
    main()
