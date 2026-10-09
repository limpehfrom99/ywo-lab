"""Idea 27: robustness checks (bt/robust.py, after Masters 2018) on the live and candidate strategies.

A. Opening candle (live rule): 4 symbols (TSLA, AAPL, US100, US500) x candle 30/60 min x exit hold/3R x Fed days
   skipped or not = 32 cells, M30 2022-2026, FTMO costs.
   Null = direction labels shuffled across days (one shuffle per symbol, shared by its 8 cells): random timing with
   the same long/short mix, exact under "the candle says nothing about the rest of the day". 5,000 shuffles.
   p_best = chance the BEST of the 32 random cells does at least as well -> corrects for having picked the winner.
   Also an approximate 11-symbol pool (the laptop scan used 11 symbols; the 7 missing ones drawn from these 4).
B. Noise band (#26a): 3 symbols x 5 variants = 15 cells, M30 2021-2026. Null = 30-minute bars shuffled across days
   within the same time-of-day slot (gaps and bar shapes separately), strategy re-run in full. 1,000 shuffles.
C. IBS (#24/#26c): US100/US500 x published / IBS<0.2 = 4 cells. Null = random entry days, same holding periods.
D. CSCV probability of overfitting on A and B. E. BCa 95% lower bounds. F. Drawdown bounds for the live plan.
"""
import sys, glob, time
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from lab import ny_session, full_days, opening_candle
from news import load_calendar, fed_days
import robust
from noise_band import rth_bars, session_matrix, run as nb_run_loop
from ibs_published import daily as ibs_daily, run as ibs_run

T0 = time.time()
FED = set(pd.to_datetime(list(fed_days(load_calendar("/home/claude/news/news_usd.csv")))))
OC_SYMS = {"TSLA": 0.00002, "AAPL": 0.00002, "US100.cash": 0.0, "US500.cash": 0.0}


