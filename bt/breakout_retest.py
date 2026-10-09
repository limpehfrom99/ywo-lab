"""#38 — RedNote 源木派讲技术 "结构已经成立了，为什么还是不敢做?" (15.9-min live session, gold/NQ) and 交易修心社 "结构力场" (8.3 min,
equal highs/lows as liquidity). Rules as told (longs; shorts mirrored):
  A "种田" (a trader's daily routine on ES/NQ, "high win rate"): two wicks reach the same level; a big-bodied candle closes through
    it; on small timeframes one more candle follows through (on big ones not needed); place a limit back at the broken level;
    stop below; take profit at the prior high (elsewhere "a simple 1:2").
  B aggressive: a strong trend candle that truly breaks the swing high (body closes above it), first pullback of the leg, with the
    bigger timeframe trending the same way -> limit at 0.382 of that candle, the candle is the defence (stop below it), 1:2.
    If the next candle is another true breakout before the fill, move the order to it.
  C (结构力场) equal highs = "potential liquidity": price runs the level and closes back below -> sell (the liquidity-grab read).
Fixed before running:
  swings = 3-bar fractals usable 3 bars later; daily ATR known before the day; "big candle" = range >= 1.5 x the median range of the
  previous 20 bars and body >= 60% of the range in the move's direction; "true breakout" = first close above the last confirmed
  swing high.
  Equal-high level = the last two confirmed swing highs within 0.1 daily ATR of each other, the older one at most 40 bars back,
  no close above the higher one since; level = the higher one; expires when the older wick is 60 bars old. One use per level.
  A: big candle closes above the level (FT variant: the next candle closes above its close; order placed after it). Buy limit at
     the level, 24 bars; cancelled by a close below the stop. Stop = breakout candle low - 0.05 ATR. Targets: 2R, or HIGH = the
     highest high since the breakout at the fill, only if >= 1R.
  B: big candle that is a true breakout; buy limit at high - 0.382 x range, 12 bars, replaced by a newer trigger, cancelled by a
     close below the stop or a move to 2R before the fill. Stop = candle low - 0.05 ATR, target 2R. HTF variant: the higher
     timeframe's last completed close above its 50-EMA (M5->H1, M15->H4, H1->D1).
  C: a bar trades above the level and closes back below it -> sell at the next minute's open, stop = that bar's high + 0.05 ATR,
     target 2R.
Exits on 1-minute bars (stop first), 5-day max; gold 2012 - Oct 2026; FTMO spread + commission; coin flip per trade. 21 cells."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, exit_nb, TF_MIN, tstat
from gold_m1 import COMM

NS = 60_000_000_000
HTF = {"M5": "H1", "M15": "H4", "H1": "D1"}


def big_candles(S):
    rng = S.h - S.l; body = S.c - S.o
    med = pd.Series(rng).rolling(20).median().shift(1).values
    return (rng >= 1.5 * med) & (body >= 0.6 * rng) & (rng > 0)


def swing_state(S, n=3):
    """For each bar i: the last two confirmed swing highs (index) as of bar i (usable at i >= j + n + 1)."""
    ph, _ = pivots(S.h, S.l, n); N = len(S.c); last = np.full(N, -1); prev = np.full(N, -1); a = b = -1
    for i in range(N):
        j = i - 1 - n
        if j >= 0 and ph[j]: a, b = j, a
        last[i], prev[i] = a, b
    return last, prev


def eq_levels(S, last, prev, tol=0.1, back=40):
    """Equal-high levels: bar i -> level (higher of the two swing highs) if active at bar i, else nan. Level dies at the first close above."""
    N = len(S.c); lev = np.full(N, np.nan); used = set(); cur = None
    for i in range(N):
        a, b = last[i], prev[i]
        if a >= 0 and b >= 0 and (a, b) not in used and i - b <= back and np.isfinite(S.atr[i]) and abs(S.h[a] - S.h[b]) <= tol * S.atr[i]:
            L = max(S.h[a], S.h[b])
            if S.c[b:i].max() <= L: cur = (a, b, L); used.add((a, b))
        if cur is not None and i - cur[1] > 60: cur = None           # the older wick is more than 60 bars old: level expires
        if cur is not None:
            lev[i] = cur[2]
            if S.c[i] > cur[2]: cur = None                       # this bar breaks it; still reported at i so i can be the breakout
    return lev


def exit_trade(G, t_from, e, stop, tgt, sp, fill_level=None, bar_ns=None):
    i0 = np.searchsorted(G.t, t_from)
    if fill_level is not None:                                     # limit order: first minute inside the bar that reaches the level
        i_end = np.searchsorted(G.t, t_from + np.timedelta64(bar_ns, "ns"))
        w = np.flatnonzero(G.l[i0:i_end] <= fill_level); i0 = i0 + (w[0] if len(w) else 0)
    i1 = min(i0 + 5 * 1440, len(G.t))
    if i1 <= i0: return None
    risk = e - stop
    X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, 1); cost = sp + COMM * (abs(e) + abs(X))
    Xf = exit_nb(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1)
    return (X - e - cost) / risk, (e - Xf - cost) / risk, (tgt - e) / risk


def rule_a(T, tf, ft, target, lev, big):
    S, G = T[tf], T["M1"]; N = len(S.c); rows = []; ns = TF_MIN[tf] * NS; i = 21
    while i < N - 2:
        L = lev[i]
        if not (np.isfinite(L) and big[i] and S.c[i] > L and S.c[i - 1] <= L and np.isfinite(S.atr[i])): i += 1; continue
        stop = S.l[i] - 0.05 * S.atr[i]; a = i + 1
        if ft:
            if S.c[i + 1] <= S.c[i]: i += 1; continue
            a = i + 2
        if L <= stop: i += 1; continue
        fill = None; hi = S.h[i:a].max()
        for m in range(a, min(a + 24, N)):
            if S.l[m] <= L: fill = m; break
            if S.c[m] < stop: break
            hi = max(hi, S.h[m])
        if fill is None: i = a; continue
        e = min(L, S.o[fill]); risk = e - stop
        if risk <= 0: i = fill + 1; continue
        tgt = e + 2 * risk if target == "2R" else hi
        if target == "HIGH" and (tgt - e) < risk: i = fill + 1; continue
        r = exit_trade(G, S.t[fill], e, stop, tgt, S.sp[fill], fill_level=e, bar_ns=ns)
        if r: rows.append((S.t[fill],) + r)
        i = fill + 1
    return rows


def htf_trend(T, tf):
    H = T[HTF[tf]]; S = T[tf]
    ema = pd.Series(H.c).ewm(span=50, adjust=False).mean().values
    end = np.r_[H.t[1:], H.t[-1] + np.timedelta64(TF_MIN[HTF[tf]] * NS, "ns")]
    up = H.c > ema
    tclose = S.t + np.timedelta64(TF_MIN[tf] * NS, "ns")
    k = np.searchsorted(end, tclose, side="right") - 1                    # last HTF bar completed by this bar's close
    return np.where(k >= 50, up[np.clip(k, 0, None)], False)


def rule_b(T, tf, use_htf, big, last):
    S, G = T[tf], T["M1"]; N = len(S.c); rows = []; ns = TF_MIN[tf] * NS
    ok = htf_trend(T, tf) if use_htf else np.ones(N, bool)
    def trig(i):
        j = last[i]
        return (j >= 0 and big[i] and S.c[i] > S.h[j] and S.c[i - 1] <= S.h[j] and ok[i] and np.isfinite(S.atr[i]))
    i = 21
    while i < N - 1:
        if not trig(i): i += 1; continue
        cand = i; fill = None; m = i + 1; end = min(i + 13, N)
        while m < end:
            rng = S.h[cand] - S.l[cand]; ent = S.h[cand] - 0.382 * rng; stop = S.l[cand] - 0.05 * S.atr[cand]; risk = ent - stop
            if S.l[m] <= ent: fill = m; break
            if S.c[m] < stop or S.h[m] >= ent + 2 * risk: break
            if trig(m): cand = m; end = min(m + 13, N)                      # a newer true breakout: move the order to it
            m += 1
        if fill is None: i = m + 1; continue
        e = min(ent, S.o[fill]); risk = e - stop
        if risk <= 0: i = fill + 1; continue
        r = exit_trade(G, S.t[fill], e, stop, e + 2 * risk, S.sp[fill], fill_level=e, bar_ns=ns)
        if r: rows.append((S.t[fill],) + r)
        i = fill + 1
    return rows


def rule_c(T, tf, lev):
    """Sweep of equal highs and close back below -> short. Computed in this frame as a short (d=-1)."""
    S, G = T[tf], T["M1"]; N = len(S.c); rows = []; ns = TF_MIN[tf] * NS; done = set()
    for i in range(21, N - 1):
        L = lev[i]
        if not np.isfinite(L) or L in done or not np.isfinite(S.atr[i]): continue
        if S.h[i] > L and S.c[i] < L:
            done.add(L)
            stop = S.h[i] + 0.05 * S.atr[i]
            i0 = np.searchsorted(G.t, S.t[i] + np.timedelta64(ns, "ns"))
            if i0 >= len(G.t) - 1: continue
            e = G.o[i0]; risk = stop - e
            if risk <= 0: continue
            tgt = e - 2 * risk; i1 = min(i0 + 5 * 1440, len(G.t))
            X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, -1); cost = S.sp[i] + COMM * (abs(e) + abs(X))
            Xf = exit_nb(G.h, G.l, G.c, i0, i1, e - risk, e + 2 * risk, 1)
            rows.append((G.t[i0], (e - X - cost) / risk, (Xf - e - cost) / risk, 2.0))
        elif S.c[i] > L: done.add(L)
    return rows


def report(lab, rows):
    df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "side"])
    if len(df) < 10: print(f"{lab:46s} n={len(df)}", flush=True); return None
    df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
    yrs = (df.t.max() - df.t.min()).days / 365.25
    print(f"{lab:46s} n={len(df):5d} ({len(df)/yrs:4.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} "
          f"coin={df.R_flip.mean():+.3f} | L {df[df.side==1].R.mean():+.3f} S {df[df.side==-1].R.mean():+.3f} | <24 {df.R[IS].mean():+.3f} "
          f"24+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} worst {yr.min():+.2f} | rr {df.rr.median():.1f}", flush=True)
    return df


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    Ts = {m: {tf: TF(df, m, atr_df) for tf, df in B.items()} for m in (False, True)}
    pre = {}
    for m in (False, True):
        for tf in ("M5", "M15", "H1"):
            S = Ts[m][tf]; last, prev = swing_state(S); pre[(m, tf)] = (last, eq_levels(S, last, prev), big_candles(S))
    print(f"prepared in {time.time() - t0:.0f}s", flush=True)
    out = []
    for tf in ("M5", "M15", "H1"):
        cells = [(f"A {tf} two-wick break, {'follow-through' if ft else 'no follow-through'}, {tg}",
                  lambda T, m, ft=ft, tg=tg: rule_a(T, tf, ft, tg, pre[(m, tf)][1], pre[(m, tf)][2]))
                 for ft in (False, True) for tg in ("2R", "HIGH")]
        cells += [(f"B {tf} trend candle 0.382, {'HTF filter' if h else 'no filter'}, 2R",
                   lambda T, m, h=h: rule_b(T, tf, h, pre[(m, tf)][2], pre[(m, tf)][0])) for h in (False, True)]
        cells += [(f"C {tf} equal-high sweep -> reverse, 2R", lambda T, m: rule_c(T, tf, pre[(m, tf)][1]))]
        for lab, fn in cells:
            rows = []
            for m in (False, True):
                side = (-1 if m else 1) * (-1 if lab.startswith("C") else 1)
                rows += [r + (side,) for r in fn(Ts[m], m)]
            df = report(lab, rows)
            if df is not None: out.append(df.assign(cell=lab))
    pd.concat(out).to_pickle("/home/claude/bt/breakout_retest_trades.pkl")
    print(f"done in {time.time() - t0:.0f}s")
