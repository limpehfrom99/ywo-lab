"""Log #50 check (backlog #49): Larry Williams volatility breakout on FTMO's own gold feed 2015-2026 (full export, M5 and M1),
rules unchanged from bt/classic_intraday.py rule_wvb (broker day, buy stop at open + k x yesterday's range, sell stop at
open - k x range, stop 0.5 x range, exit at the day's close; a bar that hits both entries = stopped). Pre-registered: the gold
CANDIDATE stands only if FTMO gold 2015+ gives >= +0.03R at k = 0.5. Also silver, platinum, palladium (same rule, not selected
on). Spread x 1.2 + 0.0007%/side.  python3 bt/wvb_ftmo.py"""
import os, sys, time, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bt")); sys.path.insert(0, os.path.join(ROOT, "quant"))
import classic_intraday as CI
import universe as U

CI.MK.update({"XAUUSD": (0.000007, 1.2, 0.0), "XAGUSD": (0.000007, 1.2, 0.0), "XPTUSD": (0.000007, 1.2, 0.0),
              "XPDUSD": (0.000007, 1.2, 0.0)})
t0 = time.time(); cat = U.catalog(); rows = []; allt = []
for sym, tf in (("XAUUSD", "M5"), ("XAUUSD", "M1"), ("XAGUSD", "M5"), ("XPTUSD", "M5"), ("XPDUSD", "M5")):
    d = U.load(sym, tf, cat); d.index = d.index.tz_localize(None); d = d[~d.index.duplicated()].sort_index()
    d = d[["open", "high", "low", "close", "sp"]]
    bm = 5 if tf == "M5" else 1
    B = CI.Bars(d, sym, bm); S = B.sessions(0, 0, broker=True)
    for k in (0.3, 0.5, 0.7):
        df = CI.rule_wvb(B, S, k, False)
        if not len(df): continue
        df["day"] = pd.to_datetime(df.day)
        r = CI.stats(f"WVB {sym} {tf} k={k}", df); rows.append(r); CI.show(r)
        allt.append(df.assign(symbol=sym, tf=tf, k=k))
    print(f"--- {sym} {tf}: {len(S)} days ({time.time() - t0:.0f}s)", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(ROOT, "results", "wvb_ftmo.csv"), index=False)
pd.concat(allt).to_csv(os.path.join(ROOT, "results", "wvb_ftmo_trades.csv.gz"), index=False, float_format="%.7g")
print(f"done in {time.time() - t0:.0f}s")
