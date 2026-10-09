"""Three RedNote videos tested together (all about entering a trend on a pullback, and judging the trend's strength):
  杰明GW "SMC，FVG和回撤进场，三法结合" (13.7 min): with the trend, enter pullbacks by (1) Fibonacci 0.618-0.886 from the leg's start
    (the low before the move that broke the prior high) to its confirmed high, stop below the start; (2) the leg's FVG (limit at
    its top), stop below the gap's first candle; (3) breakout-retest: the broken resistance becomes support. Best when all three
    coincide. Left side (limit orders) on small timeframes, right side on big ones. Target: back to / beyond the high.
  熊猫教练 "合格的短线选手，一定要看得懂动能" (7.6 min): a momentum score for a trend leg — large trend candles > 50% +1, same-
    direction trend candles > 50% +1, counter pullbacks <= 3 +1, 2+ unfilled FVGs +4 (one: +2), almost no overlap +3 (some: +2),
    inside a 250-bar range -2. 8-10 = strong ("好大哥"), 5-7 = average, <= 4 = weak. Only strong legs are worth following.
  趋势周期形态 "如何判断趋势动能强劲" (4.5 min): the same idea — many trend candles, low overlap, unfilled FVGs = strong trend.
Fixed before running (longs; shorts mirrored):
  legs: 3-bar fractals; a confirmed swing high above the previous swing high; the leg starts at the lowest swing low between them;
  usable 3 bars after the high. Entries are limit orders for 48 bars after that, cancelled if price makes a new high first or
  closes below the leg's start.
  FIB618 / FIB786: limit at the 0.618 / 0.786 retracement, stop 0.05 daily ATR below the start.
  FVG: limit at the top of the latest unfilled bullish gap in the leg, stop 0.05 ATR below the gap's first candle.
  BRK: limit at the broken swing high (old resistance), stop below the start.
  CONF: the latest unfilled gap overlaps the 0.618-0.886 zone and the broken high sits within the gap (+-0.1 ATR); limit at the gap
  top, stop below the start.
  Targets: back to the leg's high ("前高"), or a fixed 2R. Exits on 1-minute bars (stop first), 5-day max.
  Momentum score exactly per the table above with: trend candle = body >= 50% of its range in the leg's direction; large = range >=
  the median range of the 100 bars before the leg; counter pullback = a 3-bar fractal high inside the leg; overlap = mean overlap of
  consecutive candles / the smaller range (< 0.35 "almost none" +3, < 0.6 "some" +2); in a range = the 250 bars before the leg
  reach both above its high and below its start. Complex-pullback deduction not coded (0).
Gold 2012 - Oct 2026, 15-min / 1-hour / 4-hour; FTMO spread + commission; coin flip per trade."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, exit_nb, TF_MIN, tstat
from gold_m1 import COMM

NS = 60_000_000_000


def legs(S, n=3):
    h, l, o, c = S.h, S.l, S.o, S.c; N = len(c); ph, pl = pivots(h, l, n)
    H = np.flatnonzero(ph); Lw = np.flatnonzero(pl); rng = h - l
    med100 = pd.Series(rng).rolling(100).median().shift(1).values
    out = []
    for a_, j in zip(H[:-1], H[1:]):
        if not h[j] > h[a_]: continue
        lows = Lw[(Lw > a_) & (Lw < j)]
        if len(lows) == 0: continue
        s = lows[np.argmin(l[lows])]; conf = j + n + 1
        if conf >= N or s < 250: continue
        lo, hi = l[s], h[j]; L = hi - lo
        if L <= 0: continue
        seg = slice(s, j + 1); bars = j - s + 1
        body = c[seg] - o[seg]; r = np.maximum(rng[seg], 1e-12)
        trend = (body >= 0.5 * r); large = trend & (rng[seg] >= med100[s])
        fv = []
        for k in range(s + 2, j + 1):
            if l[k] > h[k - 2] and l[k + 1:conf].min(initial=np.inf) > h[k - 2]: fv.append(k)
        cp = int(ph[s + 1:j].sum())
        hh, ll = h[seg], l[seg]
        ov = np.maximum(0, np.minimum(hh[1:], hh[:-1]) - np.maximum(ll[1:], ll[:-1])) / np.maximum(np.minimum(r[1:], r[:-1]), 1e-12)
        ovm = ov.mean() if len(ov) else 1.0
        in_range = h[s - 250:s].max() > hi and l[s - 250:s].min() < lo
        score = (int(large.mean() > 0.5) + int(trend.mean() > 0.5) + int(cp <= 3) + (4 if len(fv) >= 2 else 2 if len(fv) == 1 else 0)
                 + (3 if ovm < 0.35 else 2 if ovm < 0.6 else 0) - (2 if in_range else 0))
        out.append(dict(s=s, j=j, conf=conf, lo=lo, hi=hi, broken=h[a_], fvg=fv[-1] if fv else None, score=score))
    return out


def entries(S, x, kind, atr):
    lo, hi = x["lo"], x["hi"]; L = hi - lo; buf = 0.05 * atr
    if kind == "FIB618": return hi - 0.618 * L, lo - buf
    if kind == "FIB786": return hi - 0.786 * L, lo - buf
    if kind == "FVG":
        if x["fvg"] is None: return None
        k = x["fvg"]; return S.l[k], S.l[k - 2] - buf
    if kind == "BRK":
        if not lo < x["broken"] < hi: return None
        return x["broken"], lo - buf
    if kind == "CONF":
        if x["fvg"] is None: return None
        k = x["fvg"]; bot, top = S.h[k - 2], S.l[k]
        z_lo, z_hi = hi - 0.886 * L, hi - 0.618 * L
        if top < z_lo or bot > z_hi: return None
        if not (bot - 0.1 * atr <= x["broken"] <= top + 0.1 * atr): return None
        return top, lo - buf


def run(T, tf, kind, target, side):
    S, G = T[tf], T["M1"]; rows = []; ns = TF_MIN[tf] * NS
    for x in legs(S):
        a = x["conf"]
        if a >= len(S.c): continue
        atr = S.atr[a]
        if not np.isfinite(atr): continue
        en = entries(S, x, kind, atr)
        if en is None: continue
        lvl, stop = en
        if lvl <= stop: continue
        fill = None
        for m in range(a, min(a + 48, len(S.c))):
            if S.h[m] > x["hi"] or S.c[m] < x["lo"]: break
            if S.l[m] <= lvl: fill = m; break
        if fill is None: continue
        e = min(lvl, S.o[fill]); risk = e - stop
        if risk <= 0: continue
        tgt = x["hi"] if target == "HIGH" else e + 2 * risk
        if tgt <= e: continue
        i0 = np.searchsorted(G.t, S.t[fill]); i_end = np.searchsorted(G.t, S.t[fill] + np.timedelta64(ns, "ns"))
        w = np.flatnonzero(G.l[i0:i_end] <= e); i0 = i0 + (w[0] if len(w) else 0); i1 = min(i0 + 5 * 1440, len(G.t))
        if i1 <= i0: continue
        X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, 1)
        cost = S.sp[fill] + COMM * (abs(e) + abs(X))
        Xf = exit_nb(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1)
        rows.append((S.t[fill], (X - e - cost) / risk, (e - Xf - cost) / risk, (tgt - e) / risk, x["score"], side))
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    Ts = {m: {tf: TF(df, m, atr_df) for tf, df in B.items() if tf in ("M1", "M15", "H1", "H4")} for m in (False, True)}
    allrows = []
    for tf in ("M15", "H1", "H4"):
        for kind in ("FIB618", "FIB786", "FVG", "BRK", "CONF"):
            for target in ("HIGH", "2R"):
                rows = []
                for m in (False, True): rows += run(Ts[m], tf, kind, target, -1 if m else 1)
                df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "score", "side"])
                if len(df) < 10: print(f"{tf:3s} {kind:6s} {target:4s} n={len(df)}"); continue
                df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
                b = {lab: df.R[(df.score >= a_) & (df.score <= b_)] for lab, (a_, b_) in (("<=4", (-9, 4)), ("5-7", (5, 7)), ("8-10", (8, 10)))}
                bs = " ".join(f"{k} {v.mean():+.2f}(n{len(v)})" for k, v in b.items())
                print(f"{tf:3s} {kind:6s} {target:4s} n={len(df):5d} ({len(df)/14.8:4.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} "
                      f"win={np.mean(df.R>0):.0%} coin={df.R_flip.mean():+.3f} | L {df[df.side==1].R.mean():+.3f} S {df[df.side==-1].R.mean():+.3f} "
                      f"| <24 {df.R[IS].mean():+.3f} 24+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} | rr {df.rr.median():.1f} | score {bs}", flush=True)
                allrows.append(df.assign(tf=tf, kind=kind, target=target))
    pd.concat(allrows).to_pickle("/home/claude/bt/pullback_lab_trades.pkl")
    print(f"done in {time.time() - t0:.0f}s")
