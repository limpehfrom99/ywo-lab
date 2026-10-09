"""Cross-asset, cross-timeframe test harness. Shen's standing instruction (10 Oct 2026): test every rule on every asset and every
timeframe we have data for, not only the ones the source names, and compare strategies like a quant fund would.

A rule is a function rule(S, ctx) -> list of Fill, run on one timeframe in a frame where it trades LONG; the harness runs it again on
the mirrored prices (high <-> low, prices negated) for the short side. S is a smc_grid.TF (o h l c t sp atr nym arrays; atr = the
daily ATR known before the bar's day); ctx = dict(tf=..., S_other=<the other frame's TF>, asset=..., group=...).
Fill(t_bar, bar_ns, e, stop, tgt, kind): kind "limit" = filled at e somewhere inside the entry-timeframe bar starting at t_bar;
"stop" = a buy-stop filled when price rose to e inside that bar (same fill-bar rule); "market" = entered at e at time t_bar
exactly (e.g. the next bar's open). Optional deadline_ns (flat at that time).
Exits run on the finest bars available (gold 1-minute; FTMO 30-minute files otherwise), stop first when one bar touches both. For
limit fills, inside the exit bar where the order fills the stop counts and the target does not (order unknown); the coin flip
(other side, same entry and distances) skips that bar. Max hold: the rule's max_hold_ns or max(5 days, 30 entry bars).
Costs: spread at the fill (FTMO export spread x 1.2 for 30-minute files, the yearly FTMO gold spread for the MT4 gold file) plus
commission per side (gold 0.0007%, forex 0.0025%, stocks 0.002%, indices 0, crypto 0.0325%). Swap not included.
Output: one row per (rule, asset, timeframe) with n, avgR, t, win%, coin, before/after 2024, years > 0, worst year; plus a summary
per rule across cells (share of positive cells, pooled R, cells passing the CANDIDATE bar vs the number expected by luck)."""
import sys, os, glob, time, numpy as np, pandas as pd
from dataclasses import dataclass, field
from numba import njit
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc_grid import TF, tstat
from data_standard_check import to_server, from_server, AGG
from ftmo_data import load_export

NS = 60_000_000_000
TF_NS = {"M1": NS, "M5": 5 * NS, "M15": 15 * NS, "M30": 30 * NS, "H1": 60 * NS, "H4": 240 * NS, "D1": 1440 * NS}
COMM = {"gold": 0.000007, "fx": 0.000025, "stock": 0.00002, "index": 0.0, "crypto": 0.000325}


@dataclass
class Fill:
    t_bar: np.int64
    bar_ns: np.int64
    e: float
    stop: float
    tgt: float
    kind: str = "limit"
    deadline_ns: np.int64 = 0
    max_hold_ns: np.int64 = 0
    tag: str = ""
    be_r: float = 0.0              # > 0: move the stop to the entry after be_r x R in favour


@njit(cache=True)
def _exit(h, l, c, i0, i1, stop, tgt, d, fill_bar, e=0.0, be=0.0):
    """Long if d == 1. fill_bar >= 0: limit fill on that bar (stop counts there, target doesn't). be > 0: once a bar has traded
    be x R in favour, the stop moves to the entry from the next bar on. Returns (price, index)."""
    start = i0; st = stop; risk = abs(e - stop); armed = False
    if fill_bar >= 0:
        if d == 1 and l[fill_bar] <= st: return st, fill_bar
        if d == -1 and h[fill_bar] >= st: return st, fill_bar
        start = fill_bar + 1
    for i in range(start, i1):
        if d == 1:
            if l[i] <= st: return st, i
            if h[i] >= tgt: return tgt, i
            if be > 0 and not armed and h[i] >= e + be * risk: st = e; armed = True
        else:
            if h[i] >= st: return st, i
            if l[i] <= tgt: return tgt, i
            if be > 0 and not armed and l[i] <= e - be * risk: st = e; armed = True
    j = i1 - 1                                     # time limit (or the data ended right after the fill): out at that close
    return c[j], j


class ExitSeries:
    def __init__(self, df):
        self.t = df.index.values.astype("datetime64[ns]").view("i8")
        self.h, self.l, self.c, self.o, self.sp = (df[k].values.astype(float) for k in ("high", "low", "close", "open", "sp"))

    def mirrored(self):
        m = ExitSeries.__new__(ExitSeries)
        m.t = self.t; m.h, m.l, m.c, m.o, m.sp = -self.l, -self.h, -self.c, -self.o, self.sp
        return m


