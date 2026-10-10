"""Log #99: R14 18:00 New York reopen gap fade (research/drafts/top_traders_prop.md R14, frozen in #84) for the cross-asset harness.
LONG fills in the frame (the harness mirrors for shorts). Intraday frames only (M5-H1).
  C0 = close of the last bar that starts before 17:00 NY (Friday's for the Sunday reopen); O18 = open of the first bar at/after 18:00 NY (reopen; 18:05 on FTMO's index M1);
  G = O18 - C0. |G| >= 0.10 daily ATR -> at the NEXT bar's open, trade toward C0 (long frame: G < 0); target C0; stop |G| beyond O18
  (O18 - |G|); out at 20:00 NY. Skipped when the next open is already at/through C0 or the stop. tag 'wkd' = Sunday reopen.
  On markets with no 17:00-18:00 break (forex trades through it, crypto 24/7) G is the 17-18 move, not a gap (reported as such).
  Report-only: follow the 18:00-19:00 move at 19:00 (long if O19 > O18), stop 0.25 ATR, out at 20:00; its coin flip = the fade."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from xgrid import Fill

REGISTRY = {}
MIN = 60_000_000_000


def _intraday(ctx): return ctx["tf"] in ("M5", "M15", "M30", "H1")


def _ny_date(S):
    return pd.DatetimeIndex(S.t).tz_localize("UTC").tz_convert("America/New_York").normalize().tz_localize(None).values


def _reopen_bars(S):
    """First bar starting in 18:00-18:29 NY whose previous bar started before 18:00 (FTMO's index CFDs reopen at 18:05 NY on M1,
    found on the first run: the M5 frame has no 18:00 bar). On markets without a break this is the 18:00 bar itself."""
    nym = S.nym; w = np.flatnonzero((nym >= 1080) & (nym < 1110))
    return w[(w > 0) & ((nym[w - 1] < 1080) | (nym[w - 1] >= 1110))]


def reopen_fade(S, ctx, thr=0.10):
    if not _intraday(ctx): return []
    t = S.t.view("i8"); nym = S.nym; N = len(t); out = []
    js = _reopen_bars(S)
    before = np.flatnonzero(nym < 1020)                      # bars that start before 17:00 NY
    dates = _ny_date(S)
    for j in js:
        p = np.searchsorted(before, j) - 1
        if p < 0: continue
        k = before[p]
        if t[j] - t[k] > 4 * 1440 * MIN or j + 1 >= N: continue
        atr = S.atr[j]
        if not np.isfinite(atr) or atr <= 0: continue
        c0, o18 = S.c[k], S.o[j]; g = o18 - c0
        if g > -thr * atr: continue
        e = S.o[j + 1]; stop = o18 + g; tgt = c0               # g < 0: stop |G| below the 18:00 open
        if not (stop < e < tgt): continue
        if t[j + 1] - t[j] > 2 * ctx["bar_ns"]: continue
        dl = t[j] + 120 * MIN
        if t[j + 1] >= dl: continue
        wkd = pd.Timestamp(dates[j]).weekday() == 6
        out.append(Fill(t[j + 1], ctx["bar_ns"], e, stop, tgt, kind="market", deadline_ns=dl, tag="wkd" if wkd else "wd"))
    return out


def follow_18_19(S, ctx):
    if not _intraday(ctx): return []
    t = S.t.view("i8"); nym = S.nym; out = []
    ro = _reopen_bars(S)
    for i in np.flatnonzero(nym == 1140):
        k = np.searchsorted(ro, i) - 1
        if k < 0: continue
        j = ro[k]
        if t[i] - t[j] > 60 * MIN: continue
        atr = S.atr[i]
        if not np.isfinite(atr) or atr <= 0 or S.o[i] <= S.o[j]: continue
        e = S.o[i]
        out.append(Fill(t[i], ctx["bar_ns"], e, e - 0.25 * atr, e + 1e6 * atr, kind="market", deadline_ns=t[i] + 60 * MIN))
    return out


REGISTRY["R14 reopen gap fade thr0.10"] = reopen_fade
REGISTRY["R14 report follow 18-19"] = follow_18_19
