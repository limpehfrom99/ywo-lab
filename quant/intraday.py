"""Intraday rules on session matrices (quant/sessions.py). Every rule is fixed here, before any data is seen; variants
are a short fixed list per rule and every cell gets reported.

Trade conventions (honest fills)
  * Signals use bar closes; market entries fill at the next bar's open.
  * Breakout (stop-order) entries fill at the level, or at the bar's open if it gapped through.
  * The stop is checked from the entry bar on; a bar that touches both stop and target counts as a stop.
    Stops that gap fill at the bar's open. Targets fill at the target price (no gap bonus). For stop-order
    entries the target only counts from the next bar.
  * Exit at the session close at the latest (no overnight holds, so no swap).
  * Cost per trade = spread at entry x sp_mult (1.2 by default: the bar spread is roughly the bar's minimum)
    + commission on both sides. R = (P&L - cost) / |entry - stop|.
"""
import numpy as np, pandas as pd


def simulate(S, e_col, e_px, d, stop, target=None, exit_col=None, comm=0.0, sp_mult=1.2, breakout=False):
    n, K = S.C.shape
    valid = (e_col >= 0) & np.isfinite(e_px) & np.isfinite(stop) & (d != 0)
    e = np.where(valid, e_col, 0).astype(int)
    xc = np.full(n, K - 1) if exit_col is None else np.where(valid, np.minimum(exit_col, K - 1), K - 1).astype(int)
    valid &= xc >= e
    cols = np.arange(K)[None, :]
    win = (cols >= e[:, None]) & (cols <= xc[:, None]) & valid[:, None]
    long = (d == 1)[:, None]
    hs = np.where(long, S.L <= stop[:, None], S.H >= stop[:, None]) & win
    fs = np.where(hs.any(1), hs.argmax(1), K + 9)
    if target is not None:
        tw = win & (cols > e[:, None]) if breakout else win
        ht = np.where(long, S.H >= target[:, None], S.L <= target[:, None]) & tw
        ft = np.where(ht.any(1), ht.argmax(1), K + 9)
    else:
        ft = np.full(n, K + 9)
    i = np.arange(n)
    stop_hit = fs <= np.minimum(ft, xc)
    tgt_hit = ~stop_hit & (ft <= xc)
    o_fs = S.O[i, np.minimum(fs, K - 1)]
    stop_fill = np.where(fs > e, np.where(d == 1, np.minimum(stop, o_fs), np.maximum(stop, o_fs)), stop)
    X = np.where(stop_hit, stop_fill, np.where(tgt_hit, target if target is not None else 0.0, S.C[i, xc]))
    risk = np.abs(e_px - stop)
    cost = S.SP[i, e] * sp_mult + comm * (np.abs(e_px) + np.abs(X))
    with np.errstate(invalid="ignore", divide="ignore"):
        R = (d * (X - e_px) - cost) / risk
    bad = ~valid | ~(risk > 0)
    R[bad] = np.nan
    why = np.where(stop_hit, 1, np.where(tgt_hit, 2, 0)); why[bad] = -1
    return R, why, risk / np.abs(e_px)


def flip(d, seed):
    rng = np.random.default_rng(seed)
    return np.where(rng.random(len(d)) < 0.5, -d, d)


def mirror(e_px, d_new, d_old, stop, target):
    """Same distances, other side (for coin-flip baselines)."""
    dist = np.abs(e_px - stop)
    st = e_px - d_new * dist
    tg = None if target is None else e_px + d_new * np.abs(target - e_px)
    return st, tg


# ------------------------------------------------------------------------------------------------------------ rules
# Each rule returns a dict of arrays: e_col, e_px, d, stop, target (or None), exit_col (or None), breakout flag.

def opening_candle(S, minutes=30, target_r=None):
    k = S.cols(minutes)
    n = len(S.days); i = np.arange(n)
    if S.K <= k + 1: return None
    o = S.open; c = S.C[:, k - 1]
    hi = S.H[:, :k].max(1); lo = S.L[:, :k].min(1)
    d = np.sign(c - o).astype(int)
    e_px = S.O[:, k]
    stop = np.where(d == 1, lo, hi)
    risk = np.abs(e_px - stop)
    tgt = None if target_r is None else e_px + d * target_r * risk
    ok = (d != 0) & ((e_px - stop) * d > 0)
    return dict(e_col=np.where(ok, k, -1), e_px=e_px, d=d, stop=stop, target=tgt, exit_col=None, breakout=False)


