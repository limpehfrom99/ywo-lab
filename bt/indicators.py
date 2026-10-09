"""Indicator-crossover grid with higher-timeframe filters. Fixed grid, every cell reported.
Signals on the entry timeframe (5m or 15m), long and short:
  ema9x21   EMA 9 crosses EMA 21          ema20x50  EMA 20 crosses EMA 50
  macd      MACD(12,26,9) crosses its signal line
  rsi       RSI(14) crosses back above 30 (long) / back below 70 (short)
Higher-timeframe filter: none | 1H EMA50 vs EMA200 (trade only with it) | 4H EMA50 vs EMA200 (completed bars only).
Stop: 2 x ATR(14) of the entry timeframe, or 0.5 x daily ATR. Targets 1R / 2R / 3R, or exit at the opposite signal;
time limit 8 hours. Entry at the signal bar's close + half spread; costs = spread + commission.
Baselines: the same cells with a coin-flip direction (random_dir) — the no-information benchmark.
Run: python3 indicators.py gold|TSLA|US100|US500|AAPL"""
import sys, numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv
sys.path.insert(0, "/home/claude/bt")
from gold_m1 import SPREAD_BY_YEAR, COMM as GCOMM

COMMS = {"gold": GCOMM, "TSLA": 0.00002, "AAPL": 0.00002, "US100": 0.0, "US500": 0.0}

def load(sym):
    if sym == "gold":
        g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl").loc["2014-01-01":]
        b = g[["open","high","low","close"]].resample("5min", label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
        b["sp"] = b.index.year.map(SPREAD_BY_YEAR).astype(float)
    else:
        b = pd.read_pickle(f"/home/claude/data/{sym}_m5.pkl")[["open","high","low","close","sp"]].copy()
    d = b.groupby(b.index.normalize()).agg(h=("high","max"), l=("low","min"), c=("close","last"))
    dpc = d.c.shift(1); dtr = pd.concat([d.h - d.l, (d.h - dpc).abs(), (d.l - dpc).abs()], axis=1).max(axis=1)
    b["datr"] = dtr.rolling(14).mean().shift(1).reindex(b.index.normalize()).values
    return b.dropna()

def resample(b, rule):
    x = b[["open","high","low","close"]].resample(rule, label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    x["sp"] = b.sp.resample(rule, label="left", closed="left").mean().reindex(x.index).ffill()
    x["datr"] = b.datr.resample(rule, label="left", closed="left").last().reindex(x.index).ffill()
    return x

def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); dn = (-d).clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))

def signals(x):
    c = x.close; out = {}
    f, s = ema(c, 9), ema(c, 21); up = (f > s) & (f.shift(1) <= s.shift(1)); dn = (f < s) & (f.shift(1) >= s.shift(1)); out["ema9x21"] = (up, dn)
    f, s = ema(c, 20), ema(c, 50); up = (f > s) & (f.shift(1) <= s.shift(1)); dn = (f < s) & (f.shift(1) >= s.shift(1)); out["ema20x50"] = (up, dn)
    m = ema(c, 12) - ema(c, 26); sg = ema(m, 9); up = (m > sg) & (m.shift(1) <= sg.shift(1)); dn = (m < sg) & (m.shift(1) >= sg.shift(1)); out["macd"] = (up, dn)
    r = rsi(c); up = (r > 30) & (r.shift(1) <= 30); dn = (r < 70) & (r.shift(1) >= 70); out["rsi"] = (up, dn)
    return out

def htf_filter(x, b, rule):
    h = b.close.resample(rule, label="left", closed="left").last().dropna()
    tr = np.sign(ema(h, 50) - ema(h, 200)).shift(1)                 # completed HTF bars only
    return tr.reindex(x.index, method="ffill").fillna(0).values

def simulate(x, idx, direction, stop_dist, target_r, H, opp_next=None, comm=0.0, random_dir=False, seed=0, day_end=None):
    """Vectorised: windows of H bars after each event. Returns R per trade (planned risk) after costs."""
    hi, lo, cl, sp = x.high.values, x.low.values, x.close.values, x.sp.values
    n = len(x); idx = idx[idx + H < n]; direction = direction[:len(idx)]; stop_dist = stop_dist[:len(idx)]
    if random_dir: direction = np.where(np.random.default_rng(seed).random(len(idx)) < 0.5, 1, -1)
    Wh = swv(hi, H)[idx + 1]; Wl = swv(lo, H)[idx + 1]; Wc = swv(cl, H)[idx + 1]       # bars i+1 .. i+H
    entry = cl[idx] + direction * sp[idx] / 2
    stop = entry - direction * stop_dist; tgt = entry + direction * target_r * stop_dist if target_r else None
    # in 'long frame': y = direction * price
    yl = np.where(direction[:, None] == 1, Wl, -Wh); yh = np.where(direction[:, None] == 1, Wh, -Wl); yc = direction[:, None] * Wc
    ye = direction * entry; ys = direction * stop
    hs = np.where((yl <= ys[:, None]).any(1), np.argmax(yl <= ys[:, None], 1), H)
    if tgt is not None:
        yt = direction * tgt; ht = np.where((yh >= yt[:, None]).any(1), np.argmax(yh >= yt[:, None], 1), H)
    else: ht = np.full(len(idx), H)
    limit = np.full(len(idx), H - 1)
    if day_end is not None:
        limit = np.minimum(limit, np.clip(day_end[:len(idx)] - idx - 1, 0, H - 1))
    if opp_next is not None:
        limit = np.minimum(limit, np.clip(opp_next[:len(idx)] - idx - 1, 0, H - 1))
    by_stop = (hs <= limit) & (hs <= ht)
    by_tgt = (ht <= limit) & (ht < hs)
    yt_arr = direction * tgt if tgt is not None else ys
    px = np.where(by_stop, ys, np.where(by_tgt, yt_arr, yc[np.arange(len(idx)), limit]))
    why = np.where(by_stop, "stop", np.where(by_tgt, "target", "time"))
    cost = sp[idx] / 2 + comm * entry * 2
    R = (px - ye - cost) / stop_dist
    return R, why

