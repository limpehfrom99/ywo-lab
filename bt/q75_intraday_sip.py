"""Log #75 / backlog #35: "Stocks in play" (Zarattini & Aziz 2023, "A Profitable Day Trading Strategy for the U.S. Equity
Market"), as pre-registered, on FTMO's US stock CFDs (group "stock", us_cash session, M5).

Rule (fixed): each day, relative volume (RV) = tick volume of the session's first 5-minute bar / its average over the previous 14
sessions (the 14 must lie within 31 calendar days, else no RV that day); rank the stocks with an RV that day and take the top 20%
(round(0.2 x count), at least 1). Trade each selected stock in the direction of its first 5-minute candle (skip if close == open)
at the NEXT bar's open; stop = 10% of the 14-day ATR (quant/sessions: cash-session true range, previous days only) from the entry;
exit at the session close (16:00 New York). FTMO stock CFDs open 9:35 since 2024, so the first bar is whatever the session's first
bar is (9:30-9:35 before, 9:35-9:40 after). Costs: spread x 1.2 at entry + 0.002% per side (quant/intraday.simulate fills: the stop
is checked from the entry bar on; a stop that gaps fills at the bar's open).
Baselines: the same trade on ALL stocks with an RV that day, and on a random 20% (same count per day, 1,000 draws -> p_random).
Universes: all 30 stock CFDs, and without the second batch (AMD AVGO BA CVX DIS INTC JNJ JPM KO MSTR NKE PLTR QCOM XOM).
Exit-resolution check: TSLA and NVDA on M1 bars (same days, direction, ATR; entry at the M1 open of the next 5-minute window).
python3 bt/q75_intraday_sip.py -> results/q75_intraday_sip_rows.csv (one row per stock-day), results/q75_intraday_sip.csv
"""
import os, sys, time, warnings
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "quant")); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
import universe as U  # noqa: E402
import intraday as ID  # noqa: E402
from sessions import Session  # noqa: E402
from q75_intraday import BATCH2, tstat, CUT  # noqa: E402

RES = os.path.join(ROOT, "results")
ROWS = os.path.join(RES, "q75_intraday_sip_rows.csv")
OUT = os.path.join(RES, "q75_intraday_sip.csv")
N_DRAWS = 1000


def stock_rows(sym, cat):
    d = U.load(sym, "M5", cat)
    if d is None or len(d) < 2000: return None, None
    d = d[~d.index.duplicated()].sort_index()
    if "tickvol" not in d: return None, None
    S = Session(d, "us_cash")
    n = len(S.days)
    if n < 30: return None, None
    i = np.arange(n); f = S.first.astype(int)
    fv = S.V[i, f]
    avg = pd.Series(fv).rolling(14).mean().shift(1).values
    span = np.full(n, np.nan); span[14:] = (S.days[14:] - S.days[:-14]).days
    avg = np.where((span <= 31) & (avg > 0), avg, np.nan)
    rv = fv / avg
    d1 = np.sign(S.C[i, f] - S.O[i, f]).astype(int)
    ok = (f + 1 < S.K) & np.isfinite(S.atr) & (S.atr > 0)
    e_col = np.where(ok, f + 1, -1); e_px = S.O[i, np.minimum(f + 1, S.K - 1)]
    stop = e_px - d1 * 0.1 * S.atr
    comm = U.commission_of(sym)
    R, why, rf = ID.simulate(S, e_col, e_px, d1, stop, None, None, comm, 1.2, False)
    st_o = e_px + d1 * 0.1 * S.atr
    Ro = ID.simulate(S, e_col, e_px, -d1, st_o, None, None, comm, 1.2, False)[0]
    rows = pd.DataFrame(dict(day=S.days, sym=sym, batch2=sym in BATCH2, first_bar=[S.t[x] for x in f], fv=fv, rv=rv, d=d1,
                             R=R, R_opp=Ro, why=why, atr=S.atr, e_px=e_px, risk_frac=rf, cost_R=S.SP[i, np.minimum(f + 1, S.K - 1)] * 1.2 / (0.1 * S.atr)))
    return rows, S


