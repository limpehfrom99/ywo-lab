"""#42 — RedNote 杰明GW "下方刚被扫，为何盯上前高？看首个FVG。" (42 s, gold, 30-minute chart). Rule as told (longs; shorts mirrored):
  a break of structure up; its order block is the point of interest (POI); price pulls back, sweeps the sell-side liquidity (a
  swing low above the POI) into the POI; a lower-timeframe change of character and a strong bullish reaction follow -> buy from the
  first fair value gap; stop under the sweep; main target the buy-side liquidity above (the highs of the range).
Fixed before running:
  30-minute swings = 3-bar fractals usable 3 bars later. BOS = first close above the last confirmed swing high (each used once).
  Leg low = lowest low from that swing high to the BOS; OB = last down candle among the leg-low bar and the 3 before it. POI =
  [OB low, OB high + 0.25 daily ATR]. Search 96 bars (2 days) after the BOS; void on a close below the OB low.
  SSL = the latest confirmed swing low formed after the BOS and above the POI. Sweep = a bar with low < SSL and low inside the POI.
  CHoCH, 30-minute variant: a close above the last internal swing high (2-bar fractal, usable 2 bars later) confirmed before the
  sweep, within 12 bars; FVG = first bullish 3-candle gap completed after the sweep bar up to 3 bars after the CHoCH.
  CHoCH, 5-minute variant: the same on 5-minute bars (3-bar fractals) inside 12 thirty-minute bars after the sweep.
  Entry = buy limit at the gap's top, valid 24 bars of the entry timeframe from the later of the gap and the CHoCH; cancelled if price
  reaches the target first or trades below the sweep low. Stop = sweep low - 0.05 daily ATR. Targets: BSL = the highest high since
  the leg low as of the CHoCH (only if >= 1R), or a fixed 2R.
Exits on 1-minute bars (stop first), 5-day max; gold 2012 - Oct 2026; FTMO spread + commission; coin flip per trade. 4 cells."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, exit_nb, TF_MIN, tstat
from gold_m1 import COMM

NS = 60_000_000_000
TF_MIN = dict(TF_MIN, M30=30)
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean"}


def bos_setups(S, n=3):
    ph, _ = pivots(S.h, S.l, n); N = len(S.c); out = []; sh = None; used = set()
    for i in range(1, N):
        j = i - 1 - n
        if j >= 0 and ph[j]: sh = j
        if sh is None or sh in used: continue
        if S.c[i] > S.h[sh] and S.c[i - 1] <= S.h[sh]:
            used.add(sh); k = sh + int(np.argmin(S.l[sh:i + 1]))
            ob = next((q for q in (k, k - 1, k - 2, k - 3) if q >= 0 and S.c[q] < S.o[q]), k)
            out.append((i, ob, k))
    return out


def choch_fvg(E, a, b, sweep_t, n):
    """On entry-timeframe bars a..b-1 (a = first bar at/after the sweep bar's start): CHoCH = close above the last n-fractal high
    confirmed before the sweep-low bar; FVG = first bullish gap completed after the sweep-low bar up to 3 bars after the CHoCH."""
    if b - a < 3: return None
    s_low = a + int(np.argmin(E.l[a:min(b, a + max(1, sweep_t))]))           # the bar that made the sweep low
    ph, _ = pivots(E.h[max(0, s_low - 60):b], E.l[max(0, s_low - 60):b], n); off = max(0, s_low - 60)
    hs = [off + j for j in np.flatnonzero(ph) if off + j + n + 1 <= s_low]
    if not hs: return None
    lvl = E.h[hs[-1]]
    ch = next((q for q in range(s_low + 1, b) if E.c[q] > lvl), None)
    if ch is None: return None
    fv = next((x for x in range(s_low + 2, min(ch + 4, b)) if E.l[x] > E.h[x - 2]), None)
    if fv is None: return None
    if E.l[s_low + 1:fv + 1].min(initial=np.inf) < E.l[s_low]: return None   # a lower low after the sweep: not the sweep
    return s_low, ch, fv


def run(T, etf, target):
    S, E, G = T["M30"], T[etf], T["M1"]; ph, pl = pivots(S.h, S.l, 3); N = len(S.c); rows = []
    for i, ob, k in bos_setups(S):
        atr = S.atr[i]
        if not np.isfinite(atr): continue
        ob_lo, top = S.l[ob], S.h[ob] + 0.25 * atr; ssl = None; sweep = None
        for m in range(i + 1, min(i + 97, N)):
            j = m - 4
            if j > i and pl[j] and S.l[j] > top: ssl = S.l[j]
            if S.c[m] < ob_lo: break
            if ssl is not None and S.l[m] < ssl and ob_lo <= S.l[m] <= top: sweep = m; break
        if sweep is None: continue
        a = np.searchsorted(E.t, S.t[sweep]); b = np.searchsorted(E.t, S.t[sweep] + np.timedelta64(12 * 30 * NS, "ns"))
        per = TF_MIN["M30"] // TF_MIN[etf]
        r = choch_fvg(E, a, b, per, 2 if etf == "M30" else 3)
        if r is None: continue
        s_low, ch, fv = r
        sl_px = E.l[s_low]; stop = sl_px - 0.05 * atr; ent = E.l[fv]
        i30 = np.searchsorted(S.t, E.t[ch], side="right") - 1                 # the 30-min bar holding the CHoCH bar (not finished)
        bsl = max(S.h[k:i30].max(initial=-np.inf), E.h[np.searchsorted(E.t, S.t[i30]):ch + 1].max())
        if ent <= stop: continue
        risk0 = ent - stop; tgt = bsl if target == "BSL" else ent + 2 * risk0
        if target == "BSL" and tgt - ent < risk0: continue
        fill = None; st = max(fv, ch) + 1
        for q in range(st, min(st + 24, len(E.c))):
            if E.l[q] <= ent: fill = q; break
            if E.h[q] >= tgt or E.l[q] < sl_px: break
        if fill is None: continue
        e = min(ent, E.o[fill]); risk = e - stop
        if risk <= 0: continue
        i0 = np.searchsorted(G.t, E.t[fill]); i_end = np.searchsorted(G.t, E.t[fill] + np.timedelta64(TF_MIN[etf] * NS, "ns"))
        w = np.flatnonzero(G.l[i0:i_end] <= e); i0 = i0 + (w[0] if len(w) else 0); i1 = min(i0 + 5 * 1440, len(G.t))
        if i1 <= i0: continue
        X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, 1); cost = E.sp[fill] + COMM * (abs(e) + abs(X))
        Xf = exit_nb(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1)
        rows.append((E.t[fill], (X - e - cost) / risk, (e - Xf - cost) / risk, (tgt - e) / risk))
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    B["M30"] = B["M1"].resample("30min", label="left", closed="left").agg(AGG).dropna()
    Ts = {m: {tf: TF(B[tf], m, atr_df) for tf in ("M1", "M5", "M30")} for m in (False, True)}
    for etf in ("M30", "M5"):
        for target in ("BSL", "2R"):
            rows = []
            for m in (False, True): rows += [r + (-1 if m else 1,) for r in run(Ts[m], etf, target)]
            df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "side"])
            lab = f"CHoCH + first gap on {'30-min' if etf == 'M30' else '5-min'}, target {'BSL (range high)' if target == 'BSL' else '2R'}"
            if len(df) < 10: print(f"{lab:52s} n={len(df)}"); continue
            df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
            print(f"{lab:52s} n={len(df):4d} ({len(df)/14.8:3.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} "
                  f"coin={df.R_flip.mean():+.3f} | L {df[df.side==1].R.mean():+.3f} S {df[df.side==-1].R.mean():+.3f} | <24 {df.R[IS].mean():+.3f} "
                  f"24+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} worst {yr.min():+.2f} | rr {df.rr.median():.1f}", flush=True)
    print(f"done in {time.time() - t0:.0f}s")
