"""Log #76 (live opening candle on the newest data) and #77 (FTMO risk per strategy), pre-registered in research/log.md.
Streams (FTMO export, costs as in the battery):
  OC_TSLA, OC_US100 : opening candle, first 30 minutes, stop at its far end, out at the close, Fed decision days skipped (live EA)
  GF_EU, GF_US      : index gap fade, #70 cell (1.0 ATR, stop = gap size, target = yesterday's close, out at the close), 5 EU / 4 US
                      indices; risk is a budget per region-day split equally over that day's signals
  NB_US100          : noise band on US100, the #74 CANDIDATE cell (14 days, 60-minute decisions, no VWAP stop); R per day in band units
Grid: OC 0.25/0.5/0.75/1.0% per trade x GF 0/0.25/0.5/0.75% per region-day x NB 0/0.25/0.5% per day; full / half / zero edge;
firms FTMO Swing, FTMO Standard, FundedNext Stellar 2-step. 10-day block bootstrap of business days from 2022-01-03.
python3 quant/ftmo_opt.py [n_paths]  -> results/ftmo_opt.csv, results/ftmo_opt_streams.csv"""
import os, sys, time, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "bt")); sys.path.insert(0, os.path.join(ROOT, "lab"))
import universe as U, intraday as ID
from sessions import Session
from run_battery import intraday_frame
import gapfade_opt as G
from news import load_calendar, fed_days
import robust as RB

START = pd.Timestamp("2022-01-03")
FIRMS = {  # leverage by stream, phase targets, min trading days
    "FTMO Swing": dict(lev={"OC_TSLA": 1, "OC_US100": 15, "GF": 15, "GF_low": 9, "NB_US100": 15}, targets=(0.10, 0.05), min_days=4),
    "FTMO Standard": dict(lev={"OC_TSLA": 3.3, "OC_US100": 50, "GF": 50, "GF_low": 50, "NB_US100": 50}, targets=(0.10, 0.05), min_days=4),
    "FundedNext Stellar 2-step": dict(lev={"OC_TSLA": 2, "OC_US100": 20, "GF": 20, "GF_low": 20, "NB_US100": 20}, targets=(0.08, 0.05), min_days=5),
}
LOW_LEV = {"US2000.cash", "SPN35.cash", "HK50.cash"}


def oc_stream(sym, cat, fed):
    d = U.load(sym, "M5", cat); d = d[~d.index.duplicated()].sort_index()
    if "tickvol" not in d: d["tickvol"] = 1.0
    S = Session(d, "us_cash")
    sp = ID.opening_candle(S, minutes=30)
    R, why, rf = ID.simulate(S, sp["e_col"], sp["e_px"], sp["d"], sp["stop"], None, None, U.commission_of(sym), 1.2, False)
    days = pd.DatetimeIndex(S.days)
    m = np.isfinite(R) & ~days.isin(fed)
    return pd.DataFrame({"day": days[m], "R": R[m], "risk_frac": rf[m], "dir": sp["d"][m]})


def gf_streams(cat):
    out = {"EU": [], "US": []}
    for s, sess in G.MAIN.items():
        d, _ = intraday_frame(s, cat); S = Session(d, sess)
        ii, R, dd = G.cell_arrays(S, U.commission_of(s), G.BASE)
        rf = np.abs(S.open[ii] - S.prev_close[ii]) / S.open[ii]
        out["EU" if sess == "eu_cash" else "US"].append(pd.DataFrame({"day": pd.DatetimeIndex(S.days[ii]), "R": R, "risk_frac": rf, "sym": s}))
    return {k: pd.concat(v, ignore_index=True) for k, v in out.items()}


