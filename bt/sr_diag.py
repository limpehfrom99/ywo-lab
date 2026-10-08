"""Support/resistance + 1-minute confirmation on gold: why do the stops get hit?

Levels known in advance: H4 3-bar pivots (confirmed 16h after the pivot bar opens),
previous NY-day high/low, previous week high/low. Touch zone = 0.05 x daily ATR(14).
Entry: price enters the zone, first 1-min candle that closes back beyond the level in the
level's direction. Stop beyond the touch extreme, target 3R, time limit 24h.
Every touch of a level is numbered, so 'first touch' and 'second touch (double bottom)'
can be compared, and a neckline-break entry is simulated for second touches.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc import pivots
from gold_m1 import COMM

START, END = "2020-01-01", "2026-10-08"
W_CONFIRM = 15        # minutes allowed for the confirmation candle
HOLD = 1440           # minutes
TARGET_R = 3.0
ZONE_K, BUF_K, EQ_K = 0.05, 0.02, 0.15
MIN_SEP = 20          # minutes between two touches of the same level


def load():
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl").loc[START:END]
    g = g[["open", "high", "low", "close", "sp"]].copy()
    ny = g.index.tz_localize("UTC").tz_convert("America/New_York")
    g["nyd"] = pd.DatetimeIndex(ny.tz_localize(None)).normalize()
    g["nym"] = ny.hour * 60 + ny.minute
    return g


def daily_atr(g):
    d = g.groupby("nyd").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = d.close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)          # known at the day's open
    return d, atr


def build_levels(g, d, atr):
    """Return DataFrame: price, side (+1 support, -1 resistance), start, end, kind."""
    L = []
    # previous-day high/low: active during the next NY day
    days = d.index
    for i in range(1, len(days)):
        day = days[i]; prev = days[i - 1]
        s = pd.Timestamp(day).tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)
        e = s + pd.Timedelta(hours=24)
        L.append((d.high.iloc[i - 1], -1, s, e, "PDH"))
        L.append((d.low.iloc[i - 1], +1, s, e, "PDL"))
    # previous-week high/low: active during the next week
    wk = d.groupby(pd.Grouper(freq="W-SUN")).agg(high=("high", "max"), low=("low", "min"))
    wk = wk.dropna()
    for i in range(1, len(wk)):
        s = pd.Timestamp(wk.index[i - 1] + pd.Timedelta(days=1)).tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)
        e = s + pd.Timedelta(days=7)
        L.append((wk.high.iloc[i - 1], -1, s, e, "PWH"))
        L.append((wk.low.iloc[i - 1], +1, s, e, "PWL"))
    # H4 pivots, 3 bars each side, confirmed when the 3rd following bar closes
    h4 = g[["open", "high", "low", "close"]].resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    ph, pl = pivots(h4.high.values, h4.low.values, 3)
    idx = h4.index
    recent_h, recent_l = [], []
    for i in np.where(ph | pl)[0]:
        t0 = idx[i]; s = t0 + pd.Timedelta(hours=16); e = s + pd.Timedelta(days=5)
        day = pd.Timestamp(t0).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None).normalize()
        a = atr.get(day, np.nan)
        if ph[i]:
            p = h4.high.iloc[i]; kind = "H4H"
            if any(abs(p - q) <= EQ_K * a for q, tq in recent_h if t0 - tq <= pd.Timedelta(days=10)): kind = "EQH"
            recent_h.append((p, t0)); L.append((p, -1, s, e, kind))
        if pl[i]:
            p = h4.low.iloc[i]; kind = "H4L"
            if any(abs(p - q) <= EQ_K * a for q, tq in recent_l if t0 - tq <= pd.Timedelta(days=10)): kind = "EQL"
            recent_l.append((p, t0)); L.append((p, +1, s, e, kind))
    lv = pd.DataFrame(L, columns=["price", "side", "start", "end", "kind"]).sort_values("start").reset_index(drop=True)
    return lv


def simulate(g, lv, atr, entry_mode="confirm", target_r=TARGET_R, be_r=None, random_dir=False, seed=0, stop_atr_k=None, hold=HOLD):
    rng = np.random.default_rng(seed)
    """entry_mode: 'confirm' (first 1-min close back beyond the level) or 'neck' (close beyond the
    interim extreme between the previous touch and this one; only for touch >= 2)."""
    t = g.index.values; o = g.open.values; h = g.high.values; l = g.low.values; c = g.close.values; sp = g.sp.values
    nyd = g.nyd.values; nym = g.nym.values
    atr_by_day = atr.to_dict()
    out = []
    starts = np.searchsorted(t, lv.start.values); ends = np.searchsorted(t, lv.end.values)
    for li in range(len(lv)):
        L, side, kind = lv.price.iloc[li], lv.side.iloc[li], lv.kind.iloc[li]
        a0, b0 = starts[li], min(ends[li], len(t) - 1)
        if b0 - a0 < 30: continue
        a = atr_by_day.get(pd.Timestamp(nyd[a0]), np.nan)
        if not np.isfinite(a): continue
        z, buf = ZONE_K * a, BUF_K * a
        # work in 'support' coordinates: y = side * price, level y0 = side * L
        y0 = side * L
        yo, yh, yl, yc = side * o, (side * h if side == 1 else side * l), (side * l if side == 1 else side * h), side * c
        i = a0 + 1; touch_n = 0; last_touch = -10**9; prev_touch_low = None; prev_touch_i = None
        while i < b0:
            # approach: enters the zone from above (prev close above zone, this low inside zone)
            seg_l = yl[i:b0]; seg_pc = yc[i - 1:b0 - 1]
            m = (seg_l <= y0 + z) & (seg_pc > y0 + z)
            k = np.argmax(m) if m.any() else -1
            if k < 0: break
            i = i + k
            if i - last_touch < MIN_SEP: i += 1; continue
            touch_n += 1; last_touch = i
            # confirmation within W minutes; abort if a close breaks the level by a zone
            j = -1; broken = False
            for q in range(i, min(i + W_CONFIRM, b0)):
                if yc[q] < y0 - z: broken = True; break
                if yc[q] > y0 and yc[q] > yo[q]: j = q; break
            tl = yl[i:(j if j >= 0 else q) + 1].min()
            if broken: break
            if j < 0: i = q + 1; prev_touch_low, prev_touch_i = tl, i; continue
            # entry
            if entry_mode == "neck":
                if touch_n < 2 or prev_touch_i is None: prev_touch_low, prev_touch_i = tl, i; i = j + 1; continue
                neck = yh[prev_touch_i:i].max()
                e = -1
                for q in range(j, min(j + 240, b0)):
                    if yc[q] < y0 - z: break
                    if yc[q] > neck: e = q; break
                if e < 0: prev_touch_low, prev_touch_i = tl, i; i = j + 1; continue
                j = e; stop = min(tl, prev_touch_low) - buf
            else:
                stop = tl - buf
            if stop_atr_k is not None: stop = y0 - stop_atr_k * a
            entry = yc[j] + sp[j] / 2
            risk = entry - stop
            if risk <= 0: i = j + 1; continue
            tgt = entry + target_r * risk
            # walk forward
            if random_dir and rng.random() < 0.5:
                # same event, opposite direction, same stop distance: the no-information benchmark
                entry = yc[j] - sp[j] / 2; stop = entry + risk; tgt = entry - target_r * risk
                yl2, yh2, yc2 = -yh, -yl, -yc; entry, stop, tgt = -entry, -stop, -tgt
                seg_lo = yl2[j + 1:j + 1 + hold]; seg_hi = yh2[j + 1:j + 1 + hold]; ycx = yc2
            else:
                seg_lo = yl[j + 1:j + 1 + hold]; seg_hi = yh[j + 1:j + 1 + hold]; ycx = yc
            n = len(seg_lo)
            if n == 0: break
            hs = np.argmax(seg_lo <= stop) if (seg_lo <= stop).any() else n
            ht = np.argmax(seg_hi >= tgt) if (seg_hi >= tgt).any() else n
            if be_r is not None:
                lvl = entry + be_r * risk
                ib = np.argmax(seg_hi >= lvl) if (seg_hi >= lvl).any() else n
                if ib < hs and ib < n:
                    hb = np.argmax(seg_lo[ib:] <= entry) + ib if (seg_lo[ib:] <= entry).any() else n
                    if ht < n and ht <= hb: x = j + 1 + ht; px = tgt; why = "target"
                    elif hb < n: x = j + 1 + hb; px = entry; why = "be"
                    else: x = j + n; px = ycx[x]; why = "time"
                    hs = n; ht = n if why != "target" else ht
                    if why == "target": pass
                    else: hs = -2
            if hs == -2: pass
            elif hs < n and hs <= ht: x = j + 1 + hs; px = stop; why = "stop"
            elif ht < n: x = j + 1 + ht; px = tgt; why = "target"
            else: x = j + n; px = ycx[x]; why = "time"
            mfe = (seg_hi[:max(x - j, 1)].max() - entry) / risk
            cost = sp[j] / 2 + COMM * L * 2        # half spread on exit + commission both sides (entry half spread is in 'entry')
            r = (px - entry - cost) / risk
            # what happened after a stop-out: did the target get hit anyway, or did price keep falling?
            post_tgt = post_fail = False
            if why == "stop":
                pl_ = yl[x + 1:x + 1 + hold]; ph_ = yh[x + 1:x + 1 + hold]
                if len(ph_): post_tgt = bool((ph_ >= tgt).any()); post_fail = bool((pl_ <= stop - risk).any())
            out.append(dict(time=pd.Timestamp(t[j]), kind=kind, side=side, level=L, touch=touch_n, entry_dist=(entry - y0) / risk,
                            stop_atr=risk / a, R=r, R_gross=(px - entry) / risk, why=why, mfe=mfe, bars=x - j, nym=int(nym[j]),
                            wd=int(pd.Timestamp(t[j]).weekday()), year=int(pd.Timestamp(t[j]).year), post_tgt=post_tgt, post_fail=post_fail,
                            cost_r=cost / risk))
            prev_touch_low, prev_touch_i = tl, i
            i = x + 1
    return pd.DataFrame(out)


def stats(df, label=""):
    if len(df) == 0: return f"{label:28s} n=0"
    n = len(df); m = df.R.mean(); se = df.R.std() / np.sqrt(n)
    return f"{label:28s} n={n:5d}  avgR={m:+.3f}  t={m/se:+.1f}  win={np.mean(df.why=='target'):.0%}  stop={np.mean(df.why=='stop'):.0%}  gross={df.R_gross.mean():+.3f}"


if __name__ == "__main__":
    g = load(); d, atr = daily_atr(g); lv = build_levels(g, d, atr)
    print("levels:", len(lv), lv.kind.value_counts().to_dict())
    df = simulate(g, lv, atr); df.to_pickle("/home/claude/bt/sr_diag_confirm.pkl")
    print(stats(df, "all touches, confirm entry"))
    print(stats(df[df.touch == 1], "first touch only"))
    print(stats(df[df.touch == 2], "second touch (double)"))
    print(stats(df[df.touch >= 3], "third+ touch"))
    dn = simulate(g, lv, atr, entry_mode="neck"); dn.to_pickle("/home/claude/bt/sr_diag_neck.pkl")
    print(stats(dn, "double + neckline break 3R"))
    for tr in (1.5, 2.0):
        print(stats(simulate(g, lv, atr, entry_mode="neck", target_r=tr), f"double + neckline break {tr}R"))
