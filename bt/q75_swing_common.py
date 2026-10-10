"""Shared helpers for log #75 'swing' ideas (#32 pre-holiday, #33 Bollinger squeeze, #36 ratio, #37 Clenow, #39 exit grid).

Data: FTMO MT5 export via quant/universe (UTC index). One symbol / timeframe in memory at a time.
- Intraday base = the finest bar file that is M5 (66 symbols) or M15 (forex); the 5 symbols with an M1 file use their M5 file
  (identical M15-D1 aggregates, a fraction of the memory). Trimmed like xgrid.datasets_export: from xgrid.full_intraday_start,
  days with < 50% of the usual bar count dropped, stock CFDs cut to 9:30-16:00 New York.
- Higher timeframes: M15/M30/H1 resampled on the UTC clock (identical to New York hours), H4 on FTMO's server clock
  (New York + 7 h, as xgrid.frames), D1 = the export's D1 file (server day 17:00-17:00 New York).
- Spread: the export's 'sp' (price units). It is 0 on many old bars (stocks before 2022, the second stock batch until 2026, D1
  files before 2021). Zeros are filled with the symbol's median non-zero spread of that year relative to price (years with
  >= 10% non-zero bars; else the nearest such year). A resampled bar carries the spread of its first 5/15-minute bar (= the
  spread at its open, where entries happen). A D1 bar carries the median (filled) intraday spread of that server day, or the
  yearly relative fill where there is no intraday history. Cost per trade = spread x 1.2 + commission x (|entry| + |exit|)
  + swap for every 17:00 New York rollover held (today's swap sheet; x3 on the symbol's triple day; crypto every calendar night x1).
"""
import os, sys
import numpy as np, pandas as pd

sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
import universe as U  # noqa: E402
from xgrid import full_intraday_start  # noqa: E402

RES = os.environ.get("Q75_RES", "/home/claude/ywo-lab/results")
SECOND_BATCH = {"AMD", "AVGO", "BA", "CVX", "DIS", "INTC", "JNJ", "JPM", "KO", "MSTR", "NKE", "PLTR", "QCOM", "XOM"}
NS = 1_000_000_000
H_NS = 3600 * NS
SPLIT_NS = pd.Timestamp("2024-01-01").value
TF_MIN = {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


# ------------------------------------------------------------------------------------------------------------ clocks
def to_server(idx_utc):
    return idx_utc.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)


