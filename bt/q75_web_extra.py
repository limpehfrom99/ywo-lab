"""GB4 primary cell (XAUUSD H4) by year against its random-entry long baseline (same exits, filters, costs, swaps; 4,000 random
entry bars), so the rule's excess over gold's own drift can be read per year. Writes results/q75_web_mql_primary_years.csv."""
import sys, os, zlib, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_web_common as C
import q75_web_mql as M

sym, grp, base_tf, d = next(C.datasets(symbols=["XAUUSD"]))
t = C.ns(d.index); o, h, l, c, sp = (d[k].values for k in ("open", "high", "low", "close", "sp"))
comm = C.U.commission_of(sym); base_ns = C.TF_NS[base_tf]; cal = C.swap_calendar(sym, t[0], t[-1])
send = C.session_end(t, base_ns, 30 * C.NS)
F = C.frames(d, base_tf, 0, want={"H4"})["H4"]; Ft = C.ns(F.index); sig, dist = M.gb4_signals(F)


def run(idx, one_pos):
    k0 = np.searchsorted(t, Ft[idx + 1]); k0c = np.minimum(k0, len(t) - 1)
    ok = (k0 < len(t)) & np.isfinite(dist[idx]) & ((sp[k0c] / 1.2) <= 0.10 * np.nan_to_num(dist[idx], nan=0.0)) & ((send[k0c] - t[k0c]) > 15 * C.NS)
    k0, ds = k0[ok].astype(np.int64), dist[idx][ok]
    tk, xi, xp, why = C.sim_bracket(t, o, h, l, c, k0, ds, np.full(len(k0), 2.0), 1, one_pos, M.MAXHOLD)
    k0, ds, xi, xp, why = k0[tk], ds[tk], xi[tk], xp[tk], why[tk]
    t_out = np.where(why == 3, t[xi] + base_ns - 1, t[xi] + base_ns // 2)
    R, swR, _ = C.trade_R(sym, 1, o[k0], xp, ds, sp[k0], t[k0], t_out, cal, comm)
    return pd.DataFrame(dict(t=pd.to_datetime(t[k0]), R=R, R0=R + swR))


real = run(np.flatnonzero(sig[:-1]), True)
rng = np.random.default_rng(zlib.crc32(b"q75web|XAUUSD|H4|years"))
base = run(np.sort(rng.choice(np.arange(205, len(F) - 1), 4000, replace=False)), False)
y = pd.DataFrame({"n": real.groupby(real.t.dt.year).R.size(), "rule": real.groupby(real.t.dt.year).R.mean(),
                  "rule_before_swaps": real.groupby(real.t.dt.year).R0.mean(), "baseline": base.groupby(base.t.dt.year).R.mean(),
                  "n_base": base.groupby(base.t.dt.year).R.size()})
y["excess"] = y.rule - y.baseline
for a_, b_ in (("2015-2019", (2015, 2019)), ("2020-2023", (2020, 2023)), ("2024-2026", (2024, 2026)), ("all", (2015, 2026))):
    r = real[(real.t.dt.year >= b_[0]) & (real.t.dt.year <= b_[1])]; bb = base[(base.t.dt.year >= b_[0]) & (base.t.dt.year <= b_[1])]
    y.loc[a_] = [len(r), r.R.mean(), r.R0.mean(), bb.R.mean(), len(bb), r.R.mean() - bb.R.mean()]
y.to_csv("/home/claude/ywo-lab/results/q75_web_mql_primary_years.csv")
print(y.round(3).to_string())
