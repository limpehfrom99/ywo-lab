"""Log #99 report (R14 reopen gap fade), from bt/xrun.py tag r14b."""
import glob, sys, numpy as np, pandas as pd
tag = sys.argv[1] if len(sys.argv) > 1 else "r14b"
f = sorted(glob.glob(f"/home/claude/bt/xgrid_results/*_{tag}_trades.pkl"))[-1]; T = pd.read_pickle(f)
for c in ("R", "R_coin", "rr"): T[c] = T[c].astype(float)
def st(x):
    IS = x.t < "2024-01-01"; yr = x.groupby(x.t.dt.year).R.mean()
    return pd.Series(dict(n=len(x), avgR=x.R.mean(), t=x.R.mean() / x.R.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan, win=(x.R > 0).mean(),
                          coin=x.R_coin.mean(), is_=x[IS].R.mean(), oos=x[~IS].R.mean(), worst=yr.min(), yrs=f"{(yr > 0).sum()}/{len(yr)}", rr=x.rr.median()))
pd.set_option("display.width", 250); fm = lambda v: f"{v:+.3f}"
F = T[T.rule.str.startswith("R14 reopen")]; P = F[F.asset.isin(["US500.cash", "US100.cash", "US30.cash"])]
print("PRIMARY US500+US100+US30 by tf:"); print(P.groupby("tf").apply(st).to_string(float_format=fm))
print("per index, M5:"); print(P[P.tf == "M5"].groupby("asset").apply(st).to_string(float_format=fm))
print("weekday vs Sunday reopen, M5:"); print(P[P.tf == "M5"].groupby("tag").apply(st).to_string(float_format=fm))
print("per year M5:", P[P.tf == "M5"].groupby(P.t.dt.year).R.mean().round(3).to_dict())
print("XAUUSD by tf:"); print(F[F.asset == "XAUUSD"].groupby("tf").apply(st).to_string(float_format=fm))
print("by group x tf (mean R):"); print(F.groupby(["group", "tf"]).R.mean().unstack().to_string(float_format=fm))
print("n by group:", F.groupby("group").size().to_dict())
Fo = T[T.rule.str.startswith("R14 report")]
print("follow 18-19 (R) vs fade (coin), M5 by group:"); print(Fo[Fo.tf == "M5"].groupby("group")[["R", "R_coin"]].mean().to_string(float_format=fm))
C = pd.read_csv(f.replace("_trades.pkl", "_cells.csv"))
print(C[(C.avgR > 0) & (C.t >= 2)][["rule", "asset", "tf", "n", "avgR", "t", "is_", "oos", "coin"]].to_string(index=False, float_format=fm))
print("passing", int(C.candidate.sum()), "of", int(C.avgR.notna().sum()))
