"""Checks on the breaker-block cell of ob_strategies.py (4-hour, 2R): random-timing baseline (same side, same bracket in % of
price, random minutes — removes gold's drift), one-at-a-time neighbours of every setting, per-year results."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
import ob_strategies as O
from smc import pivots
from smc_grid import load, TF, exit_nb, tstat

B = load(); atr_df = B["D1"][["atr"]]
Ts = {m: {tf: TF(df, m, atr_df) for tf, df in B.items() if tf in ("M1", "H4", "H1")} for m in (False, True)}

def strat3x(T, tf, obs, rr=2.0, life=100, buf=0.05, choch=True, entry_mid=False, rand=0, seed=5):
    S, G = T[tf], T["M1"]; ph, pl = pivots(S.h, S.l, 3); sl = O.last_swing(S.l, pl, 3); rows = []; N = len(S.c)
    rng = np.random.default_rng(seed)
    for x in obs:
        bk = None
        for q in range(x["valid"], min(x["valid"] + life, N)):
            if S.c[q] < x["lo"]:
                bk = q if (not choch) or (np.isfinite(sl[q]) and S.c[q] < sl[q]) else None; break
        if bk is None: continue
        atr = S.atr[bk]
        if not np.isfinite(atr): continue
        stop = x["hi"] + buf * atr; lvl = (x["lo"] + x["hi"]) / 2 if entry_mid else x["lo"]; fill = None
        for r_ in range(bk + 1, min(bk + 1 + life, N)):
            if S.c[r_] > x["hi"]: break
            if S.h[r_] >= lvl: fill = r_; break
        if fill is None: continue
        e = max(lvl, S.o[fill])
        if stop <= e: continue
        r = O.trade(G, S.t[fill], e, stop, e - rr * (stop - e), -1, S.sp[fill], tf_fill=O.TF_MIN[tf] * O.NS, fill_level=e)
        if not r: continue
        rb = np.nan
        if rand:
            risk = stop - e; vals = []
            for r0 in rng.integers(0, len(G.t) - 5 * 1440, rand):
                e2 = G.o[r0]; rk = risk / e * e2
                X2 = exit_nb(G.h, G.l, G.c, r0, min(r0 + 5 * 1440, len(G.t)), e2 + rk, e2 - rr * rk, -1)
                vals.append((e2 - X2) / rk - (r[0] - r[0]))
            rb = np.mean(vals) - (S.sp[fill] / risk)
        rows.append((S.t[fill], r[0], r[1], rb))
    return rows

def obs_for(tf, n=3):
    raw = {m: O.find_obs(Ts[m][tf], n=n) for m in (False, True)}
    N = len(Ts[False][tf].c)
    return {m: O.lifetimes(raw[m], raw[not m], N) for m in (False, True)}

base_obs = {"H4": obs_for("H4"), "H1": obs_for("H1")}
cells = [("base H4 (n=3, buffer 0.05 ATR, life 100, 2R, edge entry, CHoCH)", "H4", {}, None),
         ("fractal n=2", "H4", {}, 2), ("fractal n=5", "H4", {}, 5), ("stop buffer 0", "H4", dict(buf=0.0), None),
         ("stop buffer 0.1 ATR", "H4", dict(buf=0.1), None), ("life 50 bars", "H4", dict(life=50), None),
         ("life 200 bars", "H4", dict(life=200), None), ("target 1.5R", "H4", dict(rr=1.5), None), ("target 3R", "H4", dict(rr=3.0), None),
         ("entry at the block's middle", "H4", dict(entry_mid=True), None), ("no change-of-character requirement", "H4", dict(choch=False), None)]
for lab, tf, kw, n in cells:
    ob = obs_for(tf, n) if n else base_obs[tf]
    rows = []
    for m in (False, True):
        rows += [r + (-1 if not m else 1,) for r in strat3x(Ts[m], tf, ob[m], rand=10 if lab.startswith("base") else 0, **kw)]
    df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "R_rand", "side"]); df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"
    extra = f" | random-timing same side {df.R_rand.mean():+.3f}" if lab.startswith("base") else ""
    print(f"{lab:62s} n={len(df):4d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} | longs {df[df.side==1].R.mean():+.3f} shorts {df[df.side==-1].R.mean():+.3f} "
          f"| <2024 {df.R[IS].mean():+.3f} 2024+ {df.R[~IS].mean():+.3f}{extra}", flush=True)
    if lab.startswith("base"):
        print("   by year:", " ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in df.groupby(df.t.dt.year).R.mean().items()))
