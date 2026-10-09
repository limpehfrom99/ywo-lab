"""Log #67: Bernd Skorupinski's "UnFilled Order" (UFO) supply/demand zones as his indicator page defines them, alone and with his
higher-timeframe bias tools (bt/bernd_bias.py) as filters. LONG at demand in the frame; the harness mirrors for supply.
Fixed before running (research/log.md #67):
  Base = ONE candle whose body <= 0.5 x its own range and <= 0.5 x the smaller body of its two neighbours ("small body compared
  to its near candles"; his 'body candle ratio', 0.5 assumed). Leg-out (next candle) bullish with body >= 0.5 x its range, closing
  above the base's high. Leg-in (previous candle) body >= 0.5 x its range, either colour (drop-base-rally or rally-base-rally).
  Proximal = the base's body top ("buy limit on the proximal (upper) level"), distal = the lower of the base's and the leg-out's lows.
  Fresh: the first return to the proximal is the trade. Stop = distal - 0.05 daily ATR; targets 2R and 3R.
  Fills: the limit fills on the first bar that trades down to the proximal (fill checked first; a bar that opens below the distal
  cancels the order); the harness counts the stop, not the target, inside the fill bar (no same-bar look-ahead, PROTOCOL).
  UFO+room: only if price went >= 2R above the entry between the leg-out and the return ("profit margin").
  Filters (bias known at the start of the trade's server day): SEAS = 15-year seasonal mean of the next 20 days has the trade's sign;
  VAL = valuation vs the dollar index on the trade's side of zero (demand: < 0, cheap; supply: > 0); VALX = beyond his +-0.75 extreme;
  SEAS+VAL = both."""
import sys, functools, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
from xgrid import Fill
from xrules_video import bar_atr
import bernd_bias as BB

REGISTRY = {}
BUF = 0.05


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


def ufo_zones(S):
    o, h, l, c = S.o, S.h, S.l, S.c
    body = np.abs(c - o); rng = h - l; out = []
    for k in range(2, len(c) - 1):
        if rng[k] <= 0 or rng[k - 1] <= 0 or rng[k + 1] <= 0: continue
        if body[k] > 0.5 * rng[k] or body[k] > 0.5 * min(body[k - 1], body[k + 1]): continue
        if body[k - 1] < 0.5 * rng[k - 1]: continue
        j = k + 1
        if not (c[j] > o[j] and body[j] >= 0.5 * rng[j] and c[j] > h[k]): continue
        prox = max(o[k], c[k]); dist = min(l[k], l[j])
        if prox > dist: out.append((j, prox, dist))
    return out


def _entries(S, ctx, rr=2.0, room=False, life=200):
    N = len(S.c); ti = S.t.view("i8"); out = []
    for j, prox, dist in ufo_zones(S):
        hi = S.h[j]
        for q in range(j + 1, min(j + 1 + life, N - 1)):
            if S.o[q] <= dist: break
            if S.l[q] <= prox:
                atr = S.atr[q]
                if not np.isfinite(atr): break
                e = min(prox, S.o[q]); stop = dist - BUF * atr
                if e > stop and (not room or hi >= e + 2 * (e - stop)):
                    out.append(Fill(ti[q], ctx["bar_ns"], e, stop, e + rr * (e - stop), "limit"))
                break
            hi = max(hi, S.h[q])
    return out


_DK = {}


def _daykeys(S, ctx):
    """Server date (17:00 New York day) of every bar. Cached per (asset, timeframe, bar count); both mirror frames share it."""
    k = (ctx["asset"], ctx["tf"], len(S.t), int(S.t.view("i8")[0]))
    if k not in _DK:
        if len(_DK) > 8: _DK.clear()
        t = pd.DatetimeIndex(S.t).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
        _DK[k] = t.normalize().values
    return _DK[k]


@functools.lru_cache(maxsize=None)
def _bias(asset):
    try: T = BB.bias_table(asset)
    except Exception: T = None
    return T


def _filtered(S, ctx, fills, use):
    T = _bias(ctx["asset"])
    if T is None or not len(fills): return []
    sgn = -1 if ctx.get("mirrored") else 1                            # mirrored frame: its 'long' is a real short
    dk = _daykeys(S, ctx); ti = S.t.view("i8"); pos = {t: i for i, t in enumerate(ti)}
    tab = T.reindex(pd.DatetimeIndex(np.unique(dk)))
    out = []
    for f in fills:
        i = pos.get(f.t_bar)
        if i is None: continue
        row = tab.loc[pd.Timestamp(dk[i])]
        ok = True
        if "seas" in use: ok &= np.isfinite(row.seas20) and sgn * row.seas20 > 0
        if "val" in use: ok &= np.isfinite(row.val_dxy) and sgn * row.val_dxy < 0
        if "valx" in use: ok &= np.isfinite(row.val_dxy) and sgn * row.val_dxy < -0.75
        if ok: out.append(f)
    return out


@rule("UFO zone, blind limit at proximal, 2R")
def ufo2(S, ctx): return _entries(S, ctx, 2.0)


@rule("UFO zone, blind limit at proximal, 3R")
def ufo3(S, ctx): return _entries(S, ctx, 3.0)


@rule("UFO zone + room >= 2R, 2R")
def ufo_room(S, ctx): return _entries(S, ctx, 2.0, room=True)


@rule("UFO + SEAS bias, 2R")
def ufo_seas(S, ctx): return _filtered(S, ctx, _entries(S, ctx, 2.0), ("seas",))


@rule("UFO + VAL bias (cheap side), 2R")
def ufo_val(S, ctx): return _filtered(S, ctx, _entries(S, ctx, 2.0), ("val",))


@rule("UFO + VALX bias (beyond 0.75), 2R")
def ufo_valx(S, ctx): return _filtered(S, ctx, _entries(S, ctx, 2.0), ("valx",))


@rule("UFO + SEAS + VAL bias, 2R")
def ufo_seas_val(S, ctx): return _filtered(S, ctx, _entries(S, ctx, 2.0), ("seas", "val"))


@rule("UFO + room + SEAS + VAL bias, 3R")
def ufo_full(S, ctx): return _filtered(S, ctx, _entries(S, ctx, 3.0, room=True), ("seas", "val"))
