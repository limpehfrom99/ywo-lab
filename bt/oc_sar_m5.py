"""Opening candle with stop-and-reverse, on 5-minute bars (TSLA 2021-26, US100/US500 2025-26), Fed days skipped.
Leg 1: direction of the 9:30-10:00 candle, entry at the 10:00 open, stop at the candle's far end, exit 15:55 close.
Leg 2 (only after a leg-1 stop-out): enter at the stop price in the opposite direction, stop at the leg-1 entry, exit 15:55.
Leg 2 stop is checked from the NEXT 5-minute bar (a 5-min bar rarely crosses the whole opening range twice)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab")
from news import load_calendar, fed_days
FED = set(fed_days(load_calendar("/home/claude/news/news_usd.csv")))

def run(sym, comm, sar=True, same_bar=False):
    b = pd.read_pickle(f"/home/claude/data/{sym}_m5.pkl"); rows = []
    for day, x in b.groupby("nyd"):
        if day in FED: continue
        x = x[(x.nym >= 570) & (x.nym < 960)]
        f = x[x.nym < 600]; rest = x[x.nym >= 600]
        if len(f) < 4 or len(rest) < 60: continue
        o, c, hi, lo = f.open.iloc[0], f.close.iloc[-1], f.high.max(), f.low.min()
        if c == o: continue
        dr = 1 if c > o else -1; e = rest.open.iloc[0]; stop = lo if dr == 1 else hi; risk = (e - stop) * dr
        if risk <= 0: continue
        H, L, O, C = rest.high.values, rest.low.values, rest.open.values, rest.close.values; sp = rest.sp.values[0]
        px, why, k = C[-1], "close", None
        for i in range(len(rest)):
            if dr == 1 and L[i] <= stop: px, why, k = min(stop, O[i]), "stop", i; break
            if dr == -1 and H[i] >= stop: px, why, k = max(stop, O[i]), "stop", i; break
        R = (dr * (px - e) - sp - comm * (e + px)) / risk; R1 = R
        if sar and why == "stop":
            dr2, e2, stop2 = -dr, px, e; risk2 = (e2 - stop2) * dr2; px2, why2 = C[-1], "close"
            start = k if same_bar else k + 1
            for i in range(start, len(rest)):
                if dr2 == 1 and L[i] <= stop2: px2, why2 = (stop2 if i == k else min(stop2, O[i])), "stop"; break
                if dr2 == -1 and H[i] >= stop2: px2, why2 = (stop2 if i == k else max(stop2, O[i])), "stop"; break
            if risk2 > 0: R += (dr2 * (px2 - e2) - sp - comm * (e2 + px2)) / risk2
        rows.append(dict(day=day, year=day.year, R=R, R1=R1, why=why))
    return pd.DataFrame(rows).set_index("day")

def line(label, R):
    R = np.asarray(R); n = len(R); return f"{label:40s} n={n:4d} avgR={R.mean():+.3f} t={R.mean()/(R.std()/np.sqrt(n)):+.1f} win={np.mean(R>0):.0%} worst {R.min():+.2f}"

for sym, comm in (("TSLA", 0.00002), ("US100", 0.0), ("US500", 0.0), ("AAPL", 0.00002)):
    base = run(sym, comm, sar=False); s = run(sym, comm, sar=True); s2 = run(sym, comm, sar=True, same_bar=True)
    print(f"\n{sym} {base.index.min().date()}..{base.index.max().date()}")
    print(line("  base (5-min bars)", base.R)); print(line("  SAR, leg-2 stop from next bar", s.R)); print(line("  SAR, leg-2 stop incl. same bar", s2.R))
    st = base.why == "stop"; print(line("  reversal leg alone (next-bar)", (s.R - s.R1)[st]))
    print("  per year base:", base.R.groupby(base.year).mean().round(2).to_dict()); print("  per year SAR :", s.R.groupby(s.year).mean().round(2).to_dict())