def nb_stream(cat, lookback=14, interval=60, use_vwap=False):
    d, _ = intraday_frame("US100.cash", cat); S = Session(d, "us_cash"); comm = U.commission_of("US100.cash")
    step = S.cols(interval); n, K = S.C.shape; marks = np.arange(step - 1, K, step)
    Cm = S.C[:, marks]; SPm = S.SP[:, marks]
    tp = (S.H + S.L + S.C) / 3; v = np.where(S.V > 0, S.V, 1.0); vw = (np.cumsum(tp * v, 1) / np.cumsum(v, 1))[:, marks]
    sig = pd.DataFrame(np.abs(Cm / S.open[:, None] - 1)).rolling(lookback).mean().shift(1).values
    pc = S.prev_close; ub = np.maximum(S.open, pc)[:, None] * (1 + sig); lb = np.minimum(S.open, pc)[:, None] * (1 - sig)
    pos = np.zeros(n); ent = np.full(n, np.nan); ret = np.zeros(n); first_sig = np.full(n, np.nan)
    ok = np.isfinite(sig[:, 0]) & np.isfinite(pc); M = len(marks)
    for m in range(M):
        p = Cm[:, m]
        if m == M - 1: tgt = np.zeros(n)
        elif use_vwap: tgt = np.where(p > np.maximum(ub[:, m], vw[:, m]), 1, np.where(p < np.minimum(lb[:, m], vw[:, m]), -1, 0))
        else: tgt = np.where(p > ub[:, m], 1, np.where(p < lb[:, m], -1, pos))
        tgt = np.where(ok, tgt, 0); ch = tgt != pos; cs = SPm[:, m] * 1.2 / 2 / p + comm
        ret += np.where(ch & (pos != 0), pos * (p / np.where(np.isfinite(ent), ent, p) - 1) - cs, 0)
        opening = ch & (tgt != 0); ret -= np.where(opening, cs, 0)
        first_sig = np.where(opening & np.isnan(first_sig), sig[:, m], first_sig)
        ent = np.where(opening, p, np.where(ch, np.nan, ent)); pos = tgt
    tr = np.isfinite(first_sig)
    return pd.DataFrame({"day": pd.DatetimeIndex(S.days[tr]), "R": ret[tr] / first_sig[tr], "risk_frac": first_sig[tr]})


def daily(streams, risk, keep, lev, cal):
    """streams: name -> DataFrame(day, R, risk_frac[, sym]); risk: name -> risk (GF_* = budget per region-day)."""
    parts = []
    for name, T in streams.items():
        r = risk.get(name, 0.0)
        if r <= 0: continue
        R = T.R.values - (1 - keep) * T.R.mean()
        if name.startswith("GF"):
            k = T.groupby("day").R.transform("size").values                       # signals in the region that day
            each = r / k
            L = np.array([lev["GF_low"] if s in LOW_LEV else lev["GF"] for s in T.sym])
        else:
            each = np.full(len(T), r); L = np.full(len(T), lev[name])
        allowed = np.minimum(each, T.risk_frac.values * L)
        parts.append(pd.Series(R * allowed, index=T.day.values).groupby(level=0).sum())
    if not parts: return pd.Series(0.0, index=cal)
    return pd.concat(parts, axis=1).sum(axis=1).reindex(cal).fillna(0.0)


def challenge(ret, targets, min_days, n=3000, block=10, max_days=250, seed=7):
    ret = np.asarray(ret); rng = np.random.default_rng(seed); res = []
    for _ in range(n):
        eq, days, ph, pdays, ok, fail = 1.0, 0, 0, 0, False, False
        while days < max_days and not ok and not fail:
            s = rng.integers(0, len(ret) - block)
            for x in ret[s:s + block]:
                start = eq; eq *= 1 + x; days += 1; pdays += 1
                if eq - start <= -0.05 or eq <= 0.90: fail = True; break
                if eq >= 1 + targets[ph] and pdays >= min_days:
                    if ph + 1 < len(targets): ph, eq, pdays = ph + 1, 1.0, 0
                    else: ok = True; break
                if days >= max_days: break
        res.append((ok, fail, days))
    r = np.array(res, dtype=float)
    okm = r[:, 0] == 1
    out = {f"pass_{m}m": float((okm & (r[:, 2] <= 21 * m)).mean()) for m in (1, 2, 3, 6, 12)}
    out["fail"] = float(r[:, 1].mean()); out["median_months"] = float(np.median(r[okm, 2]) / 21) if okm.any() else np.nan
    return out


