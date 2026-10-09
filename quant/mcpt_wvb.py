"""Permutation test for the Williams volatility breakout on FTMO gold (#50/#65; #60 protocol), on session matrices of the broker
day (server 00:00-24:00 = 17:00-17:00 New York). Rule as in bt/classic_intraday.rule_wvb: buy stop at the day's open + k x yesterday's
range, sell stop at open - k x range, the first break decides (a bar that breaks both = a stopped long), stop 0.5 x range, exit at the
day's close; spread x 1.2 + 0.0007%/side. Cells: k = 0.3, 0.5, 0.7 (the three run in #50). Statistic: mean R; 1,000 shuffles of the
5-minute bars within their time-of-day column across days; p_alone for k = 0.5 and p_best over the three k.
python3 quant/mcpt_wvb.py [n_perm] [SYMBOL]"""
import os, sys, time, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import universe as U, permute as P, sessions as SS
from sessions import Session

SS.SESSIONS["server_day"] = ("UTC", "00:00", "23:55")


def wvb(S, k, comm):
    n, K = S.C.shape
    R0 = np.r_[np.nan, (S.high - S.low)[:-1]]
    up_lvl = S.open + k * R0; dn_lvl = S.open - k * R0
    cols = np.arange(K)[None, :]
    up = S.H >= up_lvl[:, None]; dn = S.L <= dn_lvl[:, None]
    fu = np.where(up.any(1), up.argmax(1), K + 9); fd = np.where(dn.any(1), dn.argmax(1), K + 9)
    d = np.where(fu <= fd, 1, -1); d = np.where(np.minimum(fu, fd) > K, 0, d)
    j = np.where(d == 1, fu, fd); i = np.arange(n); jj = np.clip(j, 0, K - 1)
    both = (fu == fd) & (fu < K)
    e = np.where(d == 1, np.maximum(up_lvl, S.O[i, jj]), np.minimum(dn_lvl, S.O[i, jj]))
    stop = e - d * 0.5 * R0
    win = (cols >= jj[:, None])
    hs = np.where(d[:, None] == 1, S.L <= stop[:, None], S.H >= stop[:, None]) & win
    fs = np.where(hs.any(1), hs.argmax(1), K + 9)
    o_fs = S.O[i, np.clip(fs, 0, K - 1)]
    X = np.where(fs < K, np.where(fs > jj, np.where(d == 1, np.minimum(stop, o_fs), np.maximum(stop, o_fs)), stop), S.C[:, -1])
    X = np.where(both, stop, X)
    risk = 0.5 * R0
    cost = S.SP[i, jj] * 1.2 + comm * (np.abs(e) + np.abs(X))
    with np.errstate(invalid="ignore", divide="ignore"):
        R = (d * (X - e) - cost) / risk
    ok = (d != 0) & np.isfinite(R) & (risk > 0)
    return R[ok]


def main():
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    sym = sys.argv[2] if len(sys.argv) > 2 else "XAUUSD"
    t0 = time.time(); cat = U.catalog()
    d = U.load(sym, "M5", cat); d = d[~d.index.duplicated()].sort_index()
    srv = d.copy(); srv.index = (d.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)).tz_localize("UTC")
    S = Session(srv, "server_day", min_cov=0.7, edge_min=70)     # gold/silver pause 00:00-01:00 server (17:00-18:00 New York)
    comm = U.commission_of(sym)
    ks = (0.3, 0.5, 0.7)
    real = {k: wvb(S, k, comm) for k in ks}
    for k in ks: print(f"{sym} k={k}: n {len(real[k])}, avg R {real[k].mean():+.3f}, t {real[k].mean() / real[k].std() * np.sqrt(len(real[k])):.2f}", flush=True)
    rng = np.random.default_rng(65); perm = {k: [] for k in ks}; best = []
    for i in range(n_perm):
        Pm = P.permute_session(S, rng)
        vals = {k: wvb(Pm, k, comm).mean() for k in ks}
        for k in ks: perm[k].append(vals[k])
        best.append(max(vals.values()))
        if (i + 1) % 200 == 0: print(f"  {i + 1} shuffles ({time.time() - t0:.0f}s)", flush=True)
    rb = max(real[k].mean() for k in ks)
    for k in ks:
        print(f"k={k}: real {real[k].mean():+.3f} | shuffled mean {np.mean(perm[k]):+.3f}, 95th {np.percentile(perm[k], 95):+.3f} | "
              f"p_alone {P.pvalue(real[k].mean(), perm[k]):.3f}")
    print(f"best of 3 k: real {rb:+.3f} vs shuffled bests 95th {np.percentile(best, 95):+.3f} -> p_best {P.pvalue(rb, best):.3f}; "
          f"skill {rb - np.mean(best):+.3f}R")
    # BCa-free quick bound: bootstrap 2.5th percentile of the k=0.5 mean
    b = np.random.default_rng(1); x = real[0.5]
    boots = [x[b.integers(0, len(x), len(x))].mean() for _ in range(5000)]
    print(f"k=0.5 bootstrap 95% interval of mean R: {np.percentile(boots, 2.5):+.3f} .. {np.percentile(boots, 97.5):+.3f}")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
