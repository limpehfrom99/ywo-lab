"""q75 port of #38 rules A, B, C (bt/breakout_retest.py) to the FTMO export — backlog #43, log #75.

Rules A and B are the original functions (breakout_retest.rule_a / rule_b, imported, not copied); only the module's exit_trade is
replaced at run time by one that exits on the export's finest bars and charges FTMO costs (q75_ports_common docstring). Rule C does
its own exit inline, so it is copied below with only the exit/cost lines changed. Cells as in the script: A follow-through on/off x
2R / prior-high target, B HTF filter on/off, C; on M5 / M15 / H1 (the script's) and H4 (added; B's HTF for H4 = D1, also added).
Symbols: US500.cash and US100.cash first (primary: A and B on M5/M15/H1), then every index, the metals and the 28 forex pairs.
Usage: python3 bt/q75_ports_br.py [SYMBOL ...]   (per-symbol cell rows appended to results/q75_ports_br_cells.csv)."""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q75_ports_common as C                              # noqa: E402  (sets sys.path for the originals)
import breakout_retest as BR                              # noqa: E402
from smc_grid import TF                                   # noqa: E402
import xgrid                                              # noqa: E402

BR.HTF["H4"] = "D1"
OUT = os.path.join(C.RES, "q75_ports_br_cells.csv")
TRD = os.path.join(C.SCR, "br"); os.makedirs(TRD, exist_ok=True)
PRIMARY = ("US500.cash", "US100.cash")


def make_exit(res):
    """Replacement for breakout_retest.exit_trade (same signature). Returns (R, R_coin, rr, R_naive, t_in, t_out, t_out_coin,
    |e|, risk) before swap; R_naive = the original fill-bar resolution on coarse exit bars (for reference only)."""
    coarse = res > 1; mb = 5 * 1440 // res

    def exit_trade(G, t_from, e, stop, tgt, sp, fill_level=None, bar_ns=None):
        t0 = int(t_from.astype(np.int64)); N = len(G.ti)
        i0 = int(np.searchsorted(G.ti, t0))
        if i0 >= N: return None
        if fill_level is not None:                                   # limit order: first exit bar inside the bar that reaches it
            i_end = int(np.searchsorted(G.ti, t0 + int(bar_ns)))
            w = np.flatnonzero(G.l[i0:i_end] <= fill_level); i0 = i0 + (int(w[0]) if len(w) else 0)
        i1 = min(i0 + mb, N)
        if i1 <= i0: return None
        risk = e - stop
        X, xi = C.exit_idx(G.h, G.l, G.c, i0, i1, stop, tgt, 1)
        Xf, fi = C.exit_idx(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1)
        Xn = X
        if coarse and fill_level is not None:                        # PROTOCOL: stop counts in the fill bar, target does not
            if G.l[i0] <= stop: X, xi = stop, i0
            elif i0 + 1 < i1: X, xi = C.exit_idx(G.h, G.l, G.c, i0 + 1, i1, stop, tgt, 1)
            else: X, xi = G.c[i0], i0
            if i0 + 1 < i1: Xf, fi = C.exit_idx(G.h, G.l, G.c, i0 + 1, i1, e + risk, e - (tgt - e), -1)
            else: Xf, fi = G.c[i0], i0
        cost = sp + G.comm * (abs(e) + abs(X)); cost_f = sp + G.comm * (abs(e) + abs(Xf)); cost_n = sp + G.comm * (abs(e) + abs(Xn))
        return ((X - e - cost) / risk, (e - Xf - cost_f) / risk, (tgt - e) / risk, (Xn - e - cost_n) / risk,
                G.ti[i0], G.ti[xi], G.ti[fi], abs(e), risk)
    return exit_trade


def rule_c(T, tf, lev):
    """breakout_retest.rule_c; only the exit/cost lines differ (export exit bars, scaled time limit, spread x 1.2 + commission)."""
    S, G = T[tf], T["M1"]; N = len(S.c); rows = []; ns = C.TF_MIN[tf] * C.NS; done = set(); mb = 5 * 1440 // G.res
    for i in range(21, N - 1):
        L = lev[i]
        if not np.isfinite(L) or L in done or not np.isfinite(S.atr[i]): continue
        if S.h[i] > L and S.c[i] < L:
            done.add(L)
            stop = S.h[i] + 0.05 * S.atr[i]
            i0 = int(np.searchsorted(G.ti, int(S.t[i].astype(np.int64)) + ns))
            if i0 >= len(G.ti) - 1: continue
            e = G.o[i0]; risk = stop - e
            if risk <= 0: continue
            tgt = e - 2 * risk; i1 = min(i0 + mb, len(G.ti))
            X, xi = C.exit_idx(G.h, G.l, G.c, i0, i1, stop, tgt, -1); cost = S.sp[i] + G.comm * (abs(e) + abs(X))
            Xf, fi = C.exit_idx(G.h, G.l, G.c, i0, i1, e - risk, e + 2 * risk, 1); cost_f = S.sp[i] + G.comm * (abs(e) + abs(Xf))
            R = (e - X - cost) / risk
            rows.append((G.t[i0], R, (Xf - e - cost_f) / risk, 2.0, R, G.ti[i0], G.ti[xi], G.ti[fi], abs(e), risk))
        elif S.c[i] > L: done.add(L)
    return rows