def funded(ret, months=12, split=0.8, n=2000, block=10, seed=2):
    ret = np.asarray(ret); rng = np.random.default_rng(seed); surv = 0; paid = 0.0
    for _ in range(n):
        eq, p, alive = 1.0, 0.0, True
        for _m in range(months):
            days = 0
            while days < 21 and alive:
                s = rng.integers(0, len(ret) - block)
                for x in ret[s:s + block]:
                    start = eq; eq *= 1 + x; days += 1
                    if eq - start <= -0.05 or eq <= 0.90: alive = False; break
                    if days >= 21: break
            if not alive: break
            if eq > 1: p += (eq - 1) * split; eq = 1.0
        surv += alive; paid += p
    return surv / n, paid / n / months


def last_n(T, n=60):
    return T.sort_values("day").R.tail(n).mean()


def main():
    n_paths = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    t0 = time.time(); cat = U.catalog()
    fed = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
    st = {"OC_TSLA": oc_stream("TSLA", cat, fed), "OC_US100": oc_stream("US100.cash", cat, fed)}
    gf = gf_streams(cat); st["GF_EU"], st["GF_US"] = gf["EU"], gf["US"]
    st["NB_US100"] = nb_stream(cat)
    # ---------------------------------------------------------------- #76 live opening candle on the newest data
    print("#76 live opening candle (Fed days skipped), FTMO export through", max(T.day.max() for T in st.values()).date())
    for k in ("OC_TSLA", "OC_US100"):
        T = st[k].sort_values("day"); R = T.R.values; dd = pd.DatetimeIndex(T.day)
        roll = pd.Series(R).rolling(60).mean()
        y26 = R[dd.year == 2026]; s22 = R[dd >= "2022-01-01"]
        print(f"  {k}: 2022-26 n {len(s22)} mean {s22.mean():+.3f} | 2026 YTD n {len(y26)} mean {y26.mean():+.3f} | last 60 {R[-60:].mean():+.3f} "
              f"(last trade {dd[-1].date()}) | last 20 {R[-20:].mean():+.3f} | rolling-60 since 2022: min {roll[dd >= '2022-03-01'].min():+.3f}, "
              f"share of days below 0 {(roll[dd >= '2022-03-01'] < 0).mean():.0%}")
        mo = pd.Series(R, index=dd).groupby(dd.to_period("M")).agg(["mean", "size"]).tail(8)
        print("    last 8 months: " + ", ".join(f"{p}: {r['mean']:+.2f} ({int(r['size'])})" for p, r in mo.iterrows()))
    pair = pd.concat([st["OC_TSLA"], st["OC_US100"]]).sort_values("day")
    print(f"  live pair last 60 trades {pair.R.tail(60).mean():+.3f}; last 120 {pair.R.tail(120).mean():+.3f}")
    # ---------------------------------------------------------------- streams summary + correlations
    cal = pd.bdate_range(START, max(T.day.max() for T in st.values()))
    rows = []
    for k, T in st.items():
        T = T[T.day >= START]; R = T.R.values
        rows.append(dict(stream=k, n=len(R), per_year=len(R) / (len(cal) / 261), avgR=R.mean(), t=R.mean() / R.std(ddof=1) * np.sqrt(len(R)),
                         from2024=R[pd.DatetimeIndex(T.day) >= "2024-01-01"].mean(), last60=last_n(T), median_risk_pct=np.median(T.risk_frac) * 100))
    SM = pd.DataFrame(rows); pd.set_option("display.width", 250); print("\nstreams from 2022-01-03:"); print(SM.round(3).to_string(index=False))
    SM.to_csv(os.path.join(ROOT, "results", "ftmo_opt_streams.csv"), index=False, float_format="%.4f")
    b = RB.bca_bounds(st["NB_US100"].R.values, B=20000, rng=1)
    print(f"NB_US100 (14, 60, no VWAP) BCa 95% lower bound {b['low'][0.025]:+.3f} (mean {b['theta']:+.3f})")
    st = {k: T[T.day >= START].reset_index(drop=True) for k, T in st.items()}
    unit = {k: daily({k: T}, {k: 0.01}, 1.0, FIRMS["FTMO Standard"]["lev"], cal) for k, T in st.items()}
    C = pd.DataFrame(unit); print("\ndaily P/L correlation (1% risk units):"); print(C.corr().round(2).to_string())
    act = (C != 0)
    print("days with both OC_US100 and NB_US100 active: {:.0%} of NB days; same sign on those days {:.0%}".format(
        (act.OC_US100 & act.NB_US100).sum() / act.NB_US100.sum(), (np.sign(C.OC_US100) == np.sign(C.NB_US100))[act.OC_US100 & act.NB_US100].mean()))
    # ---------------------------------------------------------------- #77 grid
    grid = list(itertools.product((0.0025, 0.005, 0.0075, 0.01), (0.0, 0.0025, 0.005, 0.0075), (0.0, 0.0025, 0.005)))
    out = []
    for firm, F in FIRMS.items():
        for oc, gfr, nbr in grid:
            risk = {"OC_TSLA": oc, "OC_US100": oc, "GF_EU": gfr, "GF_US": gfr, "NB_US100": nbr}
            for keep, lab in ((1.0, "full"), (0.5, "half"), (0.0, "zero")):
                ret = daily(st, risk, keep, F["lev"], cal)
                c = challenge(ret.values, F["targets"], F["min_days"], n=n_paths)
                row = dict(firm=firm, oc=oc, gf=gfr, nb=nbr, edge=lab, **c)
                if keep == 1.0 or (keep == 0.5):
                    s, pay = funded(ret.values, n=1500)
                    eq = (1 + ret).cumprod()
                    row.update(keep12m=s, payout_10k=pay * 10000, hist_maxDD=(eq / eq.cummax() - 1).min(), worst_day=ret.min(),
                               avg_month=((1 + ret).groupby(ret.index.to_period("M")).prod() - 1).mean())
                out.append(row)
        print(f"{firm} done ({time.time() - t0:.0f}s)", flush=True)
    O = pd.DataFrame(out); O.to_csv(os.path.join(ROOT, "results", "ftmo_opt.csv"), index=False, float_format="%.4f")
    for firm in FIRMS:
        H = O[(O.firm == firm) & (O.edge == "half")]
        okH = H[H.fail <= 0.25]
        pick = okH.loc[okH.pass_6m.idxmax()] if len(okH) else H.loc[H.pass_6m.idxmax()]
        sel = O[(O.firm == firm) & (O.oc == pick.oc) & (O.gf == pick.gf) & (O.nb == pick.nb)]
        print(f"\n{firm}: pick at HALF edge (max pass within 6 months, fail <= 25%): OC {pick.oc * 100:.2f}% / GF {pick.gf * 100:.2f}% per region-day / NB {pick.nb * 100:.2f}%")
        print(sel[["edge", "pass_1m", "pass_2m", "pass_3m", "pass_6m", "pass_12m", "fail", "median_months", "keep12m", "payout_10k", "hist_maxDD", "worst_day", "avg_month"]].round(3).to_string(index=False))
        print("  top 8 at half edge by pass within 6 months (fail <= 25%):")
        print(okH.sort_values("pass_6m", ascending=False).head(8)[["oc", "gf", "nb", "pass_3m", "pass_6m", "pass_12m", "fail", "median_months", "payout_10k"]].round(3).to_string(index=False))
        base = O[(O.firm == firm) & (O.oc == 0.005) & (O.gf == 0.0) & (O.nb == 0.0)]
        print("  reference, live plan (OC 0.5% only):"); print(base[["edge", "pass_3m", "pass_6m", "pass_12m", "fail", "median_months", "payout_10k"]].round(3).to_string(index=False))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
