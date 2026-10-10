"""Log #100: R3 Tokyo 9:55 fix (nakane) and gotobi days (research/drafts/top_traders_prop.md R3, frozen in #84) for the harness.
LONG fills in the frame (the harness mirrors for shorts: 'buy USDJPY' = the long side; 'USD bid' on EURUSD/GBPUSD = the short side).
JST clock (UTC+9, no DST). Business days: Mon-Fri, not a Japanese holiday (python holidays.JP), not 31 Dec - 3 Jan.
Gotobi: the 5th/10th/15th/20th/25th/last day of the month, rolled back to the previous business day when it is not one.
  3A: gotobi days, enter at the 09:00 JST bar open, out at the 09:45 open, stop 0.25 daily ATR, no target.
  3A-non: the same on business days that are not gotobi (baseline).  3B: every business day.
  3C: 10:00 -> 11:00 JST (after-fix reversal = the short side), gotobi days and every business day.
  Fake window: 11:00 -> 11:45 JST on gotobi days.
Bars: entries on M15 (M5/M30 give the same opens at :00 and :45/:00; H1 has no 09:45 bar)."""
import sys, numpy as np, pandas as pd, holidays
sys.path.insert(0, "/home/claude/bt")
from xgrid import Fill

REGISTRY = {}
MIN = 60_000_000_000
JST = 9 * 60 * MIN


def _calendar(y0=2014, y1=2027):
    jp = holidays.JP(years=range(y0, y1 + 1))
    days = pd.date_range(f"{y0}-01-01", f"{y1}-12-31", freq="D")
    biz = [(d.weekday() < 5 and d not in jp and not ((d.month == 12 and d.day == 31) or (d.month == 1 and d.day <= 3))) for d in days]
    biz = pd.Series(biz, index=days)
    got = set()
    for (y, m), x in biz.groupby([biz.index.year, biz.index.month]):
        last = x.index[-1].day
        for dd in (5, 10, 15, 20, 25, last):
            d = pd.Timestamp(y, m, dd)
            while not biz.get(d, False) and d.month == m: d -= pd.Timedelta(days=1)
            if d.month == m: got.add(d.normalize())
    return set(biz[biz].index), got


BIZ, GOT = _calendar()
_cache = {}


def _jst(S):
    key = (id(S.t), len(S.t))
    if key not in _cache:
        if len(_cache) > 8: _cache.clear()
        t = S.t.view("i8") + JST
        day = (t // (1440 * MIN)).astype("datetime64[D]")
        mins = (t % (1440 * MIN)) // MIN
        _cache[key] = (day, mins)
    return _cache[key]


def window(S, ctx, start, end, which):
    if ctx["tf"] not in ("M5", "M15", "M30"): return []
    day, mins = _jst(S); t = S.t.view("i8"); out = []
    a = np.flatnonzero(mins == start)
    bmap = {d: i for d, i in zip(day[mins == end].tolist(), np.flatnonzero(mins == end).tolist())}
    for i in a:
        d = pd.Timestamp(day[i])
        if d not in BIZ: continue
        g = d in GOT
        if (which == "gotobi" and not g) or (which == "non" and g): continue
        j = bmap.get(day[i].tolist())
        if j is None or j <= i: continue
        atr = S.atr[i]
        if not np.isfinite(atr) or atr <= 0: continue
        e = S.o[i]
        out.append(Fill(t[i], ctx["bar_ns"], e, e - 0.25 * atr, e + 1e6 * atr, kind="market", deadline_ns=t[j], tag="got" if g else "non"))
    return out


REGISTRY["R3A gotobi 0900-0945"] = lambda S, ctx: window(S, ctx, 540, 585, "gotobi")
REGISTRY["R3A non-gotobi 0900-0945"] = lambda S, ctx: window(S, ctx, 540, 585, "non")
REGISTRY["R3B all days 0900-0945"] = lambda S, ctx: window(S, ctx, 540, 585, "all")
REGISTRY["R3C gotobi 1000-1100"] = lambda S, ctx: window(S, ctx, 600, 660, "gotobi")
REGISTRY["R3C all days 1000-1100"] = lambda S, ctx: window(S, ctx, 600, 660, "all")
REGISTRY["R3 fake gotobi 1100-1145"] = lambda S, ctx: window(S, ctx, 660, 705, "gotobi")