def from_server(idx_srv):
    ny = (idx_srv - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    return ny.tz_convert("UTC").tz_localize(None)


def ns(idx):
    return idx.values.astype("datetime64[ns]").view("i8")


# ------------------------------------------------------------------------------------------------------------ spreads
def year_rel_spread(sp, close, years):
    """{year: median non-zero spread / price}, filled from the nearest year that has >= 10% non-zero bars."""
    sp = np.asarray(sp, float); close = np.asarray(close, float)
    df = pd.DataFrame({"y": years, "rel": np.where(sp > 0, sp / close, np.nan), "nz": sp > 0})
    g = df.groupby("y")
    med = g.rel.median(); share = g.nz.mean()
    med[share < 0.10] = np.nan
    good = med.dropna()
    out = {}
    for y in range(int(min(years)) - 30, int(max(years)) + 2):
        if y in good.index: out[y] = float(good[y]); continue
        if not len(good): out[y] = np.nan; continue
        k = np.abs(good.index.values - y); j = np.flatnonzero(k == k.min())[-1]   # nearest year (ties -> later)
        out[y] = float(good.values[j])
    return out


def fill_spread(sp, close, years, rel):
    sp = np.asarray(sp, float)
    f = np.array([rel.get(int(y), np.nan) for y in years]) * np.asarray(close, float)
    return np.where(sp > 0, sp, f)


def spec_rel_spread(sym, price):
    s = U.specs()
    if sym in s.index:
        return float(s.loc[sym, "spread"]) * float(s.loc[sym, "point"]) / price
    return np.nan


# ------------------------------------------------------------------------------------------------------------ data fixes
SPLIT_K = (2, 3, 4, 5, 7, 8, 10, 15, 20, 30)
MAX_GAP_DAYS = 10


def split_adjust(d):
    """Stock CFD histories are not always split-adjusted (AAPL D1: 7:1 on 2014-06-09 and 4:1 on 2020-08-31 show as -86% / -75%
    overnight 'moves'). A bar-to-bar open/previous-close ratio within 3% of 1/k or k (k = 2, 3, 4, 5, 7, 8, 10, 15, 20, 30) is
    treated as a split: every earlier price (and spread) is multiplied by that ratio."""
    if len(d) < 2: return d
    r = d.open.values[1:] / d.close.values[:-1]
    adj = np.ones(len(d)); hits = []
    for i in np.flatnonzero((r < 0.6) | (r > 1.7)):
        for k in SPLIT_K:
            for ratio in (1.0 / k, float(k)):
                if abs(r[i] / ratio - 1) < 0.03:
                    adj[:i + 1] *= ratio; hits.append((str(d.index[i + 1].date()), round(1 / ratio, 3)))
    if hits:
        d = d.copy()
        for k in ("open", "high", "low", "close", "sp"): d[k] = d[k].values * adj
        d.attrs["splits"] = hits
    return d


def segments(t_ns, max_gap_days=MAX_GAP_DAYS):
    """Contiguous stretches of a bar series: a gap of more than max_gap_days (missing history, e.g. AAPL/MSFT intraday
    2019-10 -> 2021-08, N25 2022-23) ends one segment. Rules run on each segment separately, so no trade spans a data hole."""
    t_ns = np.asarray(t_ns, np.int64)
    g = np.flatnonzero(np.diff(t_ns) > max_gap_days * 86400 * NS)
    b = np.r_[0, g + 1, len(t_ns)]
    return [(int(x), int(y)) for x, y in zip(b[:-1], b[1:])]


# ------------------------------------------------------------------------------------------------------------ loaders
def load_intraday(sym, cat):
    """(bars, tf, rel_spread_by_year): UTC-naive index, columns open high low close sp (sp zero-filled)."""
    tf = next((x for x in ("M5", "M15") if (sym, x) in cat), None)
    if tf is None: return None, None, {}
    d = U.load(sym, tf, cat)
    if d is None or len(d) < 1000: return None, None, {}
    d.index = d.index.tz_localize(None); d = d[~d.index.duplicated()].sort_index()
    if U.group_of(sym) == "stock":
        ny = d.index.tz_localize("UTC").tz_convert("America/New_York"); mins = ny.hour * 60 + ny.minute
        d = d[(mins >= 570) & (mins < 960)]
    d = d.loc[full_intraday_start(d):]
    if len(d) < 1000: return None, None, {}
    key = d.index.normalize()
    per_day = pd.Series(1, index=key).groupby(level=0).transform("size").values
    cnt = pd.Series(1, index=key).groupby(level=0).size()
    recent = cnt[cnt.index >= cnt.index[-1] - pd.Timedelta(days=365)].median()
    d = d[per_day >= 0.5 * recent]
    d = d[["open", "high", "low", "close", "sp"]].astype(float).copy()
    if U.group_of(sym) == "stock": d = split_adjust(d)
    yrs = d.index.year.values
    rel = year_rel_spread(d.sp.values, d.close.values, yrs)
    if not np.isfinite(list(rel.values())[0]):                  # no non-zero spread anywhere: today's spec spread
        r = spec_rel_spread(sym, d.close.iloc[-1]); rel = {y: r for y in rel}
    d["sp"] = fill_spread(d.sp.values, d.close.values, yrs, rel)
    return d, tf, rel


AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "first"}


