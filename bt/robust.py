"""Robustness tests: is an edge real, or the luck of having tried many things?

Own implementations of the methods in Timothy Masters, "Testing and Tuning Market Trading Systems" (Apress 2018;
github.com/Apress/testing-and-tuning-market-trading-systems) and the bar-permutation idea in
github.com/strix-systems/permutation-testing-tutorial. The book's C++ programs build with tools/get_masters.sh;
cscv_pbo and bca_bounds were checked against its CSCV_CORE and boot_conf_BCa on identical inputs
(tools/verify_masters.py).

  permute_bars(o, h, l, c, slots, rng)  shuffle OHLC bars in log space: the gap from the previous close and the bar's
                                        shape (high/low/close relative to its open) are shuffled separately. With
                                        `slots` (time of day), bars only swap with bars from the same slot, so the
                                        intraday volatility pattern survives and only the order information is lost.
  mcpt_select(real, null)               permutation p-values that correct for picking the best of many cells,
                                        plus Masters' "skill" estimate: real result minus what the best random cell
                                        earns on average.
  cscv_pbo(M, n_blocks, crit)           probability of backtest overfitting (Bailey, Borwein, Lopez de Prado, Zhu
                                        2014; Masters' CSCV_CORE): choose the best cell on half the blocks, rank it
                                        on the other half, over every half/half split.
  bca_bounds(x, stat, B)                BCa bootstrap confidence bounds (Efron 1987; Masters' boot_conf_BCa).
  drawdown_bound(x, n_future, q, conf)  the q-quantile of future drawdown, and the level it stays under with
                                        confidence `conf` (Masters' DRAWDOWN "correct" method: bootstrap of
                                        bootstraps). Equity starts at 0, so a loss on the first trade counts.
"""
import itertools
from statistics import NormalDist

import numpy as np
import pandas as pd

_N = NormalDist()


# ----------------------------------------------------------------------------------------------- bar permutation
def permute_bars(o, h, l, c, slots=None, rng=None, extra=()):
    """Return permuted (o, h, l, c, *extra). Bar 0 is kept. `extra` arrays (e.g. tick volume, spread) travel with
    the bar shape. Prices must be > 0."""
    rng = np.random.default_rng(rng)
    lo_, lh, ll, lc = (np.log(np.asarray(a, float)) for a in (o, h, l, c))
    n = len(lo_)
    gap = np.r_[0.0, lo_[1:] - lc[:-1]]
    hi, lw, cl = lh - lo_, ll - lo_, lc - lo_
    p1 = np.arange(n); p2 = np.arange(n)
    if slots is None:
        p1[1:] = 1 + rng.permutation(n - 1); p2[1:] = 1 + rng.permutation(n - 1)
    else:
        slots = np.asarray(slots)
        for s in np.unique(slots):
            m = np.flatnonzero(slots == s); m = m[m > 0]
            p1[m] = rng.permutation(m); p2[m] = rng.permutation(m)
    g = gap[p2]; g[0] = 0.0
    cc = cl[p1]
    close = lo_[0] + np.cumsum(g + cc)
    op = close - cc
    out = [np.exp(op), np.exp(op + hi[p1]), np.exp(op + lw[p1]), np.exp(close)]
    out += [np.asarray(e)[p1] for e in extra]
    return out


# --------------------------------------------------------------------------------- selection-aware permutation test
def mcpt_select(real, null):
    """real: Series cell -> statistic on the real data. null: array (n_perm, n_cells), same statistic on null data
    (same column order). Per cell: p_alone (vs its own null) and p_best (vs the null BEST of all cells, which is the
    honest p-value when the cell was picked because it looked best). skill = real - average null best."""
    real = pd.Series(real, dtype=float)
    null = np.asarray(null, float)
    k = len(null)
    best = np.nanmax(null, axis=1)
    rows = []
    for j, (cell, v) in enumerate(real.items()):
        rows.append(dict(cell=cell, real=v, null_avg=np.nanmean(null[:, j]),
                         p_alone=(1 + np.sum(null[:, j] >= v)) / (k + 1),
                         p_best=(1 + np.sum(best >= v)) / (k + 1),
                         skill=v - best.mean()))
    out = pd.DataFrame(rows).set_index("cell")
    out.attrs.update(null_best_avg=best.mean(), null_cell_avg=np.nanmean(null), n_perm=k,
                     null_best_q95=np.quantile(best, 0.95))
    return out


# ------------------------------------------------------------------------------------------------------------ CSCV
def _blocks(T, n_blocks):
    starts, lens, s = [], [], 0
    for i in range(n_blocks):
        L = (T - s) // (n_blocks - i); starts.append(s); lens.append(L); s += L
    return [np.arange(a, a + L) for a, L in zip(starts, lens)]


def crit_mean(x):
    return x.mean(axis=0)


def crit_sharpe(x):
    sd = x.std(axis=0, ddof=1)
    return np.where(sd > 0, x.mean(axis=0) / np.where(sd > 0, sd, 1), 0.0)


