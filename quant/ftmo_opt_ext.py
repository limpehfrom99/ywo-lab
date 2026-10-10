"""Log #77 extension: the #77 pick sat on the edge of its grid (GF 0.75%, NB 0.5% = the largest values tried), so the grid is
extended outward: OC 0 / 0.25 / 0.5% x GF 0.75 / 1.0 / 1.25 / 1.5% per region-day x NB 0.5 / 0.75 / 1.0%. Same streams, sims and
choice rule as quant/ftmo_opt.py.  python3 quant/ftmo_opt_ext.py [n_paths] -> results/ftmo_opt_ext.csv"""
import os, sys, time, itertools, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ftmo_opt as F
import universe as U
from news import load_calendar, fed_days


def main():
    n_paths = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    t0 = time.time(); cat = U.catalog(); fed = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
    st = {"OC_TSLA": F.oc_stream("TSLA", cat, fed), "OC_US100": F.oc_stream("US100.cash", cat, fed)}
    gf = F.gf_streams(cat); st["GF_EU"], st["GF_US"] = gf["EU"], gf["US"]; st["NB_US100"] = F.nb_stream(cat)
    cal = pd.bdate_range(F.START, max(T.day.max() for T in st.values()))
    st = {k: T[T.day >= F.START].reset_index(drop=True) for k, T in st.items()}
    out = []
    for firm, FF in F.FIRMS.items():
        for oc, gfr, nbr in itertools.product((0.0, 0.0025, 0.005), (0.0075, 0.01, 0.0125, 0.015), (0.005, 0.0075, 0.01)):
            risk = {"OC_TSLA": oc, "OC_US100": oc, "GF_EU": gfr, "GF_US": gfr, "NB_US100": nbr}
            for keep, lab in ((1.0, "full"), (0.5, "half"), (0.0, "zero")):
                ret = F.daily(st, risk, keep, FF["lev"], cal)
                c = F.challenge(ret.values, FF["targets"], FF["min_days"], n=n_paths)
                row = dict(firm=firm, oc=oc, gf=gfr, nb=nbr, edge=lab, **c)
                if keep > 0:
                    s, pay = F.funded(ret.values, n=1500); eq = (1 + ret).cumprod()
                    row.update(keep12m=s, payout_10k=pay * 10000, hist_maxDD=(eq / eq.cummax() - 1).min(), worst_day=ret.min())
                out.append(row)
        print(f"{firm} done ({time.time() - t0:.0f}s)", flush=True)
    O = pd.DataFrame(out); O.to_csv(os.path.join(HERE, "..", "results", "ftmo_opt_ext.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 250)
    for firm in F.FIRMS:
        H = O[(O.firm == firm) & (O.edge == "half")]; okH = H[H.fail <= 0.25]
        print(f"\n{firm}: top 6 at HALF edge by pass within 6 months with fail <= 25% (extended grid):")
        print(okH.sort_values("pass_6m", ascending=False).head(6)[["oc", "gf", "nb", "pass_3m", "pass_6m", "pass_12m", "fail", "median_months", "keep12m", "payout_10k", "hist_maxDD", "worst_day"]].round(3).to_string(index=False))
        if len(okH):
            p = okH.loc[okH.pass_6m.idxmax()]
            print(O[(O.firm == firm) & (O.oc == p.oc) & (O.gf == p.gf) & (O.nb == p.nb)][["edge", "pass_3m", "pass_6m", "pass_12m", "fail", "median_months", "keep12m", "payout_10k"]].round(3).to_string(index=False))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
