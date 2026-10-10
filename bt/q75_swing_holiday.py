"""Log #75 / backlog #32 — pre-holiday effect (Ariel 1990; Quantpedia), pre-registered, run unchanged.

Rule: long at the cash close of the last trading day before an exchange holiday, out at the cash close of the first trading day
after it (consecutive closed weekdays = one holiday). No stop. R = P/L after costs / ATR(14) of daily bars known at entry (the
lab's unit for no-stop daily rules, log #4 / #7). Costs: spread x 1.2 at entry + commission x (|entry| + |exit|) + swap for every
17:00 New York rollover held (x3 on the triple day).
- US: NYSE calendar (pandas_market_calendars), every US index CFD (US100, US500, US30, US2000) and every US stock CFD. The cash
  close is the NYSE close of that day (16:00 New York, 13:00 on early-close days). The unscheduled Hurricane Sandy closure
  (2012-10-29/30) is excluded (not known at the prior close); the mourning days (2018-12-05, 2025-01-09) count (announced days ahead).
- Other indices (EU50, GER40, FRA40, SPN35, N25, UK100, JP225, HK50, AUS200, DXY): their own holidays as the data shows them = a
  weekday on which the index has no bar inside its local cash session (intraday era) or no D1 bar (D1-only era), in clusters of
  at most 4 weekdays (longer = a data hole). Deviation from 'while the rest of the market traded': market-wide closures (Dec 25,
  Jan 1, when FX is shut too) count as holidays, as they do on the NYSE side; the detected dates are in _calendar.csv.
  Cash close = the local session close (universe.SESSIONS).
- Close prices: the last 5-minute bar ending at the cash close (at most 15 minutes early) where the export is really intraday
  (from xgrid.full_intraday_start); before that the export's D1 close (server day = 17:00 New York, so 1 hour after the US cash
  close for index CFDs). A trade uses one source for both ends (M5 if both closes exist, else D1).
- Baseline: every other trading day of the same symbol, same 1-day close-to-close hold, same costs. Per pre-holiday trade the
  baseline is the mean of that symbol's other-day trades in the same calendar year (paired by regime); the plain all-years
  other-day mean is reported too.
Output: results/q75_swing_holiday_trades.csv (every pre-holiday trade), _years.csv (cells pre_holiday / other_days),
_cells.csv (per symbol).
"""
import sys, os, time
import numpy as np, pandas as pd

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
U = C.U

OTHER_IDX = ["EU50.cash", "GER40.cash", "FRA40.cash", "SPN35.cash", "N25.cash", "UK100.cash", "JP225.cash", "HK50.cash",
             "AUS200.cash", "DXY.cash"]
LOCAL = {"EU50.cash": "eu_cash", "GER40.cash": "eu_cash", "FRA40.cash": "eu_cash", "SPN35.cash": "eu_cash", "N25.cash": "eu_cash",
         "UK100.cash": "uk_cash", "JP225.cash": "jp_cash", "HK50.cash": "hk_cash", "AUS200.cash": "au_cash", "DXY.cash": "us_cash"}
M15 = 15 * 60 * C.NS


def nyse_calendar():
    import pandas_market_calendars as mcal
    sch = mcal.get_calendar("NYSE").schedule(start_date="2006-01-01", end_date="2026-12-31")
    days = pd.DatetimeIndex(sch.index).tz_localize(None).normalize()
    close = C.ns(pd.DatetimeIndex(sch.market_close).tz_convert("UTC").tz_localize(None))
    bdays = pd.bdate_range(days[0], days[-1])
    hol = bdays.difference(days)
    sandy = pd.DatetimeIndex(["2012-10-29", "2012-10-30"])
    return days, close, hol.difference(sandy), sandy


def event_flags(days, hol, excluded):
    """For trading days i -> i+1: 'pre' if a holiday weekday lies strictly between them, 'normal' if only weekend days do,
    'skip' otherwise (unscheduled closures)."""
    kind = np.empty(len(days) - 1, dtype=object)
    hol = set(hol); exc = set(excluded)
    for i in range(len(days) - 1):
        between = pd.bdate_range(days[i] + pd.Timedelta(days=1), days[i + 1] - pd.Timedelta(days=1))
        if len(between) == 0: kind[i] = "normal"
        elif any(b in exc for b in between): kind[i] = "skip"
        elif all(b in hol for b in between) and len(between) <= 4: kind[i] = "pre"
        else: kind[i] = "skip"
    return kind


