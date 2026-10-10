"""Log #75: selection-aware permutation test for #30 Dual Thrust (run because a primary cell, US100 cash session M5 k = 0.5,
cleared the CANDIDATE bar). Every Dual Thrust cell of bt/q75_intraday.py (every symbol-session x bar size x k) is rerun on each
shuffle; statistic = per-cell t of R (cells with n >= 200 compete for "best"). p_best = share of shuffles whose best cell t >=
the real best cell's t; also p_best and p_alone of the primary cells, and BCa 95% lower bound of the primary cell.

Shuffle = quant/permute.permute_session's algorithm (Masters' bar permutation inside each time-of-day column across days: the gap
from the previous close and the bar's high/low/close relative to its open are shuffled with independent permutations; the price
path is rebuilt), compiled with numba for speed (verified against permute_session with identical permutations: `--verify`).
Shuffles are done on the finest bars (M5; forex M15); coarser bars are rebuilt from the shuffled ones, as in the real run.
Each symbol-session is shuffled independently per shuffle index (seeded by symbol, session, shuffle).

python3 bt/q75_intraday_perm.py run [n_perm] -> results/q75_intraday_perm.csv (one row per symbol-session x shuffle; resumable)
python3 bt/q75_intraday_perm.py summary      -> printed p-values (+ results/q75_intraday_perm_summary.csv)
python3 bt/q75_intraday_perm.py --verify     -> checks the numba shuffle against quant/permute.permute_session
"""
import os, sys, time, zlib, warnings
import numpy as np, pandas as pd
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "quant")); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
import universe as U  # noqa: E402
import permute as PM  # noqa: E402
import q75_intraday as Q  # noqa: E402
import robust as RB  # noqa: E402

PERM = os.path.join(Q.RES, "q75_intraday_perm.csv")
REAL = os.path.join(Q.RES, "q75_intraday_perm_real.csv")
SUMMARY = os.path.join(Q.RES, "q75_intraday_perm_summary.csv")
MIN_N = 200
PRIMARY_DT = {(s, ss): (b, k) for (idea, s, ss, b, k) in Q.PRIMARY if idea == "dt"}


# ------------------------------------------------------------------------------------------------------------- shuffle
def log_parts(S):
    O, H, L, C = (np.asarray(x, float) for x in (S.O, S.H, S.L, S.C))
    prevC = np.empty_like(C); prevC[:, 1:] = C[:, :-1]
    prevC[0, 0] = O[0, 0]; prevC[1:, 0] = C[:-1, -1]
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.log(O / prevC); h = np.log(H / O); l = np.log(L / O); c = np.log(C / O)
    for a in (g, h, l, c): a[~np.isfinite(a)] = 0.0
    g[0, 0] = 0.0
    return g, h, l, c


@njit(cache=False)
def make_perms(n, K, seed):
    np.random.seed(seed)
    PA = np.empty((K, n), np.int64); PB = np.empty((K, n), np.int64)
    for k in range(K):
        PA[k] = np.random.permutation(n)
        if k == 0:
            PB[k, 0] = 0
            PB[k, 1:] = np.random.permutation(n - 1) + 1
        else:
            PB[k] = np.random.permutation(n)
    return PA, PB


@njit(cache=False)
def rebuild(g, h, l, c, SP, o00, PA, PB):
    n, K = g.shape
    O2 = np.empty((n, K)); H2 = np.empty((n, K)); L2 = np.empty((n, K)); C2 = np.empty((n, K)); SP2 = np.empty((n, K))
    logC = np.log(o00)
    for r in range(n):
        for k in range(K):
            a = PA[k, r]
            cc = c[a, k]
            logC = logC + g[PB[k, r], k] + cc
            lo = logC - cc
            O2[r, k] = np.exp(lo); H2[r, k] = np.exp(lo + h[a, k]); L2[r, k] = np.exp(lo + l[a, k]); C2[r, k] = np.exp(logC)
            SP2[r, k] = SP[a, k]
    return O2, H2, L2, C2, SP2


