"""Log #78 — Scarface Trades "9:30 AM candle" opening-range break & retest (RedNote 油管中文配音檔案館 reposts, 6 and 8 Oct 2026).

Rule as told (v4 "My Simple 9:30AM Candle Scalping Strategy (Backtested 1000 Times)"; v5 "Trading Isn't Hard, It's Misunderstood"):
mark the high and low of the first 5-minute candle of the New York session; on the 1-minute chart wait for a candle to CLOSE beyond
one side; wait for price to come back to that level and hold it ("weak price action" at the level for shorts, "strong" for longs);
enter; stop = a break of the candle you enter on (some examples: the candle that broke out); target the low/high of the day or at
least 2R; trade only the first 90 minutes. "Works on any market as long as you use the 9:30 Eastern candle." His claim: 1,308 trades,
59% winners, profit factor 4.15. v5 adds the daily trend read from swing structure ("external/internal liquidity": trade only in
its direction) and the previous day's high/low as the target when it is >= 2R away.

Fixed before running (log #78, written before the first run):
  OR      = high/low of the first k minutes of the session (k = 5 primary; 15 and 30 as timeframe checks), measured from the
            session's first bar (FTMO stock CFDs open 9:35 since 2024, so their OR starts at 9:35).
  side    = sign of the most recent bar CLOSE outside the OR (a close beyond the other side flips it); closes inside don't change it.
  trigger = the first later bar (not the bar that set the side) whose low <= OR high and close > OR high (long; mirror for shorts),
            before 90 minutes after the open. Enter at the NEXT bar's open (market order).
  stop    E = the trigger bar's far end (primary, the rule as stated) | B = the far end of the bar that set the side.
  target  2R (primary) | 1.5R | 3R.  Exit: target, stop, or the session close (primary) | flat 90 minutes after the open (E2_90).
  TREND   (v5): E stop; only trades in the direction of the daily structure trend (3-bar session-day pivots confirmed 3 days later;
            +1 after the last close above a confirmed swing high, -1 after the last close below a confirmed swing low); target = the
            previous session's high (long) / low (short) if it is >= 2R away, else 2R.
  BRK2    baseline without the retest: enter at the next bar's open after the FIRST close beyond the OR, stop = that bar's far end,
            2R, session close. Plus the usual coin flip (same moment, other side, same distances, 10 flips) for every variant.
  One trade per day per symbol-session. Costs: spread at entry x 1.2 + commission both sides (quant/intraday.simulate). A bar that
  touches both stop and target is a stop.
Data: every symbol of the FTMO export; M1 where it exists (XAUUSD, US100, US500, TSLA, NVDA) and the battery's intraday file (M5;
FX M15) for every symbol; session us_cash for every symbol ("any market at 9:30 New York") plus each symbol's own exchange session.

python3 quant/orb_retest.py [--symbols US500.cash,TSLA] [--workers 2]
Outputs: results/orb_retest_cells.csv, results/orb_retest_pooled.csv, /home/claude/bt/orb_retest_trades.pkl
"""
import os, sys, time, argparse, warnings, pickle
import numpy as np, pandas as pd
from multiprocessing import Pool
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
from universe import catalog, load, sessions_of, group_of, commission_of  # noqa: E402
from sessions import Session  # noqa: E402
from intraday import simulate, flip, mirror  # noqa: E402
from evaluate import cell_stats, verdict, false_discovery_note  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
TRADES = "/home/claude/bt/orb_retest_trades.pkl"
WINDOW_MIN = 90
VARIANTS = [  # name, kind, stop mode, target R, exit
    ("E2", "retest", "E", 2.0, "close"),          # primary
    ("E1.5", "retest", "E", 1.5, "close"),
    ("E3", "retest", "E", 3.0, "close"),
    ("B1.5", "retest", "B", 1.5, "close"),
    ("B2", "retest", "B", 2.0, "close"),
    ("B3", "retest", "B", 3.0, "close"),
    ("E2_90", "retest", "E", 2.0, "window"),
    ("TREND", "trend", "E", 2.0, "close"),
    ("BRK2", "brk", "B", 2.0, "close"),
]


