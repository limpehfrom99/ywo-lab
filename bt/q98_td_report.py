"""Log #98 report: T1 TD Sequential cells from bt/xrun.py (tag td). Adds swaps for overnight holds: today's spec-sheet swap turned into a
fraction of the spec price per night (x3 on the triple day), divided by the trade's risk fraction (Fill tag). Primary = D1, metals +
energy + softs, C13 and S9P, H5."""
import glob, sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/ywo-lab/quant"); import universe as U
tag = sys.argv[1] if len(sys.argv) > 1 else "td"
f = sorted(glob.glob(f"/home/claude/bt/xgrid_results/*_{tag}_trades.pkl"))[-1]
T = pd.read_pickle(f); T["R"] = T.R.astype(float); T["R_coin"] = T.R_coin.astype(float); T["rf"] = T.tag.astype(float)
sp = U.specs()
def frac(sym, side):
    if sym not in sp.index: return 0.0
    px = float(sp.loc[sym, "bid"]) or 1.0
    return U.swap_per_night(sym, px, side, sp) / px
fr = {(s, d): frac(s, d) for s in T.asset.unique() for d in (1, -1)}
tri = {s: U.triple_day(s, sp) for s in T.asset.unique()}
# nights: 17:00 NY rollovers between entry and exit
ny_in = T.t.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
ny_out = ny_in + pd.to_timedelta(T.hold_h.astype(float), unit="h")
roll = lambda x: (x - pd.Timedelta(hours=17)).dt.normalize()
d0, d1 = roll(ny_in), roll(ny_out)
nights = ((d1 - d0).dt.days).clip(lower=0)
# weekday count of rollovers, triple day x3 (weekend nights are inside the triple)
bdays = np.busday_count(d0.values.astype("datetime64[D]"), d1.values.astype("datetime64[D]"))
extra = np.zeros(len(T))
for s in T.asset.unique():
    m = (T.asset == s).values
    if not m.any(): continue
    w = tri[s]; a = d0.values[m].astype("datetime64[D]"); b = d1.values[m].astype("datetime64[D]")
    mask = "".join("1" if i == w else "0" for i in range(7))
    extra[m] = 2 * np.busday_count(a, b, weekmask=mask)
T["nights"] = bdays + extra
T["swapR"] = [fr[(s, int(d))] for s, d in zip(T.asset, T.side)] * T.nights / T.rf.clip(lower=1e-6)
T["Rs"] = T.R - T.swapR; T["Rcs"] = T.R_coin - [fr[(s, -int(d))] for s, d in zip(T.asset, T.side)] * T.nights / T.rf.clip(lower=1e-6)
def st(x, col="Rs"):
    if len(x) < 3: return dict(n=len(x))
    IS = x.t < "2024-01-01"; yr = x.groupby(x.t.dt.year)[col].mean(); r = x[col]
    return dict(n=len(x), avgR=r.mean(), t=r.mean() / r.std() * np.sqrt(len(r)), win=(r > 0).mean(), noswap=x.R.mean(), coin=x.Rcs.mean(),
                L=x[x.side == 1][col].mean(), S=x[x.side == -1][col].mean(), is_=x[IS][col].mean(), oos=x[~IS][col].mean(),
                worst=yr.min(), yrs=f"{(yr > 0).sum()}/{len(yr)}")
fmt = lambda v: f"{v:+.3f}"; pd.set_option("display.width", 250)
PRIM = ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "USOIL.cash", "UKOIL.cash", "NATGAS.cash"] + [s for s in T.asset.unique() if s.endswith(".c")]
P = T[(T.tf == "D1") & T.asset.isin(PRIM)]
rows = [dict(cell=f"PRIMARY D1 commodities {r}", **st(P[P.rule == r])) for r in sorted(P.rule.unique())]
print(pd.DataFrame(rows).to_string(index=False, float_format=fmt))
nc = T[T.group != "crypto"]
print("\npooled ex-crypto by rule x tf (swap-adjusted mean R):")
print(nc.groupby(["rule", "tf"]).Rs.mean().unstack("tf")[["M30", "H1", "H4", "D1"]].to_string(float_format=fmt))
print("\nn by tf:", nc.groupby("tf").size().to_dict())
print("\npooled ex-crypto, coin (other side) by rule x tf:")
print(nc.groupby(["rule", "tf"]).Rcs.mean().unstack("tf")[["M30", "H1", "H4", "D1"]].to_string(float_format=fmt))
print("\nby group, H4+D1, H5 rules (swap-adjusted):")
h = T[T.tf.isin(["H4", "D1"]) & T.rule.str.endswith("H5")]
print(h.groupby(["rule", "group"]).Rs.mean().unstack("group").to_string(float_format=fmt))
C = pd.read_csv(f.replace("_trades.pkl", "_cells.csv"))
print("\ncells passing the bar (no swaps):", int(C.candidate.sum()), "of", int(C.avgR.notna().sum()), "luck ~", round(0.025 * C.avgR.notna().sum(), 1))
cs = pd.DataFrame([dict(rule=k[0], asset=k[1], tf=k[2], group=x.group.iloc[0], **st(x)) for k, x in T.groupby(["rule", "asset", "tf"], observed=True) if len(x) >= 10])
ok = cs[(cs.n >= 200) & (cs.t >= 2) & (cs.avgR >= 0.05) & (cs.is_ > 0) & (cs.oos > 0) & (cs.worst > -0.3)]
print("cells passing with swaps:", len(ok)); print(ok.to_string(index=False, float_format=fmt))
print("share of cells positive (swaps):", round((cs.avgR > 0).mean(), 3))
cs.to_csv(f"/home/claude/ywo-lab/results/q98_td_cells_swaps.csv", index=False)
