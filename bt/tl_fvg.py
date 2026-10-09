"""RedNote "阿基米得": "趋势线破位后，FVG就是天然压力位" (after a trendline breaks, the FVG is natural resistance). Silent 28-second video;
rules read from the frames: an uptrend with a rising trendline; price closes below the line and the break leaves a bearish FVG;
price comes back to the gap -> sell; stop just above the gap (0.15% in the example); target ~2.5R (example 2.48R). The mirror
for longs (falling trendline broken upward, bullish FVG retest; the example's second trade: 4.52R).
Fixed before running:
  trendline = line through the last two confirmed 3-bar swing lows when the second is higher (usable 3 bars after each pivot),
  with no close below it since the first point. Break = the first close below the line. The gap = the first bearish FVG
  (high[k] < low[k-2]) from the leg's high (highest high since the second swing low) to 3 bars after the break.
  Entry = sell limit at the gap's lower edge within 48 bars after the gap forms, cancelled if price takes the leg high first.
  Stop S1 = gap top + 0.05 daily ATR (the video's tight stop); S2 = leg high + 0.05 daily ATR.
  Target = fixed 2R / 3R, or (S2 only) the last pullback swing low if >= 2R (as in #33).
  Exits on 1-minute bars (stop first), 5-day max; gold 2012 - Oct 2026; FTMO spread + commission. Coin flip per trade."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from smc_grid import load, TF, exit_nb, TF_MIN, tstat
from gold_m1 import COMM


def setups(S, n=3, max_leg=80):
    h, l, c = S.h, S.l, S.c; N = len(c); ph, pl = pivots(h, l, n)
    lows = []; out = []; broken_for = None
    for i in range(N):
        j = i - 1 - n
        if j >= 0 and pl[j]: lows.append(j)
        if len(lows) < 2: continue
        p1, p2 = lows[-2], lows[-1]
        if l[p2] <= l[p1] or (broken_for == (p1, p2)) or i - p2 > max_leg: continue
        slope = (l[p2] - l[p1]) / (p2 - p1)
        line = l[p2] + slope * (i - p2)
        if c[i] < line:
            broken_for = (p1, p2)
            # the line must have held until now (no earlier close below it since p1)
            seg = np.arange(p1, i); held = np.all(c[seg] >= l[p2] + slope * (seg - p2) - 1e-12)
            if not held: continue
            top_i = p2 + int(np.argmax(h[p2:i + 1])); leg_high = h[top_i]
            for k in range(top_i + 2, min(i + 4, N)):
                if h[k] < l[k - 2]:
                    out.append((i, h[k], l[k - 2], leg_high, k)); break
    return out


def run(T, tfname, stop_mode, target, mirror_sign):
    S, G = T[tfname], T["M1"]; ph, pl = pivots(S.h, S.l, 3)
    rows = []; ns = TF_MIN[tfname] * 60_000_000_000
    for brk, bot, top, leg_high, k in setups(S):
        a = max(brk, k) + 1; b = min(a + 48, len(S.c))
        if a >= len(S.c): continue
        atr = S.atr[a]
        if not np.isfinite(atr): continue
        stop = (top if stop_mode == "S1" else leg_high) + 0.05 * atr
        post_low = S.l[brk:a].min(); last_pl = None; fill = None
        for m in range(a, b):
            q = m - 4
            if q > brk and pl[q]: last_pl = S.l[q]
            if S.h[m] >= leg_high + 0.05 * atr: break
            if S.h[m] >= bot:
                e = max(bot, S.o[m]); fill = m; break
            post_low = min(post_low, S.l[m])
        if fill is None: continue
        risk = stop - e
        if risk <= 0: continue
        if target == "T1":
            tgt = last_pl if last_pl is not None else post_low
            if (e - tgt) / risk < 2: continue
        else:
            tgt = e - float(target[0]) * risk
        i0 = np.searchsorted(G.t, S.t[fill]); i_end = np.searchsorted(G.t, S.t[fill] + np.timedelta64(ns, "ns"))
        w = np.flatnonzero(G.h[i0:i_end] >= e); i0 = i0 + (w[0] if len(w) else 0); i1 = min(i0 + 5 * 1440, len(G.t))
        X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, -1)
        cost = S.sp[fill] + COMM * (abs(e) + abs(X))
        Xf = exit_nb(G.h, G.l, G.c, i0, i1, e - risk, e + (e - tgt), 1)
        rows.append((S.t[fill], (e - X - cost) / risk, (Xf - e - cost) / risk, (e - tgt) / risk, risk / abs(e) * 100, -mirror_sign))
    return rows


if __name__ == "__main__":
    t0 = time.time(); B = load(); atr_df = B["D1"][["atr"]]
    cells = [(tf, s, t) for tf in ("M15", "H1") for s in ("S1", "S2") for t in ("2R", "3R")] + [("M15", "S2", "T1"), ("H1", "S2", "T1")]
    res = {}
    for mirror in (False, True):
        T = {tf: TF(df, mirror, atr_df) for tf, df in B.items() if tf in ("M1", "M15", "H1")}
        for c in cells: res.setdefault(c, []).extend(run(T, *c, -1 if mirror else 1))
    print(f"done in {time.time() - t0:.0f}s")
    for (tf, s, t), rows in res.items():
        df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "risk_pct", "side"]); df["t"] = pd.to_datetime(df.t)
        if len(df) < 10: print(tf, s, t, "n", len(df)); continue
        IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
        lab = {"S1": "stop above the gap", "S2": "stop above the leg high"}[s] + ", " + {"2R": "target 2R", "3R": "target 3R", "T1": "target last pullback low"}[t]
        print(f"{tf:3s} {lab:46s} n={len(df):5d} ({len(df)/14.8:4.0f}/yr) avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} "
              f"coin={df.R_flip.mean():+.3f} | shorts {df[df.side==-1].R.mean():+.3f} longs {df[df.side==1].R.mean():+.3f} | <2024 {df.R[IS].mean():+.3f} "
              f"2024+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)} | stop {df.risk_pct.median():.2f}%")
