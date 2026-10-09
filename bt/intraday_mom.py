"""Idea 14 (online): intraday momentum, Gao-Han-Li-Zhou (2018, JFE) "the first half-hour return predicts the last
half-hour return". Rule: signal = return from the prior 16:00 close to the 10:00 NY price (first 30 min incl. the
overnight gap); at 15:30 NY trade in the signal's direction, exit at the 16:00 close. Costs: spread + commission.
Baselines: coin flip (= unconditional last-30-min drift) and the opposite rule. Variant: signal = the 9:30-10:00 candle
only (the opening-candle signal without the gap). Data: FTMO M30 exports (US100/US500 2021-09+, TSLA 2019+, AAPL 2015+)."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/lab')
from ftmo_data import load_export
from lab import ny_session

def t(x): return x.mean() / (x.std() / np.sqrt(len(x)))
specs = {"US100": ("US100.cash_M30", 0.0), "US500": ("US500.cash_M30", 0.0), "TSLA": ("TSLA_M30", 0.00002), "AAPL": ("AAPL_M30", 0.00002)}
for name, (pat, comm) in specs.items():
    d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0]); s = ny_session(d)
    n = s.groupby("nyd").size(); days = n[n == 13].index
    g = s[s.nyd.isin(days)]
    o930 = g[g.nyt == "09:30"].set_index("nyd"); b1530 = g[g.nyt == "15:30"].set_index("nyd"); c1600 = b1530.close
    prev_close = c1600.shift(1)
    rows = []
    for day in days[1:]:
        if day not in prev_close.index or not np.isfinite(prev_close[day]): continue
        p10 = o930.close[day]                      # price at 10:00 = close of the 9:30 bar
        sig_gap = np.sign(p10 - prev_close[day]); sig_candle = np.sign(p10 - o930.open[day])
        e = b1530.open[day]; x = b1530.close[day]; sp = b1530.sp[day]
        ret_bp = (x - e) / e * 1e4; cost_bp = (sp / e + 2 * comm) * 1e4
        rows.append(dict(day=day, year=day.year, sig_gap=sig_gap, sig_candle=sig_candle, ret_bp=ret_bp, cost_bp=cost_bp))
    r = pd.DataFrame(rows)
    print(f"\n==== {name} {r.day.min().date()}..{r.day.max().date()} ({len(r)} days) last-30-min move avg {r.ret_bp.mean():+.2f} bp, cost {r.cost_bp.mean():.2f} bp ====")
    for sig in ("sig_gap", "sig_candle"):
        rr = r[r[sig] != 0]; net = rr[sig] * rr.ret_bp - rr.cost_bp
        print(f"  {sig:10s}: n={len(rr)} net {net.mean():+.2f} bp/trade t={t(net):+.1f} win={np.mean(rr[sig]*rr.ret_bp>0):.0%} | gross {(rr[sig]*rr.ret_bp).mean():+.2f} bp | halves {net.iloc[:len(net)//2].mean():+.2f}/{net.iloc[len(net)//2:].mean():+.2f}")
        print("     per year:", net.groupby(rr.year).mean().round(1).to_dict())
