"""Log #81 — Lance Breitstein, "Why Your Support & Resistance Lines Don't Work ($100M Trader Explains)" (RedNote 油管中文配音檔案館 repost,
4 Oct 2026). His claim: blind S/R is noise ("academics have shown it doesn't work", "you're better off flipping a coin"); a break of a
level is worth trading when (1) the product is IN PLAY (unusual volume / volatility / catalyst), (2) the level is CLEAN and obvious,
(3) price CONSOLIDATED properly into it, (4) it drew an EMOTIONAL REACTION before, (5) several TIMEFRAMES agree (his example: gold's
intraday breakout through the prior day's high "took off like a rocket"). "The more criteria you stack, the better."
Tested: does stacking his filters turn a plain prior-day high/low breakout into an edge?

Fixed before running:
  level   previous session's high (buy-stop) / low (sell-stop) - the level every trader sees, a daily level traded intraday (5).
  entry   active from 30 minutes after the session open until 2 hours before the close; the first touch of either level decides
          (one bar touching both = a long that is stopped: lab convention); fill at the level or at the bar's open if it gapped
          through; days that OPEN beyond the level are skipped for that side.
  stop    the far end of the 30 minutes before the break bar (the "consolidation"), at least 0.1 x daily ATR from the entry.
  exit    session close (primary) | 2R target. Costs: spread at entry x 1.2 + commission both sides. Coin flip x 10 at the same moments.
  filters (all known before the entry):
    IP    in play by volume: tick volume of the session's first 30 minutes >= 1.5 x its average over the previous 14 sessions
    IPV   in play by volatility: range of the first 30 minutes >= 1.5 x its 14-session average
    CONS  proper consolidation: range of the 30 minutes before the break <= 0.3 x daily ATR
    MTF   the level is also the 5-session extreme (prior-day high = 5-day high; mirror for lows)
    REACT emotional reaction at the level: the previous session closed >= 0.25 daily ATR away from it (sellers reacted at the high)
    ALL4  IP & CONS & MTF & REACT;  ANY3  at least 3 of IP, CONS, MTF, REACT
  baseline the same breakouts on every day (ALL); the question is whether each filter beats ALL (difference and its t) and its coin.
Data: every symbol of the export on its battery sessions (quant/universe.sessions_of; US stocks and indices on us_cash), M5 (FX M15)
primary; M15 resampled from M5 as a timeframe check.
python3 quant/lance_levels.py [--workers 2]  -> results/lance_cells.csv, /home/claude/bt/lance_trades.pkl
"""
import os, sys, time, argparse, warnings, pickle
import numpy as np, pandas as pd
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
from universe import catalog, load, sessions_of, group_of, commission_of  # noqa: E402
from sessions import Session  # noqa: E402
from intraday import simulate, flip, mirror  # noqa: E402
from evaluate import cell_stats, tstat  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
FILTERS = ["ALL", "IP", "IPV", "CONS", "MTF", "REACT", "ALL4", "ANY3"]


def prev14(x):
    return pd.Series(x).rolling(14, min_periods=10).mean().shift(1).values


