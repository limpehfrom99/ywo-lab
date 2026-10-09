"""Permutation tests for the live opening-candle rule (OC30) on FTMO's own export (log #63).

Per symbol: OC30 mean R vs 1,000 shuffles of that symbol's session bars (quant/permute.permute_session).
Selection bias (Masters ch. 7 / Strix): TSLA and US100 were picked as the best of a small set of markets. Each shuffle reruns
OC30 on every symbol of a universe and keeps the BEST t-statistic; the real best must beat the shuffled bests.
  universe A = the markets the opening candle was first tested on: TSLA, US100, US500, AAPL, gold (us_cash session)
  universe B = every US stock and US index in the export (34)
Also: the live pair (TSLA + US100 pooled) vs the same pair on shuffles.
python3 quant/mcpt_oc.py [n_perm] -> results/mcpt_oc.csv"""
import os, sys, time, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import universe as U, intraday as ID, permute as P
from sessions import Session


def oc_R(S, comm):
    sp = ID.opening_candle(S, minutes=30)
    R = ID.simulate(S, sp["e_col"], sp["e_px"], sp["d"], sp["stop"], None, None, comm, 1.2, False)[0]
    return R[np.isfinite(R)]


def tstat(R): return R.mean() / R.std(ddof=1) * np.sqrt(len(R)) if len(R) > 2 and R.std() > 0 else np.nan


def main():
    n_perm = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    cat = U.catalog(); t0 = time.time()
    syms = sorted({s for s, _ in cat if U.group_of(s) in ("stock", "us_index")}) + ["XAUUSD"]
    A = ["TSLA", "US100.cash", "US500.cash", "AAPL", "XAUUSD"]
    SS = {}
    for s in syms:
        d = U.load(s, "M5", cat); d = d[~d.index.duplicated()].sort_index()
        if "tickvol" not in d: d["tickvol"] = 1.0
        S = Session(d, "us_cash")
        if len(S.days) >= 300: SS[s] = (S, U.commission_of(s))
    B = [s for s in SS if s != "XAUUSD"]
    real = {s: oc_R(S, c) for s, (S, c) in SS.items()}
    rt = {s: tstat(r) for s, r in real.items()}; ra = {s: r.mean() for s, r in real.items()}
    pair_real = np.r_[real["TSLA"], real["US100.cash"]].mean()
    print(f"{len(SS)} symbols loaded ({time.time() - t0:.0f}s); real best t in A: {max(rt[s] for s in A):.2f}, in B: "
          f"{max(rt[s] for s in B):.2f}; live pair avg R {pair_real:+.3f}", flush=True)
    rng = np.random.default_rng(2026)
    perm_t = {s: [] for s in SS}; perm_a = {s: [] for s in SS}; bestA, bestB, pair = [], [], []
    for k in range(n_perm):
        Rk = {}
        for s, (S, c) in SS.items():
            r = oc_R(P.permute_session(S, rng), c); Rk[s] = r
            perm_t[s].append(tstat(r)); perm_a[s].append(r.mean())
        bestA.append(np.nanmax([perm_t[s][-1] for s in A])); bestB.append(np.nanmax([perm_t[s][-1] for s in B]))
        pair.append(np.r_[Rk["TSLA"], Rk["US100.cash"]].mean())
        if (k + 1) % 100 == 0: print(f"  {k + 1} shuffles ({time.time() - t0:.0f}s)", flush=True)
    rows = []
    for s in SS:
        rows.append(dict(symbol=s, n=len(real[s]), avgR=ra[s], t=rt[s], perm_mean=np.nanmean(perm_a[s]),
                         p_symbol=P.pvalue(ra[s], perm_a[s]), in_A=s in A))
    D = pd.DataFrame(rows).sort_values("t", ascending=False)
    D.to_csv(os.path.join(HERE, "..", "results", "mcpt_oc.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 200); pd.set_option("display.max_rows", 100)
    print(D.round(3).to_string(index=False))
    bA = max(rt[s] for s in A); bB = max(rt[s] for s in B)
    print(f"\nSelection-bias test, best t of universe A (5 markets): real {bA:.2f} ({max(A, key=lambda s: rt[s])}); shuffled bests "
          f"median {np.median(bestA):.2f}, 95th {np.percentile(bestA, 95):.2f}, 99th {np.percentile(bestA, 99):.2f}; p = {P.pvalue(bA, bestA):.3f}")
    print(f"Selection-bias test, best t of universe B ({len(B)} US stocks + indices): real {bB:.2f} ({max(B, key=lambda s: rt[s])}); "
          f"shuffled bests median {np.median(bestB):.2f}, 95th {np.percentile(bestB, 95):.2f}, 99th {np.percentile(bestB, 99):.2f}; "
          f"p = {P.pvalue(bB, bestB):.3f}")
    print(f"Live pair TSLA + US100 pooled: real {pair_real:+.3f}; shuffled mean {np.mean(pair):+.3f}, 95th {np.percentile(pair, 95):+.3f}, "
          f"99th {np.percentile(pair, 99):+.3f}; p = {P.pvalue(pair_real, pair):.3f} (not selection-corrected)")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
