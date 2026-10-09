"""Exit grid for the Tokyo-sweep entry (SessionSetups_EA rule), gold M5 from M1 2012-2026.
Entry (as the EA): at 09:00 Tokyo set open; track the low; when (open - low) >= 1 x ATR(14, M5) and a 5-min bar closes
back above the open, inside 09:00-15:00 Tokyo and before the London open -> buy at that close (+ half spread).
Stop = min(low - 0.1 ATR, close - 0.5 ATR). One trade per day.
Exits tested: London open (live), targets 1/1.5/2/3R with time limits (London / NY 08:00 / NY 16:00 / 24h), hold to those
times with no target, wider stops (1.5x, 2x, 1 daily ATR), trailing 1R after +1R, breakeven at +1R.
Baseline: buy at the 09:00 Tokyo open every day with the same stop distance (median) and the same exits."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from gold_m1 import SPREAD_BY_YEAR, COMM, eu_dst_mask

def load_m5():
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")
    b = g[["open","high","low","close"]].resample("5min", label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    b["sp"] = b.index.year.map(SPREAD_BY_YEAR).astype(float)
    pc = b.close.shift(1); tr = pd.concat([b.high - b.low, (b.high - pc).abs(), (b.low - pc).abs()], axis=1).max(axis=1)
    b["atr"] = tr.ewm(alpha=1/14, adjust=False).mean()
    d = b.groupby(b.index.normalize()).agg(h=("high","max"), l=("low","min"), c=("close","last"))
    dpc = d.c.shift(1); dtr = pd.concat([d.h - d.l, (d.h - dpc).abs(), (d.l - dpc).abs()], axis=1).max(axis=1)
    b["datr"] = dtr.rolling(14).mean().shift(1).reindex(b.index.normalize()).values
    return b.dropna()

def events(b, sweep=True):
    """One entry per Tokyo day. Returns DataFrame(idx, entry, stop, day, ldn_i, ny8_i, ny16_i)."""
    t = b.index; o = b.open.values; h = b.high.values; l = b.low.values; c = b.close.values; a = b.atr.values
    utc_day = t.normalize(); mins = t.hour * 60 + t.minute
    bst = eu_dst_mask(t); ldn_open_min = np.where(bst, 7 * 60, 8 * 60)          # 08:00 London in UTC minutes
    nydst = np.zeros(len(t), bool)                                                # US DST: 2nd Sunday Mar .. 1st Sunday Nov
    for yr in np.unique(t.year):
        m = pd.Timestamp(yr, 3, 1); s = m + pd.Timedelta(days=(6 - m.weekday()) % 7 + 7) + pd.Timedelta(hours=7)
        n = pd.Timestamp(yr, 11, 1); e = n + pd.Timedelta(days=(6 - n.weekday()) % 7) + pd.Timedelta(hours=6)
        yy = t.year == yr; nydst[yy] = (t[yy] >= s) & (t[yy] < e)
    ny8 = np.where(nydst, 12 * 60, 13 * 60); ny16 = np.where(nydst, 20 * 60, 21 * 60)
    rows = []; starts = np.where((mins == 0) & (t.weekday < 5))[0]                # 00:00 UTC = 09:00 Tokyo
    for s0 in starts:
        day = utc_day[s0]; e_i = s0
        while e_i < len(t) and utc_day[e_i] == day: e_i += 1
        seg = slice(s0, e_i); tt = mins[s0:e_i]
        ldn_i = s0 + int(np.argmax(tt >= ldn_open_min[s0])) if (tt >= ldn_open_min[s0]).any() else e_i - 1
        ny8_i = s0 + int(np.argmax(tt >= ny8[s0])) if (tt >= ny8[s0]).any() else e_i - 1
        ny16_i = s0 + int(np.argmax(tt >= ny16[s0])) if (tt >= ny16[s0]).any() else e_i - 1
        op = o[s0]; lo = l[s0]; hit = None
        for i in range(s0, min(ldn_i, s0 + 72)):                                   # window 00:00-06:00 UTC (72 bars), before London
            lo = min(lo, l[i])
            if sweep:
                if op - lo >= 1.0 * a[i] and c[i] > op: hit = i; break
            else:
                hit = s0; break
        if hit is None: continue
        i = hit; entry = c[i] + b.sp.values[i] / 2
        stop = min(lo - 0.1 * a[i], c[i] - 0.5 * a[i]) if sweep else entry - 1.0 * a[i] * 4   # baseline: fixed 4 x M5 ATR (~median sweep stop)
        rows.append(dict(i=i, entry=entry, stop=stop, day=day, ldn=ldn_i, ny8=ny8_i, ny16=ny16_i, atr=a[i], datr=b.datr.values[i]))
    return pd.DataFrame(rows)

def simulate(b, ev, target_r=None, time_exit="ldn", stop_mult=1.0, stop_mode="sweep", trail=None, be=None):
    h = b.high.values; l = b.low.values; c = b.close.values; sp = b.sp.values; n = len(b); out = []
    for r in ev.itertuples():
        i = r.i; e = r.entry
        if stop_mode == "sweep": stop0 = e - (e - r.stop) * stop_mult
        elif stop_mode == "datr": stop0 = e - r.datr * stop_mult
        risk = e - stop0
        if risk <= 0: continue
        tgt = e + target_r * risk if target_r else None
        last = {"ldn": r.ldn, "ny8": r.ny8, "ny16": r.ny16, "24h": min(i + 288, n - 1)}[time_exit]
        stop = stop0; px = None; best = e
        for q in range(i + 1, last + 1):
            if l[q] <= stop: px = stop; why = "stop"; break
            if tgt is not None and h[q] >= tgt: px = tgt; why = "target"; break
            best = max(best, h[q])
            if trail is not None and best - e >= trail * risk: stop = max(stop, best - trail * risk)
            if be is not None and best - e >= be * risk: stop = max(stop, e)
        if px is None: px = c[last]; why = time_exit
        cost = sp[i] / 2 + COMM * e * 2
        out.append(dict(day=r.day, year=r.day.year, R=(px - e - cost) / risk, why=why, risk_atr=risk / r.datr))
    return pd.DataFrame(out)

def line(label, d):
    n = len(d); m = d.R.mean(); t = m / (d.R.std() / np.sqrt(n)); yrs = d.groupby("year").R.mean()
    h = n // 2
    return f"{label:44s} n={n:5d} avgR={m:+.3f} t={t:+.1f} win={np.mean(d.R>0):.0%} years>0 {int((yrs>0).sum())}/{len(yrs)} halves {d.R.iloc[:h].mean():+.3f}/{d.R.iloc[h:].mean():+.3f} 2024-26 {d[d.year>=2024].R.mean():+.3f}"

if __name__ == "__main__":
    b = load_m5(); ev = events(b, sweep=True); base = events(b, sweep=False)
    print(f"Tokyo sweep entries: {len(ev)}  (stop median {ev.eval('(entry-stop)').median():.1f} $, {(ev.entry-ev.stop).div(ev.datr).median():.2f} daily ATR)  | baseline buy-every-day entries: {len(base)}")
    grid = [
        ("LIVE: hold to London open, no target", dict(time_exit="ldn")),
        ("1R target, else London", dict(target_r=1.0, time_exit="ldn")),
        ("1.5R target, else London", dict(target_r=1.5, time_exit="ldn")),
        ("2R target, else London", dict(target_r=2.0, time_exit="ldn")),
        ("3R target, else London", dict(target_r=3.0, time_exit="ldn")),
        ("hold to NY 08:00, no target", dict(time_exit="ny8")),
        ("2R target, else NY 08:00", dict(target_r=2.0, time_exit="ny8")),
        ("3R target, else NY 08:00", dict(target_r=3.0, time_exit="ny8")),
        ("hold to NY 16:00, no target", dict(time_exit="ny16")),
        ("2R target, else NY 16:00", dict(target_r=2.0, time_exit="ny16")),
        ("3R target, else NY 16:00", dict(target_r=3.0, time_exit="ny16")),
        ("hold 24h, no target", dict(time_exit="24h")),
        ("3R target, else 24h", dict(target_r=3.0, time_exit="24h")),
        ("stop x1.5, hold to London", dict(stop_mult=1.5, time_exit="ldn")),
        ("stop x2, hold to London", dict(stop_mult=2.0, time_exit="ldn")),
        ("stop x2, 2R, else NY 16:00", dict(stop_mult=2.0, target_r=2.0, time_exit="ny16")),
        ("stop 1 daily ATR, 2R, else 24h", dict(stop_mode="datr", stop_mult=1.0, target_r=2.0, time_exit="24h")),
        ("stop 1 daily ATR, hold to NY 16:00", dict(stop_mode="datr", stop_mult=1.0, time_exit="ny16")),
        ("trail 1R after +1R, else NY 16:00", dict(trail=1.0, time_exit="ny16")),
        ("breakeven at +1R, 3R, else NY 16:00", dict(be=1.0, target_r=3.0, time_exit="ny16")),
    ]
    print("\n== Tokyo sweep entry ==")
    res = {}
    for label, kw in grid:
        d = simulate(b, ev, **kw); res[label] = d; print(line(label, d))
    print("\n== Baseline: buy at the 09:00 Tokyo open every day (no sweep), same exits ==")
    for label, kw in grid[:5] + grid[8:9] + grid[11:12]:
        print(line("  base " + label, simulate(b, base, **kw)))
    pd.to_pickle(res, "/home/claude/bt/exits_tokyo.pkl")