@njit(cache=False)
def rebuild_fast(egT, ehT, elT, ecT, spT, o00, PA, PB):
    """Same result as rebuild() (to ~1e-12): column-wise gathers from transposed exp(parts), then the price path rebuilt by
    multiplication in time order (cache-friendly; no exp in the loop)."""
    K, n = egT.shape
    G = np.empty((K, n)); Hh = np.empty((K, n)); Ll = np.empty((K, n)); Cc = np.empty((K, n)); Sp = np.empty((K, n))
    for k in range(K):
        for r in range(n):
            a = PA[k, r]
            Hh[k, r] = ehT[k, a]; Ll[k, r] = elT[k, a]; Cc[k, r] = ecT[k, a]; Sp[k, r] = spT[k, a]
            G[k, r] = egT[k, PB[k, r]]
    O2 = np.empty((n, K)); H2 = np.empty((n, K)); L2 = np.empty((n, K)); C2 = np.empty((n, K)); SP2 = np.empty((n, K))
    px = o00
    for r in range(n):
        for k in range(K):
            o = px * G[k, r]
            O2[r, k] = o; H2[r, k] = o * Hh[k, r]; L2[r, k] = o * Ll[k, r]
            px = o * Cc[k, r]; C2[r, k] = px; SP2[r, k] = Sp[k, r]
    return O2, H2, L2, C2, SP2


def exp_parts(S, parts):
    g, h, l, c = parts
    return (np.ascontiguousarray(np.exp(g).T), np.ascontiguousarray(np.exp(h).T), np.ascontiguousarray(np.exp(l).T),
            np.ascontiguousarray(np.exp(c).T), np.ascontiguousarray(np.asarray(S.SP, float).T))


class Lite:
    """Just what the Dual Thrust needs: bar matrices + daily fields."""
    pass


def shuffled(S, parts, seed, eparts=None):
    n, K = S.C.shape
    PA, PB = make_perms(n, K, seed)
    if eparts is not None:
        O2, H2, L2, C2, SP2 = rebuild_fast(*eparts, float(S.O[0, 0]), PA, PB)
    else:
        g, h, l, c = parts
        O2, H2, L2, C2, SP2 = rebuild(g, h, l, c, np.asarray(S.SP, float), float(S.O[0, 0]), PA, PB)
    return lite(S, O2, H2, L2, C2, SP2)


def lite(S, O, H, L, C, SP):
    X = Lite(); X.O, X.H, X.L, X.C, X.SP = O, H, L, C, SP
    X.V = np.zeros_like(O); X.K = S.K; X.bar = S.bar; X.first = np.asarray(S.first, np.int64); X.days = S.days
    n = len(S.days)
    X.open = O[np.arange(n), X.first]; X.close = C[:, -1]; X.high = H.max(1); X.low = L.min(1)
    pc = np.r_[np.nan, X.close[:-1]]; pc[~np.isfinite(S.prev_close)] = np.nan; X.prev_close = pc
    return X


