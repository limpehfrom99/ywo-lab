"""#47 — RedNote repost (油管中文配音檔案館) of JJ Simon, "$2M in prop payouts — full roadmap" (29 min). His strategy ("fair pricing
theory", mean reversion): a big move on 8:30 New York red-folder news is "unfair" because the news is priced in on average ->
trade the reversion toward the pre-news price, many times a day if possible.
Fixed before running: news days = a Nonfarm Payrolls, CPI m/m, PPI m/m, Retail Sales m/m, Durable Goods Orders m/m, GDP q/q or
Core PCE m/m release at 08:30 New York (calendar export; jobless claims excluded). p0 = the 08:30 open.
  Gold (1-minute bars): move = 08:44 close - p0; if |move| >= 0.25 daily ATR, fade it at the 08:45 open; stop = the 08:30-08:44
  extreme + 0.05 ATR; target = p0 (full reversion) or half of the move; flat at 12:00 New York.
  Forex (EURUSD, GBPUSD, USDCHF 2018-26) and US100 / US500 (2022-26), FTMO 30-minute bars: move = the 08:30 bar's close - p0;
  same threshold; fade at the 09:00 open; stop = the 08:30 bar's extreme + 0.05 ATR; same targets; flat at 12:00 (exits on
  30-minute bars, stop first).
Costs: FTMO spread x 2 at the entry (spreads are still wide after a release) + commission; coin flip (= following the news move
with the same distances) per trade."""
import sys, glob, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc_grid import exit_nb, tstat
from news import load_calendar
from pdh_sweep import ftmo_m30, prep, COMM

BIG = ("Nonfarm Payrolls", "CPI m/m", "PPI m/m", "Retail Sales m/m", "Durable Goods Orders m/m", "GDP q/q", "Core PCE Price Index m/m")


def news_days():
    c = load_calendar("/home/claude/news/news_usd.csv")
    x = c[(c.ny_hhmm == "08:30") & (c.importance == "high") & c.event.isin(BIG)]
    return sorted(set(pd.to_datetime(x.ny_day)))


def run(px, comm, step_min, days, thr=0.25):
    """px: UTC bars (1-minute for gold, 30-minute otherwise)."""
    ny = px.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    _, D = prep(px); srv_day = D.atr                                  # daily ATR by broker day (known before the day)
    T, H, L, C, O, SP = px.index.values, px.high.values, px.low.values, px.close.values, px.open.values, px.sp.values
    nyv = ny.values; out = []
    for d in days:
        t0 = np.datetime64(d + pd.Timedelta(hours=8, minutes=30)); i_open = np.searchsorted(nyv, t0)
        if i_open >= len(T) or nyv[i_open] != t0: continue
        key = (d + pd.Timedelta(hours=7)).normalize()                     # broker day of 08:30 NY = same date
        atr = srv_day.get(key, np.nan)
        if not np.isfinite(atr): continue
        n_meas = 15 // step_min if step_min < 30 else 1                     # bars from 08:30 to the measurement
        i_meas = i_open + n_meas - 1; i_ent = i_open + n_meas
        if i_ent >= len(T) or (nyv[i_ent] - t0) > np.timedelta64(31 if step_min == 30 else 16, "m"): continue
        p0 = O[i_open]; move = C[i_meas] - p0
        if abs(move) < thr * atr: continue
        side = -1 if move > 0 else 1                                        # fade
        ext = H[i_open:i_meas + 1].max() if move > 0 else L[i_open:i_meas + 1].min()
        e = O[i_ent]; stop = ext - side * 0.05 * atr; risk = abs(stop - e)
        if (side == -1 and stop <= e) or (side == 1 and stop >= e) or risk <= 0: continue
        i_end = np.searchsorted(nyv, np.datetime64(d + pd.Timedelta(hours=12)))
        if i_end <= i_ent: continue
        for tname, tgt in (("full", p0), ("half", p0 + 0.5 * move)):
            if side * (tgt - e) <= 0: continue
            X = exit_nb(H, L, C, i_ent, i_end, stop, tgt, side); cost = 2 * SP[i_ent] + comm * (abs(e) + abs(X))
            Xf = exit_nb(H, L, C, i_ent, i_end, e + side * risk, 2 * e - tgt, -side)
            out.append((tname, pd.Timestamp(T[i_ent]), side, (side * (X - e) - cost) / risk, (-side * (Xf - e) - cost) / risk,
                        side * (tgt - e) / risk, abs(move) / atr))
    return pd.DataFrame(out, columns=["target", "t", "side", "R", "R_follow", "rr", "move_atr"])


def show(name, r):
    for tname, x in r.groupby("target"):
        if len(x) < 10: print(f"{name:14s} target {tname}: n={len(x)}"); continue
        IS = x.t < "2024-01-01"; yr = x.groupby(x.t.dt.year).R.mean()
        print(f"{name:14s} target {'pre-news price' if tname == 'full' else 'half the move':15s} n={len(x):4d} avgR={x.R.mean():+.3f} t={tstat(x.R):+.1f} "
              f"win={np.mean(x.R>0):.0%} rr {x.rr.median():.2f} | following the move instead {x.R_follow.mean():+.3f} | fade up-moves "
              f"{x[x.side==-1].R.mean():+.3f} down-moves {x[x.side==1].R.mean():+.3f} | <24 {x.R[IS].mean():+.3f} 24+ {x.R[~IS].mean():+.3f} "
              f"| yrs>0 {(yr>0).sum()}/{len(yr)} | median move {x.move_atr.median():.2f} ATR", flush=True)


if __name__ == "__main__":
    t0 = time.time(); days = news_days(); print(f"{len(days)} news days", flush=True); allr = []
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]
    r = run(g, COMM["gold"], 1, days); show("gold 1-min", r); allr.append(r.assign(mkt="gold"))
    for grp, syms, base in (("fx", ("EURUSD", "GBPUSD", "USDCHF"), "/home/claude/data/fx2"), ("idx", ("US100.cash", "US500.cash"), "/home/claude/data/assets")):
        rs = []
        for s in syms:
            d = ftmo_m30(glob.glob(f"{base}/{s}_M30_*.csv")[0])
            if grp == "idx": d = d.loc["2022-01-01":]
            rs.append(run(d, COMM[grp], 30, days).assign(sym=s))
        r = pd.concat(rs); show("forex x3" if grp == "fx" else "US100+US500", r); allr.append(r.assign(mkt=grp))
    pd.concat(allr).to_pickle("/home/claude/bt/news_fade_trades.pkl")
    print(f"done in {time.time() - t0:.0f}s")
