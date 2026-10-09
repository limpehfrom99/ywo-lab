"""Rules from Bernd Skorupinski's Instagram reels (41 clips, supply and demand + fundamentals), for bt/xgrid.py. LONG in the frame
(demand); the harness mirrors for supply. Fixed before running:
  Zone ("sublime demand"): a base of 1-3 candles whose ranges are each <= 0.6 x bar ATR, followed by a leg-out candle that is bullish,
  has a range >= 1.5 x bar ATR ("explosive") and closes above the base's highest high. Proximal line = the highest body top of the
  base, distal line = the lowest low of the base and the leg-out. Fresh = no bar has come back to the proximal line yet.
  Room test (his "is there 2R of room before the opposing zone"): the highest high between the leg-out and the entry is >= entry + 2R.
  The zone lives 200 bars or until a close below the distal line.
  Z1 blind: buy limit at the proximal line, stop = distal - 0.05 daily ATR ("additional protection"), target 2R.
  Z2 inside bar: once price is in the zone, an inside bar (high <= previous high, low >= previous low) inside the zone -> buy stop
     above the inside bar's high; stop = distal - 0.05 ATR; 2R.
  Z3 strict engulfing: in the zone, a bullish candle that closes above the previous candle's whole high -> buy at the next open;
     stop = distal - 0.05 ATR; 2R.
  BE: #33 and #35 with his break-even rule (stop to the entry once price has gone 1R in favour)."""
import sys, numpy as np
from dataclasses import replace
sys.path.insert(0, "/home/claude/bt")
from xgrid import Fill
from xrules_video import bar_atr, mk, BUF
import xrules as XR

REGISTRY = {}


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


def zones(S, A):
    """Yield (leg_out_index, proximal, distal) for every demand zone, in time order."""
    N = len(S.c); out = []
    for i in range(4, N):
        a = A[i]
        if not np.isfinite(a): continue
        rng = S.h[i] - S.l[i]
        if not (S.c[i] > S.o[i] and rng >= 1.5 * a): continue
        for nb in (1, 2, 3):                                           # the smallest base that qualifies
            b0 = i - nb
            if b0 < 1: break
            base = slice(b0, i)
            if np.all(S.h[base] - S.l[base] <= 0.6 * a) and S.c[i] > S.h[base].max():
                prox = np.maximum(S.o[base], S.c[base]).max(); dist = min(S.l[base].min(), S.l[i])
                if prox > dist: out.append((i, prox, dist))
                break
    return out


def plain_zones(S, A):
    """Baseline for the zone rules: no size tests. Any bullish candle that closes above the previous candle's high is a 'leg-out'
    and the previous candle is the 'base'. If these do as well as the sublime zones, the zone quality adds nothing."""
    out = []
    for i in range(4, len(S.c)):
        if not np.isfinite(A[i]) or not (S.c[i] > S.o[i] and S.c[i] > S.h[i - 1]): continue
        prox = max(S.o[i - 1], S.c[i - 1]); dist = min(S.l[i - 1], S.l[i])
        if prox > dist: out.append((i, prox, dist))
    return out


