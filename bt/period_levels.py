"""Shen's idea (2026-10-09): every past weekly open/close (and monthly, quarterly, half-year,
yearly open/close) is a horizontal level; lower-timeframe price pulls back to these levels,
respects the area and reverses. Test on gold M1 2012-2026 with the same engine as sr_diag.py.

Two measurements:
 1. Trades: touch -> 1/5/15-minute confirmation close back beyond the level, stop beyond the
    touch extreme, 3R target, 24h limit. Benchmarks: coin flip at the same moments, and the same
    rules on FAKE levels (every real level shifted by +0.37 daily ATR).
 2. Reaction odds: after price first enters a level's zone, does it move 0.2 ATR away (respect)
    before it moves 0.2 ATR through (break)? Real vs fake levels, by level rank.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
import sr_diag
from sr_diag import ZONE_K

LIFE = {"W": 12, "M": 52, "Q": 104, "H": 104, "Y": 156}     # weeks a level stays on the chart


def period_levels(g, atr, fake_shift=0.0):
    ny = g.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    o = g.open.values; c = g.close.values
    L = []
    def add(kind, price, t_known):
        e = t_known + pd.Timedelta(weeks=LIFE[kind])
        for side in (+1, -1): L.append((price, side, t_known, e, kind))
    # weekly: NY week starts Sunday 18:00 -> use ISO week of the NY time shifted by 6h
    wk = (ny + pd.Timedelta(hours=6)).to_period("W-SAT")
    grp = pd.Series(np.arange(len(g)), index=g.index).groupby(wk.values)
    for _, ix in grp:
        a, b = ix.iloc[0], ix.iloc[-1]
        add("W", o[a], g.index[a]); add("W", c[b], g.index[b])
    for kind, per in (("M", "M"), ("Q", "Q"), ("H", "2Q"), ("Y", "Y")):
        key = ny.to_period(per) if per != "2Q" else (ny.year * 2 + (ny.month > 6).astype(int))
        grp = pd.Series(np.arange(len(g)), index=g.index).groupby(np.asarray(key))
        for _, ix in grp:
            a, b = ix.iloc[0], ix.iloc[-1]
            add(kind, o[a], g.index[a]); add(kind, c[b], g.index[b])
    lv = pd.DataFrame(L, columns=["price", "side", "start", "end", "kind"]).sort_values("start").reset_index(drop=True)
    lv = lv[lv.start >= g.index[0] + pd.Timedelta(days=20)]
    if fake_shift:
        day = lv.start.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
        lv["price"] = lv.price + fake_shift * day.map(atr).values
        lv = lv.dropna(subset=["price"])
    return lv.reset_index(drop=True)


def reaction_odds(g, lv, atr, k=0.2, horizon=1440):
    """P(move k*ATR away from the level before k*ATR through it) after the first entry into the zone."""
    t = g.index.values; h = g.high.values; l = g.low.values; c = g.close.values; nyd = g.nyd.values
    atr_by_day = atr.to_dict(); rows = []
    starts = np.searchsorted(t, lv.start.values); ends = np.searchsorted(t, lv.end.values)
    for li in range(len(lv)):
        L, side, kind = lv.price.iloc[li], lv.side.iloc[li], lv.kind.iloc[li]
        a0, b0 = starts[li], min(ends[li], len(t) - 1)
        if b0 - a0 < 30: continue
        y0 = side * L; yh = side * h if side == 1 else -l; yl = side * l if side == 1 else -h; yc = side * c
        i = a0 + 1; last = -10**9
        while i < b0:
            a = atr_by_day.get(pd.Timestamp(nyd[i]), np.nan)
            if not np.isfinite(a): i += 1440; continue
            z = ZONE_K * a
            seg_l = yl[i:b0]; seg_pc = yc[i - 1:b0 - 1]
            m = (seg_l <= y0 + z) & (seg_pc > y0 + z)
            if not m.any(): break
            i = i + int(np.argmax(m))
            if i - last < 60: i += 1; continue
            last = i
            fh = yh[i + 1:i + 1 + horizon]; fl = yl[i + 1:i + 1 + horizon]
            if len(fh) == 0: break
            up = np.argmax(fh >= y0 + k * a) if (fh >= y0 + k * a).any() else len(fh)
            dn = np.argmax(fl <= y0 - k * a) if (fl <= y0 - k * a).any() else len(fl)
            res = "respect" if up < dn else ("break" if dn < len(fl) else "neither")
            rows.append((kind, side, res))
            i += 60
    r = pd.DataFrame(rows, columns=["kind", "side", "res"])
    out = r.groupby("kind").res.value_counts(normalize=True).unstack().fillna(0)
    out["n"] = r.groupby("kind").size()
    return out


def resample(g, mins):
    b = g[["open", "high", "low", "close"]].resample(f"{mins}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    b["sp"] = g.sp.resample(f"{mins}min", label="left", closed="left").mean().reindex(b.index).ffill()
    ny = b.index.tz_localize("UTC").tz_convert("America/New_York")
    b["nyd"] = pd.DatetimeIndex(ny.tz_localize(None)).normalize(); b["nym"] = ny.hour * 60 + ny.minute
    return b


if __name__ == "__main__":
    sr_diag.START = "2012-01-01"
    g = sr_diag.load(); d, atr = sr_diag.daily_atr(g)
    lv = period_levels(g, atr); fake = period_levels(g, atr, fake_shift=0.37)
    print("levels:", len(lv), lv.kind.value_counts().to_dict(), flush=True)
    print("\n== reaction odds (0.2 ATR away before 0.2 ATR through), real levels ==", flush=True)
    print(reaction_odds(g, lv, atr).round(3), flush=True)
    print("\n== same, fake levels (shifted +0.37 ATR) ==", flush=True)
    print(reaction_odds(g, fake, atr).round(3), flush=True)
    res = {}
    for tf, W, hold in ((1, 15, 1440), (5, 6, 288), (15, 4, 96)):
        b = g if tf == 1 else resample(g, tf)
        sr_diag.W_CONFIRM = W
        df = sr_diag.simulate(b, lv, atr, hold=hold); df.to_pickle(f"/home/claude/bt/period_{tf}m.pkl")
        print(f"\n== {tf}-minute confirmation, 3R ==", flush=True)
        print(sr_diag.stats(df, "real levels, all"), flush=True)
        for k_ in ("W", "M", "Q", "H", "Y"):
            print(sr_diag.stats(df[df.kind == k_], f"  {k_} levels"), flush=True)
        print(sr_diag.stats(df[df.touch == 1], "  first touch"), flush=True)
        print(df.groupby("year").R.agg(["count", "mean"]).round(2).T.to_string(), flush=True)
        fk = sr_diag.simulate(b, fake, atr, hold=hold)
        print(sr_diag.stats(fk, "fake levels"), flush=True)
        rd = sr_diag.simulate(b, lv, atr, hold=hold, random_dir=True)
        print(sr_diag.stats(rd[rd.why != "time"], "coin flip, same moments"), flush=True)
