"""Log #75 / #39 follow-up on the one exit-grid cell that passed the permutation test (crypto D1, close above the 55-bar high,
2-ATR chandelier exit). PROTOCOL: a daily result counts only if it survives other candle start times, and a pooled t over
correlated coins overstates the evidence.
1. Phase check: daily bars rebuilt from the 5-minute crypto files (2018+, the only intraday history) with the day starting at the
   server midnight (17:00 New York, = the export's D1) and 1, 2, 3, 6, 12 hours later; the same rule, costs and R on each; plus
   the export D1 restricted to 2018+ for reference.
2. Portfolio view of the real trades (results/q75_swing_exitgrid_perm_trades.csv): R summed per entry month (months without a
   trade = 0), t of the monthly sums; and the same for N20_chand2.
Output: results/q75_swing_phase.csv
"""
import sys, os
import numpy as np, pandas as pd

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
import q75_swing_trend as TR  # noqa: E402
U = C.U
CRYPTO = ["ADAUSD", "BTCUSD", "DOGEUSD", "ETHUSD", "LTCUSD", "SOLUSD", "XRPUSD"]


def daily_from_intraday(intra, offset_h):
    srv = C.to_server(intra.index) - pd.Timedelta(hours=offset_h)
    x = intra.copy(); x.index = srv
    g = x.resample("1D", label="left", closed="left")
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "sp": g.sp.median()}).dropna()
    u = C.from_server(d.index + pd.Timedelta(hours=offset_h)); d = d[~u.isna()]; d.index = u[~u.isna()]
    return d


def run_cell(d, sym, sw, comm, N=55, kind=0, k=2.0, tm=0):
    out = []
    for sa, sb in C.segments(C.ns(d.index)):
        if sb - sa < 200: continue
        xs = d.iloc[sa:sb]; I = TR.indicators(xs); t = C.ns(xs.index); sp = xs.sp.values.astype(float)
        S_i, E_i, X_i, D, EP, XP, AT, HW = TR.run_rule(I["o"], I["h"], I["l"], I["c"], I[f"sig{N}"], I["atr"], I["ll10"], I["hh10"],
                                                       I["sma50"], 60, kind, k, tm)
        if len(E_i): out.append(pd.DataFrame(dict(t=t[E_i], R=TR.costs_R(I, sp, t, sw, comm, E_i, X_i, HW, D, EP, XP, 2.0 * AT))))
    return pd.concat(out) if out else pd.DataFrame(columns=["t", "R"])


def main():
    cat = U.catalog(); rows = []
    res = {}
    for sym in CRYPTO:
        intra, btf, rel = C.load_intraday(sym, cat)
        d1 = C.load_d1(sym, cat, intra, rel)
        sw = C.Swaps(sym, C.ns(d1.index)[0], C.ns(d1.index)[-1], d1.close.iloc[-1]); comm = U.commission_of(sym)
        start = intra.index[0] + pd.Timedelta(days=1)
        for lab, d in [("export D1 (2018+)", d1.loc[start:])] + [(f"from M5, day start +{h}h", daily_from_intraday(intra, h)) for h in (0, 1, 2, 3, 6, 12)]:
            for N in (55, 20):
                T = run_cell(d, sym, sw, comm, N=N)
                T = T[T.t >= C.ns(pd.DatetimeIndex([start]))[0]]
                res.setdefault((lab, N), []).append(T.assign(symbol=sym))
        print(sym, "done", flush=True)
    for (lab, N), parts in res.items():
        T = pd.concat(parts)
        yr = T.groupby(pd.DatetimeIndex(T.t.values).year).R.mean()
        rows.append(dict(check="phase", variant=lab, cell=f"N{N}_chand2", n=len(T), meanR=T.R.mean(), t=C.tstat(T.R.values),
                         pre24=T.R[T.t < C.SPLIT_NS].mean(), from24=T.R[T.t >= C.SPLIT_NS].mean(),
                         by_year=" ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in yr.items())))
    K = pd.read_csv(os.path.join(C.RES, "q75_swing_exitgrid_perm_trades.csv"))
    for cell, x in K.groupby("cell"):
        m = pd.Series(x.R.values, index=pd.DatetimeIndex(x.t.values)).resample("MS").sum()
        rows.append(dict(check="monthly sums (all coins)", variant="export D1 2011+", cell=cell, n=len(x), meanR=x.R.mean(),
                         t=C.tstat(m.values), months=len(m), pre24=x.R[x.t < C.SPLIT_NS].mean(), from24=x.R[x.t >= C.SPLIT_NS].mean()))
        y = x[x.t >= C.ns(pd.DatetimeIndex(["2018-01-01"]))[0]]
        m = pd.Series(y.R.values, index=pd.DatetimeIndex(y.t.values)).resample("MS").sum()
        rows.append(dict(check="monthly sums (all coins)", variant="export D1 2018+", cell=cell, n=len(y), meanR=y.R.mean(),
                         t=C.tstat(m.values), months=len(m)))
    out = pd.DataFrame(rows); out.to_csv(os.path.join(C.RES, "q75_swing_phase.csv"), index=False, float_format="%.4g")
    pd.set_option("display.width", 250)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