@njit(cache=True)
def scan(H, L, C, first, k, lim):
    n, K = C.shape
    hi = np.full(n, np.nan); lo = np.full(n, np.nan)
    trig = np.full(n, -1, np.int64); side = np.zeros(n, np.int64); brk = np.full(n, -1, np.int64)
    fb = np.full(n, -1, np.int64); fside = np.zeros(n, np.int64)
    end = min(lim, K - 1)                                  # the entry bar (trigger + 1) must exist and be inside the window
    for i in range(n):
        f = first[i]
        if f + k >= end: continue
        h = -1e300; l = 1e300
        for c in range(f, f + k):
            if H[i, c] > h: h = H[i, c]
            if L[i, c] < l: l = L[i, c]
        hi[i] = h; lo[i] = l
        s = 0; jb = -1
        for c in range(f + k, end):
            if s == 1 and c > jb and L[i, c] <= h and C[i, c] > h:
                trig[i] = c; side[i] = 1; brk[i] = jb; break
            if s == -1 and c > jb and H[i, c] >= l and C[i, c] < l:
                trig[i] = c; side[i] = -1; brk[i] = jb; break
            if C[i, c] > h:
                if s != 1:
                    s = 1; jb = c
                    if fb[i] < 0: fb[i] = c; fside[i] = 1
            elif C[i, c] < l:
                if s != -1:
                    s = -1; jb = c
                    if fb[i] < 0: fb[i] = c; fside[i] = -1
    return hi, lo, trig, side, brk, fb, fside


def structure_trend(S, w=3):
    """Daily trend from session-day swing structure, known before each day opens: +1 after the last close above a confirmed
    swing high, -1 after the last close below a confirmed swing low (3-bar pivots, confirmed w days later)."""
    h, l, c = S.high, S.low, S.close
    n = len(h); tr = np.zeros(n, int)
    sh = np.nan; sl = np.nan; state = 0
    for t in range(n):
        tr[t] = state                                      # the state after yesterday's close
        p = t - w                                          # pivot candidate confirmed by today's close
        if p >= w:
            if h[p] > h[p - w:p].max() and h[p] >= h[p + 1:t + 1].max(): sh = h[p]
            if l[p] < l[p - w:p].min() and l[p] <= l[p + 1:t + 1].min(): sl = l[p]
        if np.isfinite(sh) and c[t] > sh: state = 1; sh = np.nan
        elif np.isfinite(sl) and c[t] < sl: state = -1; sl = np.nan
    return tr


def setups(S, k_min):
    k = S.cols(k_min); lim = S.cols(WINDOW_MIN)
    first = np.asarray(S.first, np.int64)
    return (k, lim) + scan(S.H, S.L, S.C, first, k, lim)


def build(S, sc, kind, stop_mode, tR, exit_mode, trend, pdh, pdl):
    k, lim, hi, lo, trig, side, brk, fb, fside = sc
    n, K = S.C.shape; i = np.arange(n)
    if kind == "brk":
        j = fb; d = fside.copy(); e = np.where(j >= 0, j + 1, -1)
        jj = np.clip(j, 0, K - 1)
        stop = np.where(d == 1, S.L[i, jj], S.H[i, jj])
    else:
        j = trig; d = side.copy(); e = np.where(j >= 0, j + 1, -1)
        jj = np.clip(j, 0, K - 1); bb = np.clip(brk, 0, K - 1)
        stop = (np.where(d == 1, S.L[i, jj], S.H[i, jj]) if stop_mode == "E" else np.where(d == 1, S.L[i, bb], S.H[i, bb]))
    ee = np.clip(e, 0, K - 1)
    e_px = S.O[i, ee]
    risk = np.abs(e_px - stop)
    if kind == "trend":
        d = np.where(d == trend, d, 0)
        pt = np.where(d == 1, pdh, pdl)
        nat = (pt - e_px) * d
        target = np.where(np.isfinite(nat) & (nat >= 2 * risk), pt, e_px + d * 2 * risk)
    else:
        target = e_px + d * tR * risk
    ok = (e >= 0) & (d != 0) & ((e_px - stop) * d > 0)
    exit_col = np.full(n, lim - 1) if exit_mode == "window" else None
    return np.where(ok, e, -1), e_px, d, stop, target, exit_col


