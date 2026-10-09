"""#48 — backlog #40/#41 (first part): our two gold leads, unchanged, on the forex pairs Shen exported (multiple_asset2.zip):
EURUSD, GBPUSD, USDCHF, FTMO 30-minute bars Aug/Sep 2018 - Oct 2026. Nothing re-tuned.
  #33: 1-hour gap retest after a break of structure, target the last pullback swing (>= 2R) (bt/fvg_retest.py, T1).
  #35: breaker-block retest, 2R (bt/ob_strategies.py strat3), 4-hour candles on FTMO's server clock (the EA's candles) and,
       for reference, from UTC midnight.
1-hour bars = two 30-minute bars; 4-hour bars cut on the server clock (17:00 New York). Exits on 30-minute bars with the
conservative fill rule: inside the bar where the limit fills, a stop touch counts and a target touch doesn't (its order
is unknown); from the next bar on, stop first when one bar touches both; max 5 days.
Costs: FTMO spread (export column x 1.2; it is about the minimum within the bar) + commission 0.0025% per side (about
$5 a lot round trip). Gold run through the same 30-minute pipeline (MT4 feed, 2018-08 .. 2026-10) to show what the coarser
exits do to the numbers found with 1-minute exits."""
import sys, glob, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc import pivots
from smc_grid import TF, exit_nb, tstat
import ob_strategies as O
import fvg_retest as F
from data_standard_check import to_server, from_server, d1_atr, AGG
from ftmo_data import load_export

NS = 60_000_000_000
COMM_FX, COMM_GOLD = 0.000025, 0.000007


def exit_conservative(G, fill_t, bar_ns, e, stop, tgt, d, max_bars=240, coin=False):
    """Trade side d filled at e inside the entry bar. Real trade: on the fill bar the stop counts (price had to pass the
    entry to reach it), the target doesn't. Coin flip (other side of the same fill): on the fill bar neither counts -
    its stop sits where price came from, so that touch was before the fill."""
    i0 = np.searchsorted(G.t, fill_t); i_end = np.searchsorted(G.t, fill_t + np.timedelta64(bar_ns, "ns"))
    if i0 >= len(G.t): return None
    fd = -d if coin else d                                          # the side whose limit filled
    w = np.flatnonzero((G.l[i0:i_end] <= e) if fd == 1 else (G.h[i0:i_end] >= e)); j = i0 + (w[0] if len(w) else 0)
    if j >= len(G.t): return None
    if not coin and ((d == 1 and G.l[j] <= stop) or (d == -1 and G.h[j] >= stop)): return stop
    i1 = min(j + 1 + max_bars, len(G.t))
    return exit_nb(G.h, G.l, G.c, j + 1, i1, stop, tgt, d) if j + 1 < i1 else G.c[j]


def run33(T, comm, n=3, buf=0.05, window=48, min_rr=2.0):
    S, G = T["H1"], T["X"]; ph, pl = pivots(S.h, S.l, n); rows = []
    for bos_i, bot, top, leg_high, k in F.setups(S, n=n):
        a = max(bos_i, k) + 1; b = min(a + window, len(S.c))
        if a >= len(S.c): continue
        atr = S.atr[a]
        if not np.isfinite(atr): continue
        stop = leg_high + buf * atr; ent = bot; post_low = S.l[bos_i:a].min(); last_pl = None; fill = None
        for m in range(a, b):
            q = m - 1 - n
            if q > bos_i and pl[q]: last_pl = S.l[q]
            if S.h[m] >= stop: break
            if S.h[m] >= ent: e = max(ent, S.o[m]); fill = m; break
            post_low = min(post_low, S.l[m])
        if fill is None: continue
        risk = stop - e
        if risk <= 0: continue
        tgt = last_pl if last_pl is not None else post_low
        rr = (e - tgt) / risk
        if rr < min_rr: continue
        X = exit_conservative(G, S.t[fill], 60 * NS, e, stop, tgt, -1)
        Xf = exit_conservative(G, S.t[fill], 60 * NS, e, e - risk, e + (e - tgt), 1, coin=True)
        if X is None or Xf is None: continue
        cost = S.sp[fill] + comm * (abs(e) + abs(X))
        rows.append((S.t[fill], (e - X - cost) / risk, (Xf - e - cost) / risk, rr))
    return rows


