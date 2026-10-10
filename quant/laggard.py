"""Log #80 — JeaFx "How I Day Trade GBPUSD (with price action)" (RedNote 油管中文配音檔案館 repost, 2 Oct 2026): the correlation read.
His bias for the trade: EURUSD, GBPUSD's closest twin, had already taken out its range low (and the dollar index was about to take its
high) while GBPUSD's matching low was still intact -> "the low is probably rather likely to go" -> sell GBPUSD, target its range low.
(His entry was a 15-minute supply-zone limit; supply/demand zone entries are already dead in #58/#67.) Question tested: when one of two
twin markets breaks its range low (high) and the other has not, does the laggard go on to take its own low (high)?

Fixed before running:
  pairs   EURUSD/GBPUSD (primary: GBPUSD lagging EURUSD's break of a low, as in the video), AUDUSD/NZDUSD, EURJPY/GBPJPY,
          US500/US100, US30/US500, GER40/EU50, XAUUSD/XAGUSD; each side of a pair can be the leader; lows (sell) and highs (buy).
  bars    FTMO export on the server clock (New York + 7 h), resampled to M15, H1 (primary), H4; leader and laggard bars aligned.
  range   the N bars before the signal bar, N = 120 (primary: about a week of H1 bars; his "couple of weeks" range) and N = 24.
  signal  bar t: the leader CLOSES below its N-bar low for the first time (previous close was not below it), and the laggard's low has
          stayed above its own N-bar low through bar t. Mirror for highs. At most one signal per N bars per pair, leader and side.
  trade   sell the laggard at the open of bar t+1; target = the laggard's N-bar low at t; D = entry - target (skip if D <= 3 spreads);
          stop = entry + D (1:1, primary) | entry + D/2 (target = 2R). Out at the target, the stop (a bar touching both = stop), or the
          close of bar t+N. Costs: spread at entry x 1.2 + commission both sides (universe.commission_of). No swap (FX holds are ~1-5 days;
          stated, not charged).
  baseline the same trade on the same laggard at moments when BOTH markets are still above their N-bar lows (no divergence), every N
          bars (non-overlapping) - same geometry, so it measures what the twin's break adds. Reported: n, avg R, t, hit rate (target
          reached), both baselines, before/after 2024, per year.
python3 quant/laggard.py   -> results/laggard_cells.csv, results/laggard_trades.pkl (in /home/claude/bt)
"""
import os, sys, time, warnings, pickle
import numpy as np, pandas as pd
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
from universe import catalog, load, commission_of, group_of  # noqa: E402
from evaluate import tstat  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
PAIRS = [("EURUSD", "GBPUSD"), ("AUDUSD", "NZDUSD"), ("EURJPY", "GBPJPY"), ("US500.cash", "US100.cash"),
         ("US30.cash", "US500.cash"), ("GER40.cash", "EU50.cash"), ("XAUUSD", "XAGUSD")]
TFS = {"M15": "15min", "H1": "1h", "H4": "4h"}
NS = (120, 24)
RRS = (1.0, 2.0)


def bars(sym, cat):
    for tf in ("M5", "M15"):
        if (sym, tf) in cat:
            d = load(sym, tf, cat)
            if d is not None and len(d) > 5000: break
    d = d[~d.index.duplicated()].sort_index()
    srv = d.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
    d = d.set_index(srv)
    return d


def resample(d, rule):
    g = d.resample(rule, label="left", closed="left")
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "sp": g.sp.median()})
    return out.dropna(subset=["open", "close"])


@njit(cache=True)
def sim(o, h, l, c, sig, tgt, rr, N, sp, comm, side):
    """side -1 = sell the laggard toward its low; +1 = buy toward its high. Returns R (nan if no trade), hit flag, entry index."""
    n = len(c); R = np.full(n, np.nan); hit = np.zeros(n, np.int64)
    for t in range(n - 1):
        if not sig[t]: continue
        e = o[t + 1]; T = tgt[t]; D = (e - T) * (-side)
        if not (D > 3 * sp[t + 1]) or not np.isfinite(D): continue
        risk = D / rr
        stop = e - side * risk
        x = np.nan
        end = min(t + N, n - 1)
        for k in range(t + 1, end + 1):
            if side == -1:
                if h[k] >= stop: x = stop; break
                if l[k] <= T: x = T; hit[t] = 1; break
            else:
                if l[k] <= stop: x = stop; break
                if h[k] >= T: x = T; hit[t] = 1; break
        if not np.isfinite(x): x = c[end]
        cost = sp[t + 1] * 1.2 + comm * (abs(e) + abs(x))
        R[t] = (side * (x - e) - cost) / risk
    return R, hit