def _zone_entries(S, ctx, mode, life=200, zone_fn=None):
    A = bar_atr(S); N = len(S.c); out = []; ti = S.t.view("i8")
    for i, prox, dist in (zone_fn or zones)(S, A):
        hi = S.h[i]; entered = None
        for q in range(i + 1, min(i + 1 + life, N - 1)):
            if entered is None:
                if S.o[q] <= dist: break                               # opened through the zone: order cancelled at the open
                if S.l[q] <= prox:
                    entered = q
                    if mode == "blind":
                        atr = S.atr[q]
                        if not np.isfinite(atr): break
                        e = min(prox, S.o[q]); stop = dist - BUF * atr
                        if e > stop and hi >= e + 2 * (e - stop):
                            out.append(Fill(ti[q], ctx["bar_ns"], e, stop, e + 2 * (e - stop), "limit"))
                        break
                else:
                    hi = max(hi, S.h[q])
                continue
            if S.c[q] < dist: break                                    # zone broken after the first touch (known at the close)
            if q - entered > 20: break
            atr = S.atr[q]
            if not np.isfinite(atr): continue
            stop = dist - BUF * atr
            if mode == "inside" and S.h[q] <= S.h[q - 1] and S.l[q] >= S.l[q - 1] and S.l[q] <= prox and q + 1 < N:
                e = S.h[q]; k = q + 1
                if S.h[k] >= e and S.o[k] > stop and hi >= e + 2 * (e - stop):     # the fill bar's own low is the harness's job
                    e2 = max(e, S.o[k]); out.append(Fill(ti[k], ctx["bar_ns"], e2, stop, e2 + 2 * (e2 - stop), "stop"))
                break
            if mode == "engulf" and S.c[q] > S.o[q] and S.c[q] > S.h[q - 1] and S.l[q] <= prox:
                f = mk(S, ctx, q, stop)
                if f and hi >= f.e + 2 * (f.e - stop): out.append(f)
                break
    return out


@rule("Z1 fresh demand zone, blind limit at proximal, 2R")
def z_blind(S, ctx): return _zone_entries(S, ctx, "blind")


@rule("Z2 fresh demand zone + inside bar breakout, 2R")
def z_inside(S, ctx): return _zone_entries(S, ctx, "inside")


@rule("Z3 fresh demand zone + strict engulfing, 2R")
def z_engulf(S, ctx): return _zone_entries(S, ctx, "engulf")


@rule("#35 breaker + break-even at 1R")
def r35_be(S, ctx): return [replace(f, be_r=1.0) for f in XR.r35(S, ctx)]


@rule("#33 gap retest + break-even at 1R")
def r33_be(S, ctx): return [replace(f, be_r=1.0) for f in XR.r33(S, ctx)]


def _filtered(S, ctx, location=False, direction=False):
    """Z1 fills kept only if (location) the entry is in the lower 40% of the previous 500 bars' range and/or (direction) the
    200-bar SMA of closes (closed bars) is above its value 50 bars earlier (his 'direction' = higher-timeframe trend up)."""
    import pandas as pd
    out = []; ti = S.t.view("i8"); idx = {t: k for k, t in enumerate(ti)}
    rl = pd.Series(S.l).rolling(500, min_periods=100).min().shift(1).values; rh = pd.Series(S.h).rolling(500, min_periods=100).max().shift(1).values
    sm = pd.Series(S.c).rolling(200).mean().shift(1).values
    for f in _zone_entries(S, ctx, "blind"):
        k = idx.get(f.t_bar)
        if k is None: continue
        if location and (not np.isfinite(rl[k]) or rh[k] <= rl[k] or (f.e - rl[k]) / (rh[k] - rl[k]) > 0.4): continue
        if direction and (k < 50 or not np.isfinite(sm[k]) or not np.isfinite(sm[k - 50]) or sm[k] <= sm[k - 50]): continue
        out.append(f)
    return out


@rule("Z0 baseline: any bullish close above the prior high as a zone, blind limit, 2R")
def z_plain(S, ctx): return _zone_entries(S, ctx, "blind", zone_fn=plain_zones)


@rule("Z1 + discount location (lower 40% of the 500-bar range)")
def z_blind_discount(S, ctx): return _filtered(S, ctx, location=True)


# rn069 "action matrix" (location x direction x zone), fixed before running: demand only in an uptrend (SMA200 rising over 50 bars),
# with and without the discount location.
@rule("Z4 action matrix: Z1 + uptrend (SMA200 rising)")
def z_trend(S, ctx): return _filtered(S, ctx, direction=True)


@rule("Z4 action matrix: Z1 + uptrend + discount")
def z_trend_discount(S, ctx): return _filtered(S, ctx, location=True, direction=True)
