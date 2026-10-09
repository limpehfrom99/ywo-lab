"""Reddit (r/Daytrading, Oct 2026, 'How to become profitable: learn to trade liquidity', GBPUSD):
4H swing points = liquidity. When price trades back through a 4H swing (takes the stops), drop to 1H and wait for a 'breakdown':
a 1H close back on the other side of the level. Stop behind the sweep extreme; target the next opposing 4H swing; only take trades
with >= 1:2; move the stop to breakeven once the trade is going. ~2 setups a week.
Fixed here before running (the post is partly discretionary):
  4H swings = n-bar fractals (n = 3 and 5), usable only once confirmed (n 4H bars later); each swing traded once.
  Sweep = a 1H high above an unswept 4H swing high (mirror for lows). Trigger = first 1H close back below the swing level within
  12 hours; short at that close. Stop = sweep extreme + 0.05 daily ATR. Target = nearest confirmed unswept 4H swing low below
  (take only if reward/risk >= 2); variant: fixed 2R. Breakeven at +1R (variant: none). Time limit 5 days.
  Costs: spread + commission. Benchmark: coin flip at the same entries with the same stop/target distances."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from smc import pivots
from gold_m1 import SPREAD_BY_YEAR, COMM as GCOMM

def hourly(sym):
    if sym == "gold":
        g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")
        x = g[["open","high","low","close"]].resample("1h", label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
        x["sp"] = x.index.year.map(SPREAD_BY_YEAR).astype(float); comm = GCOMM
    else:
        d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0]); d = d[d.index >= "2021-09-15"]
        x = d[["open","high","low","close"]].resample("1h", label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
        x["sp"] = d.sp.resample("1h", label="left", closed="left").mean().reindex(x.index).ffill(); comm = 0.0
    dd = x.groupby(x.index.normalize()).agg(h=("high","max"), l=("low","min"), c=("close","last"))
    pc = dd.c.shift(1); atr = pd.concat([dd.h - dd.l, (dd.h - pc).abs(), (dd.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    x["datr"] = atr.reindex(x.index.normalize()).values
    return x.dropna(), comm

def setups(x, n):
    """Short setups in this frame (pass negated prices for longs). Returns list of (i_entry, entry, stop, swing_target_or_nan)."""
    h4 = x[["open","high","low","close"]].resample("4h", label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    ph, pl = pivots(h4.high.values, h4.low.values, n)
    conf_t = h4.index + pd.Timedelta(hours=4 * (n + 1))          # a swing is usable once the n following 4H bars have closed
    SH = sorted([(conf_t[i], h4.high.values[i]) for i in np.where(ph)[0]]); SL = sorted([(conf_t[i], h4.low.values[i]) for i in np.where(pl)[0]])
    t = x.index; H, L, C, A = x.high.values, x.low.values, x.close.values, x.datr.values
    out = []; active_h = []; active_l = []; ih = il = 0
    for i in range(len(x)):
        while ih < len(SH) and SH[ih][0] <= t[i]: active_h.append(SH[ih][1]); ih += 1
        while il < len(SL) and SL[il][0] <= t[i]: active_l.append(SL[il][1]); il += 1
        if not active_h: continue
        swept = [lv for lv in active_h if H[i] > lv]
        if not swept: continue
        active_h = [lv for lv in active_h if lv not in swept]
        lv = min(swept)                                           # the level just taken (nearest above the prior price)
        ext = H[i]; trig = None
        for q in range(i, min(i + 12, len(x))):
            ext = max(ext, H[q])
            if C[q] < lv: trig = q; break
        if trig is None: continue
        entry = C[trig]; stop = ext + 0.05 * A[trig]
        below = [s for s in active_l if s < entry]
        tgt = max(below) if below else np.nan                     # nearest opposing swing below the entry
        out.append((trig, entry, stop, tgt))
    return out

def simulate(x, S, comm, mirrored, target_mode="swing", be=True, random_dir=False, seed=0):
    rng = np.random.default_rng(seed); H, L, C, sp = x.high.values, x.low.values, x.close.values, x.sp.values
    if mirrored: H, L, C = -L, -H, -C
    R = []
    for (i, e, s, tgt) in S:
        risk = s - e                                               # short in this frame
        if risk <= 0: continue
        if target_mode == "swing":
            if not np.isfinite(tgt) or (e - tgt) / risk < 2: continue
            tp = tgt
        else: tp = e - 2.0 * risk
        d = -1
        if random_dir and rng.random() < 0.5:                      # flip: long with the same distances
            d = 1; s, tp = e - risk, e + (e - tp)
        stop = s; px = None
        for q in range(i + 1, min(i + 120, len(C))):
            if (d == -1 and H[q] >= stop) or (d == 1 and L[q] <= stop): px = stop; break
            if (d == -1 and L[q] <= tp) or (d == 1 and H[q] >= tp): px = tp; break
            if be and ((d == -1 and C[q] <= e - risk) or (d == 1 and C[q] >= e + risk)): stop = e
        if px is None: px = C[min(i + 119, len(C) - 1)]
        cost = sp[i] + comm * abs(e) * 2
        R.append((d * (px - e) - cost) / risk)
    return np.array(R)

if __name__ == "__main__":
    for sym in ("gold", "US100.cash", "US500.cash"):
        x, comm = hourly(sym)
        print(f"\n==== {sym} 1H {x.index[0].date()}..{x.index[-1].date()} ====")
        for n in (3, 5):
            Ss = setups(x, n); xm = x.copy(); xm[["high","low","open","close"]] = -x[["low","high","open","close"]].values
            Sl = setups(xm.rename(columns={}), n)
            for tmode in ("swing", "2R"):
                for be in (True, False):
                    R = np.concatenate([simulate(x, Ss, comm, False, tmode, be), simulate(x, Sl, comm, True, tmode, be)])
                    Rc = np.concatenate([np.concatenate([simulate(x, Ss, comm, False, tmode, be, True, k), simulate(x, Sl, comm, True, tmode, be, True, k)]) for k in range(10)])
                    if len(R) < 10: print(f"  n={n} target={tmode:5s} BE={be!s:5s} n_tr={len(R)}"); continue
                    yrs = len(x) / (24 * 260) if sym == "gold" else len(x) / (23 * 252)
                    print(f"  swings n={n} target={tmode:5s} BE={be!s:5s} trades={len(R):4d} ({len(R)/yrs:.0f}/yr) avgR={R.mean():+.3f} t={R.mean()/(R.std()/np.sqrt(len(R))):+.1f} win={np.mean(R>0):.0%} | coin flip {Rc.mean():+.3f}")