def run_pair(lead_sym, lag_sym, dfs, comm_lag):
    rows, trades = [], []
    for tfn, rule in TFS.items():
        A = resample(dfs[lead_sym], rule); B = resample(dfs[lag_sym], rule)
        idx = A.index.intersection(B.index); A = A.loc[idx]; B = B.loc[idx]
        if len(idx) < 500: continue
        for N in NS:
            for side in (-1, 1):                                  # -1: lows (sell the laggard), +1: highs (buy it)
                if side == -1:
                    lvA = A.low.shift(1).rolling(N).min(); lvB = B.low.shift(1).rolling(N).min()
                    brkA = (A.close < lvA) & ~(A.close.shift(1) < lvA.shift(1))
                    intactB = B.low > lvB
                    intactA = A.low > lvA
                else:
                    lvA = A.high.shift(1).rolling(N).max(); lvB = B.high.shift(1).rolling(N).max()
                    brkA = (A.close > lvA) & ~(A.close.shift(1) > lvA.shift(1))
                    intactB = B.high < lvB
                    intactA = A.high < lvA
                raw = (brkA & intactB).values
                sig = np.zeros(len(raw), bool); last = -10 ** 9
                for t in np.flatnonzero(raw):
                    if t - last >= N: sig[t] = True; last = t
                # baseline: both intact, no leader break in the last N bars, every N bars
                calm = (intactA & intactB & (brkA.astype(int).rolling(N, min_periods=1).sum() == 0)).values
                base = np.zeros(len(calm), bool); last = -10 ** 9
                for t in np.flatnonzero(calm):
                    if t - last >= N: base[t] = True; last = t
                o, h, l, c, sp = (B[k].values.astype(float) for k in ("open", "high", "low", "close", "sp"))
                tg = lvB.values.astype(float)
                for rr in RRS:
                    R, hit = sim(o, h, l, c, sig, tg, rr, N, sp, comm_lag, side)
                    Rb, hitb = sim(o, h, l, c, base, tg, rr, N, sp, comm_lag, side)
                    m = np.isfinite(R); mb = np.isfinite(Rb)
                    tt = idx[m]
                    x = pd.DataFrame({"t": tt, "R": R[m], "hit": hit[m]})
                    xb = pd.DataFrame({"t": idx[mb], "R": Rb[mb], "hit": hitb[mb]})
                    cell = dict(leader=lead_sym, laggard=lag_sym, tf=tfn, N=N, side="low/sell" if side == -1 else "high/buy", rr=rr,
                                n=len(x), avgR=x.R.mean(), t=tstat(x.R), hit=x.hit.mean(), n_base=len(xb), base=xb.R.mean(),
                                hit_base=xb.hit.mean(), t_vs_base=np.nan,
                                is_=x.R[x.t < "2024-01-01"].mean(), oos=x.R[x.t >= "2024-01-01"].mean(),
                                by_year=" ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in x.groupby(x.t.dt.year).R.mean().items()))
                    if len(x) > 2 and len(xb) > 2:
                        se = np.sqrt(x.R.var(ddof=1) / len(x) + xb.R.var(ddof=1) / len(xb))
                        cell["t_vs_base"] = (x.R.mean() - xb.R.mean()) / se if se > 0 else np.nan
                    rows.append(cell)
                    x["leader"], x["laggard"], x["tf"], x["N"], x["side"], x["rr"] = lead_sym, lag_sym, tfn, N, side, rr
                    trades.append(x)
    return rows, trades


def main():
    t0 = time.time(); cat = catalog()
    syms = sorted({s for p in PAIRS for s in p}); dfs = {s: bars(s, cat) for s in syms}
    print("loaded", {s: (str(d.index[0].date()), str(d.index[-1].date())) for s, d in dfs.items()}, f"{time.time() - t0:.0f}s", flush=True)
    rows, trades = [], []
    for a, b in PAIRS:
        for lead, lag in ((a, b), (b, a)):
            r, tr = run_pair(lead, lag, dfs, commission_of(lag)); rows += r; trades += tr
            print(f"{lag} lagging {lead}: done ({time.time() - t0:.0f}s)", flush=True)
    C = pd.DataFrame(rows)
    C.to_csv(os.path.join(RESULTS, "laggard_cells.csv"), index=False, float_format="%.4f")
    pickle.dump(pd.concat(trades, ignore_index=True), open("/home/claude/bt/laggard_trades.pkl", "wb"))
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    show = ["leader", "laggard", "tf", "N", "side", "rr", "n", "avgR", "t", "hit", "base", "hit_base", "t_vs_base", "is_", "oos"]
    prim = C[(C.leader == "EURUSD") & (C.laggard == "GBPUSD")]
    print("\nEURUSD -> GBPUSD (primary pair):\n" + prim[show].round(3).to_string(index=False))
    T = pd.concat(trades, ignore_index=True)
    print("\npooled over all pairs:")
    g = T.groupby(["tf", "N", "rr"]).R.agg(["size", "mean", tstat]).round(3)
    print(g.to_string())
    print(f"\ncells {len(C)}; positive {(C.avgR > 0).mean():.0%}; beat their baseline {(C.avgR > C.base).mean():.0%}; "
          f"t_vs_base >= 2: {(C.t_vs_base >= 2).sum()} (luck ~{0.025 * len(C):.1f})")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
