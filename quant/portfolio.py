"""Survivors -> one portfolio -> FTMO pass odds by risk level and horizon, funded payout, correlations.

Daily returns = sum over cells of R x risk, risk per trade capped by FTMO Swing leverage (allowed = min(risk, leverage x
stop %)). Daily (multi-day) trades are booked on their exit day. Paths resample history in 10-day blocks.
FTMO: phase 1 +10%, phase 2 +5%, 5% daily loss, 10% total loss (static), at least 4 trading days per phase.
Edge haircuts: full backtest edge, half edge (R - mean/2), zero edge (R - mean) to show what luck alone gives.
python3 portfolio.py [--verdicts SURVIVOR,WATCH] [--from 2024-01-01]
"""
import os, sys, argparse, pickle
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from universe import leverage_of  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")


def mc(ret, n=4000, block=10, max_days=250, seed=7):
    ret = np.asarray(ret); rng = np.random.default_rng(seed); res = []
    for _ in range(n):
        eq, days, phase, tgt, ok, fail, pdays = 1.0, 0, 1, 0.10, False, False, 0
        while days < max_days and not ok and not fail:
            s = rng.integers(0, len(ret) - block)
            for x in ret[s:s + block]:
                start = eq; eq *= 1 + x; days += 1; pdays += 1
                if eq - start <= -0.05 or eq <= 0.90: fail = True; break
                if eq >= 1 + tgt and pdays >= 4:
                    if phase == 1: phase, tgt, eq, pdays = 2, 0.05, 1.0, 0
                    else: ok = True; break
                if days >= max_days: break
        res.append((ok, fail, days))
    r = pd.DataFrame(res, columns=["ok", "fail", "days"])
    out = {f"pass {m}m": float(((r.ok) & (r.days <= 21 * m)).mean()) for m in (1, 2, 3, 4)}
    out["pass 12m"] = float(r.ok.mean()); out["fail"] = float(r.fail.mean())
    out["median months"] = float(r[r.ok].days.median() / 21) if r.ok.any() else np.nan
    return out


def funded(ret, months=12, split=0.8, n=3000, block=10, seed=2):
    ret = np.asarray(ret); rng = np.random.default_rng(seed); surv = 0; paid = 0.0
    for _ in range(n):
        eq, p, alive = 1.0, 0.0, True
        for _m in range(months):
            days = 0
            while days < 21 and alive:
                s = rng.integers(0, len(ret) - block)
                for x in ret[s:s + block]:
                    start = eq; eq *= 1 + x; days += 1
                    if eq - start <= -0.05 or eq <= 0.90: alive = False; break
                    if days >= 21: break
            if not alive: break
            if eq > 1: p += (eq - 1) * split; eq = 1.0
        surv += alive; paid += p
    return surv / n, paid / n / months


def book_dates(key, tr):
    """Intraday trades: their session date. Daily trades: the exit day (entry + hold trading days)."""
    day = pd.DatetimeIndex(tr.day).normalize()
    if key[0] in ("daily", "xsec") and "hold" in tr:
        day = pd.DatetimeIndex([d + pd.offsets.BDay(int(h)) for d, h in zip(day, tr.hold.values)])
    return day


def daily_returns(trades, keys, risk, keep=1.0, start=None, end=None):
    parts = []
    for k in keys:
        tr = trades[k]; R = tr.R.values - (1 - keep) * tr.R.mean()
        allowed = np.minimum(risk, tr.risk_frac.values * leverage_of(k[1]))
        s = pd.Series(R * allowed, index=book_dates(k, tr)).groupby(level=0).sum()
        parts.append(s.rename("|".join(k[1:])))
    df = pd.concat(parts, axis=1, sort=True).fillna(0)
    a = pd.Timestamp(start) if start else df.index.min(); b = pd.Timestamp(end) if end else df.index.max()
    cal = pd.bdate_range(a, b)
    return df.reindex(cal).fillna(0)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verdicts", default="SURVIVOR"); ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--cells", default=os.path.join(RESULTS, "battery_cells.csv")); ap.add_argument("--trades", default="/home/claude/bt/battery_trades.pkl")
    ap.add_argument("--extra", default="", help="force-include cells, e.g. intraday|TSLA|us_cash|OC30;intraday|US100.cash|us_cash|OC30")
    ap.add_argument("--out", default="battery_ftmo.csv")
    a = ap.parse_args()
    cells = pd.read_csv(a.cells); trades = pickle.load(open(a.trades, "rb"))
    sel = cells[cells.verdict.isin(a.verdicts.split(","))]
    keys = [(r.kind, r.symbol, r.session, r.rule) for r in sel.itertuples()]
    keys += [tuple(x.split("|")) for x in a.extra.split(";") if x]
    keys = list(dict.fromkeys(k for k in keys if k in trades))
    if not keys: print("no cells with verdicts", a.verdicts); return
    print(f"{len(keys)} cells:", ", ".join("|".join(k[1:]) for k in keys))
    start = a.start or max(pd.DatetimeIndex(trades[k].day).min() for k in keys)
    D1 = daily_returns(trades, keys, 0.01, start=start)
    print("\ndaily correlation of the cells (1% risk):\n", D1.corr().round(2).to_string())
    rows = []
    for risk in (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02):
        for keep, lab in ((1.0, "full"), (0.5, "half"), (0.0, "zero")):
            ret = daily_returns(trades, keys, risk, keep, start=start).sum(axis=1)
            m = mc(ret.values)
            row = dict(risk=f"{risk * 100:.2f}%", edge=lab, **{k: round(v, 3) for k, v in m.items()})
            if keep == 1.0:
                s, pay = funded(ret.values); eq = (1 + ret).cumprod()
                row.update(hist_maxDD=round(((eq / eq.cummax()) - 1).min() * 100, 1), worst_day=round(ret.min() * 100, 2),
                           avg_month=round(((1 + ret).groupby(ret.index.to_period("M")).prod() - 1).mean() * 100, 2),
                           keep12m=round(s, 2), payout_10k=round(pay * 10000))
            rows.append(row); print(row, flush=True)
    out = pd.DataFrame(rows); out.to_csv(os.path.join(RESULTS, a.out), index=False)


if __name__ == "__main__":
    main()
