"""RedNote "K线之下": "订单块交易策略" (10.5-minute lesson, transcribed). Definitions and three strategies as taught:
  Valid order block (bullish; bearish mirrored): (1) the move leaves a gap (FVG); the OB is the key candle before the gap, zone =
  its full high-low; (2) untested: price has not come back to the zone since (a wick counts); (3) the move breaks structure (a
  new higher high above the last swing high). Trade only the latest valid OB in the direction of the current structure.
  Strategy 1, multi-timeframe: price returns to a valid higher-timeframe OB -> on the lower timeframe wait for an engulfing candle
    the reversal way -> enter at its close, stop just beyond the OB, target 2x the stop. Pairs: D1->H1, H4->M15, H1->M5.
  Strategy 2, inducement trap: a minor support with several bounces sits above the main OB; price breaks it and drops into the
    OB -> buy limit at the OB's middle, stop below the OB, target 2-3x the stop.
  Strategy 3, breaker block: a valid bullish OB is broken (close below it, making a lower low = change of character); when price
    comes back up to it, sell; stop just above it; target 2x the stop; one use only.
Fixed before running: 3-bar fractals usable 3 bars later; gap = 3-candle FVG; OB candle = last down candle among the 3 candles
ending at the gap's first candle (else that candle); structure break = a close above the last confirmed swing high within 20
bars of the gap, with no touch of the zone before it; an OB stays tradeable 100 bars after validation, until first touched, or
until a newer valid OB (either direction) appears. "Slightly beyond" = 0.05 daily ATR. Engulfing = body engulfs the previous
opposite candle; looked for over 2 higher-timeframe bars after the touch, cancelled by a close 0.1 ATR beyond the OB.
Inducement = 2+ confirmed swing lows after validation, above the OB, within 0.25 daily ATR of each other, before the fill.
Exits on 1-minute bars (stop first), 5-day max; gold 2012 - Oct 2026; FTMO spread + commission; coin flip per trade."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, exit_nb, TF_MIN, tstat
from gold_m1 import COMM

NS = 60_000_000_000


def last_swing(price, piv, n):
    """Array: price of the last swing confirmed before bar i (pivot j usable at i >= j + n + 1)."""
    N = len(price); out = np.full(N, np.nan); cur = np.nan
    for i in range(N):
        j = i - 1 - n
        if j >= 0 and piv[j]: cur = price[j]
        out[i] = cur
    return out


def find_obs(S, n=3, bos_window=20):
    h, l, o, c = S.h, S.l, S.o, S.c; N = len(c); ph, pl = pivots(h, l, n)
    sh = last_swing(h, ph, n); seen = set(); out = []
    for k in range(2, N):
        if not l[k] > h[k - 2]: continue
        ob = next((q for q in (k - 2, k - 3, k - 4) if q >= 0 and c[q] < o[q]), k - 2)
        if ob in seen or not np.isfinite(sh[k]): continue
        lo, hi = l[ob], h[ob]; ref = sh[k]
        v = None
        for q in range(k + 1, min(k + 1 + bos_window, N)):
            if l[q] <= hi: break                                        # tested before it was validated
            if c[q] > ref: v = q; break
        if v is None: continue
        seen.add(ob); out.append(dict(ob=ob, lo=lo, hi=hi, valid=v + 1))
    return out


def lifetimes(obs_same, obs_other, N, life=100):
    """End of each OB's life: 100 bars, or the next validation of any OB (same or other direction)."""
    vals = np.sort(np.array([x["valid"] for x in obs_same] + [x["valid"] for x in obs_other]))
    for x in obs_same:
        q = np.searchsorted(vals, x["valid"], side="right")
        nxt = vals[q] if q < len(vals) else N
        x["end"] = min(x["valid"] + life, nxt, N)
    return obs_same


def trade(G, t_start_ns_from, e, stop, tgt, d, sp, tf_fill=None, fill_level=None):
    """Exit on 1-minute bars. d = +1 long / -1 short in this frame. For limit fills, walk from the minute that touched the level."""
    i0 = np.searchsorted(G.t, t_start_ns_from)
    if tf_fill is not None:
        i_end = np.searchsorted(G.t, t_start_ns_from + np.timedelta64(tf_fill, "ns"))
        w = np.flatnonzero((G.l[i0:i_end] <= fill_level) if d == 1 else (G.h[i0:i_end] >= fill_level))
        i0 = i0 + (w[0] if len(w) else 0)
    i1 = min(i0 + 5 * 1440, len(G.t))
    if i1 <= i0: return None
    X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, d)
    risk = abs(e - stop); cost = sp + COMM * (abs(e) + abs(X))
    Xf = exit_nb(G.h, G.l, G.c, i0, i1, e + d * risk, e - d * abs(tgt - e), -d)
    return (d * (X - e) - cost) / risk, (-d * (Xf - e) - cost) / risk


