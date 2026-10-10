"""q75 ports — summary of the three ports (results/q75_ports_{br,va,smc}_cells.csv -> results/q75_ports_summary.csv + printout).
Per idea: cells, share positive, passing the CANDIDATE bar vs ~2.5% expected by luck, pooled R by asset group x timeframe (and by
rule variant), primary / confirm cells."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q75_ports_common as C                              # noqa: E402

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 40)
SHOW = ["sym", "tf", "cell", "n", "per_yr", "mean", "t", "win", "coin", "n_is", "mean_is", "n_oos", "mean_oos", "worst_year", "yrs_pos",
        "last60", "candidate"]


def load(name):
    p = os.path.join(C.RES, f"q75_ports_{name}_cells.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p)
    return d.drop_duplicates(subset=["sym", "tf", "cell"], keep="last").reset_index(drop=True)


def overview(C_, label):
    c = C_[C_.n >= 10]
    return dict(idea=label, cells=len(c), cells_n200=int((c.n >= 200).sum()), pos=(c["mean"] > 0).mean(),
                pooled=c.sumR.sum() / c.n.sum(), trades=int(c.n.sum()), passing=int(c.candidate.sum()), luck=round(0.025 * len(c), 1))


def main():
    out = []
    br, va, smc = load("br"), load("va"), load("smc")
    if br is not None:
        print("\n=== #43 breakout-retest (bt/breakout_retest.py rules A/B/C) ===")
        print(pd.DataFrame([overview(br, "#43 all cells"), overview(br[~br.cell.str.startswith("C")], "#43 rules A+B"),
                            overview(br[br.primary], "#43 primary (US100/US500 A+B M5/M15/H1)")]).round(3).to_string(index=False))
        print("\nprimary cells:"); print(br[br.primary][SHOW].round(3).to_string(index=False))
        g = C.pool(br, ["group", "tf"]); g.insert(0, "idea", "#43"); g.insert(1, "by", "group x tf"); out.append(g)
        print("\npooled by group x timeframe:"); print(g.round(3).to_string(index=False))
        br["rule"] = br.cell.str[0]
        g = C.pool(br, ["rule", "group"]); g.insert(0, "idea", "#43"); g.insert(1, "by", "rule x group"); out.append(g)
        print("\npooled by rule x group:"); print(g.round(3).to_string(index=False))
        g = C.pool(br, ["cell"]); g.insert(0, "idea", "#43"); g.insert(1, "by", "variant"); out.append(g)
        print("\npooled by variant:"); print(g.round(3).to_string(index=False))
        lim = br[br.exit_bars != "M1"]; lim = lim[~lim.cell.str.startswith("C")]
        print(f"\ncoarse exit bars (M5/M15), rules A+B: mean R conservative {np.average(lim['mean'], weights=lim.n):+.3f} vs original fill-bar "
              f"resolution {np.average(lim['naive'], weights=lim.n):+.3f} (trade-weighted)")
        print("\ncells passing the bar:"); print(br[br.candidate][SHOW].round(3).to_string(index=False))
        print("\nbest 12 cells by t (n >= 200):"); print(br[br.n >= 200].sort_values("t", ascending=False).head(12)[SHOW].round(3).to_string(index=False))
    if va is not None:
        print("\n=== #44 value-area (bt/value_area.py V1-V3) ===")
        main_ = va[~va.bridge]
        print(pd.DataFrame([overview(main_, "#44 all cells (5-min)")]).round(3).to_string(index=False))
        print("\nconfirm cell and its pair:")
        print(main_[(main_.sym.isin(["US100.cash", "US500.cash"])) & (main_.cell == "V3")][SHOW + ["years"]].round(3).to_string(index=False))
        print("\nUS100/US500 all cells incl. 30-min bridge:")
        print(va[va.sym.isin(["US100.cash", "US500.cash"])][SHOW + ["hit", "rr_med"]].round(3).to_string(index=False))
        print("\nall 5-min cells:"); print(main_[SHOW + ["hit"]].round(3).to_string(index=False))
        g = C.pool(main_, ["group", "tf"]); g.insert(0, "idea", "#44"); g.insert(1, "by", "group x session"); out.append(g)
        print("\npooled by group x session:"); print(g.round(3).to_string(index=False))
        g = C.pool(main_, ["cell", "tf"]); g.insert(0, "idea", "#44"); g.insert(1, "by", "rule x session"); out.append(g)
        print("\npooled by rule x session:"); print(g.round(3).to_string(index=False))
    if smc is not None:
        print("\n=== #22 SMC grid (bt/smc_grid.py) ===")
        print(pd.DataFrame([overview(smc, "#22 all cells"), overview(smc[smc.group == "us_index"], "#22 US indices"),
                            overview(smc[smc.group == "forex"], "#22 forex")]).round(3).to_string(index=False))
        g = C.pool(smc, ["group", "tf"]); g.insert(0, "idea", "#22"); g.insert(1, "by", "group x entry tf"); out.append(g)
        print("\npooled by group x entry timeframe:"); print(g.round(3).to_string(index=False))
        smc["nest"] = smc.zone + "/" + smc.structure + "/" + smc.target
        g = C.pool(smc, ["group", "nest"]); g.insert(0, "idea", "#22"); g.insert(1, "by", "group x zone/structure/target"); out.append(g)
        print("\npooled by group x nesting:"); print(g.round(3).to_string(index=False))
        print("\nUS index cells:"); print(smc[smc.group == "us_index"][SHOW].round(3).to_string(index=False))
        print("\ncells passing the bar:"); print(smc[smc.candidate][SHOW].round(3).to_string(index=False))
        print("\nbest 12 cells by t (n >= 200):"); print(smc[smc.n >= 200].sort_values("t", ascending=False).head(12)[SHOW].round(3).to_string(index=False))
    if out:
        pd.concat(out, ignore_index=True).to_csv(os.path.join(C.RES, "q75_ports_summary.csv"), index=False, float_format="%.5g")


if __name__ == "__main__":
    main()