def say(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ A. opening candle, both directions per day
def _trade(side, entry, stop, target_r, ro, rh, rl, rc, sp0, commission):
    """lab.opening_candle's exit logic for one trade. Returns (R after costs, stop distance in % of price)."""
    risk = (entry - stop) * side
    if risk <= 0:
        return np.nan, np.nan
    tgt = entry + side * target_r * risk if target_r else None
    px = rc[-1]
    for j in range(len(ro)):
        if side == 1:
            if rl[j] <= stop: px = min(stop, ro[j]); break
            if tgt is not None and rh[j] >= tgt: px = max(tgt, ro[j]); break
        else:
            if rh[j] >= stop: px = max(stop, ro[j]); break
            if tgt is not None and rl[j] <= tgt: px = min(tgt, ro[j]); break
    cost = sp0 + commission * (entry + px)
    return (side * (px - entry) - cost) / risk, risk / entry * 100


def oc_both(d, first_bars=1, target_r=None, commission=0.0, start="2022-01-01"):
    """Per day: the opening candle's direction, the rule's trade (stop at the candle's far end, exactly
    lab.opening_candle) and the MIRROR trade: the opposite direction with the same stop distance on the other side.
    RL / RS = the long / short outcome of the day (one of them is the rule's trade, the other the mirror), so a
    random direction keeps the same risk per trade. Doji days (no direction): far-end stops both ways."""
    s = ny_session(d, start)
    days = full_days(s, 13)
    rows = []
    for day, b in s.groupby("nyd"):
        if day not in days or len(b) != 13:
            continue
        f = b.iloc[:first_bars]
        o, c, hi, lo = f.open.iloc[0], f.close.iloc[-1], f.high.max(), f.low.min()
        dr = 0 if c == o else (1 if c > o else -1)
        rest = b.iloc[first_bars:]
        args = (rest.open.values, rest.high.values, rest.low.values, rest.close.values, rest.sp.iloc[0], commission)
        entry = rest.open.iloc[0]
        if dr == 0:
            L = _trade(1, entry, lo, target_r, *args); S = _trade(-1, entry, hi, target_r, *args)
        else:
            far = lo if dr == 1 else hi
            real = _trade(dr, entry, far, target_r, *args)
            if np.isnan(real[0]):
                mirror = (np.nan, np.nan)
            else:
                dist = (entry - far) * dr
                mirror = _trade(-dr, entry, entry + dr * dist, target_r, *args)
            L, S = (real, mirror) if dr == 1 else (mirror, real)
        rows.append((day, dr, L[0], S[0], L[1], S[1]))
    return pd.DataFrame(rows, columns=["day", "dir", "RL", "RS", "stopL", "stopS"]).set_index("day")


def oc_section(n_perm=5000):
    say("\n=== A. Opening candle, direction only: 32 cells, direction labels shuffled (same stop distance), 5,000 shuffles ===")
    cells, sym_data = {}, {}
    for sym, comm in OC_SYMS.items():
        d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0])
        per = {}
        for fb in (1, 2):
            for tg in (None, 3.0):
                b = oc_both(d, fb, tg, comm)
                if fb == 1 and tg is None:          # exactness check vs the lab's own function
                    ref = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01")
                    real = np.where(b.dir == 1, b.RL, np.where(b.dir == -1, b.RS, np.nan))
                    mine = pd.Series(real, index=b.index).dropna()
                    common = mine.index.intersection(ref.index)
                    assert len(common) == len(ref) == len(mine) and np.allclose(mine[common], ref.R[common], atol=1e-12), sym
                per[(fb, tg)] = b
        days = per[(1, None)].index
        assert all(v.index.equals(days) for v in per.values())
        sym_data[sym] = (days, per)
    say(f"   check: per-day both-direction simulator reproduces lab.opening_candle exactly on all 4 symbols  [{time.time() - T0:.0f}s]")

    rng = np.random.default_rng(27)
    real, null_cols, labels, per_sym_null_max = {}, [], [], {}
    for sym, (days, per) in sym_data.items():
        n = len(days); isfed = days.isin(list(FED))
        P = np.array([rng.permutation(n) for _ in range(n_perm)])          # one shuffle per perm, shared by the cells
        sym_cols = []
        for (fb, tg), b in per.items():
            dr, RL, RS = b.dir.values, b.RL.values, b.RS.values
            Rr = np.where(dr == 1, RL, np.where(dr == -1, RS, np.nan))
            dn = dr[P]
            Rn = np.where(dn == 1, RL[None, :], np.where(dn == -1, RS[None, :], np.nan))
            for fed in (True, False):
                name = f"{sym.replace('.cash', '')} {30 * fb}m {'3R' if tg else 'hold'} {'skipFed' if fed else 'allDays'}"
                keep = ~isfed if fed else np.ones(n, bool)
                real[name] = np.nanmean(Rr[keep])
                col = np.nanmean(Rn[:, keep], axis=1)
                null_cols.append(col); sym_cols.append(col); labels.append(name)
        per_sym_null_max[sym] = np.max(np.array(sym_cols), axis=0)
    null = np.array(null_cols).T
    tab = robust.mcpt_select(pd.Series(real)[labels], null)
    pd.set_option("display.width", 200)
    say(tab.sort_values("real", ascending=False).round(4).to_string())
    tab.to_csv("/home/claude/bt/robust_oc_direction.csv")
    say(f"   null: average random cell {tab.attrs['null_cell_avg']:+.4f}R, average BEST of 32 random cells "
        f"{tab.attrs['null_best_avg']:+.4f}R (95th pct {tab.attrs['null_best_q95']:+.4f})")
    # approximate 11-symbol pool: 7 extra symbols drawn from these 4 symbols' per-shuffle best cells
    pools = np.array(list(per_sym_null_max.values()))                    # 4 x n_perm
    k = pools.shape[1]
    extra = pools[rng.integers(0, 4, (k, 7)), rng.integers(0, k, (k, 7))]
    best11 = np.maximum(pools.max(axis=0), extra.max(axis=1))
    for name in ("TSLA 30m hold skipFed", "US100 30m hold skipFed"):
        v = real[name]
        say(f"   {name}: p vs best of 11 symbols (approx.) = {(1 + np.sum(best11 >= v)) / (k + 1):.4f}, "
            f"skill after an 11-symbol search = {v - best11.mean():+.4f}R (avg best of 11 random: {best11.mean():+.4f})")
    # matrix for CSCV: union of days, R per cell (0 = no trade)
    allday = sorted(set().union(*[set(v[0]) for v in sym_data.values()]))
    M = pd.DataFrame(0.0, index=pd.DatetimeIndex(allday), columns=labels)
    for sym, (days, per) in sym_data.items():
        isfed = days.isin(list(FED))
        for (fb, tg), b in per.items():
            Rr = np.where(b.dir == 1, b.RL, np.where(b.dir == -1, b.RS, np.nan))
            for fed in (True, False):
                name = f"{sym.replace('.cash', '')} {30 * fb}m {'3R' if tg else 'hold'} {'skipFed' if fed else 'allDays'}"
                x = pd.Series(Rr, index=days)
                if fed:
                    x[isfed] = np.nan
                M.loc[days, name] = x.fillna(0.0).values
    return tab, M, sym_data