# -------------------------------------------------------------------------------------------------------------- cells
@njit(cache=False)
def dt_cells_nb(O, H, L, C, SP, first, prev_ok, comm, spm, gs, ks):
    """Every Dual Thrust cell of one session in one pass: bar sizes gs (multiples of the base bar, coarse bars joined on the
    fly exactly as q75_intraday.coarsen), k values ks. Same state machine and costs as q75_intraday.dt_kernel / _trades.
    Returns n, sum R, sum R^2 per (g, k)."""
    n, K = O.shape
    ng = len(gs); nk = len(ks)
    cnt = np.zeros((ng, nk)); s1 = np.zeros((ng, nk)); s2 = np.zeros((ng, nk))
    opn = np.empty(n); hi = np.empty(n); lo = np.empty(n); cl = np.empty(n)
    for i in range(n):
        opn[i] = O[i, first[i]]; cl[i] = C[i, K - 1]
        a = H[i, 0]; b = L[i, 0]
        for j in range(1, K):
            if H[i, j] > a: a = H[i, j]
            if L[i, j] < b: b = L[i, j]
        hi[i] = a; lo[i] = b
    for i in range(4, n):
        if not (prev_ok[i] and prev_ok[i - 1] and prev_ok[i - 2] and prev_ok[i - 3]): continue
        HH = max(hi[i - 4], hi[i - 3], hi[i - 2], hi[i - 1]); LL = min(lo[i - 4], lo[i - 3], lo[i - 2], lo[i - 1])
        HC = max(cl[i - 4], cl[i - 3], cl[i - 2], cl[i - 1]); LC = min(cl[i - 4], cl[i - 3], cl[i - 2], cl[i - 1])
        rng = max(HH - LC, HC - LL)
        if not (rng > 0): continue
        for gi in range(ng):
            g = gs[gi]; Kc = K // g; f = first[i] // g
            xclose = C[i, g * Kc - 1]
            for ki in range(nk):
                bt = opn[i] + ks[ki] * rng; st = opn[i] - ks[ki] * rng; den = bt - st
                pos = 0; ep = 0.0; esp = 0.0
                for jc in range(f, Kc):
                    j0 = g * jc
                    o = O[i, j0]; h = H[i, j0]; l = L[i, j0]; sp = SP[i, j0]
                    for q in range(1, g):
                        if H[i, j0 + q] > h: h = H[i, j0 + q]
                        if L[i, j0 + q] < l: l = L[i, j0 + q]
                        sp += SP[i, j0 + q]
                    sp = sp / g
                    up = h >= bt; dn = l <= st
                    if pos == 0:
                        if up and dn:
                            if o <= st:
                                dd = -1; e = o; x = bt
                            else:
                                dd = 1; e = max(bt, o); x = st
                            R = (dd * (x - e) - (sp * spm + comm * (abs(e) + abs(x)))) / den
                            cnt[gi, ki] += 1; s1[gi, ki] += R; s2[gi, ki] += R * R
                        elif up:
                            pos = 1; ep = max(bt, o); esp = sp
                        elif dn:
                            pos = -1; ep = min(st, o); esp = sp
                    elif pos == 1:
                        if dn:
                            x = min(st, o)
                            R = ((x - ep) - (esp * spm + comm * (abs(ep) + abs(x)))) / den
                            cnt[gi, ki] += 1; s1[gi, ki] += R; s2[gi, ki] += R * R
                            if up: pos = 0
                            else:
                                pos = -1; ep = x; esp = sp
                    else:
                        if up:
                            x = max(bt, o)
                            R = (-(x - ep) - (esp * spm + comm * (abs(ep) + abs(x)))) / den
                            cnt[gi, ki] += 1; s1[gi, ki] += R; s2[gi, ki] += R * R
                            if dn: pos = 0
                            else:
                                pos = 1; ep = x; esp = sp
                if pos != 0:
                    x = xclose
                    R = (pos * (x - ep) - (esp * spm + comm * (abs(ep) + abs(x)))) / den
                    cnt[gi, ki] += 1; s1[gi, ki] += R; s2[gi, ki] += R * R
    return cnt, s1, s2


