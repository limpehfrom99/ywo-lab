"""Follow-ups to log #49-51 (pre-registered in the log): pooled NR7/NR4 difference; gold Williams k=0.5 robustness."""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classic_intraday import Bars, rule_wvb, stats, show, tstat, from_server, load_export, ROOT

t = pd.read_pickle("/home/claude/bt/classic_intraday_trades.pkl"); nr = t[t.rule == "nr"].copy(); nr["nr7"] = nr.nr7.astype(bool); nr["nr4"] = nr.nr4.astype(bool)
for flag in ("nr7", "nr4"):
    a, b = nr[nr[flag]].R, nr[~nr[flag]].R
    d = a.mean() - b.mean(); se = np.sqrt(a.var() / len(a) + b.var() / len(b))
    print(f"pooled {flag.upper()}: n={len(a)} avg {a.mean():+.3f} (t {tstat(a):+.1f}) vs other days n={len(b)} {b.mean():+.3f}; diff {d:+.3f} (t {d / se:+.1f})")
    print("   by session diff: " + " ".join(f"{m} {g[g[flag]].R.mean() - g[~g[flag]].R.mean():+.2f}" for m, g in nr.groupby("mkt")))
    s = stats(f"pooled {flag.upper()} (6 sessions)", nr[nr[flag]]); show(s)
    s = stats(f"pooled {flag.upper()} excl gold_ldn", nr[nr[flag] & (nr.mkt != "gold_ldn")]); show(s)

g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]
B = Bars(g, "gold", 1)
show(stats("WVB gold k=0.5 broker day (base)", rule_wvb(B, B.sessions(0, 0, broker=True), 0.5, False).assign(day=lambda x: pd.to_datetime(x.day))))
B.srvd = pd.DatetimeIndex(B.t).normalize().values          # UTC day instead of the broker day
show(stats("WVB gold k=0.5 UTC day", rule_wvb(B, B.sessions(0, 0, broker=True), 0.5, False).assign(day=lambda x: pd.to_datetime(x.day))))
B = Bars(g, "gold", 1)
show(stats("WVB gold k=0.5 COMEX 08:20-16:00", rule_wvb(B, B.sessions(500, 960), 0.5, False).assign(day=lambda x: pd.to_datetime(x.day))))
x = load_export(glob.glob(os.path.join(ROOT, "data", "raw", "XAUUSD_M15_*.csv.gz"))[0])
x.index = from_server(pd.DatetimeIndex(x.index)); x = x[~x.index.isna()].sort_index(); x = x[~x.index.duplicated()][["open", "high", "low", "close", "sp"]]
BX = Bars(x, "gold", 15)
show(stats("WVB gold k=0.5 FTMO M15 2022-07+", rule_wvb(BX, BX.sessions(0, 0, broker=True), 0.5, False).assign(day=lambda x: pd.to_datetime(x.day))))
gm = g.loc["2022-07-05":]; B2 = Bars(gm, "gold", 1)
show(stats("WVB gold k=0.5 MT4 M1 same period", rule_wvb(B2, B2.sessions(0, 0, broker=True), 0.5, False).assign(day=lambda x: pd.to_datetime(x.day))))
