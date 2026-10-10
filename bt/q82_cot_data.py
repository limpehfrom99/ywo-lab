"""Log #82 data layer: CFTC Commitments of Traders, release schedule, COT index signals, MT5-calendar CFTC series, synthetic
10-year Treasury bond price.  Written for the Disaggregated Futures-Only report (commodities); the Legacy report (forex, indices,
bonds) plugs into the same functions through LEGACY_GROUPS / load_report(..., kind="legacy").

All files are read with pandas only (untrusted data).

COT index (Larry Williams / Bernd Skorupinski): 100 x (net - min over the last N reports) / (max - min), the current report
included, N reports required (no partial windows); max == min -> undefined.  Groups (Disaggregated):
  comm  = producer/merchant + swap dealers, net = long - short                   (index used as is: high = bullish)
  large = managed money + other reportables, net = long - short                 (contrarian: 100 - index)
  small = non-reportables, net = long - short                                    (contrarian: 100 - index)
Spread positions are equal long and short and drop out of net.

Availability: a report (as-of Tuesday) is public at its release time (normally Friday 15:30 New York).  Release times come from the
MT5 calendar (2012+): its "CFTC Gold Non-Commercial Net Positions" value equals the Disaggregated gold managed money + other
reportables net to +-0.05k, so each calendar release is matched to its as-of date by value (crude oil gives the same matching).
Reports with no calendar match (2006-2011, a few later weeks) get the rule: Friday 15:30 New York of the as-of week, the next
business day (Monday) when a US federal holiday falls on Wednesday-Friday of that week.
Skipped (no signal, still part of the index history): reports inside SKIP_WINDOWS (as-of dates whose release was delayed: 2013,
2018-19 and 2025 shutdowns, Feb-Mar 2023 ION cyber incident) and any report released > 8.5 days after its as-of date."""
import glob
import functools

import numpy as np
import pandas as pd

COT_FILES = {
    "disagg": ["/home/claude/data/cot_raw/*/F_Disagg06_16.txt", "/home/claude/data/cot_raw/*/f_year.txt"],
    "legacy": [],                                   # fill in when the Legacy history arrives (e.g. FUT86_16.txt + annual.txt)
}
NEWS = "/home/claude/news/news_usd.csv"
DGS10 = "/root/.claude/uploads/0f9104a2-35fd-5993-8aaf-c31d50623674/60157393-DGS10.csv"

# CFTC_Contract_Market_Code -> FTMO symbol (log #82)
DISAGG_MAP = {
    "088691": "XAUUSD", "084691": "XAGUSD", "076651": "XPTUSD", "075651": "XPDUSD", "085692": "XCUUSD",
    "067651": "USOIL.cash", "06765T": "UKOIL.cash", "023651": "NATGAS.cash",
    "001602": "WHEAT.c", "002602": "CORN.c", "005602": "SOYBEAN.c",
    "080732": "SUGAR.c", "083731": "COFFEE.c", "073732": "COCOA.c", "033661": "COTTON.c",
}
MARKET_GROUP = {"XAUUSD": "metals", "XAGUSD": "metals", "XPTUSD": "metals", "XPDUSD": "metals", "XCUUSD": "metals",
                "USOIL.cash": "energy", "UKOIL.cash": "energy", "NATGAS.cash": "energy",
                "WHEAT.c": "grains", "CORN.c": "grains", "SOYBEAN.c": "grains",
                "SUGAR.c": "softs", "COFFEE.c": "softs", "COCOA.c": "softs", "COTTON.c": "softs",
                "US500.cash": "us_index", "US100.cash": "us_index"}

# group -> (long columns, short columns, contrarian)
DISAGG_GROUPS = {
    "comm": (["Prod_Merc_Positions_Long_All", "Swap_Positions_Long_All"],
             ["Prod_Merc_Positions_Short_All", "Swap__Positions_Short_All"], False),
    "large": (["M_Money_Positions_Long_All", "Other_Rept_Positions_Long_All"],
              ["M_Money_Positions_Short_All", "Other_Rept_Positions_Short_All"], True),
    "small": (["NonRept_Positions_Long_All"], ["NonRept_Positions_Short_All"], True),
}
LEGACY_GROUPS = {
    "comm": (["Comm_Positions_Long_All"], ["Comm_Positions_Short_All"], False),
    "large": (["NonComm_Positions_Long_All"], ["NonComm_Positions_Short_All"], True),
    "small": (["NonRept_Positions_Long_All"], ["NonRept_Positions_Short_All"], True),
}
GROUPS = {"disagg": DISAGG_GROUPS, "legacy": LEGACY_GROUPS}
# as-of windows whose reports came out late (no signal from them): the 2013 shutdown backlog (the MT5 calendar shows back-filled
# Friday times), the 2018-19 shutdown (calendar catch-up 1 Feb - 5 Mar 2019), the ION cyber incident (Feb-Mar 2023: calendar
# releases 24 Feb - 10 Mar; 7 Feb, 28 Feb and 7 Mar have no calendar match) and the 2025 shutdown (catch-up 19 Nov - 23 Dec 2025).
SKIP_WINDOWS = [(pd.Timestamp(a), pd.Timestamp(b)) for a, b in
                [("2013-10-01", "2013-11-12"), ("2018-12-24", "2019-02-26"), ("2023-01-31", "2023-03-07"), ("2025-09-30", "2025-12-16")]]
