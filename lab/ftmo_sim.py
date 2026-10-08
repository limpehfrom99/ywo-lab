#!/usr/bin/env python3
"""FTMO challenge odds and funded-account results from backtested trades.

In Python:
    from ftmo_sim import daily_returns, challenge, funded, scenarios
    trades = {"TSLA": tsla_trades, "US100": us100_trades}      # DataFrames with columns R and stop_pct, indexed by day
    leverage = {"TSLA": 1, "US100": 15}                         # FTMO Swing: indices 15, gold 9, stocks/crypto 1
    print(scenarios(trades, leverage, risks=(0.005, 0.01)))

Method: daily returns = sum over strategies of R x risk, with risk capped so position value <= balance x leverage.
History is resampled in 10-day blocks (keeps good and bad streaks together). Phase 1 needs +10%, Phase 2 +5%,
with the 5% daily and 10% total loss limits and at least 4 trading days. Funded: 12 months, 80% of each
month-end profit paid out and the balance reset; a breach ends the account.
"""
import numpy as np
import pandas as pd


def daily_returns(trades, leverage, risk, edge_keep=1.0):
    """trades: {name: DataFrame(R, stop_pct)}. edge_keep < 1 shrinks each strategy's average R (0.5 = half the edge)."""
    parts = []
    for name, t in trades.items():
        R = t["R"] - (1 - edge_keep) * t["R"].mean()
        allowed = np.minimum(risk, t["stop_pct"] / 100 * leverage[name])
        parts.append((R * allowed).rename(name))
    return pd.concat(parts, axis=1).fillna(0).sum(axis=1).sort_index()


def _phase(ret, rng, target, daily_limit, max_loss, min_days, max_days, block):
    eq, days = 1.0, 0
    while days < max_days:
        s = rng.integers(0, len(ret) - block)
        for x in ret[s:s + block]:
            start = eq
            eq *= 1 + x
            days += 1
            if eq - start <= -daily_limit or eq <= 1 - max_loss:
                return False, days
            if eq >= 1 + target and days >= min_days:
                return True, days
    return False, days


def challenge(ret, targets=(0.10, 0.05), daily_limit=0.05, max_loss=0.10, min_days=4,
              n=3000, block=10, max_days=750, seed=1):
    """Odds of passing every phase in `targets`, and the median trading days to finish."""
    ret = np.asarray(ret)
    rng = np.random.default_rng(seed)
    passed, durations = 0, []
    for _ in range(n):
        total, ok = 0, True
        for tg in targets:
            ok, d = _phase(ret, rng, tg, daily_limit, max_loss, min_days, max_days, block)
            total += d
            if not ok:
                break
        if ok:
            passed += 1
            durations.append(total)
    return {"pass rate": passed / n, "median months": (np.median(durations) / 21) if durations else None}


def funded(ret, months=12, split=0.8, daily_limit=0.05, max_loss=0.10, n=3000, block=10, seed=2):
    """Odds of keeping a funded account for `months`, and the average payout per month (fraction of the account)."""
    ret = np.asarray(ret)
    rng = np.random.default_rng(seed)
    survived, paid_total = 0, 0.0
    for _ in range(n):
        eq, paid, alive = 1.0, 0.0, True
        for _m in range(months):
            days = 0
            while days < 21 and alive:
                s = rng.integers(0, len(ret) - block)
                for x in ret[s:s + block]:
                    start = eq
                    eq *= 1 + x
                    days += 1
                    if eq - start <= -daily_limit or eq <= 1 - max_loss:
                        alive = False
                        break
                    if days >= 21:
                        break
            if not alive:
                break
            if eq > 1.0:
                paid += (eq - 1.0) * split
                eq = 1.0
        survived += alive
        paid_total += paid
    return {"keep account": survived / n, "payout per month": paid_total / n / months}


def scenarios(trades, leverage, risks=(0.005, 0.01), keeps=(1.0, 0.5, 0.0), account=10000, n=3000):
    rows = []
    for keep in keeps:
        for r in risks:
            ret = daily_returns(trades, leverage, r, keep).values
            c = challenge(ret, n=n)
            f = funded(ret, n=n)
            rows.append({"edge kept": f"{keep:.0%}", "risk": f"{r * 100:.2f}%",
                         "pass both phases": f"{c['pass rate']:.0%}",
                         "months to pass": None if c["median months"] is None else round(c["median months"], 1),
                         "keep funded 12 months": f"{f['keep account']:.0%}",
                         f"payout/month on ${account:,}": f"${f['payout per month'] * account:,.0f}"})
    return pd.DataFrame(rows)


def monthly_table(ret):
    """Historical month-by-month returns, plus summary figures."""
    ret = pd.Series(ret)
    m = (1 + ret).groupby(ret.index.to_period("M")).prod() - 1
    eq = (1 + ret).cumprod()
    return m, {"avg month": m.mean(), "median month": m.median(), "months positive": (m > 0).mean(),
               "worst month": m.min(), "worst drawdown": (eq / eq.cummax() - 1).min()}
