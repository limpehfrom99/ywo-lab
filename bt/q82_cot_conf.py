"""Log #82 part 3: Bernd's confluence on the 15 commodity CFDs, and COT as a filter on #66's daily VAL/SEAS trades.
  Confluence: at each COT report week's entry bar (part 1 timing), trade when the COT primary (commercials, 157 reports, 80/20),
  the Valuation tool against all three references (DXY, BOND, GOLD; gold itself DXY + BOND; ROC reading, as known at the start
  of the entry day) and True Seasonality (seas30: mean 30-day log return from the same date over the 15 previous years, >= 12
  years of data) all point the same way. Valuation agrees 'strict' = every reference beyond -0.75 / +0.75; 'cheap' = every
  reference on the right side of 0. Hold 4 weeks, non-overlapping, part 1's costs, R unit and baselines. COT+VAL and COT+SEAS
  pairs are shown as descriptive rows.
  COT filter: every trade of #66 (results/bernd_daily_trades.csv) and of part 2 (results/q82_val_trades.csv) on a market with
  COT data is labelled by the COT bias known at its entry (latest report released before the entry bar opened, delayed reports
  excluded): agree / against / neutral. Commodities use commercials 157 80/20, US500/US100 the calendar's large speculators 157
  80/20 (contrarian).
python3 -I bt/q82_cot_conf.py"""
import os, sys, time
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
import numpy as np
import pandas as pd
import universe as U            # noqa: E402
import bernd_bias as BB         # noqa: E402
import q75_swing_common as C    # noqa: E402
import q82_cot as K             # noqa: E402
import q82_cot_val as V         # noqa: E402

RES = "/home/claude/ywo-lab/results"
DAY = K.DAY


def entry_server_dates(W):
    t = pd.DatetimeIndex(np.where(W.t_ent.values > 0, W.t_ent.values, 0).astype("datetime64[ns]"))
    return C.to_server(t).normalize()


def seasonal_fixed(close, years=15, N=30, min_years=12):
    """bernd_bias.seasonal with one fix: a past year counts only if the series has a bar within 7 days on/after the same calendar
    date. (bernd_bias.seasonal maps every date before the first bar to bar 0, so a short history reuses its first N-day return
    for each missing year and passes the 12-of-15-years test from its second year on.)"""
    c = np.log(close.values); dates = close.index.values; n = len(c); out = np.full(n, np.nan)
    first = close.index[0]
    for t in range(n):
        ts = close.index[t]; vals = []
        for k in range(1, years + 1):
            try: past = ts.replace(year=ts.year - k)
            except ValueError: past = ts.replace(year=ts.year - k, day=28)
            if past < first: continue
            i = np.searchsorted(dates, np.datetime64(past))
            if i >= n or (close.index[i] - past).days > 7: continue
            if i + N < t: vals.append(c[i + N] - c[i])
        if len(vals) >= min_years: out[t] = np.mean(vals)
    return pd.Series(out, index=close.index, name=f"seas{N}")


def bias_inputs(sym, W):
    """Valuation (ROC) vs DXY/BOND/GOLD and seas30 at each week's entry day (values known at the start of that day)."""
    T = V.val_table(sym)
    d = BB.d1(sym)
    T["seas30"] = seasonal_fixed(d.close, 15, 30).shift(1).reindex(T.index)
    srv = entry_server_dates(W)
    X = T.reindex(srv)
    X.index = W.index
    return X


def conf_side(W, X, mode, use_val=True, use_seas=True):
    s = W["comm_157_80"].values.copy()
    refs = [c for c in ("val_dxy", "val_bond", "val_gold") if c in X]
    V_ = X[refs].values
    if use_val:
        fin = np.isfinite(V_).all(axis=1)
        if mode == "strict":
            okL = fin & (V_ <= -V.THR).all(axis=1); okS = fin & (V_ >= V.THR).all(axis=1)
        else:
            okL = fin & (V_ < 0).all(axis=1); okS = fin & (V_ > 0).all(axis=1)
        s = np.where((s > 0) & ~okL, 0, s); s = np.where((s < 0) & ~okS, 0, s)
    if use_seas:
        se = X["seas30"].values; fs = np.isfinite(se)
        s = np.where((s > 0) & ~(fs & (se > 0)), 0, s); s = np.where((s < 0) & ~(fs & (se < 0)), 0, s)
    return s


def cot_bias_at(W, col, t_utc_ns):
    """Side of the latest non-skipped report released before each time (0 if none)."""
    w = W[~W.skip.values]
    rel = pd.DatetimeIndex(w.release.values).values.astype("datetime64[ns]").view("i8")
    o = np.argsort(rel); rel = rel[o]; side = w[col].values[o]
    k = np.searchsorted(rel, t_utc_ns, side="left") - 1
    return np.where(k >= 0, side[np.maximum(k, 0)], 0)