def run_cell(S, spec, comm, n_flip=10, sp_mult=1.2):
    e, e_px, d, stop, tgt, xc = spec
    R, why, rf = simulate(S, e, e_px, d, stop, tgt, xc, comm, sp_mult)
    m = np.isfinite(R)
    if m.sum() == 0: return None
    G = simulate(S, e, e_px, d, stop, tgt, xc, 0.0, 0.0)[0]
    R2 = simulate(S, e, e_px, d, stop, tgt, xc, comm, sp_mult * 2)[0]
    coins = []
    for s in range(n_flip):
        dn = flip(d, s); st, tg = mirror(e_px, dn, d, stop, tgt)
        coins.append(simulate(S, e, e_px, dn, st, tg, xc, comm, sp_mult)[0])
    coin = np.nanmean(np.vstack(coins), axis=0)
    n, K = S.C.shape; i = np.arange(n); ee = np.clip(e, 0, K - 1)
    risk = np.abs(e_px - stop)
    cost_r = (S.SP[i, ee] * sp_mult + comm * 2 * np.abs(e_px)) / risk
    utc = S.utc_start + pd.to_timedelta(ee * S.bar, unit="min")
    return pd.DataFrame({"day": S.days[m], "utc": utc[m], "d": d[m], "R": R[m], "gross": G[m], "R2x": R2[m], "coin": coin[m],
                         "cost_r": cost_r[m], "risk_frac": rf[m], "why": why[m], "e_min": (ee[m] * S.bar)})


def frames_of(sym, cat):
    out = []
    if (sym, "M1") in cat:
        d = load(sym, "M1", cat)
        if d is not None and len(d) > 5000: out.append(("M1", d))
    for tf in ("M5", "M15", "M30"):
        if (sym, tf) in cat:
            d = load(sym, tf, cat)
            if d is not None and len(d) > 2000: out.append((tf, d)); break
    for tf, d in out:
        if "tickvol" not in d: d["tickvol"] = 1.0
    return [(tf, d[~d.index.duplicated()].sort_index()) for tf, d in out]


def run_symbol(args):
    sym, n_flip = args
    t0 = time.time(); cat = catalog(); comm = commission_of(sym); out = {}; log = []
    sess_list = ["us_cash"] + [s for s in sessions_of(sym) if s not in ("us_cash", "london24")]
    for tf, d in frames_of(sym, cat):
        bar = int(tf[1:])
        for sess in sess_list:
            try: S = Session(d, sess, bar=bar)
            except Exception as ex: log.append(f"{sym} {tf} {sess}: session error {ex!r}"); continue
            if len(S.days) < 150: log.append(f"{sym} {tf} {sess}: only {len(S.days)} days"); continue
            trend = structure_trend(S)
            gap = np.r_[np.nan, (S.days[1:] - S.days[:-1]).days]
            pdh = np.r_[np.nan, S.high[:-1]]; pdl = np.r_[np.nan, S.low[:-1]]
            pdh[gap > 5] = np.nan; pdl[gap > 5] = np.nan
            for k_min in (5, 15, 30):
                if k_min % bar or k_min < bar: continue
                sc = setups(S, k_min)
                for name, kind, sm, tR, xm in VARIANTS:
                    spec = build(S, sc, kind, sm, tR, xm, trend, pdh, pdl)
                    try: tr = run_cell(S, spec, comm, n_flip)
                    except Exception as ex: log.append(f"{sym} {tf} {sess} OR{k_min} {name}: {ex!r}"); continue
                    if tr is not None and len(tr): out[(sym, tf, sess, k_min, name)] = tr
            log.append(f"{sym} {tf} {sess}: {len(S.days)} days {S.days[0].date()}..{S.days[-1].date()}")
    log.append(f"{sym}: {len(out)} cells in {time.time() - t0:.0f}s")
    return out, log


