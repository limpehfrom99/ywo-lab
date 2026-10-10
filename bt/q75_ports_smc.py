"""q75 port of the #31b SMC timeframe grid (bt/smc_grid.py) to the FTMO export — backlog #22, log #75.

zone_context, setups, trigger_nb (and through them zone_obs / pivots) are the original functions, imported; run_cell is copied
with only the exit/cost lines changed: exits on the export's finest bars (M1 for US100/US500, M5 for US30, M15 for forex; the
original's 3 x 1440 one-minute bars scaled to the same market time), spread x 1.2 + commission, swap per 17:00 New York rollover.
H4 and D1 candles on FTMO's server clock (xgrid.frames; the gold original used UTC H4). Entries 08:00-16:00 New York as in the
script (trigger_nb), for every symbol. Every nesting the script defines that the data allows:
  US100.cash / US500.cash: zone D1/H4/none x structure H4/H1/M15 x entry M15/M5/M1 (21 nestings x IDM/2R = 42 cells each)
  US30.cash (M5 only): entries M15/M5 (13 nestings, 26 cells);  forex (M15 only): entry M15, structure H4/H1 (5 nestings, 10 cells).
Usage: python3 bt/q75_ports_smc.py [SYMBOL ...]"""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q75_ports_common as C                              # noqa: E402
import smc_grid as SG                                     # noqa: E402
import xgrid                                              # noqa: E402

OUT = os.path.join(C.RES, "q75_ports_smc_cells.csv")
TRD = os.path.join(C.SCR, "smc"); os.makedirs(TRD, exist_ok=True)
FIRST = ["US100.cash", "US500.cash", "US30.cash"]


def run_cell(T, zone, struct, entry, tgt_idm, ctx_cache, setup_cache, G, comm):
    """smc_grid.run_cell; only the exit/cost lines differ."""
    S, E = T[struct], T[entry]
    key = (zone, struct)
    if key not in setup_cache:
        if (zone, struct) not in ctx_cache: ctx_cache[(zone, struct)] = SG.zone_context(S, T[zone] if zone else None)
        setup_cache[key] = SG.setups(S, ctx_cache[(zone, struct)])
    st_ns = SG.TF_MIN[struct] * 60_000_000_000; en_ns = SG.TF_MIN[entry] * 60_000_000_000
    win = int(min(48 * SG.TF_MIN[struct], 5 * 1440) / SG.TF_MIN[entry]); hold = 3 * 1440 // G.res
    rows = []
    for mi, ob_lo, ob_hi in setup_cache[key]:
        t_end = S.t[mi] + np.timedelta64(st_ns, "ns")
        a = np.searchsorted(E.t, t_end); b = min(a + win, len(E.t))
        if a >= len(E.t): continue
        atr = E.atr[a]
        if not np.isfinite(atr): continue
        a0 = np.searchsorted(E.t, S.t[mi]); idm0 = E.h[a0:a].max() if a > a0 else S.h[mi]
        m, e, stop, tgt = SG.trigger_nb(E.h, E.l, E.c, E.nym, a, b, ob_lo, ob_hi, atr, idm0, 2.0, tgt_idm)
        if m < 0: continue
        i0 = int(np.searchsorted(G.ti, int(E.t[m].astype(np.int64)) + en_ns)); i1 = min(i0 + hold, len(G.ti))
        if i1 <= i0: continue
        X, xi = C.exit_idx(G.h, G.l, G.c, i0, i1, stop, tgt, 1)
        risk = e - stop; cost = E.sp[m] + comm * (abs(e) + abs(X))
        Xf, fi = C.exit_idx(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1); cost_f = E.sp[m] + comm * (abs(e) + abs(Xf))
        rows.append((E.t[m], (X - e - cost) / risk, (e - Xf - cost_f) / risk, (tgt - e) / risk, risk / abs(e) * 100,
                     G.ti[i0], G.ti[xi], G.ti[fi], abs(e), risk))
    return rows


