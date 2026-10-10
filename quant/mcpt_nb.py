"""Log #74: the noise band on every market of the export, selection-aware (pre-registered in research/log.md #74).
18 variants (lookback 10/14/20 days x decision every 15/30/60 minutes x VWAP stop on/off) on every symbol-session the battery
used (noise band scope = every session except london24). Statistic = per-cell t of daily R (>= 150 traded days). Each shuffle
permutes every session matrix (quant/permute.permute_session) and reruns every cell; p_best = share of shuffles whose best cell t
>= the real best; p_alone for US100's published variant and the pooled US-index group. Walk-forward over the 18 variants on US100.
python3 quant/mcpt_nb.py [n_perm]  -> results/mcpt_nb_cells.csv, results/mcpt_nb_perm.csv"""
import os, sys, time, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "bt"))
import universe as U, intraday as ID, permute as P
from sessions import Session
from run_battery import intraday_frame
import robust as RB

VARS = list(itertools.product((10, 14, 20), (15, 30, 60), (True, False)))
PUB = (14, 30, True)
USI = ("US100.cash", "US500.cash", "US30.cash", "US2000.cash")


def nb(S, lookback, interval, use_vwap, comm, sp_mult=1.2):
    """quant/intraday.noise_band with the decision interval as a parameter (same code otherwise)."""
    if interval % S.bar: return None
    step = S.cols(interval); n, K = S.C.shape
    marks = np.arange(step - 1, K, step)
    if len(marks) < 4: return None
    Cm = S.C[:, marks]; SPm = S.SP[:, marks]
    tp = (S.H + S.L + S.C) / 3; v = np.where(S.V > 0, S.V, 1.0)
    vw = (np.cumsum(tp * v, 1) / np.cumsum(v, 1))[:, marks]
    move = np.abs(Cm / S.open[:, None] - 1)
    sig = pd.DataFrame(move).rolling(lookback).mean().shift(1).values
    pc = S.prev_close
    ub = np.maximum(S.open, pc)[:, None] * (1 + sig); lb = np.minimum(S.open, pc)[:, None] * (1 - sig)
    pos = np.zeros(n); ent = np.full(n, np.nan); ret = np.zeros(n); first_sig = np.full(n, np.nan)
    ok = np.isfinite(sig[:, 0]) & np.isfinite(pc)
    M = len(marks)
    for m in range(M):
        p = Cm[:, m]
        if m == M - 1: tgt = np.zeros(n)
        elif use_vwap: tgt = np.where(p > np.maximum(ub[:, m], vw[:, m]), 1, np.where(p < np.minimum(lb[:, m], vw[:, m]), -1, 0))
        else: tgt = np.where(p > ub[:, m], 1, np.where(p < lb[:, m], -1, pos))
        tgt = np.where(ok, tgt, 0)
        ch = tgt != pos
        cs = SPm[:, m] * sp_mult / 2 / p + comm
        closing = ch & (pos != 0)
        ret += np.where(closing, pos * (p / np.where(np.isfinite(ent), ent, p) - 1) - cs, 0)
        opening = ch & (tgt != 0)
        ret -= np.where(opening, cs, 0)
        first_sig = np.where(opening & np.isnan(first_sig), sig[:, m], first_sig)
        ent = np.where(opening, p, np.where(ch, np.nan, ent))
        pos = tgt
    traded = np.isfinite(first_sig)
    with np.errstate(invalid="ignore", divide="ignore"):
        R = np.where(traded, ret / first_sig, np.nan)
    return R


def tstat(R):
    R = R[np.isfinite(R)]
    return R.mean() / R.std(ddof=1) * np.sqrt(len(R)) if len(R) >= 150 and R.std() > 0 else np.nan


def run_all(sessions):
    """-> {(sym, sess, variant): R per day (NaN = no trade)}"""
    out = {}
    for (sym, sess), (S, comm) in sessions.items():
        for v in VARS:
            R = nb(S, *v, comm)
            if R is not None: out[(sym, sess, v)] = R
    return out


