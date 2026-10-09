"""Regime conditioning for the selected cells only (to keep the number of tests small).

Labels, all known before the trade (computed from the symbol's daily bars up to the previous day):
  vol   : 14-day ATR % of price above / below its 250-day median
  trend : previous close above / below the 200-day average; and whether the trade goes with that trend
  dow   : weekday
  news  : US high-impact day (Fed, CPI, jobs, other 8:30/10:00 release) vs none (US sessions only)
Rule (fixed): a filter value is adopted on in-sample data if keeping only it raises avg R by >= 0.03 and keeps >= 40% of
the trades; it is confirmed if the same subset also beats the unfiltered cell out of sample.
"""
import os, sys, pickle
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "lab"))
from universe import catalog, daily_bars  # noqa: E402
from evaluate import CUT, tstat  # noqa: E402
from news import load_calendar, day_labels  # noqa: E402

NEWS_CSV = next((p for p in ("/home/claude/news/news_usd.csv", os.path.join(HERE, "..", "data", "news", "news_usd.csv")) if os.path.exists(p)), "")


def labels_for(sym, intraday=None, cat=None):
    D = daily_bars(sym, cat or catalog(), intraday=intraday)
    if D is None: return None
    c = D.close; atrp = D.atr / c
    lab = pd.DataFrame(index=D.index)
    lab["vol"] = np.where(atrp > atrp.rolling(250, min_periods=120).median(), "high vol", "low vol")
    lab["trend_up"] = c > c.rolling(200).mean()
    lab = lab.shift(1).dropna()                                   # known before the day starts
    lab.index = lab.index.normalize()
    return lab


def condition(tr, lab, news=None):
    t = tr.copy(); t["day"] = pd.DatetimeIndex(t.day).normalize()
    t = t.join(lab, on="day", how="inner")
    if len(t) == 0: return pd.DataFrame()
    t["trend"] = np.where(t.trend_up, "uptrend", "downtrend")
    if "d" in t and (t.d != 0).any():
        t["with_trend"] = np.where((t.d == 1) == t.trend_up, "with trend", "against trend")
    t["dow"] = pd.DatetimeIndex(t.day).day_name().str[:3]
    if news is not None:
        t["news"] = [news.get(x, "no big news") for x in t.day]
    is_ = t.day < CUT; base_is, base_oos = t.R[is_].mean(), t.R[~is_].mean()
    rows = []
    for col in [c for c in ("vol", "trend", "with_trend", "dow", "news") if c in t]:
        for val, g in t.groupby(col):
            gi, go = g[g.day < CUT], g[g.day >= CUT]
            if len(gi) < 30: continue
            adopted = (gi.R.mean() - base_is >= 0.03) and (len(gi) >= 0.4 * is_.sum())
            rows.append(dict(filter=f"{col} = {val}", n_is=len(gi), avg_is=gi.R.mean(), t_is=tstat(gi.R), base_is=base_is,
                             n_oos=len(go), avg_oos=go.R.mean() if len(go) else np.nan, base_oos=base_oos, adopted=adopted,
                             confirmed=bool(adopted and len(go) >= 20 and go.R.mean() > base_oos)))
    return pd.DataFrame(rows)


def run(keys, trades):
    cal = load_calendar(NEWS_CSV) if os.path.exists(NEWS_CSV) else None
    news = {pd.Timestamp(k): v for k, v in day_labels(cal).items()} if cal is not None else None
    out = []; cache = {}
    for k in keys:
        sym = k[1]
        if sym not in cache:
            from run_battery import intraday_frame
            cat = catalog(); d, _ = intraday_frame(sym, cat, dry=True)
            cache[sym] = labels_for(sym, intraday=d, cat=cat)
        lab = cache[sym]
        if lab is None: continue
        r = condition(trades[k], lab, news if k[2] in ("us_cash", "ny_fx", "nymex") else None)
        if len(r): r.insert(0, "cell", "|".join(k[1:])); out.append(r)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


if __name__ == "__main__":
    cells = pd.read_csv(os.path.join(HERE, "..", "results", "battery_cells.csv"))
    trades = pickle.load(open("/home/claude/bt/battery_trades.pkl", "rb"))
    v = sys.argv[1].split(",") if len(sys.argv) > 1 else ["SURVIVOR", "WATCH"]
    keys = [(r.kind, r.symbol, r.session, r.rule) for r in cells[cells.verdict.isin(v)].itertuples()]
    res = run([k for k in keys if k in trades], trades)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    print(res.round(3).to_string(index=False) if len(res) else "nothing")
    if len(res): res.to_csv(os.path.join(HERE, "..", "results", "battery_conditions.csv"), index=False, float_format="%.4f")
