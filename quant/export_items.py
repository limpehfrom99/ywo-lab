"""Export backlog items on every stock and index of the full FTMO export (log #69), pre-registered in research/backlog.md:
  #46  opening candle (OC30) on big-gap days (|gap| >= 0.5 ATR): first candle AGAINST the gap vs WITH it.
       Becomes an EA filter only if against - with >= +0.10R pooled AND in both halves (before 2024 / from 2024) AND on >= 60%
       of symbols.
  #48/#49  NR7 days (yesterday's cash-session range the smallest of the last 7): OC30 and ORB30 on NR7 days vs other days.
       NR7 - other >= +0.05R on >= 60% of symbols AND from 2024 -> the NR7 candidate stands; for the live OC a size-up rule only
       if NR7 - other >= +0.05R on both TSLA and US100 (and FTMO odds improve).
Same engine and fills as the battery (quant/intraday.py on quant/sessions.py matrices), FTMO costs, stock clocks fixed.
python3 quant/export_items.py -> results/export_items_cells.csv, results/export_items_trades.pkl"""
import os, sys, time, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import universe as U, intraday as ID
from sessions import Session

CUT = pd.Timestamp("2024-01-01")


def trades_for(S, comm, rule):
    sp = ID.opening_candle(S, minutes=30) if rule == "OC30" else ID.orb(S, minutes=30)
    if sp is None: return None
    R, why, rf = ID.simulate(S, sp["e_col"], sp["e_px"], sp["d"], sp["stop"], None, None, comm, 1.2, sp["breakout"])
    rng = S.high - S.low
    nr7 = np.r_[False, [rng[i - 1] <= np.nanmin(rng[max(0, i - 7):i]) if i >= 7 else False for i in range(1, len(rng))]]
    gap = (S.open - S.prev_close) / S.atr
    m = np.isfinite(R)
    return pd.DataFrame({"day": S.days[m], "d": sp["d"][m], "R": R[m], "gap_atr": gap[m], "nr7": nr7[m]})


def stats(x):
    if len(x) < 5: return dict(n=len(x))
    t = x.R.mean() / x.R.std(ddof=1) * np.sqrt(len(x)) if x.R.std() > 0 else np.nan
    return dict(n=len(x), avgR=x.R.mean(), t=t, is_=x.R[x.day < CUT].mean(), oos=x.R[x.day >= CUT].mean())


def main():
    cat = U.catalog(); rows = []; allt = []; t0 = time.time()
    syms = sorted({s for s, _ in cat if U.group_of(s) in ("stock", "us_index", "index")})
    for sym in syms:
        tf = "M5" if (sym, "M5") in cat else None
        if tf is None: continue
        d = U.load(sym, tf, cat); d = d[~d.index.duplicated()].sort_index()
        if "tickvol" not in d: d["tickvol"] = 1.0
        for sess in U.sessions_of(sym)[:1]:                      # the symbol's own cash session
            try: S = Session(d, sess)
            except Exception as e: print(sym, "session error", e); continue
            if len(S.days) < 150: continue
            for rule in ("OC30", "ORB30"):
                T = trades_for(S, U.commission_of(sym), rule)
                if T is None or not len(T): continue
                T = T.assign(symbol=sym, group=U.group_of(sym), rule=rule); allt.append(T)
                big = T[np.abs(T.gap_atr) >= 0.5]
                against = big[np.sign(big.gap_atr) == -big.d]; withg = big[np.sign(big.gap_atr) == big.d]
                r = dict(symbol=sym, group=U.group_of(sym), rule=rule, days=len(S.days), first=S.days[0].date())
                for lab, x in (("all", T), ("nr7", T[T.nr7]), ("other", T[~T.nr7]), ("gap_against", against), ("gap_with", withg)):
                    for k, v in stats(x).items(): r[f"{lab}_{k}"] = v
                rows.append(r)
        print(f"{sym}: {len(S.days) if 'S' in dir() else 0} days ({time.time() - t0:.0f}s)", flush=True)
    C = pd.DataFrame(rows); T = pd.concat(allt, ignore_index=True)
    os.makedirs(os.path.join(HERE, "..", "results"), exist_ok=True)
    C.to_csv(os.path.join(HERE, "..", "results", "export_items_cells.csv"), index=False, float_format="%.4f")
    T.to_pickle(os.path.join(HERE, "..", "results", "export_items_trades.pkl"))
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    for rule in ("OC30", "ORB30"):
        x = C[C.rule == rule]; t = T[T.rule == rule]
        print(f"\n===== {rule}: {len(x)} symbols")
        # NR7
        dn = (x.nr7_avgR - x.other_avgR).dropna()
        tn, to = t[t.nr7], t[~t.nr7]
        print(f"NR7 vs other days: pooled NR7 {tn.R.mean():+.3f} (n {len(tn)}) vs other {to.R.mean():+.3f} (n {len(to)}); "
              f"diff {tn.R.mean() - to.R.mean():+.3f}; before 2024 {tn.R[tn.day < CUT].mean() - to.R[to.day < CUT].mean():+.3f}, "
              f"from 2024 {tn.R[tn.day >= CUT].mean() - to.R[to.day >= CUT].mean():+.3f}; symbols with diff >= +0.05: "
              f"{(dn >= 0.05).mean():.0%} of {len(dn)}")
        # gap
        big = t[np.abs(t.gap_atr) >= 0.5]; ag = big[np.sign(big.gap_atr) == -big.d]; wg = big[np.sign(big.gap_atr) == big.d]
        dg = (x.gap_against_avgR - x.gap_with_avgR).dropna()
        print(f"Big gap days: against {ag.R.mean():+.3f} (n {len(ag)}) vs with {wg.R.mean():+.3f} (n {len(wg)}); diff "
              f"{ag.R.mean() - wg.R.mean():+.3f}; before 2024 {ag.R[ag.day < CUT].mean() - wg.R[wg.day < CUT].mean():+.3f}, from 2024 "
              f"{ag.R[ag.day >= CUT].mean() - wg.R[wg.day >= CUT].mean():+.3f}; symbols with diff > 0: {(dg > 0).mean():.0%} of {len(dg)}")
        for g, y in t.groupby("group"):
            b = y[np.abs(y.gap_atr) >= 0.5]; a_ = b[np.sign(b.gap_atr) == -b.d]; w_ = b[np.sign(b.gap_atr) == b.d]
            print(f"   {g:9s} all {y.R.mean():+.3f} (n {len(y)}) | NR7 {y.R[y.nr7].mean():+.3f} other {y.R[~y.nr7].mean():+.3f} | "
                  f"gap against {a_.R.mean():+.3f} with {w_.R.mean():+.3f}")
        cols = ["symbol", "all_n", "all_avgR", "all_t", "all_is_", "all_oos", "nr7_n", "nr7_avgR", "other_avgR", "gap_against_n",
                "gap_against_avgR", "gap_with_n", "gap_with_avgR"]
        print(x[[c for c in cols if c in x]].round(3).to_string(index=False))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