def resample(d, tf):
    if tf in ("M15", "M30", "H1"):
        rule = {"M15": "15min", "M30": "30min", "H1": "1h"}[tf]
        return d.resample(rule, label="left", closed="left").agg(AGG).dropna()
    if tf == "H4":
        srv = d.copy(); srv.index = to_server(d.index)
        x = srv.resample("4h", label="left", closed="left").agg(AGG).dropna()
        u = from_server(x.index); x = x[~u.isna()]; x.index = u[~u.isna()]
        return x.sort_index()
    raise ValueError(tf)


def load_d1(sym, cat, intra=None, rel=None):
    """Export D1 bars (UTC-naive index = server-day start, 17:00 New York). Weekend server days dropped except crypto.
    sp = median intraday spread of that server day where intraday bars exist, else the yearly relative fill."""
    d = U.load(sym, "D1", cat)
    if d is None: return None
    d.index = d.index.tz_localize(None); d = d[~d.index.duplicated()].sort_index()
    srv = to_server(d.index).normalize()
    if U.group_of(sym) != "crypto":
        keep = srv.weekday < 5; d = d[keep]; srv = srv[keep]
    d = d[["open", "high", "low", "close", "sp"]].astype(float).copy()
    if U.group_of(sym) == "stock": d = split_adjust(d)
    yrs = d.index.year.values
    if not rel:
        rel = year_rel_spread(d.sp.values, d.close.values, yrs)
        if not np.isfinite(list(rel.values())[0]):
            r = spec_rel_spread(sym, d.close.iloc[-1]); rel = {y: r for y in rel}
    sp_fill = np.array([rel.get(int(y), np.nan) for y in yrs]) * d.close.values
    if intra is not None and len(intra):
        isrv = to_server(intra.index).normalize()
        med = pd.Series(intra.sp.values, index=isrv).groupby(level=0).median()
        m = med.reindex(srv).values
        d["sp"] = np.where(np.isfinite(m) & (m > 0), m, sp_fill)
    else:
        d["sp"] = sp_fill
    return d


# ------------------------------------------------------------------------------------------------------------ swaps
class Swaps:
    """Rollovers at 17:00 New York. nights(t_in, t_out) counts rollovers r with t_in < r <= t_out (x3 on the triple day;
    crypto: every calendar night x1). per_night(side, price) in price units per unit, positive = cost.
    Today's swap sheet is quoted in points (fixed price units) for most symbols; applied unchanged to 2007-2026 prices (or to
    split-adjusted stock prices) it would charge e.g. 2% a night on AAPL 2009. So it is converted to a fraction of price per night
    at the symbol's latest close (p_ref) and charged on each trade's entry price."""

    def __init__(self, sym, t_first_ns, t_last_ns, p_ref=None):
        self.sym = sym; self.sp = U.specs(); self.crypto = U.group_of(sym) == "crypto"
        tri = U.triple_day(sym, self.sp)
        a = pd.Timestamp(t_first_ns).tz_localize("UTC").tz_convert("America/New_York").normalize().tz_localize(None) - pd.Timedelta(days=3)
        b = pd.Timestamp(t_last_ns).tz_localize("UTC").tz_convert("America/New_York").normalize().tz_localize(None) + pd.Timedelta(days=3)
        days = pd.date_range(a, b, freq="D")
        roll = (days + pd.Timedelta(hours=17)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)
        wd = days.weekday.values
        mult = np.ones(len(days)) if self.crypto else np.where(wd < 5, np.where(wd == tri, 3.0, 1.0), 0.0)
        self.roll = ns(roll); self.cum = np.r_[0.0, np.cumsum(mult)]
        s = self.sp
        if p_ref is None or not np.isfinite(p_ref) or p_ref <= 0: raise ValueError("p_ref (latest close) needed")
        self.prop = True
        self.unit = {+1: U.swap_per_night(sym, p_ref, +1, s) / p_ref, -1: U.swap_per_night(sym, p_ref, -1, s) / p_ref}

    def nights(self, t_in, t_out):
        t_in = np.asarray(t_in, np.int64); t_out = np.asarray(t_out, np.int64)
        return self.cum[np.searchsorted(self.roll, t_out, "right")] - self.cum[np.searchsorted(self.roll, t_in, "right")]

    def per_night(self, side, price):
        """Price units per unit per night (positive = cost); vectorised over side (+1/-1) and price."""
        side = np.asarray(side); price = np.asarray(price, float)
        u = np.where(side > 0, self.unit[1], self.unit[-1])
        return u * price if self.prop else u + 0 * price