def strat1(T, htf, ltf, obs, rr=2.0):
    H, L, G = T[htf], T[ltf], T["M1"]; rows = []
    for x in obs:
        t = next((q for q in range(x["valid"], x["end"]) if H.l[q] <= x["hi"]), None)
        if t is None: continue
        atr = H.atr[t]
        if not np.isfinite(atr): continue
        a = np.searchsorted(L.t, H.t[t]); b = np.searchsorted(L.t, H.t[t] + np.timedelta64(2 * TF_MIN[htf] * NS, "ns"))
        touched = False; ent = None
        for j in range(max(a, 1), min(b, len(L.c))):
            if L.c[j] < x["lo"] - 0.1 * atr: break
            if L.l[j] <= x["hi"]: touched = True
            if touched and L.c[j - 1] < L.o[j - 1] and L.c[j] > L.o[j] and L.o[j] <= L.c[j - 1] and L.c[j] >= L.o[j - 1]:
                ent = j; break
        if ent is None: continue
        e = L.c[ent]; stop = x["lo"] - 0.05 * atr
        if e <= stop: continue
        r = trade(G, L.t[ent] + np.timedelta64(TF_MIN[ltf] * NS, "ns"), e, stop, e + rr * (e - stop), 1, L.sp[ent])
        if r: rows.append((L.t[ent],) + r)
    return rows


def strat2(T, tf, obs, rr=2.0, inducement=True, n=3):
    S, G = T[tf], T["M1"]; ph, pl = pivots(S.h, S.l, n); rows = []
    for x in obs:
        mid = (x["lo"] + x["hi"]) / 2; lows = []; fill = None
        for q in range(x["valid"], x["end"]):
            j = q - 1 - n
            if j >= x["valid"] and pl[j] and S.l[j] > x["hi"]: lows.append(S.l[j])
            if S.l[q] <= mid: fill = q; break
        if fill is None: continue
        atr = S.atr[fill]
        if not np.isfinite(atr): continue
        if inducement:
            ok = any(abs(lows[i] - lows[k]) <= 0.25 * atr for i in range(len(lows)) for k in range(i + 1, len(lows)))
            if not ok: continue
        e = min(mid, S.o[fill]); stop = x["lo"] - 0.05 * atr
        if e <= stop: continue
        r = trade(G, S.t[fill], e, stop, e + rr * (e - stop), 1, S.sp[fill], tf_fill=TF_MIN[tf] * NS, fill_level=e)
        if r: rows.append((S.t[fill],) + r)
    return rows


def strat3(T, tf, obs, rr=2.0, life=100):
    S, G = T[tf], T["M1"]; ph, pl = pivots(S.h, S.l, 3); sl = last_swing(S.l, pl, 3); rows = []; N = len(S.c)
    for x in obs:
        bk = None
        for q in range(x["valid"], min(x["valid"] + life, N)):
            if S.c[q] < x["lo"]:
                bk = q if np.isfinite(sl[q]) and S.c[q] < sl[q] else None; break
        if bk is None: continue
        atr = S.atr[bk]
        if not np.isfinite(atr): continue
        stop = x["hi"] + 0.05 * atr; fill = None
        for r_ in range(bk + 1, min(bk + 1 + life, N)):
            if S.c[r_] > x["hi"]: break
            if S.h[r_] >= x["lo"]: fill = r_; break
        if fill is None: continue
        e = max(x["lo"], S.o[fill])
        if stop <= e: continue
        r = trade(G, S.t[fill], e, stop, e - rr * (stop - e), -1, S.sp[fill], tf_fill=TF_MIN[tf] * NS, fill_level=e)
        if r: rows.append((S.t[fill],) + r)
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    Ts = {m: {tf: TF(df, m, atr_df) for tf, df in B.items()} for m in (False, True)}
    OB = {}
    for tf in ("D1", "H4", "H1", "M15"):
        raw = {m: find_obs(Ts[m][tf]) for m in (False, True)}
        N = len(Ts[False][tf].c)
        for m in (False, True): OB[(m, tf)] = lifetimes(raw[m], raw[not m], N)
    print(f"order blocks found in {time.time() - t0:.0f}s:", {f"{tf}{'-' if m else '+'}": len(v) for (m, tf), v in OB.items()}, flush=True)
    cells = [("1 MTF engulfing, D1 -> H1, 2R", lambda T, m: strat1(T, "D1", "H1", OB[(m, "D1")])),
             ("1 MTF engulfing, H4 -> 15m, 2R", lambda T, m: strat1(T, "H4", "M15", OB[(m, "H4")])),
             ("1 MTF engulfing, H1 -> 5m, 2R", lambda T, m: strat1(T, "H1", "M5", OB[(m, "H1")]))]
    for tf in ("H4", "H1", "M15"):
        for rr in (2.0, 3.0):
            cells.append((f"2 inducement, limit at OB middle, {tf}, {rr:.0f}R", lambda T, m, tf=tf, rr=rr: strat2(T, tf, OB[(m, tf)], rr)))
        cells.append((f"2 no inducement filter, OB middle, {tf}, 2R", lambda T, m, tf=tf: strat2(T, tf, OB[(m, tf)], 2.0, inducement=False)))
        cells.append((f"3 breaker block retest, {tf}, 2R", lambda T, m, tf=tf: strat3(T, tf, OB[(m, tf)])))
    for name, fn in cells:
        rows = []
        for m in (False, True):
            side = 1 if not m else -1
            if name.startswith("3"): side = -side                        # breaker trades go against the original OB
            rows += [r + (side,) for r in fn(Ts[m], m)]
        df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "side"])
        if len(df) < 10: print(f"{name:46s} n={len(df)}"); continue
        df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
        print(f"{name:46s} n={len(df):5d} ({len(df)/14.8:4.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} "
              f"coin={df.R_flip.mean():+.3f} | longs {df[df.side==1].R.mean():+.3f} shorts {df[df.side==-1].R.mean():+.3f} | <2024 {df.R[IS].mean():+.3f} "
              f"2024+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)}", flush=True)
    print(f"done in {time.time() - t0:.0f}s")
