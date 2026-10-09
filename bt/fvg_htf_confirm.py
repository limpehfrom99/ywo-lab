"""RedNote "交易升级打怪": "FVG不是碰线就买，确认还在后面" (41 s). Rule as told (longs; shorts mirrored): a 4-hour bullish gap only
gives the location. On the 15-minute chart: (1) the prior low gets pierced by a wick and the candle closes back above it;
(2) a later close goes above the local bounce high and leaves a new bullish gap; (3) price comes back to that new gap, holds,
and strengthens again -> buy. Abandon if the swept low breaks. In the example price then returns to the prior high.
Fixed before running: 4-hour gap = 3-candle FVG, used on its first touch within 30 bars. 15-minute, for 2 days from that touch:
  sweep = a bar whose low is below the previous 12 bars' lowest low and that closes back above it; bounce high = highest high of the
  6 bars before the sweep; break = a close above it within 12 bars, with a new bullish FVG formed after the sweep; entry = the
  first bar that dips into the new gap and closes above its bottom (variant: plus a next close above that bar's high); abandon
  on a close below the swept low. Stop = swept low - 0.05 daily ATR. Target = the 4-hour high before the pullback ("前高") or 2R.
Exits on 1-minute bars (stop first), 5-day max; gold 2012 - Oct 2026; FTMO costs; coin flip per trade."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc_grid import load, TF, exit_nb, tstat
from gold_m1 import COMM

NS = 60_000_000_000


def run(T, target, confirm2, side):
    H, L, G = T["H4"], T["M15"], T["M1"]; rows = []; N4 = len(H.c); N = len(L.c)
    for k in range(2, N4 - 1):
        if not H.l[k] > H.h[k - 2]: continue
        bot, top = H.h[k - 2], H.l[k]
        t = next((q for q in range(k + 1, min(k + 31, N4)) if H.l[q] <= top), None)
        if t is None: continue
        prior_high = H.h[k:t].max() if t > k else H.h[k]
        atr = H.atr[t]
        if not np.isfinite(atr): continue
        a = np.searchsorted(L.t, H.t[t]); b = min(a + 192, N)
        sw = None; brk = None; fv = None; ent = None
        m = max(a, 12)
        while m < b:
            if sw is not None and L.c[m] < sw[0]: break                       # swept low broken: abandon
            if sw is None or brk is None:
                lo12 = L.l[m - 12:m].min()
                if L.l[m] < lo12 and L.c[m] > lo12:
                    sw = (L.l[m], m, L.h[m - 6:m].max()); brk = None; fv = None   # (swept low, bar, bounce high)
                elif sw is not None and brk is None:
                    if m - sw[1] > 12: sw = None
                    elif L.c[m] > sw[2]:
                        fvs = [q for q in range(sw[1] + 2, m + 1) if L.l[q] > L.h[q - 2]]
                        if fvs: brk = m; fv = (L.h[fvs[-1] - 2], L.l[fvs[-1]])
                m += 1; continue
            fb, ft = fv
            if L.l[m] <= ft and L.c[m] > fb:
                if confirm2:
                    if m + 1 < b and L.c[m + 1] > L.h[m]: ent = m + 1
                    else: m += 1; continue
                else: ent = m
                break
            if L.c[m] <= fb: sw = None; brk = None; fv = None
            m += 1
        if ent is None: continue
        e = L.c[ent]; stop = sw[0] - 0.05 * atr; risk = e - stop
        if risk <= 0: continue
        tgt = prior_high if target == "HIGH" else e + 2 * risk
        if tgt <= e: continue
        i0 = np.searchsorted(G.t, L.t[ent] + np.timedelta64(15 * NS, "ns")); i1 = min(i0 + 5 * 1440, len(G.t))
        if i1 <= i0: continue
        X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, 1); cost = L.sp[ent] + COMM * (abs(e) + abs(X))
        Xf = exit_nb(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1)
        rows.append((L.t[ent], (X - e - cost) / risk, (e - Xf - cost) / risk, (tgt - e) / risk, side))
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    Ts = {m: {tf: TF(df, m, atr_df) for tf, df in B.items() if tf in ("M1", "M15", "H4")} for m in (False, True)}
    for target in ("HIGH", "2R"):
        for confirm2 in (False, True):
            rows = []
            for m in (False, True): rows += run(Ts[m], target, confirm2, -1 if m else 1)
            df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "side"])
            lab = f"target {'prior 4H high' if target == 'HIGH' else '2R'}, {'extra confirmation candle' if confirm2 else 'entry on the hold'}"
            if len(df) < 10: print(lab, "n", len(df)); continue
            df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
            print(f"{lab:52s} n={len(df):4d} ({len(df)/14.8:3.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} "
                  f"coin={df.R_flip.mean():+.3f} | L {df[df.side==1].R.mean():+.3f} S {df[df.side==-1].R.mean():+.3f} | <24 {df.R[IS].mean():+.3f} "
                  f"24+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} | rr {df.rr.median():.1f}", flush=True)
    print(f"done in {time.time() - t0:.0f}s")