# ------------------------------------------------------- A2. opening candle under the time-of-day bar shuffle
def oc_vec(A, fb=1, target_r=None, comm=0.0):
    """Vectorised lab.opening_candle on day arrays (n days x 13 bars). Returns R per day (NaN = no trade)."""
    Ob, Hb, Lb, Cb, SPb = A["open"], A["high"], A["low"], A["close"], A["sp"]
    o, c = Ob[:, 0], Cb[:, fb - 1]
    hi, lo = Hb[:, :fb].max(axis=1), Lb[:, :fb].min(axis=1)
    dr = np.sign(c - o)
    entry, sp0 = Ob[:, fb], SPb[:, fb]
    stop = np.where(dr == 1, lo, hi)
    risk = (entry - stop) * dr
    ok = (dr != 0) & (risk > 0)
    tgt = entry + dr * (target_r or 0) * risk
    px = Cb[:, -1].copy(); done = ~ok
    for j in range(fb, 13):
        hs = np.where(dr == 1, Lb[:, j] <= stop, Hb[:, j] >= stop) & ~done
        px = np.where(hs, np.where(dr == 1, np.minimum(stop, Ob[:, j]), np.maximum(stop, Ob[:, j])), px)
        done |= hs
        if target_r:
            ht = np.where(dr == 1, Hb[:, j] >= tgt, Lb[:, j] <= tgt) & ~done
            px = np.where(ht, np.where(dr == 1, np.maximum(tgt, Ob[:, j]), np.minimum(tgt, Ob[:, j])), px)
            done |= ht
    with np.errstate(divide="ignore", invalid="ignore"):
        R = (dr * (px - entry) - (sp0 + comm * (entry + px))) / risk
    return np.where(ok, R, np.nan)


