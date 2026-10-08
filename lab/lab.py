#!/usr/bin/env python3
"""Backtest helpers for New York session strategies on FTMO data.

Usage:
    python lab.py EXPORT_M30.csv [--commission 0.00004] [--start 2022-01-01] [--skip-days days.txt]

    --commission  per side, as a fraction of position value (stocks 0.00004, indices 0, crypto 0.000325)
    --skip-days   optional file with one YYYY-MM-DD per line (e.g. Fed decision days) to leave out

In Python:
    from ftmo_data import load_export
    from lab import ny_session, opening_candle, stats, split_stats
    d = load_export("TSLA_M30_....csv")
    t = opening_candle(d, commission=0.00004, start="2022-01-01")
    print(stats(t.R)); print(split_stats(t.R, "2025-01-01"))

All results are in R: profit after costs divided by the money at risk (entry to stop).
"""
import argparse
import sys

import numpy as np
import pandas as pd

from ftmo_data import load_export, SERVER_MINUS_NY_HOURS


def ny_session(d, start=None, end=None, open_t="09:30", close_t="16:00"):
    """Regular New York session bars, adding `nyd` (New York date) and `nyt` (bar start time in New York, HH:MM)."""
    x = d.loc[start:end].copy() if (start or end) else d.copy()
    ny = x.index - pd.Timedelta(hours=SERVER_MINUS_NY_HOURS)
    x["nyd"] = ny.normalize()
    x["nyt"] = ny.strftime("%H:%M")
    return x[(x.nyt >= open_t) & (x.nyt < close_t)]


def full_days(session, bars=13):
    """Days with a complete session (13 x 30-min bars). Holidays and early closes drop out.
    Tip: build this from a stock's session and pass it to an index backtest, since index CFDs keep trading on early-close days."""
    n = session.groupby("nyd").size()
    return set(n[n == bars].index)


def opening_candle(d, first_bars=1, target_r=None, commission=0.0, cost_mult=1.0,
                   start=None, end=None, days=None, skip_days=None, bars_per_day=13):
    """The opening-candle rule on 30-min bars.

    At the open of bar `first_bars` (10:00 New York with first_bars=1), trade in the direction of the
    opening candle(s); stop at their far end; exit at target_r x risk (None = no target) or at the close
    of the last session bar (16:00 New York). Costs: the entry bar's spread x cost_mult + commission per side.
    Returns one row per trade: dir, R, stop_pct, exit reason.
    """
    s = ny_session(d, start, end)
    if days is None:
        days = full_days(s, bars_per_day)
    skip = set(pd.to_datetime(list(skip_days))) if skip_days is not None else set()
    out = []
    for day, b in s.groupby("nyd"):
        if day not in days or day in skip or len(b) != bars_per_day:
            continue
        f = b.iloc[:first_bars]
        o, c, hi, lo = f.open.iloc[0], f.close.iloc[-1], f.high.max(), f.low.min()
        if c == o:
            continue
        dr = 1 if c > o else -1
        rest = b.iloc[first_bars:]
        entry = rest.open.iloc[0]
        stop = lo if dr == 1 else hi
        risk = (entry - stop) * dr
        if risk <= 0:
            continue
        tgt = entry + dr * target_r * risk if target_r else None
        exit_px, why = rest.close.iloc[-1], "close"
        for _, r in rest.iterrows():
            if dr == 1:
                if r.low <= stop:
                    exit_px, why = min(stop, r.open), "stop"; break
                if tgt is not None and r.high >= tgt:
                    exit_px, why = max(tgt, r.open), "target"; break
            else:
                if r.high >= stop:
                    exit_px, why = max(stop, r.open), "stop"; break
                if tgt is not None and r.low <= tgt:
                    exit_px, why = min(tgt, r.open), "target"; break
        cost = cost_mult * rest.sp.iloc[0] + commission * (entry + exit_px)
        out.append((day, dr, (dr * (exit_px - entry) - cost) / risk, risk / entry * 100, why))
    return pd.DataFrame(out, columns=["day", "dir", "R", "stop_pct", "why"]).set_index("day")


def stats(R, label=""):
    R = pd.Series(R).dropna()
    if len(R) < 3:
        return {"version": label, "trades": len(R)}
    by_year = R.groupby(R.index.year).mean()
    return {"version": label, "trades": len(R), "win%": round((R > 0).mean() * 100),
            "avg R": round(R.mean(), 3), "t": round(R.mean() / R.std() * np.sqrt(len(R)), 1),
            "positive years": f"{(by_year > 0).sum()}/{len(by_year)}",
            "by year": " ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in by_year.items())}


def split_stats(R, cut):
    """Average R before and after `cut` (choose on the first part, check on the second)."""
    R = pd.Series(R).dropna()
    a, b = R.loc[:pd.Timestamp(cut) - pd.Timedelta(days=1)], R.loc[cut:]
    return {"before": round(a.mean(), 3), "n before": len(a), "after": round(b.mean(), 3), "n after": len(b)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Opening-candle backtest on an FTMO M30 export")
    p.add_argument("file")
    p.add_argument("--commission", type=float, default=0.0)
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--skip-days", default=None)
    p.add_argument("--cut", default="2025-01-01")
    a = p.parse_args()
    d = load_export(a.file)
    skip = None
    if a.skip_days:
        skip = [l.strip() for l in open(a.skip_days) if l.strip()]
    t = opening_candle(d, commission=a.commission, start=a.start, skip_days=skip)
    print(d.attrs["symbol"], stats(t.R, "opening candle"))
    print("split at", a.cut, split_stats(t.R, a.cut))
    print("typical stop %:", round(t.stop_pct.median(), 2))
