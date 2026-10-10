"""q75 ports (log #75; backlog #22, #43, #44) — shared pieces for running three existing rule scripts UNCHANGED on the FTMO MT5
export: bt/breakout_retest.py (#38 rules A/B/C), bt/value_area.py (#43 V1-V3) and bt/smc_grid.py (#31b SMC grid).

Only the data loading and the cost model change (rule code is imported from the original modules):
  data   quant/universe.load (export fixes), cut to where the file is really intraday (bt/xgrid.full_intraday_start), days with
         < 50% of the usual bars dropped (as xgrid.datasets_export). Base = the finest file (M1 for US100/US500/XAUUSD, else M5,
         forex M15); M5/M15/H1 resampled from it (UTC), H4 and D1 on FTMO's server clock (xgrid.frames). Daily ATR as in the
         originals (14-day, broker day, known before the day: xgrid.daily_atr).
  costs  spread = export sp x 1.2 at entry (round trip) + commission per side (universe.commission_of) x (|entry| + |exit|)
         + swap per 17:00 New York rollover held (universe.swap_per_night with the export's spec sheet; triple night from the
         sheet: Wednesday FX/metals, Friday CFDs). Swap uses today's rates for all years (an approximation).
  exits  on the finest bars available. 1-minute exit bars: exactly as the originals (stop first). Coarser exit bars and a limit
         fill: PROTOCOL's conservative rule (bt/fx_cross_check.exit_conservative): in the fill bar the stop counts and the
         target does not; the coin flip skips the fill bar. Time limits in bars are scaled to the exit resolution (the
         originals' 5 x 1440 / 3 x 1440 one-minute bars = the same span of market time).
Statistics: per cell n, mean R, t, win, coin flip, before 2024 / from 2024, per-year means, worst year, last 60; CANDIDATE bar of
PROTOCOL rule 4 (n >= 200, t >= 2, mean >= +0.05R, both halves > 0 with >= 30 trades each, no year below -0.3R) AND mean > coin."""
import os, sys, numpy as np, pandas as pd
from numba import njit

sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
import universe as U                                     # noqa: E402
import xgrid                                             # noqa: E402
from data_standard_check import to_server                # noqa: E402

NS = 60_000_000_000
TF_MIN = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
RES = "/home/claude/ywo-lab/results"
SCR = "/tmp/claude-0/-home-claude-ywo-lab/0f9104a2-35fd-5993-8aaf-c31d50623674/scratchpad"
CAT = U.catalog()
SPECS = U.specs()

INDICES = sorted({s for s, _ in CAT if U.group_of(s) in ("us_index", "index")})
FOREX = sorted({s for s, _ in CAT if U.group_of(s) == "forex"})
METALS = sorted({s for s, _ in CAT if U.group_of(s) == "metal"})


def load_base(sym, tfs=("M1", "M5", "M15"), cols=("open", "high", "low", "close", "sp")):
    """Finest export file of sym among tfs, trimmed to real intraday history. Returns (df, tf) or (None, None)."""
    for tf in tfs:
        if (sym, tf) not in CAT: continue
        d = U.load(sym, tf, CAT)
        if d is None or len(d) < 1000: continue
        if d.index.tz is not None: d.index = d.index.tz_localize(None)
        d = d[~d.index.duplicated()].sort_index()
        d = d.loc[xgrid.full_intraday_start(d):]
        day = d.index.normalize()
        cnt = pd.Series(1, index=day).groupby(level=0).size()
        recent = cnt[cnt.index >= cnt.index[-1] - pd.Timedelta(days=365)].median()
        d = d[cnt.reindex(day).values >= 0.5 * recent]
        d = d[list(cols)].astype(float)
        d["sp"] = d.sp.fillna(d.sp.median()) * 1.2
        return d, tf
    return None, None


class Exits:
    """Exit series (finest bars), mirrored for the short side like smc_grid.TF (prices negated, high <-> low)."""
    def __init__(self, df, mirror, res_min):
        s = -1.0 if mirror else 1.0
        h, l = df.high.values * s, df.low.values * s
        if mirror: h, l = l, h
        self.h, self.l, self.c, self.o = h, l, df.close.values * s, df.open.values * s
        self.t = df.index.values.astype("datetime64[ns]"); self.ti = self.t.view("i8")
        self.sp = df.sp.values; self.res = res_min


