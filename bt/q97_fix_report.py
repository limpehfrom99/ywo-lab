"""Log #97 report: R1 London fix cells from bt/xrun.py (tag r1fix). Primary = 1A thr 0.10 on the 7 USD majors, day-clustered t."""
import glob, sys, numpy as np, pandas as pd
f = sorted(glob.glob("/home/claude/bt/xgrid_results/*_r1fix_trades.pkl"))[-1]
T = pd.read_pickle(f); T["R"] = T.R.astype(float); T["R_coin"] = T.R_coin.astype(float)
MAJ = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
def tday(x, col="R"):
    d = x.groupby(x.t.dt.normalize())[col].sum(); return d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
def row(x, lab):
    IS = x.t < "2024-01-01"; yr = x.groupby(x.t.dt.year).R.mean()
    return dict(cell=lab, n=len(x), avgR=x.R.mean(), t_day=tday(x), win=(x.R > 0).mean(), coin=x.R_coin.mean(),
                is_=x.R[IS].mean(), oos=x.R[~IS].mean(), worst_yr=yr.min(), yrs_pos=f"{(yr > 0).sum()}/{len(yr)}")
rows = []
m = T[T.asset.isin(MAJ)]
for r in sorted(T.rule.unique()):
    x = m[m.rule == r]
    if r.startswith("R1B"):                              # USD bid into the fix: long USDxxx, short xxxUSD
        usd = x[((x.asset.str.startswith("USD")) & (x.side == 1)) | ((~x.asset.str.startswith("USD")) & (x.side == -1))]
        rows.append(row(usd, r + " | buy USD, 7 majors"))
    elif r.startswith("R1C"):                            # USD bid 08-16 London then USD offered 16-21
        base = x.asset.str.startswith("USD")
        o = x[((x.tag == "L1") & ((base & (x.side == 1)) | (~base & (x.side == -1)))) | ((x.tag == "L2") & ((base & (x.side == -1)) | (~base & (x.side == 1))))]
        rows.append(row(o, r + " | USD bid London, offered after fix, 7 majors"))
        if "EURUSD" in set(x.asset):
            e = o[o.asset.isin(["EURUSD", "GBPUSD", "USDCHF"])]; rows.append(row(e, r + " | same, EURUSD/GBPUSD/USDCHF (draft's cell)"))
    else:
        rows.append(row(x, r + " | 7 majors"))
g = T[(T.asset == "XAUUSD")]
for r in ["R1D fix15 (gold PM) fade thr0.10", "R1A fix16 fade thr0.10"]: rows.append(row(g[g.rule == r], r + " | XAUUSD"))
x = g[g.rule == "R1B into fix15 (gold PM)"]; rows.append(row(x[x.side == -1], "R1B into fix15 | XAUUSD short (buy USD)"))
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(R.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
p = m[m.rule == "R1A fix16 fade thr0.10"]
print("\nprimary per pair:"); print(p.groupby("asset").R.agg(["size", "mean"]).to_string(float_format=lambda v: f"{v:+.3f}"))
print("primary per year:", p.groupby(p.t.dt.year).R.mean().round(3).to_dict())
# every market: pooled by group, primary rule, with/without crypto
print("\nby group (all rules, mean R / n):")
G = T.groupby(["rule", "group"]).R.agg(["size", "mean"]).unstack("group")
print(G["mean"].to_string(float_format=lambda v: f"{v:+.3f}"))
C = pd.read_csv(f.replace("_trades.pkl", "_cells.csv"))
print("\ncells with avgR > 0 and t >= 2:"); print(C[(C.avgR > 0) & (C.t >= 2)][["rule", "asset", "n", "avgR", "t", "is_", "oos", "coin"]].to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print("candidate-bar cells:", int(C.candidate.sum()), "of", int(C.avgR.notna().sum()), "luck ~", round(0.025 * C.avgR.notna().sum(), 1))
