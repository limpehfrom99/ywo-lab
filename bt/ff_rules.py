"""Forex Factory rules, tested as written (nothing invented beyond the noted parameter choices).
A. HoLo (thread 590623): lines = highest / lowest 1-hour OPEN of the broker day (17:00 NY start). After an M15 bar has
   opened beyond a line, fade the first return to it (sell at the highest-open line, buy at the lowest-open line),
   08:00-12:00 NY. SL = day high / day low at entry. Management: at +0.07 ATR -> stop to BE+0.015 ATR; at +0.14 ATR ->
   stop to BE+0.07 ATR then trail 0.14 ATR behind the best price ("+5 pips / +10 pips" scaled to a daily ATR). Time exit 16:00 NY.
B. Trading Made Simple(r) 1:1 learner (thread 917569): long when HMA12 crosses above EMA5(shift 2) and is rising, HA candle
   bullish, Stoch(8,3,3) and Stoch(14,3,3) > 50, RSI14 > 50, previous bar closed up; enter at the close of the first
   qualifying bar within 3 bars of the cross. SL = low of 2 bars back; TP = same distance (1:1). Mirror for shorts.
C. NY open-range breakout gold, version B (thread 1388244): range = first five 1-min candles 09:30-09:34 NY. First 1-min
   candle by 09:45 closing >= 0.5 ATR(5) outside the range with body >= 0.8 ATR(5), body >= 60% of its range and volume >
   previous candle: buy-stop at its high (sell-stop at its low), filled by 09:50 or cancelled. SL = other side of that
   candle. Exits: (i) 1.5R, (ii) 2.5R, (iii) author's scale-out 50% at 1.5R (SL->BE), 30% at 2.5R (SL->+0.5R), 20% trailed
   0.8 ATR(5); all with a 12:00 NY time exit.
D. Wicks get filled (thread 1374880), M15 and M30 gold: after an up candle with an upper wick, in the next candle wait for
   price to trade below the open first, then buy-stop at the previous close; TP = previous high (wick filled), SL = 1:1.
   Cancelled if not filled within that candle. Mirror for down candles.
Costs: spread by year + commission. Benchmarks: coin flip at the same entries (same stops/targets)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from gold_m1 import SPREAD_BY_YEAR, COMM

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))
def line(label, R, years=None, why=None):
    R = np.asarray(R); n = len(R)
    if n == 0: return f"{label:48s} n=0"
    s = f"{label:48s} n={n:5d} avgR={R.mean():+.3f} t={t(R):+.1f} win={np.mean(R>0):.0%}"
    if years is not None:
        by = pd.Series(R).groupby(np.asarray(years)).mean(); s += f" years>0 {int((by>0).sum())}/{len(by)} halves {R[:n//2].mean():+.3f}/{R[n//2:].mean():+.3f}"
    return s

def gold_m1():
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl").loc["2012-01-01":].copy()
    ny = g.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    g["nym"] = ny.hour * 60 + ny.minute; g["nyd"] = ny.normalize()
    g["bday"] = (ny + pd.Timedelta(hours=7)).normalize()                      # broker day starts 17:00 NY
    d = g.groupby("nyd").agg(h=("high","max"), l=("low","min"), c=("close","last"))
    pc = d.c.shift(1); tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    g["datr"] = tr.rolling(14).mean().shift(1).reindex(g.nyd).values
    return g.dropna()

# ---------------------------------------------------------------- A. HoLo
def holo(g, confirm=True, random_dir=False, seed=0):
    rng = np.random.default_rng(seed); rows = []
    o, h, l, c, sp, nym, datr = (g[k].values for k in ("open","high","low","close","sp","nym","datr"))
    hr_open = (g.index.minute == 0); q_open = (g.index.minute % 15 == 0)
    for bday, ix in g.groupby("bday").indices.items():
        a0, a1 = ix[0], ix[-1]
        if a1 - a0 < 600: continue
        hi_line = -np.inf; lo_line = np.inf; dayh = -np.inf; dayl = np.inf
        pen_up = pen_dn = False; done_s = done_b = False; A = datr[a0]
        i = a0
        while i <= a1:
            if hr_open[i]: hi_line = max(hi_line, o[i]); lo_line = min(lo_line, o[i]); pen_up = pen_dn = False if False else pen_up
            dayh = max(dayh, h[i]); dayl = min(dayl, l[i])
            if q_open[i] and np.isfinite(hi_line):
                if o[i] > hi_line: pen_up = True
                if o[i] < lo_line: pen_dn = True
            inwin = 480 <= nym[i] < 720
            side = 0
            if inwin and not done_s and (pen_up or not confirm) and np.isfinite(hi_line) and c[i-1] > hi_line and l[i] <= hi_line: side = -1; done_s = True; lvl = hi_line
            elif inwin and not done_b and (pen_dn or not confirm) and np.isfinite(lo_line) and c[i-1] < lo_line and h[i] >= lo_line: side = 1; done_b = True; lvl = lo_line
            if side:
                if random_dir: side = 1 if rng.random() < 0.5 else -1
                e = lvl + side * sp[i] / 2; stop = dayl if side == 1 else dayh
                if side * (e - stop) <= 0: stop = e - side * 0.5 * A
                risk = side * (e - stop); best = e; px = None
                for q in range(i + 1, a1 + 1):
                    if nym[q] >= 960: px = c[q]; why = "time"; break
                    if side == 1 and l[q] <= stop or side == -1 and h[q] >= stop: px = stop; why = "stop"; break
                    best = max(best, h[q]) if side == 1 else min(best, l[q]); fav = side * (best - e)
                    if fav >= 0.14 * A: stop = max(stop, best - side * 0.14 * A) if side == 1 else min(stop, best + 0.14 * A); stop = max(stop, e + side * 0.07 * A) if side == 1 else min(stop, e - 0.07 * A)
                    elif fav >= 0.07 * A: stop = max(stop, e + 0.015 * A) if side == 1 else min(stop, e - 0.015 * A)
                if px is None: px = c[a1]; why = "end"
                cost = sp[i] / 2 + COMM * e * 2
                rows.append(dict(year=g.index[i].year, side=side, R=(side * (px - e) - cost) / risk, why=why, risk_atr=risk / A))
                i = q
            i += 1
    return pd.DataFrame(rows)

# ---------------------------------------------------------------- B. TMS(r)
def wma(s, n):
    w = np.arange(1, n + 1); return s.rolling(n).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)
def hma(s, n): return wma(2 * wma(s, n // 2) - wma(s, n), int(np.sqrt(n)))
def stoch(x, k, d, s):
    lo = x.low.rolling(k).min(); hi = x.high.rolling(k).max(); fast = 100 * (x.close - lo) / (hi - lo).replace(0, np.nan)
    return fast.rolling(s).mean().rolling(d).mean()
def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); dn = (-d).clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))
def tms(x, comm, random_dir=False, seed=0):
    c = x.close; e5 = c.ewm(span=5, adjust=False).mean().shift(2); hm = hma(c, 12)
    ha_c = (x.open + x.high + x.low + x.close) / 4; ha_o = ha_c.copy()
    ha_o.iloc[0] = x.open.iloc[0]
    hao = ha_o.values.copy(); hac = ha_c.values.copy(); xo = x.open.values
    for i in range(1, len(x)): hao[i] = (hao[i-1] + hac[i-1]) / 2
    ha_bull = pd.Series(hac > hao, index=x.index)
    s8 = stoch(x, 8, 3, 3); s14 = stoch(x, 14, 3, 3); r = rsi(c); up_bar = (c > x.open)
    cross_up = (hm > e5) & (hm.shift(1) <= e5.shift(1)); cross_dn = (hm < e5) & (hm.shift(1) >= e5.shift(1))
    long_ok = (hm > e5) & (hm > hm.shift(1)) & ha_bull & (s8 > 50) & (s14 > 50) & (r > 50) & up_bar.shift(1).fillna(False)
    short_ok = (hm < e5) & (hm < hm.shift(1)) & ~ha_bull & (s8 < 50) & (s14 < 50) & (r < 50) & (~up_bar).shift(1).fillna(False)
    h = x.high.values; l = x.low.values; cl = c.values; sp = x.sp.values; rng = np.random.default_rng(seed); rows = []
    for side, cross, ok in ((1, cross_up.values, long_ok.values), (-1, cross_dn.values, short_ok.values)):
        for i0 in np.where(cross)[0]:
            for i in range(i0, min(i0 + 3, len(x) - 1)):
                if ok[i]:
                    sd = side if not random_dir else (1 if rng.random() < 0.5 else -1)
                    e = cl[i] + sd * sp[i] / 2; stop = l[i-2] if sd == 1 else h[i-2]; risk = sd * (e - stop)
                    if risk <= 0: break
                    tgt = e + sd * risk; px = None
                    for q in range(i + 1, min(i + 200, len(x))):
                        if (sd == 1 and l[q] <= stop) or (sd == -1 and h[q] >= stop): px = stop; why = "stop"; break
                        if (sd == 1 and h[q] >= tgt) or (sd == -1 and l[q] <= tgt): px = tgt; why = "target"; break
                    if px is None: px = cl[q]; why = "time"
                    cost = sp[i] / 2 + comm * e * 2
                    rows.append(dict(year=x.index[i].year, side=sd, R=(sd * (px - e) - cost) / risk, why=why)); break
    return pd.DataFrame(rows).sort_values("year")

# ---------------------------------------------------------------- C. NY ORB gold
def orb(g, exit_mode="1.5R", random_dir=False, seed=0):
    rng = np.random.default_rng(seed); rows = []
    o, h, l, c, v, sp, nym = (g[k].values for k in ("open","high","low","close","vol","sp","nym"))
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1)))); atr5 = pd.Series(tr).rolling(5).mean().values
    for day, ix in g.groupby("nyd").indices.items():
        a0, a1 = ix[0], ix[-1]; seg = np.arange(a0, a1 + 1); m = nym[seg]
        r5 = seg[(m >= 570) & (m <= 574)]
        if len(r5) < 5: continue
        rh, rl = h[r5].max(), l[r5].min(); cand = seg[(m >= 575) & (m <= 585)]
        brk = None
        for i in cand:
            body = abs(c[i] - o[i]); rngc = h[i] - l[i]; a = atr5[i]
            if not np.isfinite(a) or a <= 0 or rngc <= 0: continue
            if c[i] >= rh + 0.5 * a and body >= 0.8 * a and body >= 0.6 * rngc and v[i] > v[i-1]: brk = (i, 1); break
            if c[i] <= rl - 0.5 * a and body >= 0.8 * a and body >= 0.6 * rngc and v[i] > v[i-1]: brk = (i, -1); break
        if brk is None: continue
        i, side = brk
        if random_dir: side = 1 if rng.random() < 0.5 else -1
        lvl = h[i] if side == 1 else l[i]; stop = l[i] if side == 1 else h[i]; fill = None
        for q in range(i + 1, a1 + 1):
            if nym[q] > 590: break
            if (side == 1 and h[q] >= lvl) or (side == -1 and l[q] <= lvl): fill = q; break
        if fill is None: continue
        e = lvl + side * sp[fill] / 2; risk = side * (e - stop)
        if risk <= 0: continue
        a = atr5[i]; cost = sp[fill] / 2 + COMM * e * 2
        if exit_mode in ("1.5R", "2.5R"):
            tr_ = float(exit_mode[:-1]); tgt = e + side * tr_ * risk; px = None
            for q in range(fill + 1, a1 + 1):
                if nym[q] >= 720: px = c[q]; why = "time"; break
                if (side == 1 and l[q] <= stop) or (side == -1 and h[q] >= stop): px = stop; why = "stop"; break
                if (side == 1 and h[q] >= tgt) or (side == -1 and l[q] <= tgt): px = tgt; why = "target"; break
            if px is None: px = c[a1]; why = "end"
            R = (side * (px - e) - cost) / risk
        else:   # scale-out: 50% at 1.5R (SL->BE), 30% at 2.5R (SL->+0.5R), 20% trailed 0.8 ATR(5)
            rem = [(0.5, 1.5), (0.3, 2.5), (0.2, None)]; stop_ = stop; best = e; R = -cost / risk; filled = 0; why = "time"
            for q in range(fill + 1, a1 + 1):
                if nym[q] >= 720:
                    for w_, _ in rem[filled:]: R += w_ * side * (c[q] - e) / risk
                    break
                if (side == 1 and l[q] <= stop_) or (side == -1 and h[q] >= stop_):
                    for w_, _ in rem[filled:]: R += w_ * side * (stop_ - e) / risk
                    why = "stop"; break
                best = max(best, h[q]) if side == 1 else min(best, l[q])
                while filled < 2 and rem[filled][1] is not None and side * (best - e) >= rem[filled][1] * risk:
                    R += rem[filled][0] * rem[filled][1]; filled += 1
                    stop_ = e if filled == 1 else e + side * 0.5 * risk
                if filled == 2: stop_ = max(stop_, best - 0.8 * a) if side == 1 else min(stop_, best + 0.8 * a)
            else:
                for w_, _ in rem[filled:]: R += w_ * side * (c[a1] - e) / risk
        rows.append(dict(year=g.index[i].year, side=side, R=R, why=why, risk_atr=risk / g.datr.values[i]))
    return pd.DataFrame(rows)

# ---------------------------------------------------------------- D. wicks get filled
def wicks(g, tf="15min", random_dir=False, seed=0, min_wick_sp=0.0):
    rng = np.random.default_rng(seed)
    b = g[["open","high","low","close"]].resample(tf, label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    starts = np.searchsorted(g.index.values, b.index.values); l1 = g.low.values; h1 = g.high.values; sp = g.sp.values; rows = []
    o, h, l, c = b.open.values, b.high.values, b.low.values, b.close.values
    for k in range(1, len(b) - 1):
        up = c[k-1] > o[k-1] and h[k-1] > c[k-1]; dn = c[k-1] < o[k-1] and l[k-1] < c[k-1]
        if not (up or dn): continue
        side = 1 if up else -1
        if random_dir: side = 1 if rng.random() < 0.5 else -1
        s0, s1 = starts[k], starts[k+1]
        if s1 - s0 < 3: continue
        lvl = c[k-1]; tgt = h[k-1] if side == 1 else l[k-1]; risk = side * (tgt - lvl)
        if risk <= 0 or risk < min_wick_sp * sp[s0]: continue
        dipped = False; fill = None
        for q in range(s0, s1):
            if side == 1 and l1[q] < o[k] or side == -1 and h1[q] > o[k]: dipped = True
            if dipped and ((side == 1 and h1[q] >= lvl) or (side == -1 and l1[q] <= lvl)): fill = q; break
        if fill is None: continue
        e = lvl + side * sp[fill] / 2; stop = e - side * risk; px = None
        for q in range(fill + 1, min(fill + 2000, len(g))):
            if (side == 1 and l1[q] <= stop) or (side == -1 and h1[q] >= stop): px = stop; why = "stop"; break
            if (side == 1 and h1[q] >= tgt) or (side == -1 and l1[q] <= tgt): px = tgt; why = "target"; break
        if px is None: continue
        cost = sp[fill] / 2 + COMM * e * 2
        rows.append(dict(year=b.index[k].year, side=side, R=(side * (px - e) - cost) / risk, why=why))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    which = sys.argv[1]
    g = gold_m1()
    if which == "A":
        d = holo(g); print(line("A HoLo gold, as written (M15 confirmation)", d.R.values, d.year.values), "| risk/ATR median %.2f" % d.risk_atr.median(), d.why.value_counts().to_dict())
        print(line("  longs", d[d.side==1].R.values), "|", line("shorts", d[d.side==-1].R.values))
        d2 = holo(g, confirm=False); print(line("  without the M15 confirmation", d2.R.values, d2.year.values))
        r = holo(g, random_dir=True); print(line("  coin flip at the same entries", r.R.values))
    elif which == "B":
        for tf in ("15min", "1h", "4h"):
            x = g[["open","high","low","close"]].resample(tf, label="left", closed="left").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
            x["sp"] = g.sp.resample(tf, label="left", closed="left").mean().reindex(x.index).ffill()
            d = tms(x, COMM); print(line(f"B TMS(r) 1:1 gold {tf}", d.R.values, d.year.values), d.why.value_counts().to_dict())
            r = tms(x, COMM, random_dir=True); print(line("  coin flip", r.R.values))
    elif which == "C":
        for ex in ("1.5R", "2.5R", "scale"):
            d = orb(g, ex); print(line(f"C NY ORB gold v.B, exit {ex}", d.R.values, d.year.values), "| risk/ATR median %.3f" % d.risk_atr.median())
        r = orb(g, "1.5R", random_dir=True); print(line("  coin flip, 1.5R", r.R.values))
    elif which == "D":
        for tf in ("15min", "30min"):
            for mw in (0.0, 5.0, 10.0):
                d = wicks(g, tf, min_wick_sp=mw); print(line(f"D wicks get filled gold {tf}, wick >= {mw:.0f}x spread", d.R.values, d.year.values), d.why.value_counts().to_dict())
            r = wicks(g, tf, random_dir=True, min_wick_sp=10.0); print(line("  coin flip (wick >= 10x spread)", r.R.values))