def oc_shuffle_section(n_perm=2000):
    say(f"\n=== A2. Opening candle: 32 cells, time-of-day bar shuffle (removes trend days AND direction), {n_perm:,} shuffles ===")
    rng = np.random.default_rng(2727)
    real, labels, null_cols, sym_best = {}, [], [], []
    variants = [(fb, tg) for fb in (1, 2) for tg in (None, 3.0)]
    for sym, comm in OC_SYMS.items():
        days, A = day_arrays(sym, start="2022-01-01")
        d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0])
        ref = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01")
        mine = pd.Series(oc_vec(A, 1, None, comm), index=days).dropna()
        assert mine.index.equals(ref.index) and np.allclose(mine.values, ref.R.values, atol=1e-12), sym
        isfed = days.isin(list(FED))
        masks = {True: ~isfed, False: np.ones(len(days), bool)}
        flat = {k: A[k].ravel() for k in A}
        slots = np.tile(np.arange(13), len(days))
        cells = [(fb, tg, fed) for fb, tg in variants for fed in (True, False)]
        for fb, tg, fed in cells:
            Rr = oc_vec(A, fb, tg, comm)
            name = f"{sym.replace('.cash', '')} {30 * fb}m {'3R' if tg else 'hold'} {'skipFed' if fed else 'allDays'}"
            real[name] = np.nanmean(Rr[masks[fed]]); labels.append(name)
        cols = np.empty((n_perm, len(cells)))
        for p in range(n_perm):                      # one shuffle per perm, shared by the symbol's 8 cells
            o, h, l, c, sp = robust.permute_bars(flat["open"], flat["high"], flat["low"], flat["close"], slots, rng,
                                                 extra=(flat["sp"],))
            B = {"open": o.reshape(-1, 13), "high": h.reshape(-1, 13), "low": l.reshape(-1, 13),
                 "close": c.reshape(-1, 13), "sp": sp.reshape(-1, 13)}
            for fb, tg in variants:
                Rn = oc_vec(B, fb, tg, comm)
                for fed in (True, False):
                    cols[p, cells.index((fb, tg, fed))] = np.nanmean(Rn[masks[fed]])
        null_cols.extend(cols.T)
        sym_best.append(cols.max(axis=1))
        say(f"   {sym}: done  [{time.time() - T0:.0f}s]")
    say("   check: vectorised opening-candle runner reproduces lab.opening_candle exactly on all 4 symbols")
    null = np.array(null_cols).T
    tab = robust.mcpt_select(pd.Series(real)[labels], null)
    say(tab.sort_values("real", ascending=False).round(4).to_string())
    say(f"   null: average shuffled cell {tab.attrs['null_cell_avg']:+.4f}R, average BEST of 32 shuffled cells "
        f"{tab.attrs['null_best_avg']:+.4f}R (95th pct {tab.attrs['null_best_q95']:+.4f})")
    # the laptop scan searched ~11 symbols: add 7 more symbols drawn from these 4 symbols' shuffled best cells
    pools = np.array(sym_best); k = pools.shape[1]
    extra = pools[rng.integers(0, len(pools), (k, 7)), rng.integers(0, k, (k, 7))]
    best11 = np.maximum(pools.max(axis=0), extra.max(axis=1))
    for name in ("TSLA 30m hold skipFed", "US100 30m hold skipFed"):
        v = real[name]
        say(f"   {name}: p vs the best of an 11-symbol search (approx.) {(1 + np.sum(best11 >= v)) / (k + 1):.3f}, "
            f"edge left after that search {v - best11.mean():+.4f}R (avg best of 11 shuffled symbols {best11.mean():+.4f}R)")
    tab.to_csv("/home/claude/bt/robust_oc_shuffle.csv")
    return tab


# ------------------------------------------------------------------------------- B. noise band, bar permutation
def day_arrays(sym, start="2021-06-01"):
    d = rth_bars(sym); d = d[d.index >= start]
    times = pd.date_range("2000-01-01 09:30", periods=13, freq="30min").strftime("%H:%M")
    s = d[d.nyt.isin(times)].sort_index()
    g = s.groupby("nyd")
    full = g.size()[lambda x: x == 13].index
    s = s[s.nyd.isin(full)]
    A = {c: s[c].values.reshape(-1, 13) for c in ("open", "high", "low", "close", "tickvol", "sp")}
    return pd.DatetimeIndex(full), A


def vwap(A):
    tp = (A["high"] + A["low"] + A["close"]) / 3
    v = np.where(A["tickvol"] == 0, 1, A["tickvol"])
    return np.cumsum(tp * v, axis=1) / np.cumsum(v, axis=1)


