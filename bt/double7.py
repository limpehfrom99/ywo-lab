"""Log #55 (backlog #29): Connors Double 7s on daily broker-day bars; baseline = same direction + holding time from random days."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classic_intraday as ci
from classic_intraday import tstat, ROOT

rng = np.random.default_rng(7)


def daily(m):
    d, bm = ci.load(m); B = ci.Bars(d, m, bm)
    x = pd.DataFrame({"close": B.C, "high": B.H, "low": B.L, "sp": B.sp}, index=pd.DatetimeIndex(B.srvd))
    g = x.groupby(level=0).agg(close=("close", "last"), high=("high", "max"), low=("low", "min"), sp=("sp", "median"))
    g = g[g.index.weekday < 5]
    if m in ("US100", "US500"): g = g.loc["2018-01-01":]
    pc = g.close.shift(1)
    g["atr"] = pd.concat([g.high - g.low, (g.high - pc).abs(), (g.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean()
    return g, B.comm


def ret(g, comm, i, k, side):
    C, idx = g.close.values, g.index
    e, x = C[i], C[k]; nights = (idx[k] - idx[i]).days
    cost = g.sp.values[i] + comm * (abs(e) + abs(x)) + 0.0001 * nights * e
    return side * (x - e) - cost


def run(g, comm):
    C = g.close.values; ma = g.close.rolling(200).mean().values; A = g.atr.values; rows = []; i = 207
    while i < len(C) - 1:
        lo7, hi7 = C[i] <= C[i - 6:i + 1].min(), C[i] >= C[i - 6:i + 1].max()
        side = 1 if (C[i] > ma[i] and lo7) else -1 if (C[i] < ma[i] and hi7) else 0
        if side == 0 or not np.isfinite(A[i]): i += 1; continue
        k = i + 1
        while k < len(C) and not ((side == 1 and C[k] >= C[k - 6:k + 1].max()) or (side == -1 and C[k] <= C[k - 6:k + 1].min())): k += 1
        if k >= len(C): break
        r = ret(g, comm, i, k, side)
        js = rng.integers(207, len(C) - (k - i), 200)
        base = np.mean([ret(g, comm, j, j + (k - i), side) / A[j] for j in js if np.isfinite(A[j])])
        rows.append(dict(day=g.index[i], side=side, hold=k - i, atrR=r / A[i], bp=r / C[i] * 1e4, base=base))
        i = k + 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    allr = []
    for m in ("gold", "US100", "US500", "AAPL", "TSLA"):
        g, comm = daily(m); df = run(g, comm); df["mkt"] = m; allr.append(df)
    df = pd.concat(allr); df["edge"] = df.atrR - df.base
    def line(lab, x):
        IS = x.day < "2024-01-01"; yr = x.groupby(x.day.dt.year).edge.mean()
        return (f"{lab:26s} n={len(x):4d} hold {x.hold.median():.0f}d  avg {x.atrR.mean():+.3f} ATR ({x.bp.mean():+.1f} bp) t={tstat(x.atrR):+.1f} "
                f"win {np.mean(x.atrR > 0):.0%} | random-day baseline {x.base.mean():+.3f} -> edge {x.edge.mean():+.3f} (t {tstat(x.edge):+.1f}) "
                f"| edge IS {x.edge[IS].mean():+.3f} OOS {x.edge[~IS].mean():+.3f} (n {(~IS).sum()}) | edge yrs+ {(yr > 0).sum()}/{len(yr)}")
    for m, x in df.groupby("mkt", sort=False):
        print(line(f"{m} long+short", x)); print(line(f"{m} longs", x[x.side == 1])); print(line(f"{m} shorts", x[x.side == -1]))
    print(line("POOLED all", df)); print(line("POOLED longs", df[df.side == 1])); print(line("POOLED shorts", df[df.side == -1]))
    df.to_csv(os.path.join(ROOT, "results", "double7_trades.csv"), index=False)
