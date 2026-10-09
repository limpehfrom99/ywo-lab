"""Aggregate a run_many(out_dir=...) result one symbol at a time (the whole trade set can exceed memory).
python3 xagg.py <dir> <out_prefix> -> <out_prefix>_cells.csv, <out_prefix>_summary.csv (per rule, by tf, by group)."""
import sys, glob, os, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
import xgrid as XG
d, out = sys.argv[1], sys.argv[2]
cells = []; acc = {}
def add(key, R):
    a = acc.setdefault(key, [0, 0.0, 0.0, 0]); a[0] += len(R); a[1] += R.sum(); a[2] += (R ** 2).sum(); a[3] += (R > 0).sum()
for f in sorted(glob.glob(os.path.join(d, "*.pkl"))):
    T = pd.read_pickle(f)
    for c in ("rule", "asset", "group", "tf", "tag"): T[c] = T[c].astype(str)
    T["R"] = T.R.astype(float); T["R_coin"] = T.R_coin.astype(float)
    for (n, a, tf), x in T.groupby(["rule", "asset", "tf"], sort=False):
        cells.append(XG.cell_stats(n, a, x.group.iloc[0], tf, x))
    for (n, tf, g), x in T.groupby(["rule", "tf", "group"], sort=False):
        R = x.R.values; add((n, "ALL", "ALL"), R); add((n, tf, "ALL"), R); add((n, "ALL", g), R); add((n, tf, g), R)
        IS = (x.t < "2024-01-01").values; add((n, "IS", "ALL"), R[IS]); add((n, "OOS", "ALL"), R[~IS])
    print(os.path.basename(f), len(T), flush=True)
C = pd.DataFrame(cells); C.to_csv(out + "_cells.csv", index=False)
rows = []
for (n, tf, g), (k, s, s2, pos) in acc.items():
    m = s / k if k else np.nan; sd = np.sqrt(max(s2 / k - m * m, 0)) * np.sqrt(k / max(k - 1, 1)) if k > 1 else np.nan
    rows.append(dict(rule=n, tf=tf, group=g, n=k, avgR=m, t=m / sd * np.sqrt(k) if sd and sd > 0 else np.nan, win=pos / k if k else np.nan))
S = pd.DataFrame(rows); S.to_csv(out + "_summary.csv", index=False)
cc = C.dropna(subset=["avgR"])
per = cc.groupby("rule").agg(cells=("avgR", "size"), pos=("avgR", lambda v: (v > 0).mean()), median_cell=("avgR", "median"),
                             passing=("candidate", "sum"))
per["by_luck"] = (0.025 * per.cells).round(1)
tot = S[(S.tf == "ALL") & (S.group == "ALL")].set_index("rule")[["n", "avgR", "t"]]
print(per.join(tot).round(3).sort_values("avgR", ascending=False).to_string())