def orb(S, minutes=30, stop_mode="opposite", last_entry_frac=0.6):
    k = S.cols(minutes); n, K = S.C.shape
    if K <= k + 1: return None
    hi = S.H[:, :k].max(1); lo = S.L[:, :k].min(1)
    lim = int(K * last_entry_frac)
    cols = np.arange(K)[None, :]
    w = (cols >= k) & (cols < lim)
    up = (S.H >= hi[:, None]) & w; dn = (S.L <= lo[:, None]) & w
    fu = np.where(up.any(1), up.argmax(1), K + 9); fd = np.where(dn.any(1), dn.argmax(1), K + 9)
    # first break decides the side; if one bar breaks both sides we can't know which came first, so count it as
    # a long that was stopped in the same bar (worst case) instead of skipping the day
    d = np.where(fu <= fd, 1, -1); d = np.where(np.minimum(fu, fd) > K, 0, d)
    j = np.where(d == 1, fu, np.where(d == -1, fd, -1))
    i = np.arange(n); jj = np.clip(j, 0, K - 1)
    e_px = np.where(d == 1, np.maximum(hi, S.O[i, jj]), np.minimum(lo, S.O[i, jj]))
    mid = (hi + lo) / 2
    stop = np.where(d == 1, lo, hi) if stop_mode == "opposite" else mid
    ok = (d != 0) & ((e_px - stop) * d > 0)
    return dict(e_col=np.where(ok, j, -1), e_px=e_px, d=d, stop=stop, target=None, exit_col=None, breakout=True)


def gap(S, min_gap_atr=0.5, mode="fade"):
    g = (S.open - S.prev_close) / S.atr
    ok = np.isfinite(g) & (np.abs(g) >= min_gap_atr)
    sg = np.sign(np.nan_to_num(g)).astype(int)
    e_col = np.where(ok, S.first, -1); e_px = S.open
    size = np.abs(S.open - S.prev_close)
    if mode == "fade":
        d = -sg; stop = S.open + sg * size; tgt = S.prev_close
    else:
        d = sg; stop = S.prev_close; tgt = None
    return dict(e_col=e_col, e_px=e_px, d=d, stop=stop, target=tgt, exit_col=None, breakout=False)


def intraday_momentum(S, signal="first30_overnight", stop_atr=0.25):
    """Gao, Han, Li & Zhou (2018): the first half-hour return predicts the last half-hour. Trade the last 30 minutes."""
    k = S.cols(30); n, K = S.C.shape
    if K < 3 * k: return None
    if signal == "first30_overnight": sig = S.C[:, k - 1] / S.prev_close - 1
    elif signal == "first30": sig = S.C[:, k - 1] / S.open - 1
    else: sig = S.C[:, K - k - 1] / S.open - 1                  # open -> 30 minutes before the close
    d = np.sign(np.nan_to_num(sig)).astype(int)
    e_col = K - k; e_px = S.O[:, e_col]
    stop = e_px - d * stop_atr * S.atr
    ok = (d != 0) & np.isfinite(stop)
    return dict(e_col=np.where(ok, e_col, -1), e_px=e_px, d=d, stop=stop, target=None, exit_col=None, breakout=False)


def first_hour_reversal(S, min_move_atr=0.5):
    k = S.cols(60); n, K = S.C.shape
    if K <= k + 2: return None
    m = (S.C[:, k - 1] - S.open) / S.atr
    ok = np.isfinite(m) & (np.abs(m) >= min_move_atr)
    sg = np.sign(np.nan_to_num(m)).astype(int); d = -sg
    e_px = S.O[:, k]
    ext = np.where(sg == 1, S.H[:, :k].max(1), S.L[:, :k].min(1))
    stop = ext + sg * 0.1 * S.atr
    tgt = S.open.copy()
    ok &= ((e_px - stop) * d > 0) & ((tgt - e_px) * d > 0)
    return dict(e_col=np.where(ok, k, -1), e_px=e_px, d=d, stop=stop, target=tgt, exit_col=None, breakout=False)