def breakouts(S):
    n, K = S.C.shape; i = np.arange(n)
    k30 = S.cols(30); lim = K - S.cols(120)
    if lim <= k30 + 1: return None
    gap = np.r_[np.nan, (S.days[1:] - S.days[:-1]).days]
    pdh = np.r_[np.nan, S.high[:-1]]; pdl = np.r_[np.nan, S.low[:-1]]; pc = np.r_[np.nan, S.close[:-1]]
    pdh[gap > 5] = np.nan; pdl[gap > 5] = np.nan
    cols = np.arange(K)[None, :]; w = (cols >= k30) & (cols < lim)
    up = (S.H >= pdh[:, None]) & w & (S.open < pdh)[:, None]
    dn = (S.L <= pdl[:, None]) & w & (S.open > pdl)[:, None]
    fu = np.where(up.any(1), up.argmax(1), K + 9); fd = np.where(dn.any(1), dn.argmax(1), K + 9)
    d = np.where(fu <= fd, 1, -1); d = np.where(np.minimum(fu, fd) > K, 0, d)
    j = np.where(d == 1, fu, np.where(d == -1, fd, -1)); jj = np.clip(j, 0, K - 1)
    lvl = np.where(d == 1, pdh, pdl)
    e_px = np.where(d == 1, np.maximum(pdh, S.O[i, jj]), np.minimum(pdl, S.O[i, jj]))
    k = S.cols(30)
    lo30 = np.full(n, np.nan); hi30 = np.full(n, np.nan)
    for a in range(n):
        if j[a] < k: continue
        lo30[a] = S.L[a, j[a] - k:j[a]].min(); hi30[a] = S.H[a, j[a] - k:j[a]].max()
    atr = S.atr
    stop = np.where(d == 1, np.minimum(lo30, e_px - 0.1 * atr), np.maximum(hi30, e_px + 0.1 * atr))
    ok = (d != 0) & np.isfinite(stop) & np.isfinite(atr) & ((e_px - stop) * d > 0)
    # filters, all known before the entry
    v30 = S.V[:, :k30].sum(1); r30 = S.H[:, :k30].max(1) - S.L[:, :k30].min(1)
    IP = v30 >= 1.5 * prev14(v30)
    IPV = r30 >= 1.5 * prev14(r30)
    CONS = (hi30 - lo30) <= 0.3 * atr
    h5 = pd.Series(S.high).rolling(5).max().shift(1).values; l5 = pd.Series(S.low).rolling(5).min().shift(1).values
    MTF = np.where(d == 1, pdh >= h5, pdl <= l5)
    REACT = np.where(d == 1, pc <= pdh - 0.25 * atr, pc >= pdl + 0.25 * atr)
    F = dict(ALL=np.ones(n, bool), IP=IP, IPV=IPV, CONS=CONS, MTF=MTF, REACT=REACT, ALL4=IP & CONS & MTF & REACT,
             ANY3=(IP.astype(int) + CONS + MTF + REACT) >= 3)
    return dict(e_col=np.where(ok, j, -1), e_px=e_px, d=d, stop=stop, F=F)


def run(S, b, comm, tR, n_flip=10, sp_mult=1.2):
    e, e_px, d, stop = b["e_col"], b["e_px"], b["d"], b["stop"]
    risk = np.abs(e_px - stop)
    tgt = None if tR is None else e_px + d * tR * risk
    R, why, rf = simulate(S, e, e_px, d, stop, tgt, None, comm, sp_mult, breakout=True)
    coins = []
    for s in range(n_flip):
        dn = flip(d, s); st, tg = mirror(e_px, dn, d, stop, tgt)
        coins.append(simulate(S, e, e_px, dn, st, tg, None, comm, sp_mult, breakout=True)[0])
    coin = np.nanmean(np.vstack(coins), axis=0)
    R2 = simulate(S, e, e_px, d, stop, tgt, None, comm, sp_mult * 2, breakout=True)[0]
    return R, coin, R2, why, rf


def resample_m15(d):
    g = d.resample("15min", label="left", closed="left")
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                        "sp": g.sp.median(), "tickvol": g.tickvol.sum()})
    return out.dropna(subset=["open", "close"])


