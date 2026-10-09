"""#39 — RedNote 格局Vision "ICT课004｜先统一看图标准" (11-min lesson): a rule that depends on whether a high was swept or a gap formed can
give different answers on a different data feed, chart clock or touch definition; fix them, and re-test after any change.
Checks on our two gold candidates (no new rules, nothing re-tuned):
  1. #35 4-hour breaker block, 2R: 4-hour candles cut at FTMO's server clock (00:00 server = 17:00 New York, the candles the EA
     would trade) instead of UTC midnight. Gold 2012 - Oct 2026, exits on 1-minute bars.
  2. #33 1-hour gap retest (pullback-low target, >= 2R) and #35 on FTMO's own MT5 feed vs the MT4 feed they were found on:
     same window (2022-07-05 .. 2026-10-07, FTMO 15-minute history starts there), every timeframe built from 15-minute bars the same
     way (4-hour on the server clock for both), the same spread model, exits on 15-minute bars (stop first). Plus the MT4 feed with
     1-minute exits to show what the coarser exits change. Trades matched on bar time + side."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc_grid import load, TF, tstat
import ob_strategies as O
import fvg_retest as F

AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean"}


def to_server(idx_utc):
    return idx_utc.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)


def from_server(idx_srv):
    ny = (idx_srv - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    return ny.tz_convert("UTC").tz_localize(None)


def h4_server(g):
    x = g.copy(); x.index = to_server(g.index)
    h = x.resample("4h", label="left", closed="left").agg(AGG).dropna()
    u = from_server(h.index); h = h[~u.isna()]; h.index = u[~u.isna()]
    return h.sort_index()


def d1_atr(g):
    key = to_server(g.index).normalize()
    d1 = g.groupby(key).agg(AGG); d1 = d1[d1.index.weekday < 5]
    pc = d1.close.shift(1)
    d1["atr"] = pd.concat([d1.high - d1.low, (d1.high - pc).abs(), (d1.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    u = from_server(d1.index); d1 = d1[~u.isna()]; d1.index = u[~u.isna()]
    return d1


def ftmo_m15(sp_by_year):
    d = pd.read_csv("/home/claude/data/mt4/XAUUSD_M15_202207050100_202610071700.csv", sep="\t")
    d.columns = [c.strip("<>").lower() for c in d.columns]
    srv = pd.DatetimeIndex(pd.to_datetime(d["date"] + " " + d["time"], format="%Y.%m.%d %H:%M:%S"))
    u = from_server(srv); d.index = u; d = d[~u.isna()]
    d = d[["open", "high", "low", "close"]].astype(float)
    d["sp"] = sp_by_year.reindex(d.index.year).values
    return d.sort_index()


def expand(m15):
    """15-minute bars as 15 identical 'minutes' each, so the 1-minute exit code keeps its 5-day cap and stop-first rule."""
    k = np.repeat(np.arange(len(m15)), 15)
    x = m15.iloc[k].copy()
    x.index = m15.index[k] + pd.to_timedelta(np.tile(np.arange(15), len(m15)), unit="min")
    return x


def build(m15, exits):
    """All timeframes from 15-minute bars; 'M1' slot = the exit series."""
    B = {"M15": m15, "H1": m15.resample("1h", label="left", closed="left").agg(AGG).dropna(), "H4": h4_server(m15), "D1": d1_atr(m15)}
    B["M1"] = exits
    return B


def run_33(B):
    atr_df = B["D1"][["atr"]]; rows = []
    for m in (False, True):
        T = {tf: TF(B[tf], m, atr_df) for tf in ("M1", "H1")}
        rows += [r[:3] + (r[5],) for r in F.run(T, "H1", "T1", -1 if m else 1)]
    df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "side"]); df["t"] = pd.to_datetime(df.t); return df


def run_35(B):
    atr_df = B["D1"][["atr"]]; Ts = {m: {tf: TF(B[tf], m, atr_df) for tf in ("M1", "H4")} for m in (False, True)}
    raw = {m: O.find_obs(Ts[m]["H4"]) for m in (False, True)}; N = len(Ts[False]["H4"].c); rows = []
    for m in (False, True):
        obs = O.lifetimes(raw[m], raw[not m], N)
        rows += [r + (-1 if not m else 1,) for r in O.strat3(Ts[m], "H4", obs)]
    df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "side"]); df["t"] = pd.to_datetime(df.t); return df


def line(lab, df):
    yr = df.groupby(df.t.dt.year).R.mean()
    return (f"{lab:44s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R > 0):.0%} coin={df.R_flip.mean():+.3f} "
            f"| by year " + " ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in yr.items()))


def compare(a, b, la, lb):
    ka = a.set_index(["t", "side"]).R; kb = b.set_index(["t", "side"]).R
    ka = ka[~ka.index.duplicated()]; kb = kb[~kb.index.duplicated()]
    common = ka.index.intersection(kb.index)
    ra, rb = ka.loc[common], kb.loc[common]
    only_a = ka.drop(common); only_b = kb.drop(common)
    same_sign = np.mean(np.sign(ra.values) == np.sign(rb.values)) if len(common) else np.nan
    return (f"   {la} vs {lb}: same trade (bar + side) {len(common)} = {len(common)/len(ka):.0%} of {la}'s, {len(common)/len(kb):.0%} of {lb}'s; "
            f"on the shared trades {ra.mean():+.3f} vs {rb.mean():+.3f} (same win/loss {same_sign:.0%}); "
            f"only on {la} {only_a.mean():+.3f} (n {len(only_a)}), only on {lb} {only_b.mean():+.3f} (n {len(only_b)})")


if __name__ == "__main__":
    t0 = time.time()
    B = load(); g = B["M1"]
    print("1. #35 4-hour breaker, 2012-2026, exits on 1-minute", flush=True)
    utc = run_35(B)
    B2 = dict(B); B2["H4"] = h4_server(g); srv = run_35(B2)
    print(line("4-hour candles from UTC midnight (as found)", utc)); print(line("4-hour candles on FTMO's server clock", srv))
    IS = srv.t < "2024-01-01"
    print(f"   server clock: before 2024 {srv.R[IS].mean():+.3f} (n {IS.sum()}), from 2024 {srv.R[~IS].mean():+.3f} (n {(~IS).sum()}); "
          f"longs {srv[srv.side==1].R.mean():+.3f} shorts {srv[srv.side==-1].R.mean():+.3f}", flush=True)

    print(f"\n2. Same window 2022-07-05 .. 2026-10-07, everything built from 15-minute bars   ({time.time() - t0:.0f}s)", flush=True)
    sp_by_year = g.sp.groupby(g.index.year).median()
    lo, hi = pd.Timestamp("2022-07-05"), pd.Timestamp("2026-10-07 21:00")
    mt4_m1 = g.loc[lo:hi]
    mt4_m15 = mt4_m1.resample("15min", label="left", closed="left").agg(AGG).dropna()
    ftm_m15 = ftmo_m15(sp_by_year).loc[lo:hi]
    print(f"   bars: MT4 15-min {len(mt4_m15)}, FTMO 15-min {len(ftm_m15)}; shared bar times {len(mt4_m15.index.intersection(ftm_m15.index))}")
    j = mt4_m15.join(ftm_m15, rsuffix="_f", how="inner")
    print(f"   price difference on shared bars (FTMO - MT4): close median {(j.close_f - j.close).median():+.3f}, |close| median "
          f"{(j.close_f - j.close).abs().median():.3f}, |high| median {(j.high_f - j.high).abs().median():.3f}, "
          f"|low| median {(j.low_f - j.low).abs().median():.3f} (gold ~$2,000-4,000)", flush=True)
    feeds = {"MT4, 1-min exits": build(mt4_m15, mt4_m1), "MT4, 15-min exits": build(mt4_m15, expand(mt4_m15)),
             "FTMO, 15-min exits": build(ftm_m15, expand(ftm_m15))}
    for name, fn in (("#33 1-hour gap retest, pullback-low target", run_33), ("#35 4-hour breaker block, 2R (server clock)", run_35)):
        print(f"\n   {name}", flush=True)
        res = {k: fn(v) for k, v in feeds.items()}
        for k, df in res.items(): print("   " + line(k, df), flush=True)
        print(compare(res["MT4, 15-min exits"], res["FTMO, 15-min exits"], "MT4", "FTMO"), flush=True)
    print(f"\ndone in {time.time() - t0:.0f}s")
