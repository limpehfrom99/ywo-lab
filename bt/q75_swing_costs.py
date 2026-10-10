"""Log #75 swing ideas — where the D1 trend results go: per group, the real trades' R split into gross move, spread + commission
and swaps (today's swap sheet, as charged in q75_swing_trend.py). Same data, segments and rules as q75_swing_trend.py (D1 only).
Output: results/q75_swing_costs_d1.csv (group x cell: n, net R, gross R, spread+commission R, swap R, median hold in days).
"""
import sys, os, time
import numpy as np, pandas as pd

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
import q75_swing_trend as TR  # noqa: E402
U = C.U


def main():
    cat = U.catalog(); t0 = time.time(); acc = {}
    jobs = [("clenow_3atr", "sig_clenow", 100, 4, 3.0, 0, 3.0)] + \
           [(f"N{N}_{name}", f"sig{N}", 60, kind, k, tm, 2.0) for N in (20, 55) for name, kind, k, tm in TR.GRID_EXITS]
    for sym in C.symbols(cat):
        grp = U.group_of(sym); comm = U.commission_of(sym)
        intra, btf, rel = C.load_intraday(sym, cat)
        d1 = C.load_d1(sym, cat, intra, rel); del intra
        if d1 is None or len(d1) < 300: continue
        sw = C.Swaps(sym, C.ns(d1.index)[0], C.ns(d1.index)[-1], d1.close.iloc[-1])
        for sa, sb in C.segments(C.ns(d1.index)):
            if sb - sa < 200: continue
            xs = d1.iloc[sa:sb]; I = TR.indicators(xs); t = C.ns(xs.index); sp = xs.sp.values.astype(float)
            for cell, sig, start, kind, k, tm, runit in jobs:
                S_i, E_i, X_i, D, EP, XP, AT, HW = TR.run_rule(I["o"], I["h"], I["l"], I["c"], I[sig], I["atr"], I["ll10"], I["hh10"],
                                                               I["sma50"], start, kind, k, tm)
                if len(E_i) == 0: continue
                risk = runit * AT
                gross = D * (XP - EP) / risk
                sc = (1.2 * sp[E_i] + comm * (np.abs(EP) + np.abs(XP))) / risk
                swp = sw.nights(t[E_i], t[X_i]) * sw.per_night(D, EP) / risk
                a = acc.setdefault((grp, cell), dict(n=0, net=0.0, gross=0.0, spread_comm=0.0, swap=0.0, holds=[], nights=0.0))
                a["n"] += len(E_i); a["gross"] += gross.sum(); a["spread_comm"] += sc.sum(); a["swap"] += swp.sum()
                a["net"] += (gross - sc - swp).sum(); a["holds"] += list(X_i - E_i); a["nights"] += sw.nights(t[E_i], t[X_i]).sum()
        print(f"{sym} {time.time() - t0:.0f}s", flush=True)
    rows = []
    for (g, cell), a in sorted(acc.items()):
        n = a["n"]
        rows.append(dict(group=g, cell=cell, n=n, net=a["net"] / n, gross=a["gross"] / n, spread_comm=-a["spread_comm"] / n,
                         swap=-a["swap"] / n, hold_med_days=float(np.median(a["holds"])), nights_mean=a["nights"] / n))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(C.RES, "q75_swing_costs_d1.csv"), index=False, float_format="%.4g")
    pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
    print(out.round(3).to_string(index=False))
    tot = out.assign(w=out.n).groupby("cell").apply(lambda x: pd.Series({k: np.average(x[k], weights=x.w) for k in ("net", "gross", "spread_comm", "swap")}
                                                                  | {"n": x.n.sum()}), include_groups=False)
    print("\nall groups, per cell:\n" + tot.round(3).to_string())
    ex = out[out.group != "crypto"].assign(w=lambda x: x.n).groupby("cell").apply(
        lambda x: pd.Series({k: np.average(x[k], weights=x.w) for k in ("net", "gross", "spread_comm", "swap")} | {"n": x.n.sum()}), include_groups=False)
    print("\nex crypto, per cell:\n" + ex.round(3).to_string())


if __name__ == "__main__":
    main()
