"""Log #82 data checks: CFTC code -> FTMO symbol mapping (names over time, continuity 2006-2026, price coverage), the release
schedule, and the cross-check of the MT5 calendar's gold / crude oil non-commercial net against the Disaggregated report.
python3 -I bt/q82_cot_checks.py"""
import os, sys
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
import numpy as np
import pandas as pd
import universe as U            # noqa: E402
import q82_cot_data as Q        # noqa: E402

RES = "/home/claude/ywo-lab/results"


def main():
    cat = U.catalog(); S = Q.release_schedule(); rows = []
    for code, sym in Q.DISAGG_MAP.items():
        r = Q.market_report(code)
        names = r.groupby("name").apply(lambda x: f"{x.index.min().date()}..{x.index.max().date()} {x.name}", include_groups=False)
        gaps = np.diff(r.index.values).astype("timedelta64[D]").astype(int)
        lo = Q.net_position(r, "comm"); oi = r.oi
        d = U.load(sym, "D1", cat)
        tot_l = r[[c for g in Q.DISAGG_GROUPS.values() for c in g[0]]].sum(axis=1)
        rows.append(dict(code=code, symbol=sym, group=Q.MARKET_GROUP[sym], reports=len(r), first=str(r.index.min().date()),
                         last=str(r.index.max().date()), max_gap_days=int(gaps.max()), gaps_over_8d=int((gaps > 8).sum()),
                         names=" | ".join(names.values), max_weekly_oi_change=float(np.abs(oi.pct_change()).max()),
                         comm_net_min=float(lo.min()), comm_net_max=float(lo.max()),
                         ftmo_d1_first=str(d.index.min().date()) if d is not None else "", ftmo_d1_last=str(d.index.max().date()) if d is not None else ""))
    M = pd.DataFrame(rows)
    M.to_csv(os.path.join(RES, "q82_cot_mapping.csv"), index=False, float_format="%.4g")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140)
    print(M.drop(columns=["names"]).to_string(index=False))
    for _, x in M.iterrows(): print(f"  {x.symbol}: {x.names}")
    # calendar cross-check
    X = []
    for code, key in (("088691", "Gold"), ("067651", "Crude Oil")):
        cal = Q.calendar_series(key); m = Q._match_calendar(code, key)
        rep = Q.market_report(code); v = Q.net_position(rep, "large") / 1000.0
        # naive alignment: latest as-of <= release date - 3 days
        k = np.searchsorted(v.index.values, (cal.index.normalize() - pd.Timedelta(days=3)).values, side="right") - 1
        naive = v.values[k]; diff = cal.values - naive
        mm = pd.DataFrame({"rel": m.values, "asof": m.index})
        mm["cal"] = cal.reindex(pd.DatetimeIndex(mm.rel)).values; mm["dis"] = v.reindex(mm["asof"]).values
        X.append(dict(series=key, releases=len(cal), first=str(cal.index.min().date()), last=str(cal.index.max().date()),
                      matched_by_value=len(m), max_abs_diff_matched=float((mm.cal - mm.dis).abs().max()),
                      naive_exact_share=float((np.abs(diff) <= 0.051).mean()), naive_corr_levels=float(np.corrcoef(cal.values, naive)[0, 1]),
                      naive_corr_changes=float(np.corrcoef(np.diff(cal.values), np.diff(naive))[0, 1])))
    X = pd.DataFrame(X); X.to_csv(os.path.join(RES, "q82_cot_xcheck.csv"), index=False, float_format="%.4g")
    print(X.to_string(index=False))
    S2 = S.reset_index(); S2.to_csv(os.path.join(RES, "q82_cot_schedule.csv"), index=False)
    print("schedule:", S.source.value_counts().to_dict(), "skipped", int(S.skip.sum()),
          S[S.skip].groupby(S[S.skip].index.year).size().to_dict())
    for key in ("S&P 500", "Nasdaq 100"):
        A = Q.calendar_release_asof(key)
        print(f"{key}: releases {len(A)} {A.index.min().date()}..{A.index.max().date()}, skipped {int(A.skip.sum())}, "
              f"min {A.value.min():.1f}k max {A.value.max():.1f}k")


if __name__ == "__main__":
    main()
