#!/usr/bin/env python3
"""Load the MT5 economic calendar export (assets/ExportNews.mq5 -> news_usd.csv) and label trading days.

The export's times use a fixed UTC+3 clock: UTC = listed time - 3 hours (checked with the jobs report,
which shows 15:30 in US summer and 16:30 in US winter).

Usage:
    python news.py news_usd.csv [--start 2022-01-01]

In Python:
    from news import load_calendar, day_labels, fed_days
    cal = load_calendar("news_usd.csv")
    labels = day_labels(cal)          # {New York date: label}
    skip = fed_days(cal)              # set of Fed decision dates
"""
import argparse

import pandas as pd

BIG_830 = {"Nonfarm Payrolls", "CPI m/m", "Core CPI m/m"}


def load_calendar(path):
    n = pd.read_csv(path)
    n["utc"] = pd.to_datetime(n["server_time"], format="%Y.%m.%d %H:%M") - pd.Timedelta(hours=3)
    ny = n["utc"].dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    n["ny_day"] = ny.dt.tz_localize(None).dt.normalize()
    n["ny_hhmm"] = ny.dt.strftime("%H:%M")
    return n


def fed_days(cal):
    h = cal[cal.importance == "high"]
    return set(h[(h.ny_hhmm == "14:00") & h.event.str.contains("Interest Rate Decision", case=False)].ny_day)


def day_labels(cal, start=None):
    """Label each New York date by its most important US event (first match wins)."""
    h = cal[cal.importance == "high"]
    if start:
        h = h[h.ny_day >= pd.Timestamp(start)]
    fed = fed_days(h)
    cpi = set(h[h.event.isin({"CPI m/m", "Core CPI m/m"})].ny_day)
    jobs = set(h[h.event == "Nonfarm Payrolls"].ny_day)
    ten = set(h[h.ny_hhmm == "10:00"].ny_day)
    other = set(h[(h.ny_hhmm >= "08:00") & (h.ny_hhmm <= "16:00")].ny_day)
    labels = {}
    for d in sorted(fed | cpi | jobs | ten | other):
        labels[d] = ("Fed decision" if d in fed else "CPI" if d in cpi else "Jobs report" if d in jobs
                     else "10am release" if d in ten else "Other high-impact")
    return labels


def label_of(labels, day):
    return labels.get(pd.Timestamp(day).normalize(), "No high-impact US news")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--start", default=None)
    a = p.parse_args()
    cal = load_calendar(a.file)
    lab = day_labels(cal, a.start)
    print(f"{len(cal):,} events, {cal.ny_day.min().date()} to {cal.ny_day.max().date()}")
    print(pd.Series(lab).value_counts().to_string())
    nfp = cal[cal.event == "Nonfarm Payrolls"]
    print("Jobs report New York time (should be 08:30):", nfp.ny_hhmm.value_counts().to_dict())