COLS = ["cell", "tf", "side", "t", "R0", "Rf0", "rr", "Rn0", "t_in", "t_out", "t_outf", "e_abs", "risk"]


def run_symbol(sym):
    t0 = time.time()
    base, btf = C.load_base(sym)
    if base is None: return []
    res = C.TF_MIN[btf]
    fr = xgrid.frames(base, btf); atr_df = xgrid.daily_atr(base)
    tfs = [tf for tf in ("M5", "M15", "H1", "H4") if tf in fr and C.TF_MIN[tf] >= res and len(fr[tf]) >= 200]
    need = sorted(set(tfs) | {BR.HTF[tf] for tf in tfs})
    BR.exit_trade = make_exit(res)
    rows = []
    for m in (False, True):
        T = {tf: TF(fr[tf], m, atr_df) for tf in need}
        G = C.Exits(base, m, res); G.comm = C.U.commission_of(sym); T["M1"] = G
        sgn = -1 if m else 1
        for tf in tfs:
            S = T[tf]; last, prev = BR.swing_state(S); lev = BR.eq_levels(S, last, prev); big = BR.big_candles(S)
            for ft in (False, True):
                for tg in ("2R", "HIGH"):
                    rows += [(f"A {'FT' if ft else 'noFT'} {tg}", tf, sgn) + r for r in BR.rule_a(T, tf, ft, tg, lev, big)]
            for h in (False, True):
                rows += [(f"B {'HTF' if h else 'noHTF'} 2R", tf, sgn) + r for r in BR.rule_b(T, tf, h, big, last)]
            rows += [("C sweep-reverse 2R", tf, -sgn) + r for r in rule_c(T, tf, lev)]
        del T, G
    if not rows: return []
    X = pd.DataFrame(rows, columns=COLS); del rows
    X["t"] = pd.to_datetime(X.t.values)
    sw = C.swap_R(sym, X.side.values, X.e_abs.values, X.risk.values, X.t_in.values, X.t_out.values)
    swf = C.swap_R(sym, -X.side.values, X.e_abs.values, X.risk.values, X.t_in.values, X.t_outf.values)
    X["R"] = X.R0 - sw; X["R_coin"] = X.Rf0 - swf; X["R_naive"] = X.Rn0 - sw; X["swapR"] = sw
    grp = C.U.group_of(sym)
    cells = []
    for (cell, tf), x in X.groupby(["cell", "tf"], sort=False):
        r = C.cell_stats(x, idea="#43 breakout-retest", sym=sym, group=grp, tf=tf, cell=cell, exit_bars=btf,
                         primary=bool(sym in PRIMARY and tf in ("M5", "M15", "H1") and not cell.startswith("C")))
        r.update(naive=x.R_naive.mean(), swap=x.swapR.mean(), rr_med=x.rr.median())
        cells.append(r)
    keep = X[["cell", "tf", "side", "t", "R", "R_coin", "R_naive", "rr"]].copy()
    for c in ("R", "R_coin", "R_naive", "rr"): keep[c] = keep[c].astype("float32")
    keep.to_pickle(os.path.join(TRD, f"{sym}.pkl"))
    C.append_csv(cells, OUT)
    print(f"{sym:12s} base {btf} {base.index[0].date()}..{base.index[-1].date()} trades {len(X):7d} cells {len(cells)} "
          f"({time.time() - t0:.0f}s)", flush=True)
    for r in cells:
        if r["n"] >= 10:
            print(f"   {r['tf']:3s} {r['cell']:20s} n={r['n']:6d} mean={r['mean']:+.3f} t={r['t']:+.1f} win={r['win']:.0%} coin={r['coin']:+.3f} "
                  f"<24 {r['mean_is']:+.3f} 24+ {r['mean_oos']:+.3f} worst {r['worst_year']:+.2f}{'  << CANDIDATE' if r['candidate'] else ''}",
                  flush=True)
    return cells


if __name__ == "__main__":
    syms = sys.argv[1:] or (list(PRIMARY) + [s for s in C.INDICES if s not in PRIMARY] + C.METALS + C.FOREX)
    t0 = time.time()
    for s in syms:
        try: run_symbol(s)
        except Exception as ex: print(f"{s}: ERROR {ex!r}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)