def d1_table(sym, cat, intra, rel):
    d1 = C.load_d1(sym, cat, intra, rel)
    srv = C.to_server(d1.index).normalize()
    pc = d1.close.shift(1)
    tr = pd.concat([d1.high - d1.low, (d1.high - pc).abs(), (d1.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)                         # known before the day's close
    end = C.ns(d1.index) + 24 * C.H_NS                            # the server day ends 24 h after it starts
    T = pd.DataFrame({"close": d1.close.values, "sp": d1.sp.values, "atr": atr.values, "t_end": end}, index=srv)
    return T[~T.index.duplicated(keep="last")]


def m5_closes(intra, close_ns):
    """Close / spread of the last intraday bar starting in [T - 15 min, T) for each target time T (NaN if none)."""
    t = C.ns(intra.index)
    j = np.searchsorted(t, close_ns, side="left") - 1
    ok = (j >= 0) & (t[np.clip(j, 0, None)] >= close_ns - M15)
    c = np.where(ok, intra.close.values[np.clip(j, 0, None)], np.nan)
    s = np.where(ok, intra.sp.values[np.clip(j, 0, None)], np.nan)
    return c, s


def build_trades(sym, days, close_ns, kind, D1, intra, sw, comm):
    """days: trading days (local dates), close_ns: cash close time (UTC ns) per day, kind[i] for i -> i+1."""
    m5c, m5s = (m5_closes(intra, close_ns) if intra is not None else (np.full(len(days), np.nan),) * 2)
    d1 = D1.reindex(days)
    rows = []
    for i in np.flatnonzero(kind != "skip"):
        j = i + 1
        atr = d1.atr.values[i]
        if not (np.isfinite(atr) and atr > 0): continue
        if np.isfinite(m5c[i]) and np.isfinite(m5c[j]):
            E, X, sp, src, t_in, t_out = m5c[i], m5c[j], m5s[i], "m5", close_ns[i], close_ns[j]
        elif np.isfinite(d1.close.values[i]) and np.isfinite(d1.close.values[j]):
            E, X, sp, src, t_in, t_out = d1.close.values[i], d1.close.values[j], d1.sp.values[i], "d1", d1.t_end.values[i], d1.t_end.values[j]
        else:
            continue
        nights = float(sw.nights([t_in], [t_out])[0])
        cost = 1.2 * sp + comm * (abs(E) + abs(X)) + nights * float(sw.per_night(1, E))
        rows.append((days[i], days[j], kind[i], src, E, X, (X - E - cost) / atr, (X - E) / atr, nights))
    return pd.DataFrame(rows, columns=["day", "exit_day", "kind", "src", "entry", "exit", "R", "R_gross", "nights"])


def local_days(sym, intra, D1, ref_days):
    """Trading days and holidays of a non-US index from its own data. Returns (days, close_ns, kind)."""
    tz, op, cl = U.SESSIONS[LOCAL[sym]]
    start = D1.index.min(); end = D1.index.max()
    cand = pd.bdate_range(start, end)
    loc = cand.tz_localize(None)
    o_ns = C.ns(pd.DatetimeIndex([pd.Timestamp(f"{d.date()} {op}") for d in loc]).tz_localize(tz, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None))
    c_ns = C.ns(pd.DatetimeIndex([pd.Timestamp(f"{d.date()} {cl}") for d in loc]).tz_localize(tz, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None))
    traded = np.zeros(len(loc), bool)
    i_start = C.ns(intra.index)[0] if intra is not None else np.iinfo(np.int64).max
    if intra is not None:
        t = C.ns(intra.index)
        a = np.searchsorted(t, o_ns, "left"); b = np.searchsorted(t, c_ns, "left")
        traded = b > a
    d1_has = loc.isin(D1.index)
    use_intra = o_ns >= i_start
    traded = np.where(use_intra, traded, d1_has)
    days = loc[traded]; close_ns = c_ns[traded]
    kind = np.empty(max(len(days) - 1, 0), dtype=object)
    for i in range(len(days) - 1):
        between = pd.bdate_range(days[i] + pd.Timedelta(days=1), days[i + 1] - pd.Timedelta(days=1))
        if len(between) == 0: kind[i] = "normal"
        elif len(between) <= 4: kind[i] = "pre"           # 1-4 closed weekdays: a holiday (own, or market-wide like Dec 25)
        else: kind[i] = "skip"                             # longer: a data hole
    return days, close_ns, kind


def main():
    cat = U.catalog(); t0 = time.time()
    pre = os.path.join(C.RES, "q75_swing_holiday")
    for suf in ("_trades.csv", "_years.csv", "_cells.csv", "_calendar.csv"):
        if os.path.exists(pre + suf): os.remove(pre + suf)
    ndays, nclose, nhol, sandy = nyse_calendar()
    nkind = event_flags(ndays, nhol, sandy)
    eu = C.load_d1("EURUSD", cat); ref_days = pd.DatetimeIndex(C.to_server(eu.index).normalize()).unique()
    syms = [s for s in C.symbols(cat) if U.group_of(s) in ("stock", "us_index")] + OTHER_IDX
    cal_rows = []
    for sym in syms:
        grp = U.group_of(sym); comm = U.commission_of(sym)
        intra, btf, rel = C.load_intraday(sym, cat)
        D1 = d1_table(sym, cat, intra, rel)
        p_ref = D1.close.iloc[-1]
        sw = C.Swaps(sym, C.ns(pd.DatetimeIndex([D1.index.min() - pd.Timedelta(days=5)]))[0],
                     C.ns(pd.DatetimeIndex([D1.index.max() + pd.Timedelta(days=5)]))[0], p_ref)
        if sym in OTHER_IDX:
            days, close_ns, kind = local_days(sym, intra, D1, ref_days)
            cal = "own data"
        else:
            m = (ndays >= D1.index.min()) & (ndays <= D1.index.max())
            idx = np.flatnonzero(m)
            days = ndays[idx]; close_ns = nclose[idx]; kind = nkind[idx[:-1]]
            cal = "NYSE"
        if len(days) < 50: continue
        T = build_trades(sym, days, close_ns, kind, D1, intra, sw, comm)
        if not len(T): continue
        T["year"] = pd.DatetimeIndex(T.day).year
        oth = T[T.kind == "normal"]; ph = T[T.kind == "pre"].copy()
        ymean = oth.groupby("year").R.mean()
        ph["base"] = ph.year.map(ymean).values
        ph["base_all"] = oth.R.mean()
        ph["symbol"] = sym; ph["group"] = grp; ph["calendar"] = cal
        C.append_csv(ph.drop(columns=["year"]), pre + "_trades.csv")
        t_ph = C.ns(pd.DatetimeIndex(ph.day)); t_ot = C.ns(pd.DatetimeIndex(oth.day))
        Y = C.year_rows(ph.R.values, t_ph, ph.base.values, idea="holiday", symbol=sym, group=grp, tf="D1", cell="pre_holiday")
        Y += C.year_rows(oth.R.values, t_ot, None, idea="holiday", symbol=sym, group=grp, tf="D1", cell="other_days")
        C.append_csv(pd.DataFrame(Y), pre + "_years.csv")
        st = C.stats_from_years(pd.DataFrame([r for r in Y if r["cell"] == "pre_holiday"]))
        st.pop("by_year", None)
        C.append_csv(pd.DataFrame([dict(symbol=sym, group=grp, calendar=cal, events=len(ph), m5_share=(ph.src == "m5").mean(),
                                        first=str(pd.Timestamp(ph.day.min()).date()) if len(ph) else "",
                                        m5_from=str(pd.Timestamp(ph.day[ph.src == "m5"].min()).date()) if (ph.src == "m5").any() else "",
                                        **st, other_mean=oth.R.mean(), other_n=len(oth), gross_mean=ph.R_gross.mean(),
                                        nights_mean=ph.nights.mean())]), pre + "_cells.csv")
        print(f"  {sym:11s} [{cal}] " + C.fmt_stats(st) + f" | other days {oth.R.mean():+.3f} (n={len(oth)}) m5 {np.mean(ph.src == 'm5'):.0%}",
              flush=True)
        if sym in OTHER_IDX:
            hl = sorted({str(b.date()) for i in np.flatnonzero(kind == "pre")
                         for b in pd.bdate_range(days[i] + pd.Timedelta(days=1), days[i + 1] - pd.Timedelta(days=1))})
            cal_rows.append(dict(symbol=sym, holidays=len(hl), per_year=len(hl) / max(len(set(d[:4] for d in hl)), 1),
                                 list=" ".join(hl)))
    if cal_rows: pd.DataFrame(cal_rows).to_csv(pre + "_calendar.csv", index=False)
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
