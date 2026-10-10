"""Shared pieces for log #75 'web' ideas (#34 MQL5 CodeBase EAs, #38 freqtrade-strategies).

- datasets(): the FTMO export one symbol at a time, trimmed exactly like xgrid.datasets_export (finest real intraday file, stock
  session only, days with < 50% of the usual bars dropped) but keeping tick volume; sp = export spread x 1.2 (price units).
- frames(): M5..H1 on the UTC clock, H4 and D1 on FTMO's server clock (17:00 New York), as xgrid.frames, plus tick volume.
- sim_bracket(): market entry at a bar's open, fixed stop / target (stop first when one bar touches both; a bar that OPENS beyond
  the stop or target exits at that open), optional time exit, optional one-position-at-a-time.
- sim_ft(): freqtrade backtest semantics (exit signal at the next candle's open, honoured only in profit when exit_profit_only;
  then stoploss; then the minimal_roi table by trade age), one trade per pair at a time.
- Costs per trade (PROTOCOL): spread x 1.2 at entry (round trip) + commission x (|entry| + |exit|) + swap for every 17:00 New
  York rollover held (Mon-Fri, x3 on the symbol's triple-swap weekday; U.swap_per_night from the exporter's spec sheet).
- cell_stats(), pooled sums by group x timeframe.
Exits always run on the finest bars of the symbol (M1 for 5 symbols, M5 for most, M15 for forex)."""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/bt")
import universe as U
import xgrid as XG
from data_standard_check import to_server, from_server

NS = 60_000_000_000
TF_NS = XG.TF_NS
AGGV = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean", "tickvol": "sum"}
SPECS = U.specs()


def clean_crypto(d):
    """Crypto data repairs (found while testing #38, applied to every rule alike, decided from data diagnostics, not results):
    1) drop every year before 2021 whose median spread exceeds 0.5% of price (ETHUSD, LTCUSD, XRPUSD 2018-20 show 1-12%: broken
       spread units; BTCUSD 2018-20 is 0.03-0.2% and stays); 2) drop bars whose high or low is > 50% (log 0.5) away from the centred
       25-bar median close (LTCUSD 2018-20 has ~600 bars at 1/100 of the price around the rollover); 3) drop bars whose spread
       exceeds 5% of price (ADAUSD has single bars at 1,000%)."""
    spr = d.sp / d.close
    yr = spr.groupby(d.index.year).median()
    bad_years = [y for y, v in yr.items() if y < 2021 and v > 0.005]
    if bad_years: d = d[d.index.year > max(bad_years)]
    med = d.close.rolling(25, center=True, min_periods=5).median()
    dev = np.maximum(np.abs(np.log(d.low / med)), np.abs(np.log(d.high / med)))
    return d[(dev <= 0.5).values & ((d.sp / d.close) <= 0.05).values]


def datasets(groups=None, symbols=None, min_years=1.5, clean=False):
    """Yields (sym, group, base_tf, df[open high low close sp tickvol]) — same symbol set and trimming as xgrid.datasets_export.
    clean=True applies clean_crypto() to crypto symbols."""
    cat = U.catalog()
    for sym in sorted({s for s, _ in cat}):
        grp = "gold" if sym.startswith("XAUUSD") else XG.GROUP.get(U.group_of(sym), U.group_of(sym))
        if groups and grp not in groups: continue
        if symbols and sym not in symbols: continue
        for base_tf in ("M1", "M5", "M15", "M30"):
            if (sym, base_tf) not in cat: continue
            d = U.load(sym, base_tf, cat)
            if d is None or len(d) < 1000: continue
            d.index = d.index.tz_localize(None) if d.index.tz is not None else d.index
            d = d[~d.index.duplicated()].sort_index()
            if U.group_of(sym) == "stock":
                ny = d.index.tz_localize("UTC").tz_convert("America/New_York"); mins = ny.hour * 60 + ny.minute
                d = d[(mins >= 570) & (mins < 960)]
            d = d.loc[XG.full_intraday_start(d):]
            per_day = pd.Series(1, index=d.index.normalize()).groupby(level=0).transform("size")
            recent = pd.Series(1, index=d.index.normalize()).groupby(level=0).size()
            recent = recent[recent.index >= recent.index[-1] - pd.Timedelta(days=365)].median()
            d = d[per_day.values >= 0.5 * recent]
            if len(d) < 1000 or (d.index[-1] - d.index[0]).days / 365.25 < min_years: continue
            d = d[["open", "high", "low", "close", "sp", "tickvol"]].astype(float).copy(); d["sp"] = d.sp * 1.2
            if clean and grp == "crypto":
                d = clean_crypto(d)
                if len(d) < 1000 or (d.index[-1] - d.index[0]).days / 365.25 < min_years: continue
            yield sym, grp, base_tf, d
            break