def m1_rows(sym, cat, S5, rows5):
    """Same trades on 1-minute bars (TSLA, NVDA): direction and ATR from the M5 rows; entry at the M1 open of the next 5-minute window."""
    d = U.load(sym, "M1", cat)
    if d is None: return None
    d = d[~d.index.duplicated()].sort_index()
    S1 = Session(d, "us_cash", bar=1)
    m = pd.Series(np.arange(len(S1.days)), index=S1.days)
    r5 = rows5.set_index("day")
    common = r5.index.intersection(S1.days)
    i1 = m.loc[common].values
    j5 = np.array([S5.t.index(t) for t in r5.loc[common, "first_bar"]])        # first 5-minute column
    e_col = 5 * (j5 + 1)
    dd = r5.loc[common, "d"].values.astype(int); atr = r5.loc[common, "atr"].values
    ok = (e_col < S1.K) & np.isfinite(atr)
    O = S1.O[i1]; e_px = O[np.arange(len(i1)), np.minimum(e_col, S1.K - 1)]
    stop = e_px - dd * 0.1 * atr

    class Sub: pass
    X = Sub(); X.O, X.H, X.L, X.C, X.SP = S1.O[i1], S1.H[i1], S1.L[i1], S1.C[i1], S1.SP[i1]
    R1 = ID.simulate(X, np.where(ok, e_col, -1), e_px, dd, stop, None, None, U.commission_of(sym), 1.2, False)[0]
    return pd.DataFrame(dict(day=common, sym=sym, R_m1=R1)).set_index(["day", "sym"])


def stats(R, day, label):
    R = np.asarray(R, float); day = pd.DatetimeIndex(day)
    m = np.isfinite(R); R = R[m]; day = day[m]
    if len(R) == 0: return dict(set=label, n=0)
    is_ = day < CUT
    yr = pd.DataFrame(dict(R=R, y=day.year)).groupby("y").R.agg(["mean", "size"])
    y10 = yr[yr["size"] >= 10]
    return dict(set=label, n=len(R), mean=R.mean(), t=tstat(R), win=(R > 0).mean(), n_is=int(is_.sum()),
                mean_is=R[is_].mean() if is_.any() else np.nan, n_oos=int((~is_).sum()), mean_oos=R[~is_].mean() if (~is_).any() else np.nan,
                worst_year=int(y10["mean"].idxmin()) if len(y10) else np.nan, worst_mean=y10["mean"].min() if len(y10) else np.nan,
                by_year=" ".join(f"{y % 100:02d}:{v:+.3f}({c})" for y, (v, c) in yr.iterrows()))


def select(A, rng=None):
    """A: rows with a finite RV. Returns a boolean mask of the selected rows (top 20% by RV per day, or random if rng)."""
    key = rng.random(len(A)) if rng is not None else A.rv.values
    day = A.day.values.astype("datetime64[ns]").view("i8")
    order = np.lexsort((-key, day))                         # by day, then key descending
    ds = day[order]
    start = np.r_[0, np.flatnonzero(ds[1:] != ds[:-1]) + 1]
    cnt = np.diff(np.r_[start, len(ds)])
    rank = np.arange(len(ds)) - np.repeat(start, cnt)
    nsel = np.maximum(1, np.floor(0.2 * cnt + 0.5)).astype(int)
    sel = np.zeros(len(A), bool); sel[order] = rank < np.repeat(nsel, cnt)
    return sel