def all_cells_fast(S, comm):
    gs = np.array([b // S.bar for b in Q.bar_sizes(S.bar)], np.int64); ks = np.array(Q.KS, float)
    prev_ok = np.isfinite(np.asarray(S.prev_close, float))
    cnt, s1, s2 = dt_cells_nb(np.asarray(S.O, float), np.asarray(S.H, float), np.asarray(S.L, float), np.asarray(S.C, float),
                              np.asarray(S.SP, float), np.asarray(S.first, np.int64), prev_ok, comm, Q.SPM, gs, ks)
    out = {}
    for a, g in enumerate(gs):
        for b, k in enumerate(Q.KS):
            nn = cnt[a, b]
            if nn < 3: out[(int(g * S.bar), k)] = (int(nn), np.nan, np.nan); continue
            m = s1[a, b] / nn; var = (s2[a, b] - nn * m * m) / (nn - 1)
            out[(int(g * S.bar), k)] = (int(nn), m, m / np.sqrt(var / nn) if var > 0 else np.nan)
    return out


def dt_R(S, X, k, comm):
    BT, ST, _ = Q.dt_levels(S, k)
    t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, m = Q.dt_kernel(X.O, X.H, X.L, X.C, np.asarray(X.first, np.int64), BT, ST, max(16 * len(S.days), 1000))
    if m < 0: raise RuntimeError("capacity")
    t_i, t_e, t_d, t_ep, t_xp = t_i[:m], t_e[:m], t_d[:m], t_ep[:m], t_xp[:m]
    cost = X.SP[t_i, t_e] * Q.SPM + comm * (np.abs(t_ep) + np.abs(t_xp))
    with np.errstate(invalid="ignore", divide="ignore"):
        R = (t_d * (t_xp - t_ep) - cost) / (BT - ST)[t_i]
    return R[np.isfinite(R)]


def all_cells(S, comm):
    """{(bar, k): (n, mean, t)} for every Dual Thrust cell of this session."""
    out = {}
    for b in Q.bar_sizes(S.bar):
        X = Q.coarsen(S, b // S.bar)
        for k in Q.KS:
            R = dt_R(S, X, k, comm)
            out[(b, k)] = (len(R), R.mean() if len(R) else np.nan, Q.tstat(R))
    return out


def best_of(cells):
    el = [(v[2], key) for key, v in cells.items() if v[0] >= MIN_N and np.isfinite(v[2])]
    if not el: return np.nan, None, 0
    t, key = max(el)
    return t, key, len(el)


# ---------------------------------------------------------------------------------------------------------------- run
def cmd_run(n_perm):
    cat = U.catalog()
    syms = sorted({s for s, _ in cat if U.sessions_of(s)})
    done = set()
    if os.path.exists(PERM):
        x = pd.read_csv(PERM, usecols=["symbol", "session", "shuffle"])
        cnt = x.groupby(["symbol", "session"]).shuffle.nunique()
        done = set(cnt[cnt >= n_perm].index)
    t0 = time.time()
    for sym in syms:
        sessions, tf = Q.symbol_sessions(sym, cat)
        comm = U.commission_of(sym)
        for sess, S in sessions:
            if (sym, sess) in done: continue
            t1 = time.time()
            real = all_cells_fast(S, comm)
            rbest, rkey, rn = best_of(real)
            prim = PRIMARY_DT.get((sym, sess))
            pd.DataFrame([dict(symbol=sym, session=sess, bar=b, k=k, n=v[0], mean=v[1], t=v[2]) for (b, k), v in real.items()]).to_csv(
                REAL, mode="a", header=not os.path.exists(REAL), index=False, float_format="%.6g")
            parts = log_parts(S); eparts = exp_parts(S, parts)
            rows = []
            for s in range(n_perm):
                seed = zlib.crc32(f"{sym}|{sess}|{s}".encode()) & 0x7FFFFFFF
                X = shuffled(S, parts, seed, eparts)
                cells = all_cells_fast(X, comm)
                bt, bkey, bn = best_of(cells)
                r = dict(symbol=sym, session=sess, shuffle=s, max_t=bt, max_cell=f"{bkey[0]}|{bkey[1]}" if bkey else "", n_elig=bn)
                if prim is not None and prim in cells:
                    r.update(prim_n=cells[prim][0], prim_mean=cells[prim][1], prim_t=cells[prim][2])
                rows.append(r)
            D = pd.DataFrame(rows).reindex(columns=["symbol", "session", "shuffle", "max_t", "max_cell", "n_elig", "prim_n", "prim_mean", "prim_t"])
            D.to_csv(PERM, mode="a", header=not os.path.exists(PERM), index=False, float_format="%.5g")
            print(f"{sym} {sess}: real best t {rbest:.2f} ({rkey}, {rn} eligible cells); shuffled best t median {np.nanmedian(D.max_t):.2f}, "
                  f"95th {np.nanpercentile(D.max_t, 95):.2f}; {time.time() - t1:.0f}s [{(time.time() - t0) / 60:.1f} min]", flush=True)


def cmd_summary():
    P = pd.read_csv(PERM); Rl = pd.read_csv(REAL).drop_duplicates(["symbol", "session", "bar", "k"], keep="last")
    n_perm = P.shuffle.nunique()
    best = P.groupby("shuffle").max_t.max()
    el = Rl[Rl.n >= MIN_N]
    rb = el.loc[el.t.idxmax()]
    p_best = (1 + (best >= rb.t).sum()) / (1 + len(best))
    rows = [dict(test="real best cell", symbol=rb.symbol, session=rb.session, bar=rb.bar, k=rb.k, n=rb.n, mean=rb["mean"], t=rb.t,
                 p_best=p_best, shuffled_best_median=best.median(), shuffled_best_q95=best.quantile(0.95), n_perm=len(best),
                 cells=len(Rl), eligible=len(el))]
    print(f"{len(Rl)} Dual Thrust cells ({len(el)} with n >= {MIN_N}); {len(best)} complete shuffles (min per session {P.groupby(['symbol', 'session']).shuffle.nunique().min()})")
    print(f"real best: {rb.symbol} {rb.session} bar {rb.bar} k {rb.k}: n {rb.n}, mean {rb['mean']:+.3f}, t {rb.t:.2f}")
    print(f"shuffled best t: median {best.median():.2f}, 90th {best.quantile(0.9):.2f}, 95th {best.quantile(0.95):.2f}, max {best.max():.2f} -> p_best {p_best:.3f}")
    T = pd.read_csv(Q.PRIMARY_TRADES, parse_dates=["day"])
    for (sym, sess), (b, k) in sorted(PRIMARY_DT.items()):
        x = Rl[(Rl.symbol == sym) & (Rl.session == sess) & (Rl.bar == b) & (Rl.k == k)]
        if not len(x): continue
        x = x.iloc[0]; pp = P[(P.symbol == sym) & (P.session == sess)]
        p_alone_t = (1 + (pp.prim_t >= x.t).sum()) / (1 + pp.prim_t.notna().sum())
        p_alone_m = (1 + (pp.prim_mean >= x["mean"]).sum()) / (1 + pp.prim_mean.notna().sum())
        pb = (1 + (best >= x.t).sum()) / (1 + len(best))
        tr = T[(T.idea == "dt") & (T.symbol == sym) & (T.session == sess) & (T.bar == b) & (T.k == k)].R.values
        bca = RB.bca_bounds(tr, "mean", B=20000, rng=75) if len(tr) > 20 else None
        rows.append(dict(test="primary", symbol=sym, session=sess, bar=b, k=k, n=x.n, mean=x["mean"], t=x.t, p_best=pb, p_alone_t=p_alone_t,
                         p_alone_mean=p_alone_m, shuffled_mean_avg=pp.prim_mean.mean(), skill=x["mean"] - pp.prim_mean.mean(),
                         bca_low95=bca["low"][0.025] if bca else np.nan, bca_low90=bca["low"][0.05] if bca else np.nan))
        print(f"primary {sym} {sess} M{b} k={k}: n {x.n}, mean {x['mean']:+.3f}, t {x.t:.2f} | p_alone (t) {p_alone_t:.3f}, (mean) {p_alone_m:.3f}; "
              f"shuffled mean {pp.prim_mean.mean():+.3f} -> skill {x['mean'] - pp.prim_mean.mean():+.3f} | p_best {pb:.3f} | "
              f"BCa 95% lower bound {rows[-1]['bca_low95']:+.3f}")
    pd.DataFrame(rows).to_csv(SUMMARY, index=False, float_format="%.5g")


def cmd_verify():
    cat = U.catalog()
    for sym, sess in (("US100.cash", "us_cash"), ("XAUUSD", "server_day"), ("EURUSD", "london24")):
        S = dict(Q.symbol_sessions(sym, cat)[0])[sess]
        n, K = S.C.shape
        rng = np.random.default_rng(7); PA = np.empty((K, n), np.int64); PB = np.empty((K, n), np.int64)
        for k in range(K):                                  # the exact call sequence of permute_session
            PA[k] = rng.permutation(n); PB[k] = np.r_[0, rng.permutation(n - 1) + 1] if k == 0 else rng.permutation(n)
        g, h, l, c = log_parts(S)
        O2, H2, L2, C2, SP2 = rebuild(g, h, l, c, np.asarray(S.SP, float), float(S.O[0, 0]), PA, PB)
        ref = PM.permute_session(S, np.random.default_rng(7))
        err = max(np.nanmax(np.abs(a / b - 1)) for a, b in ((O2, ref.O), (H2, ref.H), (L2, ref.L), (C2, ref.C)))
        print(f"{sym} {sess}: max relative difference vs permute_session {err:.2e}; spread identical {np.array_equal(SP2, ref.SP)}")
        X = lite(S, S.O, S.H, S.L, S.C, S.SP)
        a = all_cells(X, U.commission_of(sym)); b = all_cells(S, U.commission_of(sym)); f = all_cells_fast(S, U.commission_of(sym))
        print("  lite vs Session cells identical:", all(np.allclose(a[q], b[q], equal_nan=True) for q in a),
              "| fused numba vs engine:", all(np.allclose(f[q], b[q], rtol=1e-9, equal_nan=True) for q in b))
        Xs = shuffled(S, log_parts(S), 3)
        a = all_cells(Xs, U.commission_of(sym)); f = all_cells_fast(Xs, U.commission_of(sym))
        print("  on a shuffle, fused numba vs engine:", all(np.allclose(f[q], a[q], rtol=1e-9, equal_nan=True) for q in a), list(f.items())[:2])


def cmd_skill():
    """Masters' skill: real mean R minus the average mean R of each shuffle's best cell. The best session-cell of every shuffle is
    regenerated from its seed (shuffles are deterministic) and its mean R read off."""
    P = pd.read_csv(PERM)
    top = P.loc[P.groupby("shuffle").max_t.idxmax()].sort_values(["symbol", "session"])
    cat = U.catalog(); means = []; cur = None
    for _, r in top.iterrows():
        if cur != r.symbol:
            sess = dict(Q.symbol_sessions(r.symbol, cat)[0]); cur = r.symbol
        S = sess[r.session]
        seed = zlib.crc32(f"{r.symbol}|{r.session}|{int(r.shuffle)}".encode()) & 0x7FFFFFFF
        cells = all_cells_fast(shuffled(S, None, seed, exp_parts(S, log_parts(S))), U.commission_of(r.symbol))
        b, k = r.max_cell.split("|"); v = cells[(int(b), float(k))]
        assert abs(v[2] - r.max_t) < 1e-3, (r.symbol, r.session, r.shuffle, v, r.max_t)
        means.append(dict(shuffle=int(r.shuffle), symbol=r.symbol, session=r.session, cell=r.max_cell, n=v[0], mean=v[1], t=v[2]))
    M = pd.DataFrame(means)
    Rl = pd.read_csv(REAL).drop_duplicates(["symbol", "session", "bar", "k"], keep="last")
    print(f"shuffled best cells: average mean R {M['mean'].mean():+.4f} (median {M['mean'].median():+.4f}), average n {M.n.mean():.0f}, average t {M.t.mean():.2f}")
    for (sym, sess), (b, k) in sorted(PRIMARY_DT.items()):
        x = Rl[(Rl.symbol == sym) & (Rl.session == sess) & (Rl.bar == b) & (Rl.k == k)].iloc[0]
        print(f"  {sym} {sess} M{b} k={k}: real {x['mean']:+.4f} -> Masters skill {x['mean'] - M['mean'].mean():+.4f}R")
    el = Rl[Rl.n >= MIN_N]; rb = el.loc[el.t.idxmax()]
    print(f"  real best {rb.symbol} {rb.session} {rb.bar} {rb.k}: {rb['mean']:+.4f} -> skill {rb['mean'] - M['mean'].mean():+.4f}R")
    S0 = pd.read_csv(SUMMARY)
    S0["shuffled_best_cell_mean_avg"] = M["mean"].mean(); S0["masters_skill"] = S0["mean"] - M["mean"].mean()
    S0.to_csv(SUMMARY, index=False, float_format="%.5g")


if __name__ == "__main__":
    if "--verify" in sys.argv: cmd_verify()
    elif sys.argv[1] == "run": cmd_run(int(sys.argv[2]) if len(sys.argv) > 2 else 200)
    elif sys.argv[1] == "skill": cmd_skill()
    else: cmd_summary()
