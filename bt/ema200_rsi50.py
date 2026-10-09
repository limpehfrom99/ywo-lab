"""Reddit (r/Daytrading, '15 years trading indices'): trade only in the direction of the 1-hour 200 EMA; enter when RSI(14) crosses 50
(long above / short below). S/R marking is discretionary and the post gives no stop or exit, so fixed here before running:
stop 1.5 x ATR(14) of the signal timeframe, targets 1R / 2R / 3R, time limit 24 bars (1H) or 32 bars (15m). Signal on 1H, and on 15m
with the 1H 200-EMA filter. Costs: spread + commission. Benchmark: coin flip at the same entries."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from indicators import simulate, rsi, ema
from gold_m1 import SPREAD_BY_YEAR, COMM as GCOMM

def bars(sym, rule):
    if sym == "gold":
        g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl").loc["2014-01-01":]
        x = g[["open","high","low","close"]].resample(rule, label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
        x["sp"] = x.index.year.map(SPREAD_BY_YEAR).astype(float); return x, GCOMM
    pat = {"US100": "US100.cash_M30", "US500": "US500.cash_M30", "TSLA": "TSLA_M30"}[sym]
    d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0]); d = d[d.index >= "2021-09-15"]
    x = d[["open","high","low","close"]].resample(rule, label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    x["sp"] = d.sp.resample(rule, label="left", closed="left").mean().reindex(x.index).ffill()
    return x, (0.00002 if sym == "TSLA" else 0.0)

def run(sym):
    h1, comm = bars(sym, "1h"); trend = np.sign(h1.close - ema(h1.close, 200))
    for tf, rule, H in (("1H", "1h", 24), ("15m", "15min", 32)):
        x = h1 if tf == "1H" else bars(sym, rule)[0]
        tr_ = trend.shift(1).reindex(x.index, method="ffill").fillna(0).values if tf == "15m" else trend.values
        r = rsi(x.close, 14); up = ((r > 50) & (r.shift(1) <= 50)).values; dn = ((r < 50) & (r.shift(1) >= 50)).values
        pc = x.close.shift(1); atr = pd.concat([x.high - x.low, (x.high - pc).abs(), (x.low - pc).abs()], axis=1).max(axis=1).ewm(alpha=1/14, adjust=False).mean().values
        li = np.where(up & (tr_ > 0))[0]; si = np.where(dn & (tr_ < 0))[0]
        idx = np.concatenate([li, si]); dirs = np.concatenate([np.ones(len(li), int), -np.ones(len(si), int)]); o = np.argsort(idx); idx, dirs = idx[o], dirs[o]
        idx, dirs = idx[idx > 220], dirs[idx > 220]
        for tgt in (1.0, 2.0, 3.0):
            R, _ = simulate(x, idx, dirs, 1.5 * atr[idx], tgt, H, comm=comm)
            Rc, _ = simulate(x, idx, dirs, 1.5 * atr[idx], tgt, H, comm=comm, random_dir=True)
            yrs = pd.Series(R, index=x.index[idx[:len(R)]]); by = yrs.groupby(yrs.index.year).mean(); h = len(R) // 2
            print(f"{sym:5s} {tf:3s} {tgt:.0f}R  n={len(R):5d} avgR={R.mean():+.3f} t={R.mean()/(R.std()/np.sqrt(len(R))):+.1f} win={np.mean(R>0):.0%} "
                  f"years>0 {int((by>0).sum())}/{len(by)} halves {R[:h].mean():+.3f}/{R[h:].mean():+.3f} | coin flip {Rc.mean():+.3f}")

for s in ("gold", "US100", "US500", "TSLA"): run(s)