def asia_breakout(S, range_end="07:00", stop_mode="opposite", last_entry="11:00"):
    """For the london24 session (00:00-16:30 London): range = 00:00 to range_end; first break before last_entry."""
    k = S.col_at(range_end); lim = S.col_at(last_entry); n, K = S.C.shape
    if k < 2 or lim <= k: return None
    hi = S.H[:, :k].max(1); lo = S.L[:, :k].min(1)
    cols = np.arange(K)[None, :]
    w = (cols >= k) & (cols < lim)
    up = (S.H >= hi[:, None]) & w; dn = (S.L <= lo[:, None]) & w
    fu = np.where(up.any(1), up.argmax(1), K + 9); fd = np.where(dn.any(1), dn.argmax(1), K + 9)
    # first break decides the side; if one bar breaks both sides we can't know which came first, so count it as
    # a long that was stopped in the same bar (worst case) instead of skipping the day
    d = np.where(fu <= fd, 1, -1); d = np.where(np.minimum(fu, fd) > K, 0, d)
    j = np.where(d == 1, fu, np.where(d == -1, fd, -1)); i = np.arange(n); jj = np.clip(j, 0, K - 1)
    e_px = np.where(d == 1, np.maximum(hi, S.O[i, jj]), np.minimum(lo, S.O[i, jj]))
    stop = np.where(d == 1, lo, hi) if stop_mode == "opposite" else (hi + lo) / 2
    ok = (d != 0) & ((e_px - stop) * d > 0)
    return dict(e_col=np.where(ok, j, -1), e_px=e_px, d=d, stop=stop, target=None, exit_col=None, breakout=True)


def noise_band(S, lookback=14, comm=0.0, sp_mult=1.2, use_vwap=True, seed=None):
    """Zarattini, Aziz & Barbon (2024), as in bt/noise_band.py but on any session: exposure decided at every 30-minute
    mark (+1 above max(UB, VWAP), -1 below min(LB, VWAP), else flat), flat at the close. Returns per-day R where
    R = day return / sigma at the first entry mark (the band width, a volatility unit) so it sits on the same scale."""
    step = S.cols(30); n, K = S.C.shape
    marks = np.arange(step - 1, K, step)
    if len(marks) < 4: return None
    Cm = S.C[:, marks]; SPm = S.SP[:, marks]
    tp = (S.H + S.L + S.C) / 3; v = np.where(S.V > 0, S.V, 1.0)
    vw = (np.cumsum(tp * v, 1) / np.cumsum(v, 1))[:, marks]
    move = np.abs(Cm / S.open[:, None] - 1)
    sig = pd.DataFrame(move).rolling(lookback).mean().shift(1).values
    pc = S.prev_close
    ub = np.maximum(S.open, pc)[:, None] * (1 + sig); lb = np.minimum(S.open, pc)[:, None] * (1 - sig)
    rng = np.random.default_rng(seed) if seed is not None else None
    sgn = np.where(rng.random(n) < 0.5, -1, 1) if rng is not None else np.ones(n)
    pos = np.zeros(n); ent = np.full(n, np.nan); ret = np.zeros(n); first_sig = np.full(n, np.nan)
    ok = np.isfinite(sig[:, 0]) & np.isfinite(pc)
    M = len(marks)
    for m in range(M):
        p = Cm[:, m]
        if m == M - 1: tgt = np.zeros(n)
        elif use_vwap:
            tgt = np.where(p > np.maximum(ub[:, m], vw[:, m]), 1, np.where(p < np.minimum(lb[:, m], vw[:, m]), -1, 0))
        else:
            tgt = np.where(p > ub[:, m], 1, np.where(p < lb[:, m], -1, pos))
        tgt = np.where(ok, tgt, 0)
        ch = tgt != pos
        cs = SPm[:, m] * sp_mult / 2 / p + comm                   # half the spread per side
        closing = ch & (pos != 0)
        ret += np.where(closing, sgn * pos * (p / np.where(np.isfinite(ent), ent, p) - 1) - cs, 0)
        opening = ch & (tgt != 0)
        ret -= np.where(opening, cs, 0)
        first_sig = np.where(opening & np.isnan(first_sig), sig[:, m], first_sig)
        ent = np.where(opening, p, np.where(ch, np.nan, ent))
        pos = tgt
    traded = np.isfinite(first_sig)
    R = np.where(traded, ret / first_sig, np.nan)
    return R, np.where(traded, first_sig, np.nan)


