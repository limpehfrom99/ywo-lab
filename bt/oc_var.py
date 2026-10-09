"""Opening-candle variations on the FTMO M30 exports (TSLA 2022-26, US100 2021-09..26, US500 same), Fed days skipped.
Base rule: at 10:00 NY trade the direction of the 9:30-10:00 candle, stop at its far end, exit at the 16:00 close, costs.
Everything below is a fixed list; every cell is reported (no cherry-picking)."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab")
from ftmo_data import load_export
from lab import ny_session, full_days
from news import load_calendar, fed_days

FED = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
COMM = {"TSLA": 0.00002, "US100.cash": 0.0, "US500.cash": 0.0, "AAPL": 0.00002}

def session(sym, start="2022-01-01"):
    d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0]); s = ny_session(d, start)
    days = full_days(s, 13); return s[s.nyd.isin(days) & ~s.nyd.isin(FED)]

def trades(s, comm, first_bars=1, exit_t="16:00", reverse=False):
    rows = []; prev_close = None
    for day, b in s.groupby("nyd"):
        if len(b) != 13: continue
        f = b.iloc[:first_bars]; o, c, hi, lo = f.open.iloc[0], f.close.iloc[-1], f.high.max(), f.low.min()
        day_atr = None
        if c == o: prev_close = b.close.iloc[-1]; continue
        dr = 1 if c > o else -1; rest = b.iloc[first_bars:]; rest = rest[rest.nyt < exit_t] if exit_t != "16:00" else rest
        if len(rest) == 0: prev_close = b.close.iloc[-1]; continue
        e = rest.open.iloc[0]; stop = lo if dr == 1 else hi; risk = (e - stop) * dr
        if risk <= 0: prev_close = b.close.iloc[-1]; continue
        px, why = rest.close.iloc[-1], "close"; stopped_at = None
        for k, r in enumerate(rest.itertuples()):
            if dr == 1 and r.low <= stop: px, why, stopped_at = min(stop, r.open), "stop", k; break
            if dr == -1 and r.high >= stop: px, why, stopped_at = max(stop, r.open), "stop", k; break
        cost = rest.sp.iloc[0] + comm * (e + px); R = (dr * (px - e) - cost) / risk
        if reverse and why == "stop":                                  # stop-and-reverse: flip at the stop, new stop = old entry
            e2 = px; dr2 = -dr; stop2 = e; risk2 = (e2 - stop2) * dr2; px2, why2 = rest.close.iloc[-1], "close"
            bar = rest.iloc[stopped_at]                                  # the stop-out bar itself can also stop leg 2 (order within the bar unknown: assume it does)
            if (dr2 == 1 and bar.low <= stop2) or (dr2 == -1 and bar.high >= stop2): px2, why2 = stop2, "stop"
            else:
                for r in rest.iloc[stopped_at + 1:].itertuples():
                    if dr2 == 1 and r.low <= stop2: px2, why2 = min(stop2, r.open), "stop"; break
                    if dr2 == -1 and r.high >= stop2: px2, why2 = max(stop2, r.open), "stop"; break
            R += (dr2 * (px2 - e2) - rest.sp.iloc[0] - comm * (e2 + px2)) / risk2                     # second leg sized at the same $ risk as the first
        gap = np.sign(o - prev_close) if prev_close else 0
        rows.append(dict(day=day, dir=dr, R=R, why=why, rng=hi - lo, body=abs(c - o), gap=gap, wd=day.weekday(), entry=e))
        prev_close = b.close.iloc[-1]
    t = pd.DataFrame(rows).set_index("day")
    # daily ATR of the session days (known at the open: previous 14 days)
    dly = s.groupby("nyd").agg(h=("high","max"), l=("low","min"), c=("close","last")); pc = dly.c.shift(1)
    atr = pd.concat([dly.h - dly.l, (dly.h - pc).abs(), (dly.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    t["rng_atr"] = (t.rng / atr.reindex(t.index)).values; t["body_rng"] = (t.body / t.rng.replace(0, np.nan)).values
    t["prev_ret"] = np.sign(dly.c.pct_change().shift(1).reindex(t.index)).values
    return t

def line(label, R):
    R = np.asarray(R); n = len(R)
    if n < 20: return f"{label:46s} n={n:4d} (too few)"
    return f"{label:46s} n={n:4d} avgR={R.mean():+.3f} t={R.mean()/(R.std()/np.sqrt(n)):+.1f} win={np.mean(R>0):.0%}"

if __name__ == "__main__":
    S = {sym: session(sym) for sym in ("TSLA", "US100.cash", "US500.cash")}
    T = {sym: trades(S[sym], COMM[sym]) for sym in S}
    for sym, t in T.items():
        print(f"\n==== {sym} ({t.index.min().date()} .. {t.index.max().date()}) ====")
        print(line("base: 30-min candle, exit 16:00", t.R))
        print(line("  60-min candle (first two bars)", trades(S[sym], COMM[sym], first_bars=2).R))
        print(line("  exit 12:00", trades(S[sym], COMM[sym], exit_t="12:00").R)); print(line("  exit 14:00", trades(S[sym], COMM[sym], exit_t="14:00").R))
        print(line("  stop-and-reverse after a stop-out", trades(S[sym], COMM[sym], reverse=True).R))
        for lo, hi in ((0, 0.2), (0.2, 0.35), (0.35, 0.5), (0.5, 9)):
            m = (t.rng_atr >= lo) & (t.rng_atr < hi); print(line(f"  candle range {lo}-{hi} x daily ATR", t.R[m]))
        for lo, hi in ((0, 0.3), (0.3, 0.7), (0.7, 1.01)):
            m = (t.body_rng >= lo) & (t.body_rng < hi); print(line(f"  body/range {lo}-{hi}", t.R[m]))
        print(line("  candle direction = gap direction", t.R[t.dir == t.gap])); print(line("  candle direction against the gap", t.R[(t.dir == -t.gap) & (t.gap != 0)]))
        print(line("  candle direction = yesterday's direction", t.R[t.dir == t.prev_ret])); print(line("  against yesterday", t.R[(t.dir == -t.prev_ret) & (t.prev_ret != 0)]))
        for wd, nm in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri")): print(line(f"  {nm}", t.R[t.wd == wd]))
        print(line("  longs", t.R[t.dir == 1])); print(line("  shorts", t.R[t.dir == -1]))
    print("\n==== cross-asset agreement (same day, candle directions) ====")
    pairs = (("TSLA", "US100.cash"), ("US100.cash", "US500.cash"), ("US100.cash", "TSLA"), ("US500.cash", "US100.cash"))
    for a, b in pairs:
        j = T[a].join(T[b].dir.rename("other"), how="inner")
        print(line(f"  {a} when {b} candle agrees", j.R[j.dir == j.other])); print(line(f"  {a} when {b} candle disagrees", j.R[j.dir != j.other]))
    j = T["TSLA"].join(T["US100.cash"].dir.rename("o1"), how="inner").join(T["US500.cash"].dir.rename("o2"), how="inner")
    print(line("  TSLA when both indices agree", j.R[(j.dir == j.o1) & (j.dir == j.o2)])); print(line("  TSLA when both indices disagree", j.R[(j.dir != j.o1) & (j.dir != j.o2)]))
    # portfolio of the three with equal risk, daily correlation
    D = pd.concat([T[s].R.rename(s) for s in T], axis=1)
    print("\ndaily R correlations:\n", D.corr().round(2).to_string())
