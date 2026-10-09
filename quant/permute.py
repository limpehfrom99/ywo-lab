"""Monte Carlo permutation tests (MCPT) for intraday session rules and daily rules.

Sources: Timothy Masters, "Testing and Tuning Market Trading Systems" (Apress 2018), ch. 7 "Permutation Tests", and the Strix
Systems video "Your Backtest is Lying to You" (log #62). The idea: a rule with a real edge exploits a pattern in the ORDER of
price moves. Shuffle the moves (destroying the order but keeping every move) many times, rerun the rule on each shuffle, and
count how often the shuffled data does at least as well as the real data. That share is the p-value.

Intraday version (permute_session): Masters' bar permutation, done inside each time-of-day column across days, so the
open-of-session bars stay open-of-session bars (time-of-day volatility is kept) while the link between bars of the same day
(e.g. the first half hour and the rest of the day) is destroyed. Each bar is split into its gap from the previous close and its
high/low/close relative to its own open (logs); the two parts are shuffled with independent permutations per column, then the
price path is rebuilt. Every column's moves are kept, so the end price and the drift are unchanged.

Daily version (permute_bars): the same on a single series of bars (Masters' original), for daily rules.

Selection-bias version (best_of): rerun EVERY rule/symbol cell on the same shuffles and take the best cell each time; the real
best cell must beat the shuffled bests. That is the test for "the best of N things I tried", which a per-cell p-value is not.
p-values use (1 + count) / (1 + n_perm) so they are never 0.
"""
import copy
import numpy as np, pandas as pd


# --------------------------------------------------------------------------------------------------- bar permutations
def _rebuild(first_px, g, h, l, c):
    """Flattened bars (time order): g = log gap from the previous close, h/l/c = log high/low/close minus log open."""
    logC = np.log(first_px) + np.cumsum(g + c)
    logO = logC - c
    return np.exp(logO), np.exp(logO + h), np.exp(logO + l), np.exp(logC)


def permute_session(S, rng):
    """Shuffled copy of a quant.sessions.Session (see the module note)."""
    n, K = S.C.shape
    O, H, L, C = (np.asarray(x, float) for x in (S.O, S.H, S.L, S.C))
    prevC = np.empty_like(C); prevC[:, 1:] = C[:, :-1]
    prevC[0, 0] = O[0, 0]; prevC[1:, 0] = C[:-1, -1]
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.log(O / prevC); h = np.log(H / O); l = np.log(L / O); c = np.log(C / O)
    for a in (g, h, l, c): a[~np.isfinite(a)] = 0.0
    g[0, 0] = 0.0
    gi = np.empty_like(g); hi = np.empty_like(h); li = np.empty_like(l); ci = np.empty_like(c)
    SP = np.asarray(S.SP, float).copy(); V = np.asarray(S.V, float).copy()
    for k in range(K):
        pa = rng.permutation(n)
        pb = np.r_[0, rng.permutation(n - 1) + 1] if k == 0 else rng.permutation(n)   # the very first bar has no gap
        hi[:, k], li[:, k], ci[:, k] = h[pa, k], l[pa, k], c[pa, k]
        SP[:, k], V[:, k] = S.SP[pa, k], S.V[pa, k]
        gi[:, k] = g[pb, k]
    O2, H2, L2, C2 = (x.reshape(n, K) for x in _rebuild(O[0, 0], gi.ravel(), hi.ravel(), li.ravel(), ci.ravel()))
    P = copy.copy(S)
    P.O, P.H, P.L, P.C, P.SP, P.V = O2, H2, L2, C2, SP, V
    P.open = O2[np.arange(n), S.first] if n else np.array([])
    P.close = C2[:, -1]; P.high, P.low = H2.max(1), L2.min(1)
    pc = np.r_[np.nan, P.close[:-1]]; pc[~np.isfinite(S.prev_close)] = np.nan; P.prev_close = pc
    tr = np.nanmax(np.vstack([P.high - P.low, np.abs(P.high - pc), np.abs(P.low - pc)]), axis=0)
    P.atr = pd.Series(tr).rolling(14, min_periods=10).mean().shift(1).values
    return P


def permute_bars(df, rng, start=0):
    """Masters' bar permutation of one OHLC frame (index kept): bars before `start` are left as they are (use it to keep the
    in-sample part real when testing an out-of-sample stretch). Gaps and intrabar shapes are shuffled independently."""
    o, h, l, c = (df[x].values.astype(float) for x in ("open", "high", "low", "close"))
    n = len(c)
    if n - start < 3: return df.copy()
    pc = np.r_[o[0], c[:-1]]
    g = np.log(o / pc); hh = np.log(h / o); ll = np.log(l / o); cc = np.log(c / o)
    s = start + 1
    pa = rng.permutation(n - s) + s; pb = rng.permutation(n - s) + s
    g2, h2, l2, c2 = g.copy(), hh.copy(), ll.copy(), cc.copy()
    h2[s:], l2[s:], c2[s:] = hh[pa], ll[pa], cc[pa]; g2[s:] = g[pb]; g2[0] = 0.0
    O, H, L, C = _rebuild(o[0], g2, h2, l2, c2)
    out = df.copy()
    out["open"], out["high"], out["low"], out["close"] = O, H, L, C
    for col in ("sp", "tickvol", "volume"):
        if col in df: out[col] = np.r_[df[col].values[:s], df[col].values[pa]] if len(pa) else df[col].values
    return out


# --------------------------------------------------------------------------------------------------- tests
def pvalue(real, perms):
    perms = np.asarray(perms, float); perms = perms[np.isfinite(perms)]
    return (1 + np.sum(perms >= real)) / (1 + len(perms))


def mcpt_session(S, stat_fn, n_perm=200, seed=0):
    """stat_fn(S) -> float (e.g. mean R of a rule on that session). Returns (real, perm values, p)."""
    real = stat_fn(S); rng = np.random.default_rng(seed)
    perms = np.array([stat_fn(permute_session(S, rng)) for _ in range(n_perm)])
    return real, perms, pvalue(real, perms)


def best_of(cells, n_perm=200, seed=0, stat="t"):
    """cells: list of (S, stat_fn) where stat_fn(S) -> (avgR, t, n). Each permutation shuffles every S once (independently)
    and records the best `stat` over all cells. Returns real best value, its cell index, perm bests, p (selection-bias
    corrected), plus each cell's own p-value against its own shuffles."""
    rng = np.random.default_rng(seed)
    real = [fn(S) for S, fn in cells]
    key = 1 if stat == "t" else 0
    rv = np.array([r[key] if r is not None else np.nan for r in real])
    best_i = int(np.nanargmax(rv)); best = rv[best_i]
    bests = []; per_cell = [[] for _ in cells]
    for _ in range(n_perm):
        vals = []
        for j, (S, fn) in enumerate(cells):
            r = fn(permute_session(S, rng)); v = r[key] if r is not None else np.nan
            vals.append(v); per_cell[j].append(v)
        bests.append(np.nanmax(vals))
    bests = np.array(bests)
    cell_p = np.array([pvalue(rv[j], per_cell[j]) for j in range(len(cells))])
    return dict(best=best, best_cell=best_i, perm_bests=bests, p_best=pvalue(best, bests), real=rv, cell_p=cell_p)
