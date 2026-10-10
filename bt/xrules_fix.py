"""Log #97: R1 London 4 pm WMR fix (research/drafts/top_traders_prop.md R1, frozen in #84) for the cross-asset harness.
LONG fills in the frame; the harness mirrors prices for the short side (ctx['mirrored']).
London clock (Europe/London, DST-aware); Mon-Fri; 24 Dec - 2 Jan skipped. P1/P2/P3 = opens of the bars that start at
fix-1h / fix / fix+1h London. Only intraday frames (M5-H1) trade; H4/D1 return nothing.
  1A fade: |P2-P1| >= thr x ATR -> enter at P2 against the move into the fix; target half retrace; stop max(|move|, 0.15 ATR) beyond
     P2; out at P3 (or fix+30 min).
  1B into the fix: enter at P1, out at P2, stop 0.15 ATR, no target (both sides; USD side read off the side column).
  1C session flip: leg 1 enter at 08:00 London, out at P2 (tag 'L1'); leg 2 the other side from P2 to 21:00 London (tag 'L2');
     stop 0.5 ATR each. In the long frame leg 1 is long and leg 2 short is produced in the mirrored frame, so the long frame's 'L1'
     and the mirrored frame's 'L2' together are one orientation."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from xgrid import Fill

REGISTRY = {}
MIN = 60_000_000_000
_cache = {}


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


def _london(S):
    key = (id(S.t), len(S.t), int(S.t[0].view("i8")))
    if key not in _cache:
        if len(_cache) > 8: _cache.clear()
        idx = pd.DatetimeIndex(S.t).tz_localize("UTC").tz_convert("Europe/London")
        mins = (idx.hour * 60 + idx.minute).values
        day = idx.normalize().tz_localize(None).values.astype("datetime64[D]")
        ok = (idx.weekday.values < 5) & ~(((idx.month == 12) & (idx.day >= 24)) | ((idx.month == 1) & (idx.day <= 2)))
        _cache[key] = (mins, day, ok)
    return _cache[key]


def _bars_at(S, minute):
    """{london day: bar index} for bars starting exactly at that London minute."""
    mins, day, ok = _london(S)
    w = np.flatnonzero((mins == minute) & ok)
    return dict(zip(day[w].tolist(), w.tolist()))


def _intraday(ctx): return ctx["tf"] in ("M1", "M5", "M15", "M30", "H1")


def fade(S, ctx, fix_h=16, thr=0.10, exit_min=60):
    if not _intraday(ctx): return []
    a = _bars_at(S, fix_h * 60 - 60); b = _bars_at(S, fix_h * 60); t = S.t.view("i8"); out = []
    for d, j in b.items():
        i = a.get(d)
        if i is None: continue
        atr = S.atr[j]
        if not np.isfinite(atr) or atr <= 0: continue
        p1, p2 = S.o[i], S.o[j]; mv = p2 - p1
        if mv > -thr * atr: continue                       # long frame: price fell into the fix -> buy
        stop = p2 - max(-mv, 0.15 * atr); tgt = p2 + 0.5 * (-mv)
        out.append(Fill(t[j], ctx["bar_ns"], p2, stop, tgt, kind="market", deadline_ns=t[j] + exit_min * MIN))
    return out


def into_fix(S, ctx, fix_h=16):
    if not _intraday(ctx): return []
    a = _bars_at(S, fix_h * 60 - 60); b = _bars_at(S, fix_h * 60); t = S.t.view("i8"); out = []
    for d, i in a.items():
        j = b.get(d)
        if j is None: continue
        atr = S.atr[i]
        if not np.isfinite(atr) or atr <= 0: continue
        e = S.o[i]
        out.append(Fill(t[i], ctx["bar_ns"], e, e - 0.15 * atr, e + 1e6 * atr, kind="market", deadline_ns=t[j]))
    return out


def session_flip(S, ctx):
    if not _intraday(ctx): return []
    a = _bars_at(S, 8 * 60); b = _bars_at(S, 16 * 60); t = S.t.view("i8"); out = []
    mins, day, ok = _london(S)
    for d, j in b.items():
        atr = S.atr[j]
        if not np.isfinite(atr) or atr <= 0: continue
        i = a.get(d)
        if i is not None:                                   # leg 1: long 08:00 -> 16:00 London
            e = S.o[i]; out.append(Fill(t[i], ctx["bar_ns"], e, e - 0.5 * atr, e + 1e6 * atr, kind="market", deadline_ns=t[j], tag="L1"))
        e = S.o[j]                                          # leg 2: long 16:00 -> 21:00 London (the short leg comes from the mirror)
        out.append(Fill(t[j], ctx["bar_ns"], e, e - 0.5 * atr, e + 1e6 * atr, kind="market", deadline_ns=t[j] + 300 * MIN, tag="L2"))
    return out


for thr in (0.05, 0.10, 0.20):
    REGISTRY[f"R1A fix16 fade thr{thr:.2f}"] = (lambda th: lambda S, ctx: fade(S, ctx, 16, th, 60))(thr)
REGISTRY["R1A fix16 fade thr0.10 exit1630"] = lambda S, ctx: fade(S, ctx, 16, 0.10, 30)
REGISTRY["R1A fake14 fade thr0.10"] = lambda S, ctx: fade(S, ctx, 14, 0.10, 60)
REGISTRY["R1A fake18 fade thr0.10"] = lambda S, ctx: fade(S, ctx, 18, 0.10, 60)
REGISTRY["R1D fix15 (gold PM) fade thr0.10"] = lambda S, ctx: fade(S, ctx, 15, 0.10, 60)
REGISTRY["R1B into fix16"] = lambda S, ctx: into_fix(S, ctx, 16)
REGISTRY["R1B into fix15 (gold PM)"] = lambda S, ctx: into_fix(S, ctx, 15)
REGISTRY["R1C session flip"] = session_flip