def resolve(fill, X, d_coin_skip=True):
    """Trade LONG in this frame. Returns (R, R_coin, rr, hold_hours, t_entry) or None."""
    t0 = fill.t_bar; e, stop, tgt = fill.e, fill.stop, fill.tgt
    risk = e - stop
    if risk <= 0 or tgt <= e: return None
    i0 = np.searchsorted(X.t, t0)
    if i0 >= len(X.t): return None
    max_hold = fill.max_hold_ns or max(5 * 1440 * NS, 30 * fill.bar_ns)
    t_end = t0 + max_hold
    if fill.deadline_ns: t_end = min(t_end, fill.deadline_ns)
    i1 = np.searchsorted(X.t, t_end)
    if i1 <= i0: return None
    fb = -1
    if fill.kind in ("limit", "stop"):                     # limit: price came down to e; stop order: price rose to e
        ie = np.searchsorted(X.t, t0 + fill.bar_ns)
        w = np.flatnonzero(X.l[i0:ie] <= e) if fill.kind == "limit" else np.flatnonzero(X.h[i0:ie] >= e)
        fb = i0 + (w[0] if len(w) else 0)
        if fb >= i1: return None
    Xp, xi = _exit(X.h, X.l, X.c, i0, i1, stop, tgt, 1, fb, e, fill.be_r)
    Xf, _ = _exit(X.h, X.l, X.c, (fb + 1) if fb >= 0 else i0, i1, e + risk, 2 * e - tgt, -1, -1, e, fill.be_r)
    sp = X.sp[fb if fb >= 0 else i0]
    return Xp, Xf, sp, (tgt - e) / risk, (X.t[min(xi, len(X.t) - 1)] - t0) / 3.6e12, X.t[fb if fb >= 0 else i0]


@dataclass
class Dataset:
    name: str
    group: str
    base: pd.DataFrame            # UTC-indexed bars with open high low close sp
    base_tf: str
    exits: pd.DataFrame = None    # finest bars for exits (defaults to base)
    tfs: tuple = ()


H4_OFFSET_H = 0     # phase check: H4 bars start at server hour 0/4/8/... + this (xrun.py --h4-offset); 0 = FTMO's own H4 candles


def frames(base, base_tf):
    """All timeframes >= the base one. H4 and D1 on FTMO's server clock (17:00 New York)."""
    out = {base_tf: base}
    srv = base.copy(); srv.index = to_server(base.index)
    for tf, rule in (("M5", "5min"), ("M15", "15min"), ("M30", "30min"), ("H1", "1h")):
        if TF_NS[tf] > TF_NS[base_tf]: out[tf] = base.resample(rule, label="left", closed="left").agg(AGG).dropna()
    for tf, rule in (("H4", "4h"), ("D1", "1D")):
        off = f"{H4_OFFSET_H}h" if (tf == "H4" and H4_OFFSET_H) else None
        x = srv.resample(rule, label="left", closed="left", offset=off).agg(AGG).dropna()
        if tf == "D1": x = x[x.index.weekday < 5]
        u = from_server(x.index); x = x[~u.isna()]; x.index = u[~u.isna()]; out[tf] = x.sort_index()
    return out