def run(sym):
    b = load(sym); comm = COMMS[sym]; rows = []
    for tf, rule, H in (("5m", "5min", 96), ("15m", "15min", 32)):
        x = b if tf == "5m" else resample(b, rule)
        pc = x.close.shift(1); tr = pd.concat([x.high - x.low, (x.high - pc).abs(), (x.low - pc).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/14, adjust=False).mean().values
        sig = signals(x); filt = {"none": np.ones(len(x)), "1H": htf_filter(x, b, "1h"), "4H": htf_filter(x, b, "4h")}
        for sname, (up, dn) in sig.items():
            up_i = np.where(up.values)[0]; dn_i = np.where(dn.values)[0]
            for fname, fv in filt.items():
                ui = up_i[fv[up_i] >= (1 if fname != "none" else -1)]; di = dn_i[fv[dn_i] <= (-1 if fname != "none" else 1)]
                idx = np.concatenate([ui, di]); dirs = np.concatenate([np.ones(len(ui), int), -np.ones(len(di), int)])
                order = np.argsort(idx); idx, dirs = idx[order], dirs[order]
                # next opposite signal for 'exit on opposite cross'
                all_up, all_dn = np.sort(up_i), np.sort(dn_i)
                nxt = np.where(dirs == 1, all_dn[np.minimum(np.searchsorted(all_dn, idx, side="right"), len(all_dn) - 1)] if len(all_dn) else len(x),
                               all_up[np.minimum(np.searchsorted(all_up, idx, side="right"), len(all_up) - 1)] if len(all_up) else len(x))
                days = x.index.normalize().values; last_of_day = np.r_[np.where(days[1:] != days[:-1])[0], len(x) - 1]
                dend = last_of_day[np.searchsorted(last_of_day, idx)]
                for smode in ("2xATR", "0.5dATR"):
                    sd = 2 * atr[idx] if smode == "2xATR" else 0.5 * x.datr.values[idx]
                    ok = np.isfinite(sd) & (sd > 0); idx2, d2, sd2, nx2, de2 = idx[ok], dirs[ok], sd[ok], nxt[ok], dend[ok]
                    for ex in ("1R", "2R", "3R", "opp"):
                        tr_ = {"1R": 1.0, "2R": 2.0, "3R": 3.0, "opp": None}[ex]
                        R, why = simulate(x, idx2, d2, sd2, tr_, H, opp_next=nx2 if ex == "opp" else None, comm=comm, day_end=de2)
                        Rr, _ = simulate(x, idx2, d2, sd2, tr_, H, opp_next=nx2 if ex == "opp" else None, comm=comm, random_dir=True, day_end=de2)
                        yrs = pd.Series(R, index=x.index[idx2[:len(R)]]); by = yrs.groupby(yrs.index.year).mean()
                        hlf = len(R) // 2
                        rows.append(dict(sym=sym, tf=tf, signal=sname, htf=fname, stop=smode, exit=ex, n=len(R), avgR=R.mean(), excess=R.mean() - Rr.mean(),
                                         t=R.mean() / (R.std() / np.sqrt(len(R))), win=np.mean(R > 0), h1=R[:hlf].mean(), h2=R[hlf:].mean(),
                                         years_pos=f"{int((by>0).sum())}/{len(by)}", coin=Rr.mean(), longs=R[d2[:len(R)] == 1].mean(), shorts=R[d2[:len(R)] == -1].mean()))
    df = pd.DataFrame(rows); df.to_csv(f"/home/claude/bt/indicators_{sym}.csv", index=False)
    return df

if __name__ == "__main__":
    sym = sys.argv[1]; df = run(sym)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    print(f"{sym}: {len(df)} cells; cells with avgR > 0: {int((df.avgR > 0).sum())}; with avgR >= 0.05 and t >= 2 and both halves > 0: {int(((df.avgR >= 0.05) & (df.t >= 2) & (df.h1 > 0) & (df.h2 > 0)).sum())}")
    print(df.sort_values("avgR", ascending=False).head(12).round(3).to_string(index=False))
    print("...")
    print(df.sort_values("avgR").head(5).round(3).to_string(index=False))
    print("by signal:", df.groupby("signal").avgR.mean().round(3).to_dict(), "| by htf:", df.groupby("htf").avgR.mean().round(3).to_dict())
    print("by exit:", df.groupby("exit").avgR.mean().round(3).to_dict(), "| by stop:", df.groupby("stop").avgR.mean().round(3).to_dict(), "| coin-flip mean:", round(df.coin.mean(), 3))