def nb_vec(O, C, VW, SP, comm=0.0, lookback=14, vm=1.0, use_vwap=True):
    """Vectorised noise_band.run (all days at once, mark by mark). Returns daily return at 1x (NaN = no trade day)."""
    n, K = C.shape
    sig = pd.DataFrame(np.abs(C / O[:, None] - 1)).rolling(lookback).mean().shift(1).values * vm
    prev_c = np.r_[np.nan, C[:-1, -1]]
    dret = np.r_[np.nan, C[1:, -1] / C[:-1, -1] - 1]
    lev = np.minimum(4.0, 0.02 / pd.Series(dret).rolling(14).std().shift(1).values)
    valid = ~np.isnan(sig[:, 0]) & ~np.isnan(prev_c) & ~np.isnan(lev)
    ub = np.maximum(O, prev_c)[:, None] * (1 + sig); lb = np.minimum(O, prev_c)[:, None] * (1 - sig)
    pos = np.zeros(n); entry = np.ones(n); r = np.zeros(n)
    for k in range(K):
        p = C[:, k]
        if k == K - 1:
            tgt = np.zeros(n)
        elif use_vwap:
            tgt = np.where(p > np.maximum(ub[:, k], VW[:, k]), 1.0, np.where(p < np.minimum(lb[:, k], VW[:, k]), -1.0, 0.0))
        else:
            tgt = np.where(p > ub[:, k], 1.0, np.where(p < lb[:, k], -1.0, pos))
        ch = valid & (tgt != pos)
        cs = SP[:, k] / 2 / p + comm
        r += np.where(ch & (pos != 0), pos * (p / entry - 1) - cs, 0.0)
        op = ch & (tgt != 0)
        r -= np.where(op, cs, 0.0)
        entry = np.where(op, p, entry)
        pos = np.where(ch, tgt, pos)
    return np.where(valid, r, np.nan)


NB_VARIANTS = {"published": dict(), "opposite-band": dict(use_vwap=False), "band x0.75": dict(vm=0.75),
               "band x1.25": dict(vm=1.25), "band x1.5": dict(vm=1.5)}
NB_SYMS = {"US100.cash": 0.0, "US500.cash": 0.0, "TSLA": 0.00002}


def sharpe(x):
    x = x[~np.isnan(x)]
    return x.mean() / x.std(ddof=1) * np.sqrt(252)


def nb_section(n_perm=1000):
    say(f"\n=== B. Noise band: 15 cells, time-of-day bar shuffle, {n_perm:,} shuffles ===")
    real, labels, null_cols, series = {}, [], [], {}
    rng = np.random.default_rng(2626)
    for sym, comm in NB_SYMS.items():
        days, A = day_arrays(sym)
        # exactness: arrays == session_matrix, vectorised runner == loop runner
        d = rth_bars(sym); d = d[d.index >= "2021-06-01"]
        days2, O2, C2, VW2, SP2 = session_matrix(d)
        VW = vwap(A)
        assert days.equals(days2) and np.allclose(A["open"][:, 0], O2) and np.allclose(A["close"], C2) and np.allclose(VW, VW2)
        loop, _, _ = nb_run_loop(days2, O2, C2, VW2, SP2, comm=comm)
        vec = nb_vec(A["open"][:, 0], A["close"], VW, A["sp"], comm)
        assert np.allclose(np.nan_to_num(loop.values, nan=9), np.nan_to_num(vec, nan=9), atol=1e-12), sym
        for vname, kw in NB_VARIANTS.items():
            x = nb_vec(A["open"][:, 0], A["close"], VW, A["sp"], comm, **kw)
            name = f"{sym.replace('.cash', '')} {vname}"
            real[name] = sharpe(x); labels.append(name); series[name] = pd.Series(x, index=days)
        flat = {c: A[c].ravel() for c in A}
        slots = np.tile(np.arange(13), len(days))
        cols = np.full((n_perm, len(NB_VARIANTS)), np.nan)
        for p in range(n_perm):
            o, h, l, c, v, sp = robust.permute_bars(flat["open"], flat["high"], flat["low"], flat["close"], slots,
                                                    rng, extra=(flat["tickvol"], flat["sp"]))
            B = {"open": o.reshape(-1, 13), "high": h.reshape(-1, 13), "low": l.reshape(-1, 13),
                 "close": c.reshape(-1, 13), "tickvol": v.reshape(-1, 13), "sp": sp.reshape(-1, 13)}
            vw = vwap(B)
            for j, kw in enumerate(NB_VARIANTS.values()):
                cols[p, j] = sharpe(nb_vec(B["open"][:, 0], B["close"], vw, B["sp"], comm, **kw))
        null_cols.extend(cols.T)
        say(f"   {sym}: done  [{time.time() - T0:.0f}s]")
    say("   check: vectorised runner reproduces noise_band.run exactly on all 3 symbols")
    null = np.array(null_cols).T
    tab = robust.mcpt_select(pd.Series(real)[labels], null)
    say(tab.sort_values("real", ascending=False).round(3).to_string())
    tab.to_csv("/home/claude/bt/robust_noise_band.csv")
    say(f"   null (Sharpe): average random cell {tab.attrs['null_cell_avg']:+.3f}, average BEST of 15 "
        f"{tab.attrs['null_best_avg']:+.3f} (95th pct {tab.attrs['null_best_q95']:+.3f})")
    M = pd.DataFrame(series).fillna(0.0)
    return tab, M, series


