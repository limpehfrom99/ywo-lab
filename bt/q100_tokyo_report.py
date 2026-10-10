"""Log #100 report (R3 Tokyo fix / gotobi), from bt/xrun.py tag r3."""
import glob, sys, numpy as np, pandas as pd
f = sorted(glob.glob("/home/claude/bt/xgrid_results/*_r3_trades.pkl"))[-1]; T = pd.read_pickle(f)
for c in ("R", "R_coin"): T[c] = T[c].astype(float)
def st(x, col="R", ccol="R_coin"):
    IS = x.t < "2024-01-01"; yr = x.groupby(x.t.dt.year)[col].mean()
    return pd.Series(dict(n=len(x), avgR=x[col].mean(), t=x[col].mean() / x[col].std() * np.sqrt(len(x)) if len(x) > 2 else np.nan,
                          win=(x[col] > 0).mean(), coin=x[ccol].mean(), is_=x[IS][col].mean(), oos=x[~IS][col].mean(), worst=yr.min(), yrs=f"{(yr > 0).sum()}/{len(yr)}"))
pd.set_option("display.width", 250); fm = lambda v: f"{v:+.3f}"
M = T[T.tf == "M15"]
print("USDJPY long, M15:"); print(M[(M.asset == "USDJPY") & (M.side == 1)].groupby("rule").apply(st).to_string(float_format=fm))
u = M[(M.asset == "USDJPY") & (M.side == 1) & (M.rule == "R3A gotobi 0900-0945")]
print("3A per year:", u.groupby(u.t.dt.year).R.mean().round(3).to_dict())
b = M[(M.asset == "USDJPY") & (M.side == 1) & (M.rule == "R3B all days 0900-0945")]
print("3B per year:", b.groupby(b.t.dt.year).R.mean().round(3).to_dict())
print("USDJPY short 10-11 (3C reversal):"); print(M[(M.asset == "USDJPY") & (M.side == -1) & M.rule.str.startswith("R3C")].groupby("rule").apply(st).to_string(float_format=fm))
X = M[((M.asset.isin(["EURJPY", "GBPJPY", "AUDJPY"])) & (M.side == 1)) | ((M.asset.isin(["EURUSD", "GBPUSD"])) & (M.side == -1))]
print("draft's report pairs (yen crosses long, EUR/GBP-USD short):"); print(X.groupby(["rule", "asset"]).R.mean().unstack().to_string(float_format=fm))
print("every market, gotobi 0900-0945 mean R by group and side:")
g = M[M.rule == "R3A gotobi 0900-0945"]; print(g.groupby(["group", "side"]).R.mean().unstack().to_string(float_format=fm))
print("JPY-quoted pairs long, gotobi vs non-gotobi:", M[(M.asset.str.endswith("JPY")) & (M.side == 1)].groupby("rule").R.mean().round(3).to_dict())
C = pd.read_csv(f.replace("_trades.pkl", "_cells.csv"))
print(C[(C.avgR > 0) & (C.t >= 2)][["rule", "asset", "tf", "n", "avgR", "t", "is_", "oos", "coin", "longs", "shorts"]].to_string(index=False, float_format=fm))
print("passing", int(C.candidate.sum()), "of", int(C.avgR.notna().sum()))
