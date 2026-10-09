"""Walk-forward selection: the honest way to "optimise". Every year, choose settings using only the years before it, trade
them the next year, roll forward. Only the stitched forward results count — the same thing an EA re-optimised once a year
would have earned.

1. Per rule family (e.g. ORB = ORB15/ORB30/ORB60/ORB30_mid) and per symbol-session: each year pick the variant with the best
   average R over the previous LOOKBACK years (at least MIN_N trades; if the best is not positive, sit out the year), trade it.
   Compare with the plain average of all variants (no selection).
2. Hedge-fund style book: each year rank every cell (symbol x session x variant) by its trailing t-stat, take the top TOP cells
   with t >= 2, trade all of them the next year at equal risk. Stitched daily R -> Sharpe, avg R per trade, per-year.
python3 quant/walkforward.py   (reads the battery's trades pickle; writes results/battery_walkforward*.csv)
"""
import os, re, sys, pickle
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from universe import group_of  # noqa: E402
from portfolio import book_dates  # noqa: E402

RES = os.path.join(HERE, "..", "results")
LOOKBACK, MIN_N, TOP = 3, 30, 15


def family(rule):
    for pre in ("ASIA_BO", "IMOM", "GAP", "ORB", "OC", "FHR", "DON", "TSMOM", "RSI2", "MA", "HIGH52", "TOM", "XSMOM", "XSREV", "NB"):
        if rule.startswith(pre): return pre
    return re.sub(r"[\d_.]+.*$", "", rule) or rule


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def by_year(tr):
    return pd.DatetimeIndex(tr.day).year


def wf_family(trades):
    groups = {}
    for k in trades:
        groups.setdefault((k[0], k[1], k[2], family(k[3])), []).append(k)
    rows, picks = [], []
    for (kind, sym, sess, fam), ks in groups.items():
        yrs = sorted({y for k in ks for y in by_year(trades[k])})
        if len(yrs) < LOOKBACK + 1: continue
        fwd, allv = [], []
        for Y in yrs[LOOKBACK:]:
            best, best_s = None, -np.inf
            for k in ks:
                yy = by_year(trades[k]); past = trades[k].R.values[(yy >= Y - LOOKBACK) & (yy < Y)]
                if len(past) >= MIN_N and past.mean() > best_s: best, best_s = k, past.mean()
            for k in ks:
                cur = trades[k][by_year(trades[k]) == Y]
                allv.append(cur.R.values)                            # every variant traded (no selection)
                if k == best and best_s > 0:
                    fwd.append(cur.R.values); picks.append(dict(kind=kind, symbol=sym, session=sess, family=fam, year=Y, pick=k[3], past_avg=best_s))
        f = np.concatenate(fwd) if fwd else np.array([])
        a = np.concatenate(allv) if allv else np.array([])
        rows.append(dict(kind=kind, group=group_of(sym), symbol=sym, session=sess, family=fam, variants=len(ks),
                         fwd_n=len(f), fwd_avgR=f.mean() if len(f) else np.nan, fwd_t=tstat(f), mix_avgR=a.mean() if len(a) else np.nan))
    return pd.DataFrame(rows), pd.DataFrame(picks)


def wf_book(trades):
    keys = list(trades)
    yrs = sorted({y for k in keys for y in by_year(trades[k])})
    daily, chosen = [], []
    for Y in yrs[LOOKBACK:]:
        scores = []
        for k in keys:
            yy = by_year(trades[k]); past = trades[k].R.values[(yy >= Y - LOOKBACK) & (yy < Y)]
            if len(past) >= MIN_N:
                s = tstat(past)
                if np.isfinite(s) and s >= 2: scores.append((s, k))
        top = [k for s, k in sorted(scores, reverse=True)[:TOP]]
        for k in top:
            tr = trades[k]; m = by_year(tr) == Y
            if m.any():
                d = pd.Series(tr.R.values[m], index=book_dates(k, tr[m])).groupby(level=0).sum() / max(1, len(top))
                daily.append(d); chosen.append(dict(year=Y, cell="|".join(k[1:]), n=int(m.sum()), avgR=tr.R.values[m].mean()))
    if not daily: return None, pd.DataFrame(chosen)
    r = pd.concat(daily, axis=1, sort=True).sum(axis=1).sort_index()
    r = r.reindex(pd.bdate_range(r.index.min(), r.index.max())).fillna(0)
    return r, pd.DataFrame(chosen)


def main():
    trades = pickle.load(open("/home/claude/bt/battery_trades.pkl", "rb"))
    fam, picks = wf_family(trades)
    fam.to_csv(os.path.join(RES, "battery_walkforward.csv"), index=False, float_format="%.4f")
    picks.to_csv(os.path.join(RES, "battery_walkforward_picks.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print("Per family, per symbol-session: forward results of 'pick last 3 years' best variant' vs an equal mix of all variants")
    agg = fam.groupby(["kind", "family"]).agg(cells=("symbol", "size"), fwd_pos=("fwd_avgR", lambda s: np.mean(s > 0)),
                                              fwd_med=("fwd_avgR", "median"), mix_med=("mix_avgR", "median")).reset_index()
    print(agg.round(3).to_string(index=False))
    print("\nBest forward cells:\n" + fam.sort_values("fwd_t", ascending=False).head(15).round(3).to_string(index=False))
    r, chosen = wf_book(trades)
    if r is not None:
        sh = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
        yr = r.groupby(r.index.year).sum()
        print(f"\nHedge-fund book (top {TOP} cells by trailing {LOOKBACK}-year t-stat, re-picked every year): "
              f"Sharpe {sh:.2f}, avg R per day {r.mean():+.4f}, by year " + " ".join(f"{y % 100:02d}:{v:+.1f}R" for y, v in yr.items()))
        r.rename("R").to_csv(os.path.join(RES, "battery_walkforward_book.csv"))
        chosen.to_csv(os.path.join(RES, "battery_walkforward_book_cells.csv"), index=False, float_format="%.4f")
    else:
        print("\nHedge-fund book: no cell reached a trailing t-stat of 2 in any year")


if __name__ == "__main__":
    main()