# ------------------------------------------------------------------------------------ C. IBS random-entry null
def ibs_section(n_perm=5000):
    say(f"\n=== C. IBS: 4 cells, random entry days with the same holding periods, {n_perm:,} draws ===")
    rng = np.random.default_rng(24)
    real, labels, null_cols, trades = {}, [], [], {}
    for sym, spread in (("US100.cash", 1.5), ("US500.cash", 0.5)):
        d = ibs_daily(sym)
        c, A, idx = d.c.values, d.atr.values, d.index
        for rule in ("published", "ibs<0.2"):
            t = ibs_run(d, spread, rule)
            name = f"{sym.replace('.cash', '')} {rule}"
            real[name] = t.R.mean(); labels.append(name); trades[name] = t
            h = t.days.values.astype(int)
            hi = len(d) - 1 - h                                         # last valid entry per trade
            e = (30 + rng.random((n_perm, len(h))) * (hi - 30 + 1)).astype(int)
            x = e + h[None, :]
            nights = (idx.values[x] - idx.values[e]).astype("timedelta64[D]").astype(float)
            R = (c[x] - c[e] - spread - 0.0001 * c[e] * nights) / A[e]
            null_cols.append(R.mean(axis=1))
    null = np.array(null_cols).T
    tab = robust.mcpt_select(pd.Series(real)[labels], null)
    say(tab.round(3).to_string())
    tab.to_csv("/home/claude/bt/robust_ibs.csv")
    say(f"   null: average random-entry cell {tab.attrs['null_cell_avg']:+.3f}R (this is the index's own drift), "
        f"average BEST of 4 {tab.attrs['null_best_avg']:+.3f}R")
    return tab, trades


