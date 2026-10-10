"""q75 ports — permutation check of the only cell of the three ports that passed the per-cell CANDIDATE bar:
#22 SMC grid, US30.cash, zone none / structure H1 / entry M5 / target 2R (+0.158R, t 2.3, 474 trades).
No pre-registered primary cell passed, so the full selection-aware test over all 390 cells of the idea (31 symbols) was not
triggered and would take hours here. This is the affordable part: US30's 5-minute bars shuffled across days within their New York
time-of-day slot (bt/robust.permute_bars; the spread travels with the bar), all 26 US30 cells re-run per shuffle (same code as
bt/q75_ports_smc.py), statistic = t of the cell's trades (cells with < 30 trades ignored). p_best here only corrects for the 26 US30
cells; the cell was really picked from 390, so the true selection penalty is larger. Plus robust.bca_bounds of the real cell.
Usage: python3 bt/q75_ports_perm.py [n_shuffles=200]"""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q75_ports_common as C                              # noqa: E402
import q75_ports_smc as P                                 # noqa: E402
import smc_grid as SG                                     # noqa: E402
import xgrid                                              # noqa: E402
import robust                                             # noqa: E402

SYM, TARGET = "US30.cash", "none/H1/M5/2R"
OUT = os.path.join(C.RES, "q75_ports_perm_smc_us30.csv")


def grid_stats(base, btf):
    res = C.TF_MIN[btf]; fr = xgrid.frames(base, btf); atr_df = xgrid.daily_atr(base)
    entries = [e for e in ("M15", "M5", "M1") if e in fr and C.TF_MIN[e] >= res]
    cells = [(z, s, e) for z in ("D1", "H4", None) for s in ("H4", "H1", "M15") for e in entries
             if SG.TF_MIN[s] > SG.TF_MIN[e] and (z is None or SG.TF_MIN[z] > SG.TF_MIN[s])]
    need = sorted({tf for c in cells for tf in c if tf}); comm = C.U.commission_of(SYM); rows = []
    for mirror in (False, True):
        T = {tf: SG.TF(fr[tf], mirror, atr_df) for tf in need}; G = C.Exits(base, mirror, res); cc, sc = {}, {}
        for z, s, e in cells:
            for tgt_idm in (True, False):
                rows += [(f"{z or 'none'}/{s}/{e}/{'IDM' if tgt_idm else '2R'}", -1 if mirror else 1) + r
                         for r in P.run_cell(T, z, s, e, tgt_idm, cc, sc, G, comm)]
    X = pd.DataFrame(rows, columns=["cell", "side", "t", "R0", "Rf0", "rr", "risk_pct", "t_in", "t_out", "t_outf", "e_abs", "risk"])
    X["R"] = X.R0 - C.swap_R(SYM, X.side.values, X.e_abs.values, X.risk.values, X.t_in.values, X.t_out.values)
    names = [f"{z or 'none'}/{s}/{e}/{tg}" for z, s, e in cells for tg in ("IDM", "2R")]
    g = X.groupby("cell").R
    st = pd.DataFrame({"n": g.size(), "mean": g.mean(), "t": g.apply(C.tstat)}).reindex(names)
    st.loc[st.n.fillna(0) < 30, ["t", "mean"]] = np.nan
    return st


if __name__ == "__main__":
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    t0 = time.time()
    tr = pd.read_pickle(os.path.join(C.SCR, "smc", f"{SYM}.pkl"))
    x = tr[(tr.zone == "none") & (tr.structure == "H1") & (tr.entry == "M5") & (tr.target == "2R")].R.values.astype(float)
    b = robust.bca_bounds(x, "mean", 20000, rng=1)
    print(f"real cell {TARGET}: n={len(x)} mean={x.mean():+.3f}  BCa 95% lower {b['low'][0.025]:+.3f} / 90% lower {b['low'][0.05]:+.3f}", flush=True)
    base, btf = C.load_base(SYM)
    real = grid_stats(base, btf)
    print(f"real grid recomputed in {time.time() - t0:.0f}s: {TARGET} t={real.loc[TARGET, 't']:+.2f} mean={real.loc[TARGET, 'mean']:+.3f}", flush=True)
    ny = base.index.tz_localize("UTC").tz_convert("America/New_York"); slots = np.asarray(ny.hour * 60 + ny.minute)
    o, h, l, c, sp = (base[k].values for k in ("open", "high", "low", "close", "sp"))
    rng = np.random.default_rng(75)
    if os.path.exists(OUT): os.remove(OUT)
    null_t, null_m = [], []
    for k in range(n_perm):
        po, ph, pl, pc, psp = robust.permute_bars(o, h, l, c, slots, rng, extra=(sp,))
        pb = pd.DataFrame({"open": po, "high": ph, "low": pl, "close": pc, "sp": psp}, index=base.index)
        st = grid_stats(pb, btf); null_t.append(st.t.values); null_m.append(st["mean"].values)
        pd.DataFrame([dict(shuffle=k, cell=i, n=r.n, mean=r["mean"], t=r.t) for i, r in st.iterrows()]).to_csv(
            OUT, mode="a", header=(k == 0), index=False, float_format="%.5g")
        if (k + 1) % 10 == 0:
            res = robust.mcpt_select(real.t, np.array(null_t))
            print(f"  {k + 1} shuffles ({time.time() - t0:.0f}s): p_alone {res.loc[TARGET, 'p_alone']:.3f} p_best {res.loc[TARGET, 'p_best']:.3f} "
                  f"null best t avg {res.attrs['null_best_avg']:+.2f}", flush=True)
    res_t = robust.mcpt_select(real.t, np.array(null_t)); res_m = robust.mcpt_select(real["mean"], np.array(null_m))
    print(res_t.round(3).to_string(), flush=True)
    print(f"\n{TARGET}: statistic t  -> p_alone {res_t.loc[TARGET, 'p_alone']:.3f}, p_best (26 US30 cells) {res_t.loc[TARGET, 'p_best']:.3f}, "
          f"null best t avg {res_t.attrs['null_best_avg']:+.2f}, q95 {res_t.attrs['null_best_q95']:+.2f}", flush=True)
    print(f"{TARGET}: statistic mean -> p_alone {res_m.loc[TARGET, 'p_alone']:.3f}, p_best {res_m.loc[TARGET, 'p_best']:.3f}, "
          f"skill {res_m.loc[TARGET, 'skill']:+.3f}R", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)