def main():
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    t0 = time.time(); cat = U.catalog(); sessions = {}
    for sym in sorted({s for s, _ in cat}):
        d, tf = intraday_frame(sym, cat)
        if d is None or len(d) < 2000: continue
        for sess in U.sessions_of(sym):
            if not ID.applies("cash", sess): continue
            try: S = Session(d, sess)
            except Exception: continue
            if len(S.days) >= 150: sessions[(sym, sess)] = (S, U.commission_of(sym))
    print(f"{len(sessions)} symbol-sessions ({time.time() - t0:.0f}s)", flush=True)
    real = run_all(sessions)
    rows = []
    for (sym, sess, v), R in real.items():
        S = sessions[(sym, sess)][0]; m = np.isfinite(R); dd = pd.DatetimeIndex(S.days)
        yrs = pd.Series(R[m]).groupby(dd[m].year).mean()
        rows.append(dict(sym=sym, sess=sess, group=U.group_of(sym), lookback=v[0], interval=v[1], vwap=v[2], n=int(m.sum()),
                         avgR=np.nanmean(R) if m.any() else np.nan, t=tstat(R),
                         from2024=np.nanmean(R[m & (dd >= "2024-01-01")]) if (m & (dd >= "2024-01-01")).any() else np.nan,
                         by_year=" ".join(f"{y % 100}:{x:+.2f}" for y, x in yrs.items())))
    C = pd.DataFrame(rows); C.to_csv(os.path.join(ROOT, "results", "mcpt_nb_cells.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 250)
    print(f"{len(C)} cells ({time.time() - t0:.0f}s); cells with t: {C.t.notna().sum()}; positive: {(C.avgR > 0).mean():.0%}")
    print(C.sort_values("t", ascending=False).head(15).round(3).to_string(index=False))
    print("\nby group (all variants): " + ", ".join(f"{g} {x.avgR.mean():+.3f}" for g, x in C.groupby("group")))
    pub = C[(C.lookback == 14) & (C.interval == 30) & (C.vwap == True)]
    print("published variant by symbol (indices):"); print(pub[pub.group.isin(["us_index", "index"])][["sym", "sess", "n", "avgR", "t", "from2024", "by_year"]].round(3).to_string(index=False))

    def usi_pooled(res):
        R = np.concatenate([res[(s, "us_cash", PUB)] for s in USI if (s, "us_cash", PUB) in res]); return np.nanmean(R)
    real_t = {k: tstat(R) for k, R in real.items()}
    best_k = max((k for k in real_t if np.isfinite(real_t[k])), key=lambda k: real_t[k]); best_t = real_t[best_k]
    us100 = ("US100.cash", "us_cash", PUB); us100_m = np.nanmean(real[us100]); usi_m = usi_pooled(real)
    print(f"\nreal best cell {best_k} t {best_t:.2f}; US100 published mean {us100_m:+.3f} t {real_t[us100]:.2f}; US-index pooled mean {usi_m:+.3f}")
    # walk-forward over the 18 variants on US100
    S = sessions[("US100.cash", "us_cash")][0]; dd = pd.DatetimeIndex(S.days)
    oos = []; picks = []
    for Y in (2023, 2024, 2025, 2026):
        tr = dd < f"{Y}-01-01"; te = (dd >= f"{Y}-01-01") & (dd < f"{Y + 1}-01-01")
        cand = {v: real[("US100.cash", "us_cash", v)] for v in VARS if ("US100.cash", "us_cash", v) in real}
        tt = {v: (np.nanmean(R[tr]) / np.nanstd(R[tr]) * np.sqrt(np.isfinite(R[tr]).sum())) for v, R in cand.items()}
        v = max(tt, key=tt.get); x = cand[v][te]; oos.append(x[np.isfinite(x)]); picks.append((Y, v, np.nanmean(x), np.nanmean(real[us100][te])))
    o = np.concatenate(oos)
    print("US100 walk-forward picks: " + "; ".join(f"{Y}: {v} -> {m:+.3f} (published {p:+.3f})" for Y, v, m, p in picks))
    pubo = np.concatenate([real[us100][(dd >= f"{Y}-01-01") & (dd < f"{Y + 1}-01-01")] for Y in (2023, 2024, 2025, 2026)])
    print(f"US100 WF OOS mean {o.mean():+.3f} (n {len(o)}) vs published on the same years {np.nanmean(pubo):+.3f}")
    b = RB.bca_bounds(real[us100][np.isfinite(real[us100])], B=20000, rng=1)
    print(f"US100 published BCa 95% lower bound {b['low'][0.025]:+.3f} (mean {b['theta']:+.3f})", flush=True)
    rng = np.random.default_rng(74); bests, u100, usi = [], [], []
    for k in range(n_perm):
        sh = {key: (P.permute_session(S_, rng), c) for key, (S_, c) in sessions.items()}
        pr = run_all(sh)
        pt = [tstat(R) for R in pr.values()]
        bests.append(np.nanmax(pt)); u100.append(np.nanmean(pr[us100])); usi.append(usi_pooled(pr))
        if (k + 1) % 10 == 0:
            print(f"  {k + 1} shuffles ({time.time() - t0:.0f}s): best t median {np.nanmedian(bests):.2f}, 95th {np.nanpercentile(bests, 95):.2f}", flush=True)
            pd.DataFrame(dict(best_t=bests, us100=u100, usi=usi)).to_csv(os.path.join(ROOT, "results", "mcpt_nb_perm.csv"), index=False)
    pd.DataFrame(dict(best_t=bests, us100=u100, usi=usi)).to_csv(os.path.join(ROOT, "results", "mcpt_nb_perm.csv"), index=False)
    print(f"\nbest cell {best_k}: t {best_t:.2f} vs shuffled best t median {np.nanmedian(bests):.2f}, 95th {np.nanpercentile(bests, 95):.2f} -> p_best {P.pvalue(best_t, bests):.3f}")
    print(f"US100 published: mean {us100_m:+.3f} vs shuffled 95th {np.nanpercentile(u100, 95):+.3f} -> p_alone {P.pvalue(us100_m, u100):.3f}; "
          f"its t {real_t[us100]:.2f} vs shuffled bests -> p_best {P.pvalue(real_t[us100], bests):.3f}")
    print(f"US-index pooled (published): mean {usi_m:+.3f} vs shuffled 95th {np.nanpercentile(usi, 95):+.3f} -> p_alone {P.pvalue(usi_m, usi):.3f}")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
