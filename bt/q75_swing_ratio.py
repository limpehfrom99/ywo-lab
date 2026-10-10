"""Log #75 / backlog #36 — gold/silver ratio mean reversion (E. Chan style), and the same rule on every pair within metals,
within US indices and within EU indices; D1 primary, H4 (server clock) and H1 with the same bar counts. Pre-registered, unchanged.

Rule: x = log(close_A / close_B) on bars where both trade (inner join on bar time); z = (x - mean of the last 60 x) / std of the
last 60 x (current bar included). z > 2 at a close -> short A, long B at the next bar's opens; z < -2 -> long A, short B. Equal
dollar notional per leg. Exit at the next bar's opens after a close where z has crossed 0 (z <= 0 for a short-A trade, >= 0 for a
long-A trade), or at the open 20 bars after entry. No stop. One position per pair. A data hole > 10 days ends a segment.
Return per trade = long leg % + short leg % of one leg's notional, after both legs' spread x 1.2, commission x (|entry| + |exit|)
and swaps (each leg's own side, rate and triple day).
R (for the CANDIDATE bar) = that return / the 60-bar std of x at the signal bar (1 sigma of the ratio = the z unit; entry at z = 2,
exit at z = 0 is ~ +2R if the mean stays put).
Baselines: coin = the opposite trade at the same moments (same exit bar); random timing = same direction and holding time from 20
random entry bars of the same pair (R per that bar's sigma). A cell must beat both.
Output: results/q75_swing_ratio_years.csv, _cells.csv, _trades.csv (every pair trade).
"""
import sys, os, time, itertools, zlib
import numpy as np, pandas as pd
from numba import njit

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
U = C.U

SETS = {"metal_pairs": ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "XCUUSD"],
        "us_index_pairs": ["US100.cash", "US500.cash", "US30.cash", "US2000.cash"],
        "eu_index_pairs": ["GER40.cash", "EU50.cash", "FRA40.cash", "SPN35.cash", "N25.cash"]}
N_Z, Z_IN, MAX_HOLD, M_RAND = 60, 2.0, 20, 20


@njit(cache=True)
def kernel(z, start, z_in, max_hold):
    n = len(z)
    E_i = np.empty(n, np.int64); X_i = np.empty(n, np.int64); D = np.empty(n, np.int64); S_i = np.empty(n, np.int64)
    K = np.empty(n, np.int64)
    nt = 0; pos = 0; e = 0
    for i in range(start, n):
        if pos != 0:
            hit = (pos == -1 and z[i] <= 0) or (pos == 1 and z[i] >= 0)
            tim = (i + 1 - e) >= max_hold
            if hit or tim or i == n - 1:
                if i + 1 < n:
                    X_i[nt - 1] = i + 1; K[nt - 1] = 0 if hit else 1
                else:
                    X_i[nt - 1] = i; K[nt - 1] = 2
                pos = 0
            continue
        if i + 1 < n and np.isfinite(z[i]):
            if z[i] > z_in: d = -1
            elif z[i] < -z_in: d = 1
            else: d = 0
            if d != 0:
                pos = d; e = i + 1
                E_i[nt] = e; D[nt] = d; S_i[nt] = i; X_i[nt] = -1; K[nt] = -1; nt += 1
    return E_i[:nt], X_i[:nt], D[:nt], S_i[:nt], K[:nt]


def load_sym(sym, cat):
    intra, btf, rel = C.load_intraday(sym, cat)
    d1 = C.load_d1(sym, cat, intra, rel)
    fr = {"D1": d1}
    if intra is not None:
        for tf in ("H4", "H1"): fr[tf] = C.resample(intra, tf)
    p_ref = d1.close.iloc[-1]
    sw = C.Swaps(sym, C.ns(d1.index)[0] - 10 * 86400 * C.NS, C.ns(d1.index)[-1] + 10 * 86400 * C.NS, p_ref)
    return fr, sw, U.commission_of(sym)


def leg_net(o, sp, sw, comm, side, e, x, t):
    """Per-trade net return of one leg (fraction of its notional), entry at o[e], exit at o[x] (or close for end-of-data)."""
    E = o[0][e]; X = np.where(x[1] == 2, o[1][x[0]], o[0][x[0]])
    gross = side * (X / E - 1)
    nights = sw.nights(t[e], t[x[0]])
    cost = 1.2 * sp[e] / E + comm * (np.abs(E) + np.abs(X)) / E + nights * sw.per_night(side, E) / E
    return gross - cost, gross, cost


