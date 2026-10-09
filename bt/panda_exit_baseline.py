"""#32D baseline: the same exit rules applied from random entry days (400 draws per market)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/lab")
import panda_bull as P
from universe import catalog, daily_bars
from run_battery import intraday_frame
from daily import Daily, sma

def exit_from(x, a, i, rule, max_hold=250):
    O, H, L, C, A = x.O, x.H, x.L, x.C, x.A; N = len(C)
    ll10 = pd.Series(L).rolling(10).min().shift(1).values; s50 = sma(C, 50)
    E = O[a]; unit = 2.0 * A[i]; stop = E - unit; best = C[a]; X = None; b = None
    for k in range(a, min(a + max_hold, N)):
        if L[k] <= stop: X = min(stop, O[k]) if k > a else stop; b = k; break
        best = max(best, C[k])
        if rule.startswith("chand"): stop = max(stop, best - float(rule[5:]) * A[k])
        elif rule == "low10" and C[k] < ll10[k]: X, b = (O[k+1] if k+1 < N else C[k]), min(k+1, N-1); break
        elif rule == "ma50" and C[k] < s50[k]: X, b = (O[k+1] if k+1 < N else C[k]), min(k+1, N-1); break
        elif rule.startswith("hold") and k - a + 1 >= int(rule[4:]): X, b = C[k], k; break
    if X is None: b = min(a + max_hold, N) - 1; X = C[b]
    cost = x.SP[a] + x.comm * (abs(E) + abs(X)) + x.swap_cost(a, b, 1, E)
    return (X - E - cost) / unit

cat = catalog(); rng = np.random.default_rng(3)
for sym in ("XAUUSD", "US100.cash", "US500.cash", "TSLA", "AAPL", "BTCUSD"):
    d, tf = intraday_frame(sym, cat, dry=True); D = daily_bars(sym, cat, intraday=d)
    if sym in ("US100.cash", "US500.cash"): D = D[D.index >= "2018-01-01"]
    x = Daily(D, sym, None); N = len(x.C)
    out = []
    for rule in ("chand2", "chand3", "chand4", "low10", "ma50", "hold20", "hold60"):
        real = pd.DataFrame(P.exits_D(x, rule), columns=["day", "R", "nights"])
        idx = np.arange(60, N - 2); idx = idx[np.isfinite(x.A[idx])]
        base = [exit_from(x, i + 1, i, rule) for i in rng.choice(idx, size=min(400, len(idx)), replace=False)]
        out.append(f"{rule}: real {real.R.mean():+.2f} vs random-day {np.mean(base):+.2f} (edge {real.R.mean() - np.mean(base):+.2f})")
    print(f"{sym:11s} " + " | ".join(out))
