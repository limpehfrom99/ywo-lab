"""#40 — RedNote 交易修心社 "结构力场，一张图从哪里看起?" (8.3 min, reading an SMC indicator): the volume number and percentage inside an
order block "do not automatically mean stronger support/resistance or a higher win rate". Checked on our order-block trades:
  OB = the #35 definition (bt/ob_strategies.py find_obs + lifetimes). Its volume = tick volume of the OB candle / median tick volume
  of the 50 bars before it (relative volume), split into thirds per timeframe.
  Trades: (a) first return to the block, buy limit at its middle, stop below it, 2R (#35's strategy 2 without the inducement
  filter); (b) the breaker retest (#35 strategy 3, 2R). Exits on 1-minute bars, FTMO costs. Gold 2012 - Oct 2026, 4-hour on UTC
  and on FTMO's server clock, 1-hour, 15-minute. Nothing tuned; the question is only whether R rises with the block's volume."""
import sys, time, numpy as np, pandas as pd
from scipy.stats import ttest_ind
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, tstat
import ob_strategies as O
from data_standard_check import to_server, from_server, AGG

AGGV = dict(AGG, vol="sum")


def first_touch(T, tf, obs, rv):
    S, G = T[tf], T["M1"]; rows = []
    for x in obs:
        mid = (x["lo"] + x["hi"]) / 2; fill = next((q for q in range(x["valid"], x["end"]) if S.l[q] <= mid), None)
        if fill is None: continue
        atr = S.atr[fill]
        if not np.isfinite(atr): continue
        e = min(mid, S.o[fill]); stop = x["lo"] - 0.05 * atr
        if e <= stop: continue
        r = O.trade(G, S.t[fill], e, stop, e + 2 * (e - stop), 1, S.sp[fill], tf_fill=O.TF_MIN[tf] * O.NS, fill_level=e)
        if r: rows.append((S.t[fill], r[0], rv[x["ob"]]))
    return rows


def breaker(T, tf, obs, rv, life=100):
    S, G = T[tf], T["M1"]; ph, pl = pivots(S.h, S.l, 3); sl = O.last_swing(S.l, pl, 3); rows = []; N = len(S.c)
    for x in obs:
        bk = None
        for q in range(x["valid"], min(x["valid"] + life, N)):
            if S.c[q] < x["lo"]:
                bk = q if np.isfinite(sl[q]) and S.c[q] < sl[q] else None; break
        if bk is None or not np.isfinite(S.atr[bk]): continue
        stop = x["hi"] + 0.05 * S.atr[bk]; fill = None
        for r_ in range(bk + 1, min(bk + 1 + life, N)):
            if S.c[r_] > x["hi"]: break
            if S.h[r_] >= x["lo"]: fill = r_; break
        if fill is None: continue
        e = max(x["lo"], S.o[fill])
        if stop <= e: continue
        r = O.trade(G, S.t[fill], e, stop, e - 2 * (stop - e), -1, S.sp[fill], tf_fill=O.TF_MIN[tf] * O.NS, fill_level=e)
        if r: rows.append((S.t[fill], r[0], rv[x["ob"]]))
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp", "vol"]]
    atr_df = B["D1"][["atr"]]
    frames = {"H4 (UTC)": g.resample("4h", label="left", closed="left").agg(AGGV).dropna(),
              "H1": g.resample("1h", label="left", closed="left").agg(AGGV).dropna(),
              "M15": g.resample("15min", label="left", closed="left").agg(AGGV).dropna()}
    x = g.copy(); x.index = to_server(g.index); srv = x.resample("4h", label="left", closed="left").agg(AGGV).dropna()
    u = from_server(srv.index); srv = srv[~u.isna()]; srv.index = u[~u.isna()]; frames["H4 (FTMO clock)"] = srv.sort_index()
    M1 = {m: TF(B["M1"], m, atr_df) for m in (False, True)}
    for name, df in frames.items():
        tf = "H4" if name.startswith("H4") else name
        Ts = {m: {"M1": M1[m], tf: TF(df, m, atr_df)} for m in (False, True)}
        v = df.vol.values.astype(float); med = pd.Series(v).rolling(50).median().shift(1).values
        rv = np.where(med > 0, v / med, np.nan)
        raw = {m: O.find_obs(Ts[m][tf]) for m in (False, True)}; N = len(df)
        obs = {m: O.lifetimes(raw[m], raw[not m], N) for m in (False, True)}
        for lab, fn in (("first return to the block (middle, 2R)", first_touch), ("breaker retest (2R)", breaker)):
            rows = []
            for m in (False, True): rows += fn(Ts[m], tf, obs[m], rv)
            d = pd.DataFrame(rows, columns=["t", "R", "rv"]).dropna()
            if len(d) < 30: print(f"{name:16s} {lab:40s} n={len(d)}"); continue
            d["third"] = pd.qcut(d.rv, 3, labels=["low", "mid", "high"])
            s = d.groupby("third", observed=True).R.agg(["mean", "size"])
            hi_, lo_ = d.R[d.third == "high"], d.R[d.third == "low"]; tt = ttest_ind(hi_, lo_, equal_var=False).statistic
            print(f"{name:16s} {lab:40s} n={len(d):5d} all {d.R.mean():+.3f} | by block volume: low {s.loc['low','mean']:+.3f} "
                  f"mid {s.loc['mid','mean']:+.3f} high {s.loc['high','mean']:+.3f} (rel. vol cut-offs {d.rv.quantile(1/3):.2f} / "
                  f"{d.rv.quantile(2/3):.2f}) | win low {np.mean(d.R[d.third=='low']>0):.0%} high {np.mean(d.R[d.third=='high']>0):.0%} "
                  f"| high - low {hi_.mean() - lo_.mean():+.3f}R (t {tt:+.1f})", flush=True)
    print(f"done in {time.time() - t0:.0f}s")