NY = "America/New_York"


# ------------------------------------------------------------------------------------------------------------ reports
@functools.lru_cache(maxsize=4)
def load_report(kind="disagg"):
    """All rows of a COT report history: columns code, name, asof (Timestamp) + every position column the groups use + OI."""
    cols = sorted({c for g in GROUPS[kind].values() for c in g[0] + g[1]})
    base = ["Market_and_Exchange_Names", "Report_Date_as_YYYY-MM-DD", "CFTC_Contract_Market_Code", "Open_Interest_All"]
    files = [f for pat in COT_FILES[kind] for f in sorted(glob.glob(pat))]
    if not files: raise FileNotFoundError(f"no {kind} COT files")
    parts = [pd.read_csv(f, usecols=base + cols, dtype={"CFTC_Contract_Market_Code": str}, low_memory=False) for f in files]
    D = pd.concat(parts, ignore_index=True)
    D["asof"] = pd.to_datetime(D["Report_Date_as_YYYY-MM-DD"])
    D["code"] = D["CFTC_Contract_Market_Code"].str.strip()
    D = D.rename(columns={"Market_and_Exchange_Names": "name", "Open_Interest_All": "oi"})
    for c in cols + ["oi"]: D[c] = pd.to_numeric(D[c], errors="coerce")
    D = D.drop(columns=["Report_Date_as_YYYY-MM-DD", "CFTC_Contract_Market_Code"])
    return D.drop_duplicates(["code", "asof"]).sort_values(["code", "asof"]).reset_index(drop=True)


def market_report(code, kind="disagg"):
    D = load_report(kind)
    return D[D.code == code].set_index("asof").sort_index()


def net_position(rep, group, kind="disagg"):
    lo, sh, _ = GROUPS[kind][group]
    return rep[lo].sum(axis=1) - rep[sh].sum(axis=1)


def cot_index(net, N):
    """100 x (net - min) / (max - min) over the last N reports including the current one."""
    lo = net.rolling(N, min_periods=N).min(); hi = net.rolling(N, min_periods=N).max()
    rng = (hi - lo).where(hi > lo)
    return 100.0 * (net - lo) / rng


def cot_signal(rep, group, N, hi_thr, lo_thr, kind="disagg", groups=None):
    """The reusable COT rule: rep = one market's weekly report (index = as-of date, the report's position columns), group name,
    lookback N (reports), thresholds (80/20 or 90/10). Returns a DataFrame indexed by as-of date with net, idx (raw COT index),
    bias_idx (contrarian groups inverted) and side (+1 bullish if bias_idx >= hi_thr, -1 bearish if <= lo_thr, else 0)."""
    g = (groups or GROUPS[kind])[group]
    net = rep[g[0]].sum(axis=1) - rep[g[1]].sum(axis=1)
    idx = cot_index(net, N)
    b = 100.0 - idx if g[2] else idx
    side = np.where(b >= hi_thr, 1, np.where(b <= lo_thr, -1, 0))
    side = np.where(b.isna(), 0, side)
    return pd.DataFrame({"net": net, "idx": idx, "bias_idx": b, "side": side.astype(int)}, index=rep.index)


def series_signal(values, N, hi_thr, lo_thr, contrarian=True):
    """Same rule on a bare net-position series (the MT5 calendar's non-commercial net, i.e. large speculators)."""
    idx = cot_index(values, N)
    b = 100.0 - idx if contrarian else idx
    side = np.where(b >= hi_thr, 1, np.where(b <= lo_thr, -1, 0)); side = np.where(b.isna(), 0, side)
    return pd.DataFrame({"net": values, "idx": idx, "bias_idx": b, "side": side.astype(int)}, index=values.index)


# ------------------------------------------------------------------------------------------------------------ calendar
@functools.lru_cache(maxsize=1)
def calendar():
    n = pd.read_csv(NEWS)
    c = n[n.event.astype(str).str.startswith("CFTC")].copy()
    c["t_utc"] = pd.to_datetime(c.server_time, format="%Y.%m.%d %H:%M") - pd.Timedelta(hours=3)     # calendar clock = UTC+3
    c["actual"] = pd.to_numeric(c.actual, errors="coerce")
    c = c[c.actual.notna()].drop_duplicates(["event", "t_utc"]).sort_values(["event", "t_utc"])
    return c[["event", "t_utc", "actual"]].reset_index(drop=True)