def daily_atr(base):
    key = to_server(base.index).normalize()
    d1 = base.groupby(key).agg(AGG); d1 = d1[d1.index.weekday < 5]; pc = d1.close.shift(1)
    d1["atr"] = pd.concat([d1.high - d1.low, (d1.high - pc).abs(), (d1.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    u = from_server(d1.index); d1 = d1[~u.isna()]; d1.index = u[~u.isna()]
    return d1[["atr"]]


def ftmo_csv(path, start=None, spx=1.2):
    d = load_export(path); d.index = from_server(pd.DatetimeIndex(d.index)); d = d[~d.index.isna()].sort_index()
    d = d[["open", "high", "low", "close", "sp"]].copy(); d["sp"] = d.sp * spx
    return d.loc[start:] if start else d


def datasets(which=None):
    """The data in hand (until the full export arrives): gold 1-minute 2012-26; FTMO 30-minute forex 2018-26, US100/US500/TSLA/
    AAPL 2022-26 (earlier years have no 30-minute history), BTCUSD 2020-26."""
    out = []
    if which is None or "gold" in which:
        g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]
        out.append(Dataset("XAUUSD", "gold", g, "M1", g, ("M5", "M15", "M30", "H1", "H4", "D1")))
    for sym, grp, base, start in (("EURUSD", "fx", "/home/claude/data/fx2", None), ("GBPUSD", "fx", "/home/claude/data/fx2", None),
                                  ("USDCHF", "fx", "/home/claude/data/fx2", None), ("US100.cash", "index", "/home/claude/data/assets", "2021-12-01"),
                                  ("US500.cash", "index", "/home/claude/data/assets", "2021-12-01"), ("TSLA", "stock", "/home/claude/data/assets", "2021-12-01"),
                                  ("AAPL", "stock", "/home/claude/data/assets", "2021-12-01"), ("BTCUSD", "crypto", "/home/claude/data/assets", "2020-09-01")):
        if which is not None and sym not in which and grp not in which: continue
        f = glob.glob(f"{base}/{sym}_M30_*.csv")
        if not f: continue
        d = ftmo_csv(f[0], start)
        out.append(Dataset(sym, grp, d, "M30", d, ("M30", "H1", "H4", "D1")))
    return out


def run_rule(rule, name, ds_list, tfs=None, min_trades=10, verbose=True):
    rows = []; trades = []
    for ds in ds_list:
        fr = frames(ds.base, ds.base_tf); atr_df = daily_atr(ds.base)
        X = ExitSeries(ds.exits if ds.exits is not None else ds.base); Xm = X.mirrored()
        comm = COMM[ds.group]
        for tf in (tfs or ds.tfs):
            if tf not in fr or tf not in ds.tfs: continue
            S = {m: TF(fr[tf], m, atr_df) for m in (False, True)}
            for m in (False, True):
                ctx = dict(tf=tf, S_other=S[not m], asset=ds.name, group=ds.group, bar_ns=TF_NS[tf], mirrored=m)
                Xs = Xm if m else X
                for f in rule(S[m], ctx):
                    r = resolve(f, Xs)
                    if r is None: continue
                    Xp, Xf, sp, rr, hold, t_in = r; e = f.e; risk = e - f.stop
                    if risk < 2e-5 * abs(e): continue                    # a stop within 0.2 bp of the entry is a data artefact
                    cost = sp + comm * (abs(e) + abs(Xp)); cost_f = sp + comm * (abs(e) + abs(Xf))
                    trades.append((name, ds.name, ds.group, tf, pd.Timestamp(int(t_in)), -1 if m else 1, (Xp - e - cost) / risk,
                                   (e - Xf - cost_f) / risk, rr, hold, f.tag))
    T = pd.DataFrame(trades, columns=["rule", "asset", "group", "tf", "t", "side", "R", "R_coin", "rr", "hold_h", "tag"])
    for (a, tf), x in T.groupby(["asset", "tf"], sort=False):
        rows.append(cell_stats(name, a, x.group.iloc[0], tf, x, min_trades))
    C = pd.DataFrame(rows)
    if verbose and len(C): print_cells(C)
    return C, T


def cell_stats(name, asset, group, tf, x, min_trades=10):
    n = len(x)
    if n < min_trades: return dict(rule=name, asset=asset, group=group, tf=tf, n=n)
    IS = x.t < "2024-01-01"; yr = x.groupby(x.t.dt.year).R.mean(); yrs = max((x.t.max() - x.t.min()).days / 365.25, 0.5)
    t_ = tstat(x.R); a_is = x.R[IS].mean() if IS.sum() else np.nan; a_os = x.R[~IS].mean() if (~IS).sum() else np.nan
    cand = (n >= 200 and t_ >= 2 and x.R.mean() >= 0.05 and (a_is > 0 if IS.sum() >= 30 else True) and (a_os > 0 if (~IS).sum() >= 30 else True)
            and yr.min() > -0.3)
    return dict(rule=name, asset=asset, group=group, tf=tf, n=n, per_yr=n / yrs, avgR=x.R.mean(), t=t_, win=(x.R > 0).mean(),
                coin=x.R_coin.mean(), longs=x.R[x.side == 1].mean(), shorts=x.R[x.side == -1].mean(), is_=a_is, oos=a_os,
                yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", worst=yr.min(), hold_h=x.hold_h.median(), rr=x.rr.median(), candidate=cand)


def print_cells(C):
    for _, r in C.iterrows():
        if not np.isfinite(r.get("avgR", np.nan)): print(f"{r.rule[:34]:34s} {r.asset:10s} {r.tf:3s} n={int(r.n)}"); continue
        print(f"{r.rule[:34]:34s} {r.asset:10s} {r.tf:3s} n={int(r.n):5d} ({r.per_yr:4.0f}/yr) avgR={r.avgR:+.3f} t={r.t:+.1f} win={r.win:.0%} "
              f"coin={r.coin:+.3f} | L {r.longs:+.3f} S {r.shorts:+.3f} | <24 {r.is_:+.3f} 24+ {r.oos:+.3f} | yrs>0 {r.yrs_pos} worst {r.worst:+.2f}"
              f" | hold {r.hold_h:.0f}h rr {r.rr:.1f}{'  << CANDIDATE bar' if r.candidate else ''}", flush=True)


def summary(C, T=None):
    """Per rule across cells: how many cells, share positive, pooled R, cells passing the bar vs expected by luck (~2.5% of cells)."""
    out = []
    for name, x in C.dropna(subset=["avgR"]).groupby("rule"):
        pooled = T[T.rule == name].R if T is not None else None
        out.append(dict(rule=name, cells=len(x), pos=(x.avgR > 0).mean(), median_cell=x.avgR.median(),
                        pooled=pooled.mean() if pooled is not None else np.nan, pooled_t=tstat(pooled) if pooled is not None else np.nan,
                        trades=int(x.n.sum()), passing=int(x.candidate.sum()), by_luck=round(0.025 * len(x), 1)))
    return pd.DataFrame(out)


COMM.update({"metal": 0.000007, "energy": 0.0, "soft": 0.0})      # FTMO: metals as gold; energy / softs assumed 0 (check the spec sheet)
GROUP = {"forex": "fx", "metal": "metal", "us_index": "index", "index": "index", "stock": "stock", "crypto": "crypto", "energy": "energy", "soft": "soft"}


def full_intraday_start(d):
    """First month from which the file really is intraday: bars per active day >= 60% of the median over the last 12 months.
    FTMO's index/stock histories before 2021-22 hold one bar a day (or hourly bars) under an M1/M5 label; left in, they would be
    resampled into fake 5-minute bars."""
    per_day = pd.Series(1, index=d.index.normalize()).groupby(level=0).size()
    recent = per_day[per_day.index >= per_day.index[-1] - pd.Timedelta(days=365)].median()
    by_month = per_day.groupby(per_day.index.to_period("M")).median()
    ok = by_month[by_month >= 0.6 * recent]
    if not len(ok): return d.index[0]
    # first month after which every month stays full (a later dip, e.g. holidays, is tolerated if the next 3 months are full)
    months = list(by_month.index); good = set(ok.index)
    for i, m in enumerate(months):
        if all(x in good for x in months[i:i + 4]): return m.to_timestamp()
    return ok.index[0].to_timestamp()


def datasets_export(groups=None, symbols=None, min_years=1.5):
    """Generator over the full FTMO export (quant/universe catalog -> /home/claude/data/x): per symbol the finest intraday file that
    covers >= min_years of REAL intraday bars (M1, else M5, else M15, else M30), trimmed to where it becomes intraday, is the base
    and the exit series; timeframes from it up to D1. Stock clocks fixed in universe.load. One symbol at a time. XAUUSD comes out
    as group 'gold'. Commission per side from universe.commission_of."""
    sys.path.insert(0, "/home/claude/ywo-lab/quant")
    import universe as U
    cat = U.catalog()
    for sym in sorted({s for s, _ in cat}):
        grp = "gold" if sym.startswith("XAUUSD") else GROUP.get(U.group_of(sym), U.group_of(sym))
        if groups and grp not in groups: continue
        if symbols and sym not in symbols: continue
        for base_tf in ("M1", "M5", "M15", "M30"):
            if (sym, base_tf) not in cat: continue
            d = U.load(sym, base_tf, cat)
            if d is None or len(d) < 1000: continue
            d.index = d.index.tz_localize(None) if d.index.tz is not None else d.index
            d = d[~d.index.duplicated()].sort_index()
            if U.group_of(sym) == "stock":                       # CFD session only (pre/after-market bars in 2015-19 files)
                ny = d.index.tz_localize("UTC").tz_convert("America/New_York"); mins = ny.hour * 60 + ny.minute
                d = d[(mins >= 570) & (mins < 960)]
            d = d.loc[full_intraday_start(d):]
            per_day = pd.Series(1, index=d.index.normalize()).groupby(level=0).transform("size")
            recent = pd.Series(1, index=d.index.normalize()).groupby(level=0).size()
            recent = recent[recent.index >= recent.index[-1] - pd.Timedelta(days=365)].median()
            d = d[per_day.values >= 0.5 * recent]                # drop days that are really hourly/daily bars
            if len(d) < 1000 or (d.index[-1] - d.index[0]).days / 365.25 < min_years: continue
            d = d[["open", "high", "low", "close", "sp"]].copy(); d["sp"] = d.sp * 1.2
            tfs = tuple(tf for tf in ("M5", "M15", "M30", "H1", "H4", "D1") if TF_NS[tf] >= TF_NS[base_tf] and tf != "M1")
            ds = Dataset(sym, grp, d, base_tf, d, tfs); ds.comm = U.commission_of(sym)
            yield ds
            break


def run_many(rules, ds_iter, tfs=None, verbose=False, out_dir=None):
    """rules: {name: fn}. Datasets outer, rules inner (each symbol's frames are built once). Trades are kept as one compact
    frame per symbol (categoricals + float32) so ~10M trades fit in memory; out_dir also saves each symbol's trades.
    Returns (cells, trades)."""
    cols = ["rule", "asset", "group", "tf", "t", "side", "R", "R_coin", "rr", "hold_h", "tag"]
    chunks = []; t0 = time.time(); n_all = 0
    for ds in ds_iter:
        rows = []
        try:
            fr = frames(ds.base, ds.base_tf); atr_df = daily_atr(ds.base)
        except Exception as e:
            print(f"  {ds.name}: frame error {e!r}", flush=True); continue
        X = ExitSeries(ds.exits if ds.exits is not None else ds.base); Xm = X.mirrored(); comm = getattr(ds, "comm", None)
        if comm is None: comm = COMM.get(ds.group, 0.0)
        for tf in (tfs or ds.tfs):
            if tf not in fr or tf not in ds.tfs or len(fr[tf]) < 100: continue
            S = {m: TF(fr[tf], m, atr_df) for m in (False, True)}
            for name, fn in rules.items():
                for m in (False, True):
                    ctx = dict(tf=tf, S_other=S[not m], asset=ds.name, group=ds.group, bar_ns=TF_NS[tf], mirrored=m)
                    Xs = Xm if m else X
                    try: fills = fn(S[m], ctx)
                    except Exception as e:
                        print(f"  {ds.name} {tf} {name[:30]}: {e!r}", flush=True); continue
                    for f in fills:
                        r = resolve(f, Xs)
                        if r is None: continue
                        Xp, Xf, sp, rr, hold, t_in = r; e = f.e; risk = e - f.stop
                        if risk < 2e-5 * abs(e): continue
                        cost = sp + comm * (abs(e) + abs(Xp)); cost_f = sp + comm * (abs(e) + abs(Xf))
                        rows.append((name, ds.name, ds.group, tf, int(t_in), -1 if m else 1, (Xp - e - cost) / risk,
                                     (e - Xf - cost_f) / risk, rr, hold, f.tag))
        if rows:
            T = pd.DataFrame(rows, columns=cols); del rows
            T["t"] = pd.to_datetime(T.t.values)
            for c in ("rule", "asset", "group", "tf", "tag"): T[c] = T[c].astype("category")
            for c in ("R", "R_coin", "rr", "hold_h"): T[c] = T[c].astype("float32")
            T["side"] = T.side.astype("int8")
            if out_dir: os.makedirs(out_dir, exist_ok=True); T.to_pickle(os.path.join(out_dir, f"{ds.name}.pkl"))
            chunks.append(T); n_all += len(T)
        print(f"  {ds.name} {ds.base_tf} {ds.base.index[0].date()}..{ds.base.index[-1].date()} done ({time.time() - t0:.0f}s, "
              f"{n_all} trades so far)", flush=True)
    if not chunks: return pd.DataFrame(), pd.DataFrame(columns=cols)
    T = pd.concat(chunks, ignore_index=True)
    for c in ("rule", "asset", "group", "tf", "tag"): T[c] = T[c].astype(str)
    C = pd.DataFrame([cell_stats(n, a, x.group.iloc[0], tf, x) for (n, a, tf), x in T.groupby(["rule", "asset", "tf"], sort=False)])
    if verbose and len(C): print_cells(C)
    return C, T
