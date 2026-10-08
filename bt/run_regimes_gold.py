import pandas as pd, numpy as np, time, regimes, strategies_gold as S
b = pd.read_pickle("/home/claude/data/gold_m5.pkl"); labs = regimes.labels(b)
t0 = time.time(); fam = S.all_families(b); print("families done", round(time.time() - t0), flush=True)
rows = []
for name, tr in fam.items():
    if len(tr) < 100: continue
    m, _ = regimes.matrix(tr, labs)
    m.insert(0, "strategy", name); m.insert(1, "all: avg R", round(tr.R.mean(), 3)); m.insert(2, "all: n", len(tr)); rows.append(m)
res = pd.concat(rows); res.to_csv("/home/claude/bt/regimes_gold.csv", index=False); print("done", round(time.time() - t0))