def calendar_series(key):
    """key in {'S&P 500', 'Nasdaq 100', 'Gold', 'Crude Oil'} -> Series value (thousand contracts) indexed by release time (UTC)."""
    c = calendar(); c = c[c.event == f"CFTC {key} Non-Commercial Net Positions"]
    return pd.Series(c.actual.values, index=pd.DatetimeIndex(c.t_utc.values), name=key)


def _match_calendar(code, key, tol=0.051):
    """Match each calendar release to an as-of date by value (large-spec net of the Disaggregated report, in thousands).
    Returns Series as-of -> release time (UTC)."""
    rep = market_report(code)
    v = (net_position(rep, "large") / 1000.0).round(3)
    cal = calendar_series(key)
    asof = v.index.values; vals = v.values; out = {}; last = -1
    for t, x in cal.items():
        lo = max(np.searchsorted(asof, np.datetime64(t - pd.Timedelta(days=150))), last + 1)
        hi = np.searchsorted(asof, np.datetime64(t.normalize() - pd.Timedelta(days=2)), side="right")
        cand = [j for j in range(lo, hi) if abs(vals[j] - x) <= tol]
        if not cand: continue
        j = cand[0]                    # reports are released in as-of order: the earliest report after the last matched one
        last = j; out[pd.Timestamp(asof[j])] = t
    return pd.Series(out).sort_index()


def _rule_release(asof):
    """Friday 15:30 New York of the as-of week; Monday (next business day) if a US federal holiday falls on Wed-Fri of that week."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = set(USFederalHolidayCalendar().holidays("2005-01-01", "2027-12-31").normalize())
    fri = asof + pd.Timedelta(days=(4 - asof.weekday()) % 7)
    d = fri
    if any((fri - pd.Timedelta(days=k)) in hol for k in (0, 1, 2)):
        d = fri + pd.Timedelta(days=3)
        while d in hol or d.weekday() >= 5: d += pd.Timedelta(days=1)
    return pd.Timestamp(d.strftime("%Y-%m-%d") + " 15:30").tz_localize(NY).tz_convert("UTC").tz_localize(None)


@functools.lru_cache(maxsize=1)
def release_schedule():
    """DataFrame indexed by as-of date (every as-of date of the Disaggregated report): release (UTC-naive), source
    ('calendar'|'rule'), delay_days, skip (bool), crude_agrees (bool or NaN)."""
    gold = _match_calendar("088691", "Gold"); crude = _match_calendar("067651", "Crude Oil")
    asof = pd.DatetimeIndex(sorted(load_report("disagg")["asof"].unique()))
    rows = []
    for a in asof:
        if a in gold.index and a in crude.index: r, src = max(gold[a], crude[a]), "calendar"     # one week disagrees: take the later
        elif a in gold.index: r, src = gold[a], "calendar"
        elif a in crude.index: r, src = crude[a], "calendar_crude"
        else: r, src = _rule_release(a), "rule"
        agree = (crude[a] == gold[a]) if (a in gold.index and a in crude.index) else np.nan
        delay = (r - a).total_seconds() / 86400.0
        skip = bool(delay > 8.5) or any(w0 <= a <= w1 for w0, w1 in SKIP_WINDOWS)
        rows.append(dict(asof=a, release=r, source=src, delay_days=delay, skip=skip, crude_agrees=agree))
    return pd.DataFrame(rows).set_index("asof")


def calendar_release_asof(key):
    """For an MT5 calendar CFTC series: DataFrame indexed by release time with value, the matched as-of date (same release time as
    the gold/crude match; else the latest as-of <= release - 3 days) and the skip flag."""
    s = calendar_series(key); R = release_schedule()
    by_rel = pd.Series(R.index, index=R.release)
    by_rel = by_rel[~by_rel.index.duplicated()]
    rows = []
    for t, v in s.items():
        if t in by_rel.index: a = by_rel[t]
        else:
            k = np.searchsorted(R.index.values, np.datetime64(t.normalize() - pd.Timedelta(days=3)), side="right") - 1
            a = R.index[k]
        rows.append(dict(release=t, value=v, asof=a, skip=bool(R.loc[a, "skip"]) if a in R.index else False))
    return pd.DataFrame(rows).set_index("release")


# ------------------------------------------------------------------------------------------------------------ bonds
@functools.lru_cache(maxsize=1)
def bond_price():
    """Synthetic 10-year Treasury price (the ZB1! reference): 100 / (1 + y/200)^20 with y = FRED DGS10 in %, daily, holidays
    forward-filled. Index = calendar date (New York), every day from the first observation (so any market's date finds a value)."""
    b = pd.read_csv(DGS10)
    b["d"] = pd.to_datetime(b.observation_date); b["y"] = pd.to_numeric(b.DGS10, errors="coerce")
    s = b.set_index("d").y
    full = pd.date_range(s.index.min(), s.index.max(), freq="D")
    y = s.reindex(full).ffill()
    return (100.0 / (1.0 + y / 200.0) ** 20).rename("BOND")
