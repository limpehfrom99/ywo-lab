"""RedNote "熊猫聊交易系统" (Coach Panda), 2026-10-09: "如何判断牛市来了 / 你有没有陷入别人设下的牛熊陷阱". A talk, no rules. Its three
claims, turned into tests fixed before running (daily bars, signal at the close, entry at the next open):
  A. "The bull signal is not rising but not falling — dips get bought" (跌不动才是真强):
     dip-bought day = the day trades >= 0.5 ATR below its open but closes in the top third of its range.
     Trade: buy the next open, exit at the close 5 days later, 2-ATR stop. Also only when above the 200-day average.
  B. "Price grinds up in a channel; pullbacks stay shallow": above the 200-day average and the deepest close-to-close pullback
     from the 20-day high is <= 1.5 ATR. Trade: buy the next open, hold 20 days, 3-ATR stop.
  C. "Bad news can't push it down" (US indices): on a US high-impact news day the 9:30-10:00 candle falls >= 0.25 ATR but the
     day closes above its open -> buy the next open, hold 5 days. Compared with the other news days.
  D. "How you exit decides what you make" (会卖才是师傅): the same entries (close above the 20-day high, long) with 7 exits:
     chandelier 2/3/4 ATR from the highest close, 10-day-low exit, close below the 50-day average, fixed 20 and 60 days.
     Initial stop 2 ATR for all; R = P&L / (2 ATR at entry).
Costs: spread + commission + swap per night (quant/universe.py; swap assumed 5%/yr long on CFDs, 1%/yr on gold — no spec sheet
yet). Baselines: same direction and holding time from a random day (does the timing beat just being long?) and the coin flip.
Markets: gold 2012-2026, US100/US500 2018-2026, TSLA 2019-2026, AAPL 2015-2026, BTC 2020-2026 (daily bars)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/lab")
from universe import catalog, daily_bars, swap_per_night, commission_of
from run_battery import intraday_frame
from daily import Daily, sma
from news import load_calendar, day_labels


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def line(label, tr):
    if len(tr) < 10: return f"  {label:44s} n={len(tr)}"
    IS = pd.DatetimeIndex(tr.day) < "2024-01-01"
    return (f"  {label:44s} n={len(tr):4d} avgR={tr.R.mean():+.3f} t={tstat(tr.R):+.1f} win={np.mean(tr.R > 0):.0%} | random-day {tr.base.mean():+.3f} "
            f"coin {tr.coin.mean():+.3f} | before 2024 {tr.R[IS].mean():+.3f} (n {IS.sum()}) from 2024 {tr.R[~IS].mean():+.3f}")


def sig_A(x, uptrend_only=False):
    O, H, L, C, A = x.O, x.H, x.L, x.C, x.A; s200 = sma(C, 200); out = []
    for i in range(200, len(C) - 6):
        rng = H[i] - L[i]
        if not np.isfinite(A[i]) or rng <= 0: continue
        if (O[i] - L[i]) >= 0.5 * A[i] and (C[i] - L[i]) / rng >= 2 / 3 and (not uptrend_only or C[i] > s200[i]):
            out.append((i + 1, 1, 2.0 * A[i], i + 5, "close"))
    return out


def sig_B(x):
    C, A = x.C, x.A; s200 = sma(C, 200); out = []; i = 220
    while i < len(C) - 21:
        w = C[i - 19:i + 1]; hi = np.argmax(w); dd = w[hi] - w[hi:].min()
        if np.isfinite(A[i]) and C[i] > s200[i] and dd <= 1.5 * A[i]:
            out.append((i + 1, 1, 3.0 * A[i], i + 20, "close")); i += 20        # non-overlapping 20-day holds
        else: i += 1
    return out


def sig_C(x, d30, news):
    """d30: 30-min bars with nyd/nyt; first 30-min candle 9:30-10:00."""
    first = d30[d30.nyt == "09:30"].set_index("nyd")
    out_news, out_cond = [], []
    days = x.days.normalize()
    for i in range(1, len(x.C) - 6):
        d = days[i]
        if d not in news or d not in first.index or not np.isfinite(x.A[i - 1]): continue
        f = first.loc[d]
        if isinstance(f, pd.DataFrame): f = f.iloc[0]
        drop = (f.close - f.open) / x.A[i - 1]
        sig = (i + 1, 1, 2.0 * x.A[i], i + 5, "close")
        out_news.append(sig)
        if drop <= -0.25 and x.C[i] > x.O[i]: out_cond.append(sig)
    return out_news, out_cond


def exits_D(x, rule, max_hold=250):
    """Entries: close above the previous 20-day high (long). Returns list of (day, R, nights)."""
    O, H, L, C, A = x.O, x.H, x.L, x.C, x.A; N = len(C)
    hh = pd.Series(H).rolling(20).max().shift(1).values; ll10 = pd.Series(L).rolling(10).min().shift(1).values; s50 = sma(C, 50)
    rows = []; i = 60
    while i < N - 2:
        if not (np.isfinite(A[i]) and C[i] > hh[i]): i += 1; continue
        a = i + 1; E = O[a]; unit = 2.0 * A[i]; stop = E - unit; best = C[a]; X = None; b = None
        for k in range(a, min(a + max_hold, N)):
            if L[k] <= stop: X = min(stop, O[k]) if k > a else stop; b = k; break
            best = max(best, C[k])
            if rule.startswith("chand"):
                m = float(rule[5:]); stop = max(stop, best - m * A[k])
            elif rule == "low10" and C[k] < ll10[k]: X, b = (O[k + 1] if k + 1 < N else C[k]), min(k + 1, N - 1); break
            elif rule == "ma50" and C[k] < s50[k]: X, b = (O[k + 1] if k + 1 < N else C[k]), min(k + 1, N - 1); break
            elif rule.startswith("hold") and k - a + 1 >= int(rule[4:]): X, b = C[k], k; break
        if X is None: b = min(a + max_hold, N) - 1; X = C[b]
        cost = x.SP[a] + x.comm * (abs(E) + abs(X)) + x.swap_cost(a, b, 1, E)
        rows.append((x.days[a], (X - E - cost) / unit, b - a)); i = max(b, i + 1)
    return rows


def main():
    cat = catalog()
    cal = load_calendar("/home/claude/news/news_usd.csv"); labels = day_labels(cal)
    news = {pd.Timestamp(k).normalize() for k, v in labels.items() if v in ("Fed decision", "CPI", "Jobs report")}
    for sym in ("XAUUSD", "US100.cash", "US500.cash", "TSLA", "AAPL", "BTCUSD"):
        d, tf = intraday_frame(sym, cat, dry=True)
        D = daily_bars(sym, cat, intraday=d)
        if sym in ("US100.cash", "US500.cash"): D = D[D.index >= "2018-01-01"]
        x = Daily(D, sym, None)
        print(f"\n==== {sym}: {len(D)} days {D.index[0].date()}..{D.index[-1].date()} ====")
        print(line("A dip bought (next open -> 5-day close)", x.run(sig_A(x))))
        print(line("A  ... only above the 200-day average", x.run(sig_A(x, True))))
        print(line("B shallow pullbacks in an uptrend, 20 days", x.run(sig_B(x))))
        if sym in ("US100.cash", "US500.cash"):
            m30 = d.copy(); ny = m30.index.tz_convert("America/New_York")
            m30["nyd"] = ny.tz_localize(None).normalize(); m30["nyt"] = ny.strftime("%H:%M")
            # the 9:30 candle from 30-min (or 5-min aggregated) bars
            b30 = m30[(m30.nyt >= "09:30") & (m30.nyt < "10:00")].groupby("nyd").agg(open=("open", "first"), close=("close", "last"))
            b30["nyt"] = "09:30"; b30 = b30.reset_index()
            sn, sc = sig_C(x, b30, news)
            print(line("C all Fed/CPI/jobs days (next open, 5 days)", x.run(sn)))
            print(line("C  ... early drop >= 0.25 ATR, closed up", x.run(sc)))
        for rule in ("chand2", "chand3", "chand4", "low10", "ma50", "hold20", "hold60"):
            r = pd.DataFrame(exits_D(x, rule), columns=["day", "R", "nights"])
            if len(r) < 5: continue
            IS = r.day < "2024-01-01"
            print(f"  D exit {rule:7s} n={len(r):3d} avgR={r.R.mean():+.3f} t={tstat(r.R):+.1f} win={np.mean(r.R > 0):.0%} "
                  f"avg hold {r.nights.mean():4.0f}d | before 2024 {r.R[IS].mean():+.3f} from 2024 {r.R[~IS].mean():+.3f}")


if __name__ == "__main__":
    main()