# ------------------------------------------------------------------------------------------------------------ main
if __name__ == "__main__":
    if sys.argv[1:] == ["A2"]:                     # run only the bar-shuffle opening-candle test
        oc_shuffle_section(); sys.exit(0)
    oc_tab, oc_M, oc_data = oc_section()
    oc2_tab = oc_shuffle_section()
    nb_tab, nb_M, nb_series = nb_section()
    ibs_tab, ibs_trades = ibs_section()

    say("\n=== D. CSCV probability of backtest overfitting (10 blocks = 252 half/half splits) ===")
    for name, M, crit, unit in (("Opening candle, 32 cells, criterion mean R", oc_M, robust.crit_mean, "R"),
                                ("Opening candle, TSLA's 8 cells", oc_M[[c for c in oc_M if c.startswith("TSLA")]], robust.crit_mean, "R"),
                                ("Opening candle, US100's 8 cells", oc_M[[c for c in oc_M if c.startswith("US100")]], robust.crit_mean, "R"),
                                ("Noise band, 15 cells, criterion daily Sharpe", nb_M, robust.crit_sharpe, "daily Sharpe"),
                                ("Noise band, US100's 5 cells", nb_M[[c for c in nb_M if c.startswith("US100")]], robust.crit_sharpe, "daily Sharpe")):
        r = robust.cscv_pbo(M.values, 10, crit)
        say(f"   {name}: PBO {r['pbo']:.0%} | in-sample winner {r['is_best']:+.3f} {unit} -> out of sample "
            f"{r['oos_best']:+.3f} (median cell {r['oos_median']:+.3f}); winner loses out of sample in {r['p_oos_loss']:.0%} of splits")

    say("\n=== E. BCa bootstrap bounds (20,000 resamples): the 95% one-sided lower bound ===")
    oc_trades = {}
    for sym in ("TSLA", "US100.cash"):
        days, per = oc_data[sym]; b = per[(1, None)]
        Rr = pd.Series(np.where(b.dir == 1, b.RL, np.where(b.dir == -1, b.RS, np.nan)), index=days)
        Rr[days.isin(list(FED))] = np.nan
        oc_trades[sym] = Rr.dropna()
    oc_trades["both"] = pd.concat([oc_trades["TSLA"], oc_trades["US100.cash"]])
    for name, x, stat, fmt in (("OC TSLA 30m hold skipFed, mean R", oc_trades["TSLA"], "mean", "{:+.3f}R"),
                               ("OC US100 30m hold skipFed, mean R", oc_trades["US100.cash"], "mean", "{:+.3f}R"),
                               ("OC both, mean R", oc_trades["both"], "mean", "{:+.3f}R"),
                               ("OC both, profit factor", oc_trades["both"], "pf", "{:.2f}"),
                               ("Noise band US100, mean daily return at 1x", nb_series["US100 published"].dropna(), "mean", "{:+.4%}"),
                               ("IBS<0.2 US100, mean R", ibs_trades["US100 ibs<0.2"].R, "mean", "{:+.3f}R"),
                               ("IBS published US100, mean R", ibs_trades["US100 published"].R, "mean", "{:+.3f}R")):
        b = robust.bca_bounds(np.asarray(x, float), stat, B=20000, rng=5)
        say(f"   {name:46s} backtest {fmt.format(b['theta'])}  95% lower bound {fmt.format(b['low'][0.05])}  "
            f"(90%: {fmt.format(b['low'][0.10])})  n={len(x)}")

    say("\n=== F. Drawdown bounds for the live plan (OC TSLA + US100, Fed days skipped, Swing leverage caps) ===")
    for risk in (0.005, 0.01):
        parts = []
        for sym, lev in (("TSLA", 1), ("US100.cash", 15)):
            days, per = oc_data[sym]; b = per[(1, None)]
            Rr = pd.Series(np.where(b.dir == 1, b.RL, np.where(b.dir == -1, b.RS, np.nan)), index=days)
            st = pd.Series(np.where(b.dir == 1, b.stopL, b.stopS), index=days)
            Rr[days.isin(list(FED))] = np.nan
            parts.append((Rr * np.minimum(risk, st / 100 * lev)).fillna(0.0).rename(sym))
        daily = pd.concat(parts, axis=1).fillna(0.0).sum(axis=1).values
        for horizon, label in ((63, "3 months"), (126, "6 months"), (252, "12 months")):
            pk = robust.drawdown_bound(daily, horizon, 0.95, 0.90, rng=7, mode="peak")
            st_ = robust.drawdown_bound(daily, horizon, 0.95, 0.90, rng=8, mode="start")
            say(f"   risk {risk:.1%}, {label:9s}: drawdown from peak 95th pct {pk[0]:.1%} (90%-confidence bound {pk[1]:.1%}); "
                f"loss below the starting balance 95th pct {st_[0]:.1%} (bound {st_[1]:.1%})")
    say(f"\n[total {time.time() - T0:.0f}s]")