def extra_stats(tr):
    R = tr.R.values
    w = R[R > 0].sum(); l = -R[R < 0].sum()
    return dict(gross=tr.gross.mean(), cost_r=tr.cost_r.median(), pf=(w / l if l > 0 else np.nan),
                tgt_rate=(tr.why == 2).mean(), stop_rate=(tr.why == 1).mean(), risk_bp=tr.risk_frac.median() * 1e4,
                long_share=(tr.d == 1).mean())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbols", default=""); ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--flips", type=int, default=10)
    a = ap.parse_args()
    cat = catalog()
    syms = sorted({k[0] for k in cat}) if not a.symbols else a.symbols.split(",")
    print(f"{len(syms)} symbols", flush=True)
    trades, logs = {}, []; t0 = time.time()
    with Pool(a.workers) as pool:
        for tr, log in pool.imap_unordered(run_symbol, [(s, a.flips) for s in syms]):
            trades.update(tr); logs += log
            print(log[-1], f"| {(time.time() - t0) / 60:.1f} min", flush=True)
    pickle.dump(trades, open(TRADES, "wb"))
    rows = []
    for (sym, tf, sess, k_min, name), tr in trades.items():
        s = cell_stats(tr); s.update(extra_stats(tr))
        s.update(symbol=sym, group=group_of(sym), tf=tf, session=sess, OR=k_min, rule=name); s["verdict"] = verdict(s)
        rows.append(s)
    cells = pd.DataFrame(rows)
    lead = ["group", "symbol", "tf", "session", "OR", "rule", "verdict", "n", "per_year", "avgR", "t", "win", "pf", "coin", "gross",
            "cost_r", "R2x", "risk_bp", "n_is", "avg_is", "t_is", "coin_is", "n_oos", "avg_oos", "t_oos", "coin_oos", "pos_years_is",
            "by_year", "first", "last"]
    cells = cells[[c for c in lead if c in cells] + [c for c in cells if c not in lead]]
    os.makedirs(RESULTS, exist_ok=True)
    cells.to_csv(os.path.join(RESULTS, "orb_retest_cells.csv"), index=False, float_format="%.4f")
    pooled = []
    keys = pd.DataFrame(list(trades.keys()), columns=["symbol", "tf", "session", "OR", "rule"])
    keys["group"] = keys.symbol.map(group_of); keys["exec"] = np.where(keys.tf == "M1", "M1", "M5+")
    for by in (["rule", "OR", "exec"], ["rule", "OR", "exec", "group"]):
        for g, kk in keys.groupby(by):
            for tag, sub in (("all", kk), ("ex-crypto", kk[kk.group != "crypto"])):
                if len(by) == 4 and tag == "ex-crypto": continue
                if not len(sub): continue
                tr = pd.concat([trades[tuple(r)] for r in sub[["symbol", "tf", "session", "OR", "rule"]].values], ignore_index=True)
                s = cell_stats(tr); s.update(extra_stats(tr)); s.update(dict(zip(by, g if isinstance(g, tuple) else (g,))))
                s.update(cells=len(sub), scope=tag); pooled.append(s)
    pooled = pd.DataFrame(pooled)
    pooled.to_csv(os.path.join(RESULTS, "orb_retest_pooled.csv"), index=False, float_format="%.4f")
    enough = int((cells.n_is >= 60).sum())
    print("\n" + false_discovery_note(enough))
    print(cells.verdict.value_counts().to_string())
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    show = ["symbol", "tf", "session", "OR", "rule", "verdict", "n", "avgR", "t", "win", "coin", "gross", "cost_r", "n_oos", "avg_oos", "t_oos"]
    sel = cells[cells.verdict.isin(["SURVIVOR", "WATCH", "FAILED out of sample"])]
    print("\nSelected in-sample:\n" + (sel[show].round(3).to_string(index=False) if len(sel) else "none"))
    with open(os.path.join(RESULTS, "orb_retest_log.txt"), "w") as f: f.write("\n".join(logs))
    print(f"\ndone in {(time.time() - t0) / 60:.1f} min; {len(cells)} cells")


if __name__ == "__main__":
    main()