def run35(T, obs, comm, rr=2.0, life=100):
    S, G = T["H4"], T["X"]; ph, pl = pivots(S.h, S.l, 3); sl = O.last_swing(S.l, pl, 3); rows = []; N = len(S.c)
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
        risk = stop - e; tgt = e - rr * risk
        X = exit_conservative(G, S.t[fill], 240 * NS, e, stop, tgt, -1)
        Xf = exit_conservative(G, S.t[fill], 240 * NS, e, e - risk, e + rr * risk, 1, coin=True)
        if X is None or Xf is None: continue
        cost = S.sp[fill] + comm * (abs(e) + abs(X))
        rows.append((S.t[fill], (e - X - cost) / risk, (Xf - e - cost) / risk, rr))
    return rows


def frames(m30, clock):
    h4 = m30.resample("4h", label="left", closed="left").agg(AGG).dropna() if clock == "utc" else None
    if clock == "server":
        x = m30.copy(); x.index = to_server(m30.index); h4 = x.resample("4h", label="left", closed="left").agg(AGG).dropna()
        u = from_server(h4.index); h4 = h4[~u.isna()]; h4.index = u[~u.isna()]; h4 = h4.sort_index()
    return {"X": m30, "H1": m30.resample("1h", label="left", closed="left").agg(AGG).dropna(), "H4": h4, "D1": d1_atr(m30)}


def evaluate(name, m30, comm):
    out = {}
    for clock in ("server", "utc"):
        B = frames(m30, clock); atr_df = B["D1"][["atr"]]
        Ts = {m: {k: TF(B[k], m, atr_df) for k in ("X", "H1", "H4")} for m in (False, True)}
        if clock == "server":
            rows = []
            for m in (False, True): rows += [r + (1 if m else -1,) for r in run33(Ts[m], comm)]
            out["#33 1-hour gap retest"] = rows
        raw = {m: O.find_obs(Ts[m]["H4"]) for m in (False, True)}; N = len(Ts[False]["H4"].c); rows = []
        for m in (False, True):
            obs = O.lifetimes(raw[m], raw[not m], N)
            rows += [r + (-1 if not m else 1,) for r in run35(Ts[m], obs, comm)]
        out[f"#35 4-hour breaker ({'FTMO clock' if clock == 'server' else 'UTC candles'})"] = rows
    res = {}
    for lab, rows in out.items():
        df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "side"]); df["t"] = pd.to_datetime(df.t)
        res[lab] = df
        if len(df) < 10: print(f"{name:7s} {lab:34s} n={len(df)}"); continue
        yrs = (df.t.max() - df.t.min()).days / 365.25; IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
        print(f"{name:7s} {lab:34s} n={len(df):4d} ({len(df)/yrs:3.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} "
              f"coin={df.R_flip.mean():+.3f} | L {df[df.side==1].R.mean():+.3f} S {df[df.side==-1].R.mean():+.3f} | <24 {df.R[IS].mean():+.3f} "
              f"24+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} worst {yr.min():+.2f}", flush=True)
    return res


if __name__ == "__main__":
    t0 = time.time(); allres = {}
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]].loc["2018-08-20":]
    g30 = g.resample("30min", label="left", closed="left").agg(AGG).dropna()
    allres["XAUUSD"] = evaluate("XAUUSD", g30, COMM_GOLD)
    for sym in ("EURUSD", "GBPUSD", "USDCHF"):
        d = load_export(glob.glob(f"/home/claude/data/fx2/{sym}_M30_*.csv")[0])
        d.index = from_server(pd.DatetimeIndex(d.index)); d = d[~d.index.isna()].sort_index()
        d = d[["open", "high", "low", "close", "sp"]].copy(); d["sp"] = d.sp * 1.2
        allres[sym] = evaluate(sym, d, COMM_FX)
    print("\npooled forex (3 pairs):")
    for lab in allres["EURUSD"]:
        df = pd.concat([allres[s][lab] for s in ("EURUSD", "GBPUSD", "USDCHF")])
        IS = df.t < "2024-01-01"
        print(f"   {lab:34s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} | <24 {df.R[IS].mean():+.3f} (n {IS.sum()}) 24+ {df.R[~IS].mean():+.3f} (n {(~IS).sum()}) | coin {df.R_flip.mean():+.3f}")
    pd.to_pickle(allres, "/home/claude/bt/fx_cross_check.pkl")
    print(f"done in {time.time() - t0:.0f}s")