def run_symbol(args):
    sym, n_flip = args
    t0 = time.time(); cat = catalog(); comm = commission_of(sym); out = {}; log = []
    base = None
    for tf in ("M5", "M15", "M30"):
        if (sym, tf) in cat:
            base = (tf, load(sym, tf, cat)); break
    if base is None or base[1] is None or len(base[1]) < 2000: return out, [f"{sym}: no intraday file"]
    tf0, d0 = base
    if "tickvol" not in d0: d0["tickvol"] = 1.0
    d0 = d0[~d0.index.duplicated()].sort_index()
    frames = [(tf0, d0)]
    if tf0 == "M5": frames.append(("M15", resample_m15(d0)))
    for tf, d in frames:
        for sess in sessions_of(sym):
            try: S = Session(d, sess, bar=int(tf[1:]))
            except Exception as ex: log.append(f"{sym} {tf} {sess}: {ex!r}"); continue
            if len(S.days) < 150: log.append(f"{sym} {tf} {sess}: only {len(S.days)} days"); continue
            b = breakouts(S)
            if b is None: continue
            for xname, tR in (("close", None), ("2R", 2.0)):
                R, coin, R2, why, rf = run(S, b, comm, tR, n_flip)
                m0 = np.isfinite(R)
                for fname, fm in b["F"].items():
                    m = m0 & fm
                    if m.sum() == 0: continue
                    out[(sym, tf, sess, xname, fname)] = pd.DataFrame({"day": S.days[m], "d": b["d"][m], "R": R[m], "coin": coin[m],
                                                                      "R2x": R2[m], "why": why[m], "risk_frac": rf[m]})
            log.append(f"{sym} {tf} {sess}: {len(S.days)} days")
    log.append(f"{sym}: {len(out)} cells in {time.time() - t0:.0f}s")
    return out, log


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--symbols", default="")
    a = ap.parse_args()
    cat = catalog(); syms = sorted({k[0] for k in cat}) if not a.symbols else a.symbols.split(",")
    trades, logs = {}, []; t0 = time.time()
    with Pool(a.workers) as pool:
        for tr, log in pool.imap_unordered(run_symbol, [(s, 10) for s in syms]):
            trades.update(tr); logs += log; print(log[-1], f"| {(time.time() - t0) / 60:.1f} min", flush=True)
    pickle.dump(trades, open("/home/claude/bt/lance_trades.pkl", "wb"))
    rows = []
    for (sym, tf, sess, xname, fname), tr in trades.items():
        s = cell_stats(tr); s.update(symbol=sym, group=group_of(sym), tf=tf, session=sess, exit=xname, filter=fname); rows.append(s)
    C = pd.DataFrame(rows); C.to_csv(os.path.join(RESULTS, "lance_cells.csv"), index=False, float_format="%.4f")
    # pooled: each filter vs ALL on the same symbol-session-tf-exit sets
    keys = pd.DataFrame(list(trades.keys()), columns=["symbol", "tf", "session", "exit", "filter"]); keys["group"] = keys.symbol.map(group_of)
    P = []
    for scope, kk in (("all", keys), ("ex-crypto", keys[keys.group != "crypto"]), ("us stocks", keys[keys.group == "stock"]),
                      ("indices", keys[keys.group.isin(["us_index", "index"])]), ("metals", keys[keys.group == "metal"]),
                      ("forex", keys[keys.group == "forex"])):
        for (tf, xname), k2 in kk.groupby(["tf", "exit"]):
            base = pd.concat([trades[tuple(r)] for r in k2[k2["filter"] == "ALL"][["symbol", "tf", "session", "exit", "filter"]].values], ignore_index=True) if (k2["filter"] == "ALL").any() else None
            for fname in FILTERS:
                k3 = k2[k2["filter"] == fname]
                if not len(k3): continue
                tr = pd.concat([trades[tuple(r)] for r in k3[["symbol", "tf", "session", "exit", "filter"]].values], ignore_index=True)
                diff_t = np.nan
                if base is not None and len(tr) > 2 and fname != "ALL":
                    se = np.sqrt(tr.R.var(ddof=1) / len(tr) + base.R.var(ddof=1) / len(base)); diff_t = (tr.R.mean() - base.R.mean()) / se
                P.append(dict(scope=scope, tf=tf, exit=xname, filter=fname, n=len(tr), avgR=tr.R.mean(), t=tstat(tr.R), win=(tr.R > 0).mean(),
                              coin=tr.coin.mean(), vs_all=(tr.R.mean() - base.R.mean()) if base is not None else np.nan, t_vs_all=diff_t,
                              is_=tr.R[pd.DatetimeIndex(tr.day) < "2024-01-01"].mean(), oos=tr.R[pd.DatetimeIndex(tr.day) >= "2024-01-01"].mean()))
    P = pd.DataFrame(P); P.to_csv(os.path.join(RESULTS, "lance_pooled.csv"), index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    print(P.round(3).to_string(index=False))
    with open(os.path.join(RESULTS, "lance_log.txt"), "w") as f: f.write("\n".join(logs))
    print(f"done in {(time.time() - t0) / 60:.1f} min; {len(C)} cells")


if __name__ == "__main__":
    main()