COLS = ["zone", "structure", "entry", "target", "side", "t", "R0", "Rf0", "rr", "risk_pct", "t_in", "t_out", "t_outf", "e_abs", "risk"]


def run_symbol(sym):
    t0 = time.time()
    base, btf = C.load_base(sym)
    if base is None: return []
    res = C.TF_MIN[btf]; fr = xgrid.frames(base, btf); atr_df = xgrid.daily_atr(base)
    entries = [e for e in ("M15", "M5", "M1") if e in fr and C.TF_MIN[e] >= res]
    cells = [(z, s, e) for z in ("D1", "H4", None) for s in ("H4", "H1", "M15") for e in entries
             if SG.TF_MIN[s] > SG.TF_MIN[e] and (z is None or SG.TF_MIN[z] > SG.TF_MIN[s])]
    need = sorted({tf for c in cells for tf in c if tf})
    comm = C.U.commission_of(sym); rows = []
    for mirror in (False, True):
        T = {tf: SG.TF(fr[tf], mirror, atr_df) for tf in need}
        G = C.Exits(base, mirror, res)
        ctx_cache, setup_cache = {}, {}
        for z, s, e in cells:
            for tgt_idm in (True, False):
                rows += [(z or "none", s, e, "IDM" if tgt_idm else "2R", -1 if mirror else 1) + r
                         for r in run_cell(T, z, s, e, tgt_idm, ctx_cache, setup_cache, G, comm)]
        del T, G
    X = pd.DataFrame(rows, columns=COLS); del rows
    X["t"] = pd.to_datetime(X.t.values)
    X["swapR"] = C.swap_R(sym, X.side.values, X.e_abs.values, X.risk.values, X.t_in.values, X.t_out.values)
    X["R"] = X.R0 - X.swapR
    X["R_coin"] = X.Rf0 - C.swap_R(sym, -X.side.values, X.e_abs.values, X.risk.values, X.t_in.values, X.t_outf.values)
    out = []
    for z, s, e in cells:
        for tg in ("IDM", "2R"):
            x = X[(X.zone == (z or "none")) & (X.structure == s) & (X.entry == e) & (X.target == tg)]
            r = C.cell_stats(x, idea="#22 SMC grid", sym=sym, group=C.U.group_of(sym), tf=e, cell=f"{z or 'none'}/{s}/{e}/{tg}",
                             zone=z or "none", structure=s, entry=e, target=tg, exit_bars=btf, primary=False)
            if len(x): r.update(swap=x.swapR.mean(), rr_med=x.rr.median(), stop_pct=x.risk_pct.median())
            out.append(r)
    keep = X[["zone", "structure", "entry", "target", "side", "t", "R", "R_coin", "rr", "risk_pct"]].copy()
    for c in ("R", "R_coin", "rr", "risk_pct"): keep[c] = keep[c].astype("float32")
    keep.to_pickle(os.path.join(TRD, f"{sym}.pkl"))
    C.append_csv(out, OUT)
    print(f"{sym:12s} base {btf} {base.index[0].date()}..{base.index[-1].date()} trades {len(X):6d} cells {len(out)} ({time.time() - t0:.0f}s)",
          flush=True)
    for r in out:
        if r["n"] >= 10:
            print(f"   {r['cell']:22s} n={r['n']:5d} mean={r['mean']:+.3f} t={r['t']:+.1f} win={r['win']:.0%} coin={r['coin']:+.3f} "
                  f"<24 {r['mean_is']:+.3f} 24+ {r['mean_oos']:+.3f} worst {r['worst_year']:+.2f}{'  << CANDIDATE' if r['candidate'] else ''}", flush=True)
        else:
            print(f"   {r['cell']:22s} n={r['n']}", flush=True)
    return out


if __name__ == "__main__":
    syms = sys.argv[1:] or (FIRST + C.FOREX)
    t0 = time.time()
    for s in syms:
        try: run_symbol(s)
        except Exception as ex: print(f"{s}: ERROR {ex!r}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)
