"""Selection-aware permutation test for the battery's pooled intraday cells (log #70; #60 protocol).
Every intraday variant (quant/intraday.VARIANTS except the noise band) on every symbol's sessions, pooled by (rule, group,
session) exactly like results/battery_groups.csv. Statistic = pooled t of R (n >= 60). Each shuffle permutes every session
matrix (quant/permute.permute_session: bars shuffled across days within their time-of-day column; the overnight gap shuffled
separately), reruns all variants, and keeps the best pooled t. p_best = share of shuffles whose best pooled cell >= the real best;
also p_alone for the named cells and skill = real avg R - average of the shuffled best cell's avg R (Masters' estimate).
python3 quant/mcpt_battery.py [n_perm]  -> results/mcpt_battery.csv"""
import os, sys, time, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import universe as U, intraday as ID, permute as P
from sessions import Session
from run_battery import intraday_frame

WATCH = [("GAPfade1.0", "index", "eu_cash"), ("GAPfade1.0", "us_index", "us_cash"), ("ORB15", "us_index", "us_cash"),
         ("ORB30", "us_index", "us_cash"), ("OC30", "us_index", "us_cash")]


def run_all(sessions):
    """-> {(rule, group, session): concatenated R array}"""
    pooled = {}
    for (sym, sess), (S, comm, grp) in sessions.items():
        for name, fn, kw, scope in ID.VARIANTS:
            if name == "NB" or not ID.applies(scope, sess): continue
            if "minutes" in kw and kw["minutes"] % S.bar: continue
            sp = fn(S, **kw)
            if sp is None: continue
            R = ID.simulate(S, sp["e_col"], sp["e_px"], sp["d"], sp["stop"], sp["target"], sp["exit_col"], comm, 1.2, sp["breakout"])[0]
            R = R[np.isfinite(R)]
            if len(R): pooled.setdefault((name, grp, sess), []).append(R)
    return {k: np.concatenate(v) for k, v in pooled.items()}


def tstat(R): return R.mean() / R.std(ddof=1) * np.sqrt(len(R)) if len(R) >= 60 and R.std() > 0 else np.nan


def main():
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    t0 = time.time(); cat = U.catalog(); sessions = {}
    for sym in sorted({s for s, _ in cat}):
        d, tf = intraday_frame(sym, cat)
        if d is None or len(d) < 2000: continue
        for sess in U.sessions_of(sym):
            try: S = Session(d, sess)
            except Exception: continue
            if len(S.days) >= 150: sessions[(sym, sess)] = (S, U.commission_of(sym), U.group_of(sym))
    print(f"{len(sessions)} symbol-sessions loaded ({time.time() - t0:.0f}s)", flush=True)
    real = run_all(sessions)
    rt = {k: tstat(v) for k, v in real.items()}; ra = {k: v.mean() for k, v in real.items()}
    best_k = max((k for k in rt if np.isfinite(rt[k])), key=lambda k: rt[k])
    print(f"real: {len(real)} pooled cells; best {best_k} t {rt[best_k]:.2f} avg {ra[best_k]:+.3f} ({time.time() - t0:.0f}s)", flush=True)
    rng = np.random.default_rng(70); bests_t, bests_a = [], []; watch = {k: [] for k in WATCH}
    for i in range(n_perm):
        sh = {key: (P.permute_session(S, rng), c, g) for key, (S, c, g) in sessions.items()}
        pr = run_all(sh)
        pt = {k: tstat(v) for k, v in pr.items()}
        kk = max((k for k in pt if np.isfinite(pt[k])), key=lambda k: pt[k])
        bests_t.append(pt[kk]); bests_a.append(pr[kk].mean())
        for k in WATCH: watch[k].append(pr[k].mean() if k in pr else np.nan)
        if (i + 1) % 20 == 0: print(f"  {i + 1} shuffles ({time.time() - t0:.0f}s); best shuffled t so far: median {np.median(bests_t):.2f}", flush=True)
    bests_t = np.array(bests_t)
    rows = []
    for k in sorted(real, key=lambda k: -np.nan_to_num(rt[k], nan=-99))[:25]:
        rows.append(dict(rule=k[0], group=k[1], session=k[2], n=len(real[k]), avgR=ra[k], t=rt[k], p_best=P.pvalue(rt[k], bests_t),
                         p_alone=P.pvalue(ra[k], watch[k]) if k in watch else np.nan, skill=ra[k] - np.nanmean(bests_a)))
    D = pd.DataFrame(rows); D.to_csv(os.path.join(HERE, "..", "results", "mcpt_battery.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 200); print(D.round(3).to_string(index=False))
    print(f"shuffled best pooled t: median {np.median(bests_t):.2f}, 90th {np.percentile(bests_t, 90):.2f}, 95th {np.percentile(bests_t, 95):.2f}, "
          f"99th {np.percentile(bests_t, 99):.2f}; average best cell avg R {np.nanmean(bests_a):+.3f}")
    for k in WATCH:
        if k in real: print(f"  {k}: real {ra[k]:+.3f} (t {rt[k]:.2f}) | p_alone {P.pvalue(ra[k], watch[k]):.3f} | p_best {P.pvalue(rt[k], bests_t):.3f}")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