# ------------------------------------------------------------------------------------------------------------ stats
def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def year_rows(R, t_ns, base=None, **keys):
    """Sufficient statistics per calendar year of the entry: n, sum, sum of squares, wins, baseline sum."""
    R = np.asarray(R, float); y = pd.DatetimeIndex(np.asarray(t_ns, "datetime64[ns]")).year.values
    b = np.full(len(R), np.nan) if base is None else np.asarray(base, float)
    rows = []
    for yy in np.unique(y):
        m = y == yy; bb = b[m]; fb = np.isfinite(bb)
        rows.append(dict(**keys, year=int(yy), n=int(m.sum()), s=float(R[m].sum()), ss=float((R[m] ** 2).sum()),
                         w=int((R[m] > 0).sum()), bn=int(fb.sum()), bs=float(bb[fb].sum())))
    return rows


def stats_from_years(Y):
    """Cell statistics from year rows (a DataFrame slice with year n s ss w bn bs). Returns a dict incl. the CANDIDATE flag."""
    n = Y.n.sum()
    if n == 0: return dict(n=0)
    s, ss = Y.s.sum(), Y.ss.sum(); mean = s / n
    var = (ss - n * mean ** 2) / (n - 1) if n > 1 else np.nan
    t = mean / np.sqrt(var / n) if n > 2 and var > 0 else np.nan
    yr = Y.groupby("year")[["n", "s"]].sum(); ym = yr.s / yr.n
    pre = yr[yr.index < 2024]; post = yr[yr.index >= 2024]
    m_pre = pre.s.sum() / pre.n.sum() if pre.n.sum() else np.nan
    m_post = post.s.sum() / post.n.sum() if post.n.sum() else np.nan
    bn = Y.bn.sum(); base = Y.bs.sum() / bn if bn else np.nan
    cand = bool(n >= 200 and np.isfinite(t) and t >= 2 and mean >= 0.05 and np.isfinite(m_pre) and m_pre > 0
                and np.isfinite(m_post) and m_post > 0 and ym.min() > -0.3 and np.isfinite(base) and mean > base)
    return dict(n=int(n), meanR=mean, t=t, win=Y.w.sum() / n, pre24=m_pre, from24=m_post, n_pre=int(pre.n.sum()),
                n_post=int(post.n.sum()), years_pos=f"{int((ym > 0).sum())}/{len(ym)}", worst_year=ym.min(),
                worst_yr=int(ym.idxmin()), base=base, beats_base=bool(np.isfinite(base) and mean > base), candidate=cand,
                by_year=" ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in ym.items()))


def summarize(Yall, by, extra_filters=None):
    """Group the year rows by the columns in `by` and compute stats per group."""
    out = []
    for k, Y in Yall.groupby(by, sort=True):
        k = k if isinstance(k, tuple) else (k,)
        out.append(dict(zip(by, k), **stats_from_years(Y)))
    return pd.DataFrame(out)


def fmt_stats(d):
    if not d or d.get("n", 0) == 0: return "n=0"
    return (f"n={d['n']} mean={d['meanR']:+.3f}R t={d['t']:+.2f} win={d['win']:.0%} <24 {d['pre24']:+.3f} 24+ {d['from24']:+.3f} "
            f"yrs>0 {d['years_pos']} worst {d['worst_year']:+.2f} ({d['worst_yr']}) base {d['base']:+.3f}"
            f"{'  << CANDIDATE' if d['candidate'] else ''}")


def append_csv(df, path):
    if df is None or not len(df): return
    df.to_csv(path, mode="a", header=not os.path.exists(path), index=False, float_format="%.5g")


def symbols(cat):
    return sorted({s for s, _ in cat})
