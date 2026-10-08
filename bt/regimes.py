"""Regime labels per New York day, all computed from information available before that day opens."""
import sys; sys.path.insert(0, "/home/claude/lab")
import numpy as np, pandas as pd
from news import load_calendar, day_labels

def daily_frame(b):
    g = b.groupby("nyd"); d = pd.DataFrame({"high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "open": g.open.first()})
    return d[d.index.weekday < 5]

def labels(b):
    d = daily_frame(b)
    pc = d.close.shift(1); tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean(); atr_pct = atr / d.close
    vol = np.where(atr_pct > atr_pct.rolling(250, min_periods=120).median(), "high vol", "low vol")
    ema = d.close.ewm(span=50, adjust=False).mean(); score = (d.close - ema) / atr
    trend = np.where(score > 1, "uptrend", np.where(score < -1, "downtrend", "range"))
    rng20 = (d.high.rolling(20).max() - d.low.rolling(20).min()) / atr
    comp = np.where(rng20 < rng20.rolling(250, min_periods=120).median(), "compressed", "expanded")
    yday = np.where(d.close > d.open, "prev day up", "prev day down")
    out = pd.DataFrame({"vol": vol, "trend": trend, "range20": comp, "prev": yday}, index=d.index).shift(1)   # known the next morning
    out["dow"] = out.index.weekday.map({0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"})
    cal = load_calendar("/home/claude/news/news_usd.csv"); lab = day_labels(cal)
    out["news"] = [lab.get(pd.Timestamp(x), "no big news") for x in out.index]
    return out.dropna()

def matrix(trades, labs, min_n=40):
    """trades: DataFrame with t (UTC) and R. Returns avg R, n, t-stat per regime value, plus early/late halves."""
    tr = trades.copy()
    tr["day"] = pd.DatetimeIndex(tr.t).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None).normalize()
    tr = tr.join(labs, on="day", how="inner")
    mid = tr.day.quantile(0.5)
    rows = []
    for col in ["vol", "trend", "range20", "prev", "dow", "news"]:
        for val, g in tr.groupby(col):
            if len(g) < min_n: continue
            e, l = g[g.day <= mid], g[g.day > mid]
            rows.append({"regime": f"{col} = {val}", "n": len(g), "avg R": round(g.R.mean(), 3), "t": round(g.R.mean() / g.R.std() * np.sqrt(len(g)), 1),
                         "early": round(e.R.mean(), 3) if len(e) >= 15 else None, "late": round(l.R.mean(), 3) if len(l) >= 15 else None})
    return pd.DataFrame(rows), tr