def filter_table(trades, weeks, label):
    rows = []
    trades = trades.copy()
    trades["bias"] = np.nan
    for sym, g in trades.groupby("symbol"):
        if sym not in weeks: continue
        W = weeks[sym]; col = "large_157_80" if sym in K.INDEX_SERIES else "comm_157_80"
        t_srv = pd.DatetimeIndex(pd.to_datetime(g.day.values))
        t_utc = C.from_server(t_srv).values.astype("datetime64[ns]").view("i8")
        trades.loc[g.index, "bias"] = cot_bias_at(W, col, t_utc)
    T = trades[trades.bias.notna()].copy()
    T["agree"] = np.where(T.bias == T.side, "agree", np.where(T.bias == -T.side, "against", "neutral"))
    first = {s_: BB.d1(s_).index[0] for s_ in T.symbol.unique()}
    T["seas_valid"] = [pd.Timestamp(dd) - pd.DateOffset(years=12) >= first[s_] for s_, dd in zip(T.symbol, T.day)]
    T["family"] = np.where(T.rule.str.startswith("SEAS"), np.where(T.seas_valid, "SEAS (valid seasonal)", "SEAS (bernd_bias bug)"), T.rule)
    for fam, x in list(T.groupby("family")) + [("ALL rules", T)]:
        base = dict(source=label, family=fam, n_all=len(x), R_all=x.R.mean(), edge_all=x.edge.mean())
        for a in ("agree", "against", "neutral"):
            y = x[x.agree == a]
            base.update({f"n_{a}": len(y), f"R_{a}": y.R.mean() if len(y) else np.nan, f"edge_{a}": y.edge.mean() if len(y) else np.nan,
                         f"t_edge_{a}": K.tstat(y.edge.dropna()) if len(y) > 2 else np.nan})
        y = x[x.agree == "agree"]; z = x[x.agree != "agree"]
        base["diff_R_agree_vs_rest"] = (y.R.mean() - z.R.mean()) if len(y) and len(z) else np.nan
        if len(y) > 2 and len(z) > 2:
            base["t_diff"] = (y.R.mean() - z.R.mean()) / np.sqrt(y.R.var(ddof=1) / len(y) + z.R.var(ddof=1) / len(z))
        rows.append(base)
    return pd.DataFrame(rows), T


def main():
    t0 = time.time(); cat = U.catalog()
    print("building weekly tables ...", flush=True)
    weeks = K.build(cat, verbose=False)
    # ---------------------------------------------------------------- confluence
    rng = np.random.default_rng(8203); rows = []; trades = []
    variants = [("CONF_strict", "strict", True, True), ("CONF_cheap", "cheap", True, True),
                ("COT+VAL_strict", "strict", True, False), ("COT+VAL_cheap", "cheap", True, False), ("COT+SEAS", "cheap", False, True),
                ("COT_only", "cheap", False, False)]
    per = {}
    for sym in K.COMMODITIES:
        W = weeks[sym]; X = bias_inputs(sym, W)
        cov = dict(sym=sym, weeks_cot_signal=int(((W.comm_157_80 != 0) & W.ok4).sum()),
                   weeks_val=int(X[[c for c in ("val_dxy", "val_bond", "val_gold") if c in X]].notna().all(axis=1).sum()),
                   weeks_seas=int(X.seas30.notna().sum()))
        print(f"  {sym:12s} COT-signal weeks {cov['weeks_cot_signal']}, valuation known {cov['weeks_val']}, seasonality known {cov['weeks_seas']}", flush=True)
        pools, longm = K.baselines(W, 4)
        for name, mode, uv, us in variants:
            W2 = W.copy(); W2["sig"] = conf_side(W, X, mode, uv, us)
            T = K.trades_for(W2, "sig", 4, rng, pools, longm)
            if T is not None:
                T["variant"] = name; trades.append(T); per.setdefault(name, []).append(T)
        rows.append(cov)
    cov = pd.DataFrame(rows)
    cells = []
    for name, parts in per.items():
        T = pd.concat(parts, ignore_index=True)
        cells.append(dict(variant=name, scope="commodities15", **K.stats(T), markets=",".join(sorted(T.sym.unique()))))
        for sym, x in T.groupby("sym"): cells.append(dict(variant=name, scope=sym, **K.stats(x)))
    cells = pd.DataFrame(cells)
    cells.to_csv(os.path.join(RES, "q82_conf_cells.csv"), index=False, float_format="%.5g")
    pd.concat(trades, ignore_index=True).to_csv(os.path.join(RES, "q82_conf_trades.csv"), index=False, float_format="%.5g")
    cov.to_csv(os.path.join(RES, "q82_conf_coverage.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    show = ["variant", "scope", "n", "meanR", "t", "half1", "half2", "worst_year", "base_rand", "base_long", "edge", "t_edge", "rule4", "candidate"]
    print(cells[cells.scope == "commodities15"][show].round(3).to_string(index=False))
    print(cells[(cells.scope != "commodities15") & cells.variant.str.startswith("CONF")][show].round(3).to_string(index=False))
    # ---------------------------------------------------------------- COT filter on #66 / part-2 trades
    out = []
    t66 = pd.read_csv(os.path.join(RES, "bernd_daily_trades.csv"))
    t66 = t66.rename(columns={})
    f66, T66 = filter_table(t66[t66.symbol.isin(weeks)], weeks, "#66")
    out.append(f66)
    p2 = os.path.join(RES, "q82_val_trades.csv")
    if os.path.exists(p2):
        tv = pd.read_csv(p2)
        tv = tv[tv.symbol.isin(weeks) & ~tv.in66.astype(bool)]
        if len(tv):
            fv, _ = filter_table(tv, weeks, "#82 part 2 (new VAL rules)")
            out.append(fv)
    F = pd.concat(out, ignore_index=True)
    F.to_csv(os.path.join(RES, "q82_cotfilter.csv"), index=False, float_format="%.5g")
    T66.to_csv(os.path.join(RES, "q82_cotfilter_trades66.csv"), index=False, float_format="%.5g")
    print("\nCOT filter:")
    print(F[["source", "family", "n_all", "R_all", "edge_all", "n_agree", "R_agree", "edge_agree", "t_edge_agree", "n_against", "R_against",
             "edge_against", "n_neutral", "R_neutral", "diff_R_agree_vs_rest", "t_diff"]].round(3).to_string(index=False))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
