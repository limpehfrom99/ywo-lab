"""RedNote "Trading Dimsum", "5:1 Reward to Risk Ratio" (45-second video, FX chart). Rule as told (short; longs mirrored):
  a strong drop leaves a bearish fair value gap (FVG) and breaks structure (BOS, takes the equal lows); price comes back up to the
  gap along a rising trendline ("trendline liquidity": retail buys the trendline, stops sit under it); sell when price touches
  the gap, stop at the high, target the liquidity under the trendline -> "a nice 5:1".
Fixed here before running:
  swings = 3-bar fractals usable 3 bars later. BOS = a close below the last swing low (each swing low used once). The leg = from
  the highest high since the last swing high to the BOS bar; its first bearish FVG (high[k] < low[k-2], k up to 3 bars after the
  BOS) is the gap. Stop = the leg's high + 0.05 daily ATR. Entry = sell limit at the gap's lower edge, valid 48 bars; cancelled
  if price trades above the leg high first.
  Targets: T1 = the last confirmed swing low made during the pullback (the trendline's last touch); T2 = fixed 5R (the claim);
  T3 = the low after the BOS. T1/T3 only if reward/risk >= 2.
  Exits on 1-minute bars (stop first if one minute touches both), max 5 days. FTMO gold spread by year + commission.
  Timeframes 15-min and 1-hour; gold 2012 - Oct 2026 (the poster's FX pairs come with the full export).
Baseline: coin flip per trade (same entry, other side, same distances)."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, exit_nb, TF_MIN, tstat
from gold_m1 import COMM


def setups(S, n=3, max_leg=60):
    """Short setups in this frame. Returns (bos_i, fvg_bot, fvg_top, leg_high, fvg_k)."""
    h, l, c = S.h, S.l, S.c; N = len(c); ph, pl = pivots(h, l, n)
    out = []; SL = None; SL_used = True; SH_i = None
    for i in range(N):
        j = i - 1 - n
        if j >= 0:
            if pl[j]: SL, SL_used = l[j], False
            if ph[j]: SH_i = j
        if SL is None or SL_used or c[i] >= SL: continue
        SL_used = True
        a = SH_i if SH_i is not None and i - SH_i <= max_leg else max(0, i - max_leg)
        top_i = a + int(np.argmax(h[a:i + 1])); leg_high = h[top_i]
        for k in range(top_i + 2, min(i + 4, N)):
            if h[k] < l[k - 2]:
                out.append((i, h[k], l[k - 2], leg_high, k)); break
    return out


def run(T, tfname, target, mirror_sign, n=3, buf=0.05, window=48, min_rr=2.0, entry_mid=False, rand_base=0, seed=1):
    S, G = T[tfname], T["M1"]; ph, pl = pivots(S.h, S.l, n); rng = np.random.default_rng(seed)
    rows = []; ns = TF_MIN[tfname] * 60_000_000_000
    for bos_i, bot, top, leg_high, k in setups(S, n=n):
        a = max(bos_i, k) + 1; b = min(a + window, len(S.c))
        atr = S.atr[min(a, len(S.c) - 1)]
        if not np.isfinite(atr) or a >= len(S.c): continue
        stop = leg_high + buf * atr; ent = (bot + top) / 2 if entry_mid else bot; post_low = S.l[bos_i:a].min(); last_pl = None; fill = None
        for m in range(a, b):
            q = m - 1 - n                                                # pivot lows confirmed before bar m
            if q > bos_i and pl[q]: last_pl = S.l[q]
            if S.h[m] >= stop: break                                     # ran through the high first: no trade
            if S.h[m] >= ent:
                e = max(ent, S.o[m]); fill = m; break
            post_low = min(post_low, S.l[m])
        if fill is None: continue
        risk = stop - e
        if risk <= 0: continue
        if target == "T2": tgt = e - 5 * risk
        elif target == "T1": tgt = last_pl if last_pl is not None else post_low
        else: tgt = post_low
        rr = (e - tgt) / risk
        if target != "T2" and rr < min_rr: continue
        # fill minute inside the bar: first 1-minute bar whose high reaches the entry (in this frame shorts are 'down')
        i0 = np.searchsorted(G.t, S.t[fill]); i_end = np.searchsorted(G.t, S.t[fill] + np.timedelta64(ns, "ns"))
        w = np.flatnonzero(G.h[i0:i_end] >= e); i0 = i0 + (w[0] if len(w) else 0)
        i1 = min(i0 + 5 * 1440, len(G.t))
        X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, -1)               # short in this frame
        cost = S.sp[fill] + COMM * (abs(e) + abs(X))
        Xf = exit_nb(G.h, G.l, G.c, i0, i1, e - risk, e + (e - tgt), 1)  # coin flip: long, same distances
        rb = np.nan
        if rand_base:                                                    # same side and bracket (in % of price) from random minutes
            vals = []
            for r0 in rng.integers(0, len(G.t) - 5 * 1440, rand_base):
                e2 = G.o[r0]; rk = risk / e * e2
                X2 = exit_nb(G.h, G.l, G.c, r0, min(r0 + 5 * 1440, len(G.t)), e2 + rk, e2 - rr * rk, -1)
                vals.append((e2 - X2 - cost / risk * rk) / rk)
            rb = np.mean(vals)
        rows.append((S.t[fill], (e - X - cost) / risk, (Xf - e - cost) / risk, rr, risk / abs(e) * 100, -mirror_sign, rb))
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    res = {}
    for mirror in (False, True):
        T = {tf: TF(df, mirror, atr_df) for tf, df in B.items() if tf in ("M1", "M15", "H1")}
        for tfname in ("M15", "H1"):
            for target in ("T1", "T2", "T3"):
                res.setdefault((tfname, target), []).extend(run(T, tfname, target, -1 if mirror else 1))
        print(f"{'longs' if mirror else 'shorts'} done {time.time() - t0:.0f}s", flush=True)
    for (tfname, target), rows in res.items():
        df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "risk_pct", "side", "R_rand"]); df["t"] = pd.to_datetime(df.t)
        IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
        lab = {"T1": "target = last pullback low (trendline)", "T2": "target = fixed 5R (the claim)", "T3": "target = low after the BOS"}[target]
        print(f"{tfname:3s} {lab:40s} n={len(df):5d} ({len(df)/14.8:5.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} "
              f"win={np.mean(df.R > 0):.0%} coin={df.R_flip.mean():+.3f} | shorts {df[df.side==-1].R.mean():+.3f} longs {df[df.side==1].R.mean():+.3f} "
              f"| before 2024 {df.R[IS].mean():+.3f} from 2024 {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} | med rr {df.rr.median():.1f} stop {df.risk_pct.median():.2f}%")