def cscv_pbo(M, n_blocks=10, crit=crit_mean):
    """M: (T periods x N cells), period results aligned in time (0 where a cell did not trade).
    Returns dict: pbo (share of splits where the in-sample winner ranks at or below the out-of-sample median),
    is_best (avg in-sample criterion of the winner), oos_best (its avg out-of-sample criterion), oos_median
    (avg out-of-sample median of all cells), p_oos_loss (share of splits where the winner loses out of sample)."""
    M = np.asarray(M, float)
    T, N = M.shape
    n_blocks = n_blocks // 2 * 2
    blocks = _blocks(T, n_blocks)
    nless = 0; is_b, oos_b, oos_med, logits = [], [], [], []
    combos = list(itertools.combinations(range(n_blocks), n_blocks // 2))
    for is_set in combos:
        is_idx = np.concatenate([blocks[i] for i in is_set])
        oos_idx = np.concatenate([blocks[i] for i in range(n_blocks) if i not in is_set])
        ic = crit(M[is_idx]); oc = crit(M[oos_idx])
        ib = int(np.argmax(ic))                     # first maximum, as in CSCV_CORE
        n = int(np.sum(oc <= oc[ib]))               # includes the winner itself
        rel = n / (N + 1)
        nless += rel <= 0.5
        logits.append(np.log(rel / (1 - rel)))
        is_b.append(ic[ib]); oos_b.append(oc[ib]); oos_med.append(np.median(oc))
    oos_b = np.array(oos_b)
    return dict(pbo=nless / len(combos), n_splits=len(combos), is_best=float(np.mean(is_b)),
                oos_best=float(oos_b.mean()), oos_median=float(np.mean(oos_med)),
                p_oos_loss=float(np.mean(oos_b < 0)), logit_median=float(np.median(logits)))


# ------------------------------------------------------------------------------------------------------------- BCa
def _q_index(frac, n):
    return max(int(frac * (n + 1)) - 1, 0)


def bca_bounds(x, stat="mean", B=20000, rng=None, alphas=(0.025, 0.05, 0.10)):
    """BCa bounds for a statistic of a sample. stat: 'mean', 'sharpe', 'pf' (profit factor) or a function f(2-D
    array, axis=1) -> 1-D. Returns {'theta': value, 'low': {a: bound}, 'high': {a: bound}}."""
    x = np.asarray(x, float); n = len(x)
    f = {"mean": lambda a: a.mean(axis=1),
         "sharpe": lambda a: a.mean(axis=1) / a.std(axis=1, ddof=1),
         "pf": lambda a: np.clip(a, 0, None).sum(axis=1) / np.maximum(-np.clip(a, None, 0).sum(axis=1), 1e-60),
         }.get(stat, stat) if isinstance(stat, str) else stat
    theta = float(f(x[None, :])[0])
    rng = np.random.default_rng(rng)
    boot = np.empty(B); step = max(1, 4_000_000 // n)
    for s in range(0, B, step):
        e = min(B, s + step)
        boot[s:e] = f(x[rng.integers(0, n, (e - s, n))])
    cnt = int(np.sum(boot < theta)); cnt = min(max(cnt, 1), B - 1)
    z0 = _N.inv_cdf(cnt / B)
    jack = np.array([float(f(np.delete(x, i)[None, :])[0]) for i in range(n)])
    d = jack.mean() - jack
    accel = np.sum(d ** 3) / (6.0 * np.sum(d ** 2) ** 1.5 + 1e-60)
    boot.sort()
    low, high = {}, {}
    for a in alphas:
        zl, zh = _N.inv_cdf(a), _N.inv_cdf(1 - a)
        al = _N.cdf(z0 + (z0 + zl) / (1 - accel * (z0 + zl)))
        ah = _N.cdf(z0 + (z0 + zh) / (1 - accel * (z0 + zh)))
        low[a] = boot[_q_index(al, B)]
        high[a] = boot[B - 1 - _q_index(1 - ah, B)]
    return dict(theta=theta, low=low, high=high, z0=z0, accel=accel)


# -------------------------------------------------------------------------------------------------------- drawdown
def max_drawdown(r):
    """Max drawdown of each row of summed returns (non-compounded), equity starting at 0."""
    r = np.atleast_2d(r)
    c = np.cumsum(r, axis=1)
    peak = np.maximum.accumulate(np.maximum(c, 0.0), axis=1)
    return (peak - c).max(axis=1)


def max_loss_from_start(r):
    """Deepest point below the starting balance (FTMO's static max-loss rule), per row, non-compounded."""
    c = np.cumsum(np.atleast_2d(r), axis=1)
    return np.maximum(-c.min(axis=1), 0.0)


def drawdown_bound(x, n_future, q=0.95, conf=0.90, n_outer=300, n_inner=1000, rng=None, mode="peak"):
    """x: history of per-period returns. mode 'peak' = drawdown from the running peak, 'start' = loss below the
    starting balance. Returns (naive q-quantile over n_future periods, the level that q-quantile stays under with
    confidence `conf`)."""
    x = np.asarray(x, float); n = len(x)
    rng = np.random.default_rng(rng)
    dd_fn = max_drawdown if mode == "peak" else max_loss_from_start

    def q_dd(sample):
        dd = np.sort(dd_fn(sample[rng.integers(0, n, (n_inner, n_future))]))
        return dd[_q_index(q, n_inner)]

    naive = q_dd(x)
    outer = np.sort([q_dd(x[rng.integers(0, n, n)]) for _ in range(n_outer)])
    return naive, outer[_q_index(conf, n_outer)]