@njit(cache=True)
def exit_idx(h, l, c, i0, i1, stop, tgt, d):
    """smc_grid.exit_nb (stop first when one bar touches both), also returning the exit bar."""
    for i in range(i0, i1):
        if d == 1:
            if l[i] <= stop: return stop, i
            if h[i] >= tgt: return tgt, i
        else:
            if h[i] >= stop: return stop, i
            if l[i] <= tgt: return tgt, i
    return c[i1 - 1], i1 - 1


def nights(t_in, t_out, triple_wd):
    """17:00 New York rollovers between entry and exit (server-day boundaries), weighted 3 on the triple day, 0 on weekends."""
    t_in = np.asarray(t_in, dtype="i8"); t_out = np.asarray(t_out, dtype="i8")
    if len(t_in) == 0: return np.zeros(0)
    a = to_server(pd.DatetimeIndex(t_in)).normalize().values.astype("datetime64[D]").astype("i8")
    b = to_server(pd.DatetimeIndex(t_out)).normalize().values.astype("datetime64[D]").astype("i8")
    span = np.maximum(b - a, 0); tot = np.zeros(len(a))
    for k in range(int(span.max())):
        wd = (a + k + 3) % 7                                    # 1970-01-01 was a Thursday
        tot += np.where(k < span, np.where(wd == triple_wd, 3.0, np.where(wd < 5, 1.0, 0.0)), 0.0)
    return tot


def swap_R(sym, side, e_abs, risk, t_in, t_out):
    """Swap over the holding period in R (positive = cost), side +1 long / -1 short (arrays)."""
    side = np.asarray(side); e_abs = np.asarray(e_abs, float); risk = np.asarray(risk, float)
    n = nights(t_in, t_out, U.triple_day(sym, SPECS)); out = np.zeros(len(n))
    for s in (1, -1):
        m = side == s
        if m.any(): out[m] = n[m] * np.broadcast_to(U.swap_per_night(sym, e_abs[m], s, SPECS), (m.sum(),)) / risk[m]
    return out


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def cell_stats(x, **keys):
    """x: trades of one cell with columns t (datetime), R, R_coin, side."""
    out = dict(keys); n = len(x); out["n"] = n
    if n == 0: return out
    x = x.sort_values("t"); R = x.R.values.astype(float); IS = (x.t < "2024-01-01").values
    yr = x.groupby(x.t.dt.year).R.mean()
    m_is = R[IS].mean() if IS.any() else np.nan; m_os = R[~IS].mean() if (~IS).any() else np.nan
    out.update(first=str(x.t.iloc[0].date()), last=str(x.t.iloc[-1].date()),
               per_yr=n / max((x.t.iloc[-1] - x.t.iloc[0]).days / 365.25, 0.25), mean=R.mean(), t=tstat(R),
               win=(R > 0).mean(), coin=x.R_coin.mean(), longs=x.R[x.side == 1].mean(), shorts=x.R[x.side == -1].mean(),
               n_is=int(IS.sum()), mean_is=m_is, n_oos=int((~IS).sum()), mean_oos=m_os, worst_year=yr.min(),
               yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", years=" ".join(f"{y}:{v:+.2f}" for y, v in yr.items()),
               last60=R[-60:].mean(), sumR=R.sum(), sumR2=(R ** 2).sum(), sumC=x.R_coin.sum())
    out["beats_coin"] = bool(out["mean"] > out["coin"])
    out["candidate"] = bool(n >= 200 and out["t"] >= 2 and out["mean"] >= 0.05 and out["n_is"] >= 30 and m_is > 0
                            and out["n_oos"] >= 30 and m_os > 0 and yr.min() > -0.3 and out["beats_coin"])
    return out


def pool(C, by):
    """Pooled R of all trades in the cells of each group (from per-cell sums)."""
    C = C[C.n > 0]
    g = C.groupby(by).agg(cells=("n", "size"), pos=("mean", lambda s: (s > 0).mean()), n=("n", "sum"), S1=("sumR", "sum"),
                          S2=("sumR2", "sum"), SC=("sumC", "sum"), passing=("candidate", "sum"))
    g["pooled"] = g.S1 / g.n
    var = (g.S2 - g.n * g.pooled ** 2) / (g.n - 1)
    g["t"] = g.pooled / np.sqrt(var / g.n); g["coin"] = g.SC / g.n
    g["luck"] = 0.025 * g.cells
    return g[["cells", "pos", "n", "pooled", "t", "coin", "passing", "luck"]].reset_index()


def append_csv(rows, path):
    df = pd.DataFrame(rows)
    if not len(df): return
    df.to_csv(path, mode="a", header=not os.path.exists(path), index=False, float_format="%.5g")