def frames(base, base_tf, h4_offset=0, want=None):
    out = {base_tf: base}
    for tf, rule in (("M5", "5min"), ("M15", "15min"), ("M30", "30min"), ("H1", "1h")):
        if want and tf not in want: continue
        if TF_NS[tf] > TF_NS[base_tf]: out[tf] = base.resample(rule, label="left", closed="left").agg(AGGV).dropna()
    if not want or "H4" in want or "D1" in want:
        srv = base.copy(); srv.index = to_server(base.index)
        for tf, rule in (("H4", "4h"), ("D1", "1D")):
            if want and tf not in want: continue
            off = f"{h4_offset}h" if (tf == "H4" and h4_offset) else None
            x = srv.resample(rule, label="left", closed="left", offset=off).agg(AGGV).dropna()
            if tf == "D1": x = x[x.index.weekday < 5]
            u = from_server(x.index); x = x[~u.isna()]; x.index = u[~u.isna()]; out[tf] = x.sort_index()
        del srv
    return out


def ns(idx):
    return np.asarray(idx.values.astype("datetime64[ns]").view("i8"))


# ------------------------------------------------------------------------------------------------------------- swaps
def swap_calendar(sym, t0_ns, t1_ns):
    """UTC ns of every Mon-Fri 17:00 New York rollover around [t0, t1] and the cumulative night weights (x3 on the triple day)."""
    days = pd.date_range(pd.Timestamp(int(t0_ns)).normalize() - pd.Timedelta(days=3),
                         pd.Timestamp(int(t1_ns)).normalize() + pd.Timedelta(days=3), freq="D")
    days = days[days.weekday < 5]
    ny = (days + pd.Timedelta(hours=17)).tz_localize("America/New_York")
    r = ny.tz_convert("UTC").tz_localize(None).values.astype("datetime64[ns]").view("i8")
    w = np.where(days.weekday == U.triple_day(sym, SPECS), 3.0, 1.0)
    return r, np.r_[0.0, np.cumsum(w)]


def nights(cal, t_in, t_out):
    roll, cumw = cal
    a = np.searchsorted(roll, t_in, side="right"); b = np.searchsorted(roll, t_out, side="left")
    return np.maximum(cumw[b] - cumw[a], 0.0)


def swap_rate(sym, side):
    """Function price -> swap cost per night in price units per unit (positive = cost). Swaps quoted in points (swap_mode 1) are
    turned into a fraction of the spec sheet's price (bid at export) and applied to the trade's own price: FTMO sets swap points
    from rates x price, so today's points on 2015 prices (gold $1,200 vs $4,190) would overstate old swaps ~3.5x."""
    if sym in SPECS.index and int(SPECS.loc[sym].get("swap_mode", 1)) == 1 and float(SPECS.loc[sym].get("bid", 0) or 0) > 0:
        frac = U.swap_per_night(sym, 1.0, side, SPECS) / float(SPECS.loc[sym, "bid"])
        return lambda p: frac * np.asarray(p, float)
    a = U.swap_per_night(sym, 1.0, side, SPECS); b = U.swap_per_night(sym, 2.0, side, SPECS)
    if abs(b - a) > 1e-15 * max(1.0, abs(a)):
        return lambda p: a * np.asarray(p, float)
    return lambda p: np.full(np.shape(np.atleast_1d(p)), a, float)