def pair_trades(A, B, tf, swA, swB, cA, cB, seed):
    x = pd.concat([A[["open", "close", "sp"]].add_suffix("_a"), B[["open", "close", "sp"]].add_suffix("_b")], axis=1, join="inner").dropna()
    out = []
    for sa, sb in C.segments(C.ns(x.index)):
        if sb - sa < N_Z + 40: continue
        xs = x.iloc[sa:sb]
        lr = np.log(xs.close_a.values / xs.close_b.values)
        s = pd.Series(lr); m = s.rolling(N_Z).mean().values; sd = s.rolling(N_Z).std(ddof=1).values
        z = (lr - m) / sd
        E_i, X_i, D, S_i, K = kernel(z, N_Z - 1, Z_IN, MAX_HOLD)
        if len(E_i) == 0: continue
        t = C.ns(xs.index)
        oa = (xs.open_a.values, xs.close_a.values); ob = (xs.open_b.values, xs.close_b.values)
        spa, spb = xs.sp_a.values, xs.sp_b.values

        def net(d, e, xi, k):
            na, ga, ca_ = leg_net(oa, spa, swA, cA, d, e, (xi, k), t)
            nb, gb, cb_ = leg_net(ob, spb, swB, cB, -d, e, (xi, k), t)
            return na + nb, ga + gb, ca_ + cb_

        r_net, r_gross, r_cost = net(D, E_i, X_i, K)
        c_net, _, _ = net(-D, E_i, X_i, K)
        sig = sd[S_i]
        # random timing: same direction and holding, 20 random entries per trade
        rng = np.random.default_rng(seed + sa)
        hold = X_i - E_i
        n = len(xs); base = np.full(len(E_i), np.nan)
        for q in range(len(E_i)):
            hi = n - 1 - hold[q] - 1
            if hi <= N_Z: continue
            r = rng.integers(N_Z - 1, hi, M_RAND)
            ok = np.isfinite(sd[r]) & (sd[r] > 0)
            r = r[ok]
            if not len(r): continue
            e2 = r + 1; x2 = e2 + hold[q]
            nn, _, _ = net(np.full(len(r), D[q]), e2, x2, np.zeros(len(r), np.int64))
            base[q] = np.mean(nn / sd[r])
        out.append(pd.DataFrame(dict(t=t[E_i], t_exit=t[X_i], side=D, ret=r_net, gross=r_gross, cost=r_cost, coin_ret=c_net,
                                     sigma=sig, R=r_net / sig, R_coin=c_net / sig, R_rand=base, hold=hold, z_exit=(K == 0))))
    return pd.concat(out, ignore_index=True) if out else None


def main():
    cat = U.catalog(); t0 = time.time()
    pre = os.path.join(C.RES, "q75_swing_ratio")
    for suf in ("_years.csv", "_cells.csv", "_trades.csv"):
        if os.path.exists(pre + suf): os.remove(pre + suf)
    for grp, syms in SETS.items():
        cache = {}
        for a, b in itertools.combinations(syms, 2):
            for s in (a, b):
                if s not in cache: cache[s] = load_sym(s, cat)
            (FA, swA, cA), (FB, swB, cB) = cache[a], cache[b]
            for tf in ("D1", "H4", "H1"):
                if tf not in FA or tf not in FB: continue
                T = pair_trades(FA[tf], FB[tf], tf, swA, swB, cA, cB, zlib.crc32(f"{a}|{b}|{tf}".encode()) & 0x7FFFFFF)
                pair = f"{a.replace('.cash', '')}/{b.replace('.cash', '')}"
                if T is None or not len(T):
                    print(f"  {pair:14s} {tf}: no trades", flush=True); continue
                base = np.where(np.isfinite(T.R_rand), T.R_rand, T.R_coin)     # random-timing baseline (coin checked per cell)
                Y = C.year_rows(T.R.values, T.t.values, base, idea="ratio", symbol=pair, group=grp, tf=tf, cell="z60_2_0_h20")
                C.append_csv(pd.DataFrame(Y), pre + "_years.csv")
                st = C.stats_from_years(pd.DataFrame(Y)); by_year = st.pop("by_year", "")
                yr = pd.Series(T.ret.values * 100, index=pd.DatetimeIndex(T.t.values).year).groupby(level=0).sum()
                row = dict(pair=pair, group=grp, tf=tf, start=str(pd.Timestamp(T.t.min()).date()), **st,
                           coin=T.R_coin.mean(), rand=np.nanmean(T.R_rand),
                           beats_coin=bool(T.R.mean() > T.R_coin.mean()), beats_rand=bool(T.R.mean() > np.nanmean(T.R_rand)),
                           ret_pct=T.ret.mean() * 100, gross_pct=T.gross.mean() * 100, cost_pct=T.cost.mean() * 100,
                           pct_per_year_mean=yr.mean(), pct_by_year=" ".join(f"{y % 100:02d}:{v:+.1f}" for y, v in yr.items()),
                           hold_med=T.hold.median(), z_exit_share=T.z_exit.mean(), sigma_med_pct=T.sigma.median() * 100)
                row["candidate"] = bool(st.get("candidate", False) and row["beats_coin"])   # must beat both baselines
                C.append_csv(pd.DataFrame([row]), pre + "_cells.csv")
                C.append_csv(T.assign(pair=pair, group=grp, tf=tf), pre + "_trades.csv")
                print(f"  {pair:14s} {tf} " + C.fmt_stats(st) + f" | {row['ret_pct']:+.3f}%/trade, {row['pct_per_year_mean']:+.1f}%/yr"
                      f" coin {row['coin']:+.3f} rand {row['rand']:+.3f}", flush=True)
        print(f"{grp} done {time.time() - t0:.0f}s", flush=True)
        del cache


if __name__ == "__main__":
    main()
