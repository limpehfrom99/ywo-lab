"""FTMO scenario engine: P(pass by 1/2/3/4 months), P(fail), median months, funded income, for strategy mixes x risk levels.
Trades are the real backtest trade lists (R per trade, planned risk). Daily returns = sum over strategies of R x risk,
risk capped by leverage. Paths resample history in 10-day blocks. FTMO: phase 1 +10%, phase 2 +5%, 5% daily loss,
10% total loss (static), min 4 trading days per phase."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from lab import opening_candle
from news import load_calendar, fed_days
import sr_diag
from daily_ideas import donchian, daily_from_export

def trade_lists():
    fed = fed_days(load_calendar("/home/claude/news/news_usd.csv")); out = {}
    for name, pat, comm in (("OC_TSLA", "TSLA_M30", 0.00002), ("OC_US100", "US100.cash_M30", 0.0)):
        d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0])
        out[name] = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01", skip_days=fed)[["R", "stop_pct"]]
    # gold trend: Donchian 20/10, 2-ATR stop -> R per planned risk = R_atr / 2; booked on the exit day
    sr_diag.START = "2012-01-01"; g = sr_diag.load(); dd, atr = sr_diag.daily_atr(g)
    dly = g.groupby("nyd").agg(o=("open","first"), h=("high","max"), l=("low","min"), c=("close","last"), sp=("sp","mean")); dly["atr"] = atr; dly = dly.dropna()
    tr = donchian(dly, comm=0.000007); tr = tr[tr.day >= "2022-01-01"]
    idx = dly.index; exit_day = [idx[min(idx.get_loc(r.day) + int(r.days), len(idx) - 1)] for r in tr.itertuples()]
    out["GOLD_TREND"] = pd.DataFrame({"R": (tr.R / 2).values, "stop_pct": (2 * dly.atr.reindex(tr.day).values / dly.c.reindex(tr.day).values * 100)}, index=pd.DatetimeIndex(exit_day))
    # pre-FOMC drift on US100: long from the day-before 15:30 close to the FOMC-day 13:30 close, 1-ATR stop (never hit in sample)
    b = daily_from_export("US100.cash")
    import index_ideas  # noqa: reuse frame builder
    g2 = index_ideas.frame("US100.cash"); d2, atr2 = sr_diag.daily_atr(g2)
    c1530 = g2[g2.nym == 930].set_index("nyd"); c1330 = g2[g2.nym == 810].set_index("nyd")
    days = sorted(set(c1530.index) & set(c1330.index)); rows = []
    for i in range(1, len(days)):
        dprev, day = days[i-1], days[i]
        if day not in fed: continue
        A = atr2.get(day, np.nan)
        if not np.isfinite(A): continue
        e = c1530.close[dprev] + c1530.sp[dprev] / 2; x = c1330.close[day] - c1330.sp[day] / 2
        rows.append((day, (x - e - 0.0001 * e) / A, A / e * 100))
    out["PRE_FOMC"] = pd.DataFrame([(r, s) for _, r, s in rows], index=pd.DatetimeIndex([d for d, _, _ in rows]), columns=["R", "stop_pct"])
    return out

LEV = {"OC_TSLA": 1, "OC_US100": 15, "GOLD_TREND": 9, "PRE_FOMC": 15}

def daily(trades, names, risk, keep=1.0):
    parts = []
    for n in names:
        t = trades[n]; R = t.R - (1 - keep) * t.R.mean()
        allowed = np.minimum(risk, t.stop_pct / 100 * LEV[n]); parts.append((R * allowed).groupby(level=0).sum().rename(n))
    df = pd.concat(parts, axis=1, sort=True)
    cal = pd.bdate_range("2022-01-03", "2026-10-07")            # every weekday counts; idle days are zero-return days
    return df.reindex(cal).fillna(0).sum(axis=1)

def mc(ret, n=4000, block=10, max_days=250, seed=7):
    ret = np.asarray(ret); rng = np.random.default_rng(seed); res = []
    for _ in range(n):
        eq, days, phase, tgt, ok, fail = 1.0, 0, 1, 0.10, False, False
        pdays = 0
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
    out = {f"pass by {m}m": float(((r.ok) & (r.days <= 21 * m)).mean()) for m in (1, 2, 3, 4)}
    out["pass by 12m"] = float(r.ok.mean()); out["fail"] = float(r.fail.mean())
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

if __name__ == "__main__":
    T = trade_lists()
    for k, v in T.items(): print(k, len(v), "avgR %+.3f" % v.R.mean(), "stop%% median %.2f" % v.stop_pct.median())
    pd.to_pickle(T, "/home/claude/bt/trade_lists.pkl")
    mixes = {"OC TSLA+US100 (live)": ["OC_TSLA", "OC_US100"], "live + gold trend": ["OC_TSLA", "OC_US100", "GOLD_TREND"],
             "live + gold trend + pre-FOMC": ["OC_TSLA", "OC_US100", "GOLD_TREND", "PRE_FOMC"], "OC US100 only": ["OC_US100"],
             "OC TSLA only": ["OC_TSLA"], "gold trend only": ["GOLD_TREND"]}
    rows = []
    for mname, names in mixes.items():
        for risk in (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02):
            ret = daily(T, names, risk); m = mc(ret.values); s, pay = funded(ret.values)
            eq = (1 + ret).cumprod(); dd = (eq / eq.cummax() - 1).min()
            rows.append(dict(mix=mname, risk=f"{risk*100:.2f}%", **{k: round(v, 3) for k, v in m.items()}, hist_maxDD=round(dd * 100, 1),
                             avg_month=round(((1 + ret).groupby(ret.index.to_period("M")).prod() - 1).mean() * 100, 2), keep12m=round(s, 2), payout_pm=round(pay * 10000)))
            print(rows[-1], flush=True)
    df = pd.DataFrame(rows); df.to_csv("/home/claude/bt/scenarios.csv", index=False)
    # half-edge robustness for the live mix
    for risk in (0.005, 0.01):
        ret = daily(T, ["OC_TSLA", "OC_US100"], risk, keep=0.5); m = mc(ret.values)
        print("HALF EDGE live mix", f"{risk*100:.2f}%", {k: round(v, 3) for k, v in m.items()}, flush=True)