def main():
    t0 = time.time(); cat = U.catalog()
    stocks = sorted(s for s, tf in cat if tf == "M5" and U.group_of(s) == "stock")
    parts, m1 = [], []
    for s in stocks:
        rows, S = stock_rows(s, cat)
        if rows is None: print(f"{s}: no data", flush=True); continue
        v = rows[np.isfinite(rows.rv)]
        print(f"{s}{'*' if s in BATCH2 else ''}: {len(rows)} days {rows.day.min().date()}..{rows.day.max().date()}, RV days {len(v)}, "
              f"all-days mean R {rows.R.mean():+.3f} (n {rows.R.notna().sum()}), cost {rows.cost_R.median():.3f}R, "
              f"first-bar vol median {np.median(rows.fv):.0f} ({time.time() - t0:.0f}s)", flush=True)
        parts.append(rows)
        if (s, "M1") in cat:
            x = m1_rows(s, cat, S, rows)
            if x is not None: m1.append(x)
    A = pd.concat(parts, ignore_index=True)
    if m1:
        M1 = pd.concat(m1); A = A.join(M1, on=["day", "sym"])
    A.to_csv(ROWS, index=False, float_format="%.6g")
    out = []
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    for uni, X in (("all 30 stocks", A), ("without batch 2", A[~A.batch2])):
        E = X[np.isfinite(X.rv)].reset_index(drop=True)
        tradable = (E.d != 0) & np.isfinite(E.R)
        top = select(E)
        T = E[top & tradable]
        rng = np.random.default_rng(35)
        draws = []
        for _ in range(N_DRAWS):
            s = select(E, rng) & tradable
            draws.append(E.R.values[s].mean())
        draws = np.array(draws)
        p_rand = (1 + np.sum(draws >= T.R.mean())) / (1 + N_DRAWS)
        rows = [stats(T.R, T.day, "TOP 20% by RV"), stats(E.R[tradable], E.day[tradable], "ALL stocks"),
                stats(T.R_opp, T.day, "TOP 20%, opposite direction")]
        r = dict(set="RANDOM 20% (mean of draws)", n=int(np.mean([((select(E, np.random.default_rng(k)) & tradable).sum()) for k in range(5)])),
                 mean=draws.mean(), draw_p5=np.percentile(draws, 5), draw_p95=np.percentile(draws, 95), p_random=p_rand)
        rows.append(r)
        D = pd.DataFrame(rows); D.insert(0, "universe", uni)
        s0 = rows[0]
        D["passes"] = False
        D.loc[0, "passes"] = bool(s0["n"] >= 200 and s0["t"] >= 2 and s0["mean"] >= 0.05 and s0["mean_is"] > 0 and s0["mean_oos"] > 0
                                  and (not np.isfinite(s0["worst_mean"]) or s0["worst_mean"] >= -0.3)
                                  and s0["mean"] > rows[1]["mean"] and s0["mean"] > draws.mean())
        D.loc[0, "p_random"] = p_rand
        out.append(D)
        print(f"\n=== {uni}: {E.sym.nunique()} stocks, {E.day.nunique()} days with RV ===")
        print(D.drop(columns=["by_year"]).round(4).to_string(index=False))
        for _, rr in D.iterrows():
            if isinstance(rr.get("by_year"), str): print(f"  {rr['set']}: {rr['by_year']}")
        bys = T.groupby("sym").R.agg(["size", "mean"]).sort_values("size", ascending=False)
        print("  TOP trades by stock:", ", ".join(f"{k} {int(v['size'])}/{v['mean']:+.2f}" for k, v in bys.iterrows()))
        print("  TOP: share exited at the stop", f"{(T.why == 1).mean():.2f}", "| median cost", f"{T.cost_R.median():.3f}R",
              "| first-bar 9:35 share", f"{(T.first_bar == '09:35').mean():.2f}")
        if "R_m1" in E:
            for s in ("TSLA", "NVDA"):
                a = E[(E.sym == s) & tradable & np.isfinite(E.R_m1)]
                tt = a[top[a.index]] if len(a) else a
                print(f"  M1 check {s}: all days n {len(a)} M5 {a.R.mean():+.3f} vs M1 {a.R_m1.mean():+.3f}; "
                      f"selected days n {len(tt)} M5 {tt.R.mean():+.3f} vs M1 {tt.R_m1.mean():+.3f}")
                out.append(pd.DataFrame([dict(universe=uni, set=f"M1 check {s} all days", n=len(a), mean=a.R_m1.mean(), mean_m5=a.R.mean()),
                                         dict(universe=uni, set=f"M1 check {s} TOP days", n=len(tt), mean=tt.R_m1.mean(), mean_m5=tt.R.mean())]))
    pd.concat(out, ignore_index=True).to_csv(OUT, index=False, float_format="%.5g")
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