# ----------------------------------------------------------------------------------------------------------- sessions
def session_end(t, base_ns, gap_ns=30 * NS):
    """For each finest bar: the end time of its continuous trading block (next gap >= gap_ns)."""
    n = len(t); brk = np.flatnonzero(np.diff(t) >= gap_ns)
    brk = np.r_[brk, n - 1]
    k = brk[np.searchsorted(brk, np.arange(n))]
    return t[k] + base_ns


# --------------------------------------------------------------------------------------------------------- simulators
@njit
def sim_bracket(t, o, h, l, c, k0s, dists, mults, d, one_pos, max_hold_ns):
    """Entry at the OPEN of finest bar k0s[m] (sorted). Long (d=1): stop = e - dist, target = e + mult*dist; short mirrored.
    Stop first when one bar touches both; a bar opening beyond the stop (target) exits at that open. Time exit: close of the last
    bar starting before t[k0] + max_hold_ns (or the last bar of the data). one_pos: skip entries while a position is open.
    Returns took, exit index, exit price, reason (1 stop, 2 target, 3 time/data end)."""
    n = len(k0s); N = len(t)
    took = np.zeros(n, np.bool_); xi = np.full(n, -1, np.int64); xp = np.zeros(n); why = np.zeros(n, np.int8)
    last = -1
    for m in range(n):
        k0 = k0s[m]
        if k0 < 0 or k0 >= N: continue
        if one_pos and k0 <= last: continue
        dist = dists[m]
        if not (dist > 0): continue
        e = o[k0]
        if d == 1:
            stop = e - dist; tgt = e + mults[m] * dist
        else:
            stop = e + dist; tgt = e - mults[m] * dist
        t_end = t[k0] + max_hold_ns
        k = k0; r = 0; px = 0.0
        while k < N and t[k] < t_end:
            if d == 1:
                if l[k] <= stop:
                    px = min(stop, o[k]); r = 1; break
                if h[k] >= tgt:
                    px = max(tgt, o[k]); r = 2; break
            else:
                if h[k] >= stop:
                    px = max(stop, o[k]); r = 1; break
                if l[k] <= tgt:
                    px = min(tgt, o[k]); r = 2; break
            k += 1
        if r == 0:
            k -= 1
            if k < k0: continue
            px = c[k]; r = 3
        took[m] = True; xi[m] = k; xp[m] = px; why[m] = r; last = k
    return took, xi, xp, why


@njit
def sim_ft(t, o, h, l, c, sp, k0s, stop_frac, roi_min_ns, roi_val, exit_open, comm, exit_profit_only, one_pos, max_hold_ns):
    """freqtrade backtest order inside each (finest) bar: 1) exit signal at the open (exit_open[k]; if exit_profit_only, only
    when the trade is in profit after costs at that open), 2) stoploss e*(1-stop_frac) (a bar opening below it exits at the open),
    3) ROI: threshold for the trade's age at the bar's start (largest roi_min_ns <= age); exit where the net-of-cost profit
    ratio reaches it (or at the open if the bar opened above). Long only. reason 1 stop, 2 roi, 4 exit signal, 3 time/data end."""
    n = len(k0s); N = len(t); nr = len(roi_min_ns)
    took = np.zeros(n, np.bool_); xi = np.full(n, -1, np.int64); xp = np.zeros(n); why = np.zeros(n, np.int8)
    last = -1
    for m in range(n):
        k0 = k0s[m]
        if k0 < 0 or k0 >= N: continue
        if one_pos and k0 <= last: continue
        e = o[k0]; stop = e * (1.0 - stop_frac); s0 = sp[k0]
        t_end = t[k0] + max_hold_ns
        k = k0; r = 0; px = 0.0
        while k < N and t[k] < t_end:
            if k > k0 and exit_open[k]:
                pnl = o[k] - e - s0 - comm * (e + o[k])
                if (not exit_profit_only) or pnl > 0:
                    px = o[k]; r = 4; break
            if l[k] <= stop:
                px = min(stop, o[k]); r = 1; break
            age = t[k] - t[k0]; j = 0
            for q in range(nr):
                if roi_min_ns[q] <= age: j = q
            x_roi = (e * (1.0 + roi_val[j]) + s0 + comm * e) / (1.0 - comm)
            if h[k] >= x_roi:
                px = max(x_roi, o[k]); r = 2; break
            k += 1
        if r == 0:
            k -= 1
            if k < k0: continue
            px = c[k]; r = 3
        took[m] = True; xi[m] = k; xp[m] = px; why[m] = r; last = k
    return took, xi, xp, why