# fixed variant list: (rule name, function, kwargs, sessions it applies to)
VARIANTS = [
    ("OC15", opening_candle, dict(minutes=15), "cash"),
    ("OC30", opening_candle, dict(minutes=30), "cash"),
    ("OC60", opening_candle, dict(minutes=60), "cash"),
    ("OC30_2R", opening_candle, dict(minutes=30, target_r=2.0), "cash"),
    ("ORB15", orb, dict(minutes=15), "cash"),
    ("ORB30", orb, dict(minutes=30), "cash"),
    ("ORB60", orb, dict(minutes=60), "cash"),
    ("ORB30_mid", orb, dict(minutes=30, stop_mode="mid"), "cash"),
    ("GAPfade0.5", gap, dict(min_gap_atr=0.5, mode="fade"), "cash"),
    ("GAPfade1.0", gap, dict(min_gap_atr=1.0, mode="fade"), "cash"),
    ("GAPgo0.5", gap, dict(min_gap_atr=0.5, mode="go"), "cash"),
    ("GAPgo1.0", gap, dict(min_gap_atr=1.0, mode="go"), "cash"),
    ("IMOM_ovn", intraday_momentum, dict(signal="first30_overnight"), "cash"),
    ("IMOM_30", intraday_momentum, dict(signal="first30"), "cash"),
    ("IMOM_day", intraday_momentum, dict(signal="day"), "cash"),
    ("FHR0.5", first_hour_reversal, dict(min_move_atr=0.5), "cash"),
    ("FHR0.8", first_hour_reversal, dict(min_move_atr=0.8), "cash"),
    ("ASIA_BO7", asia_breakout, dict(range_end="07:00"), "london24"),
    ("ASIA_BO8", asia_breakout, dict(range_end="08:00", last_entry="12:00"), "london24"),
    ("ASIA_BO7_mid", asia_breakout, dict(range_end="07:00", stop_mode="mid"), "london24"),
    ("NB", None, dict(), "cash"),                                   # noise band, handled separately
]


def applies(scope, session_name):
    if scope == "london24": return session_name == "london24"
    return session_name != "london24"            # "cash": every exchange-hours session (and ny_fx for FX)


def run_variant(S, name, fn, kw, comm, n_flip=20, sp_mult=1.2):
    """Returns a DataFrame of trades (one per day traded) with R, coin-flip mean R per trade, and 2x-spread R."""
    if name == "NB":
        out = noise_band(S, comm=comm, sp_mult=sp_mult)
        if out is None: return None
        R, unit = out
        R2 = noise_band(S, comm=comm, sp_mult=sp_mult * 2)[0]
        coin = np.nanmean([noise_band(S, comm=comm, sp_mult=sp_mult, seed=s)[0] for s in range(n_flip)], axis=0)
        m = np.isfinite(R)
        return pd.DataFrame({"day": S.days[m], "utc": S.utc_start[m], "d": 0, "R": R[m], "R2x": R2[m], "coin": coin[m],
                             "risk_frac": unit[m], "why": 0})
    sp = fn(S, **kw)
    if sp is None: return None
    tgt = sp["target"]
    R, why, rf = simulate(S, sp["e_col"], sp["e_px"], sp["d"], sp["stop"], tgt, sp["exit_col"], comm, sp_mult, sp["breakout"])
    R2 = simulate(S, sp["e_col"], sp["e_px"], sp["d"], sp["stop"], tgt, sp["exit_col"], comm, sp_mult * 2, sp["breakout"])[0]
    coins = []
    for s in range(n_flip):
        dn = flip(sp["d"], s); st, tg = mirror(sp["e_px"], dn, sp["d"], sp["stop"], tgt)
        coins.append(simulate(S, sp["e_col"], sp["e_px"], dn, st, tg, sp["exit_col"], comm, sp_mult, sp["breakout"])[0])
    coin = np.nanmean(np.vstack(coins), axis=0)
    m = np.isfinite(R)
    e_col = np.clip(sp["e_col"], 0, S.K - 1)
    utc = S.utc_start + pd.to_timedelta(e_col * S.bar, unit="min")
    return pd.DataFrame({"day": S.days[m], "utc": utc[m], "d": sp["d"][m], "R": R[m], "R2x": R2[m], "coin": coin[m],
                         "risk_frac": rf[m], "why": why[m]})