def trade_R(sym, side, e, x, dist, sp_entry, t_in, t_out, cal, comm):
    """R after costs: (P/L - spread - commission - swaps) / initial risk; side +1 long, -1 short. Returns (R, swap_R, nights)."""
    e = np.asarray(e, float); x = np.asarray(x, float); dist = np.asarray(dist, float)
    nt = nights(cal, t_in, t_out)
    sw = swap_rate(sym, side)(e) * nt
    pnl = side * (x - e) - sp_entry - comm * (np.abs(e) + np.abs(x)) - sw
    return pnl / dist, sw / dist, nt


# --------------------------------------------------------------------------------------------------------------- stats
def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def cell_stats(T, base=np.nan, coin=np.nan, min_trades=10):
    """T: trades of one cell with columns t (entry, datetime), R. base: random-entry baseline mean R (same side, same exits);
    coin: same moments, other side, same distances."""
    n = len(T)
    if n < min_trades: return dict(n=n)
    R = T.R.values.astype(float); t = pd.DatetimeIndex(T.t)
    IS = t < "2024-01-01"; yr = pd.Series(R).groupby(t.year).mean(); yrs = max((t.max() - t.min()).days / 365.25, 0.5)
    a_is = R[IS].mean() if IS.sum() else np.nan; a_os = R[~IS].mean() if (~IS).sum() else np.nan
    m = R.mean(); tt = tstat(R)
    cand = bool(n >= 200 and tt >= 2 and m >= 0.05 and (a_is > 0 if IS.sum() >= 30 else True) and (a_os > 0 if (~IS).sum() >= 30 else True)
                and yr.min() > -0.3 and (not np.isfinite(base) or m > base))
    return dict(n=n, per_yr=n / yrs, avgR=m, t=tt, win=(R > 0).mean(), base=base, coin=coin, is_=a_is, n_is=int(IS.sum()), oos=a_os,
                n_oos=int((~IS).sum()), last60=R[-60:].mean(), yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", worst=yr.min(),
                worst_yr=int(yr.idxmin()), by_year=" ".join(f"{y}:{v:+.2f}" for y, v in yr.items()), hold_h=T.hold_h.median() if "hold_h" in T else np.nan,
                candidate=cand)


class Pool:
    """Running sums of R by key (no trade lists kept)."""
    def __init__(self): self.acc = {}

    def add(self, key, R):
        R = np.asarray(R, float)
        if not len(R): return
        a = self.acc.setdefault(key, [0, 0.0, 0.0, 0]); a[0] += len(R); a[1] += R.sum(); a[2] += (R ** 2).sum(); a[3] += int((R > 0).sum())

    def frame(self, names):
        rows = []
        for key, (k, s, s2, pos) in self.acc.items():
            m = s / k; sd = np.sqrt(max(s2 / k - m * m, 0) * k / max(k - 1, 1)) if k > 1 else np.nan
            rows.append(dict(zip(names, key), n=k, avgR=m, t=m / sd * np.sqrt(k) if sd and sd > 0 else np.nan, win=pos / k))
        return pd.DataFrame(rows)
