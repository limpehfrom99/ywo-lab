"""#34 MQL5 CodeBase EAs with published performance claims (log #75, backlog #34) on every symbol and timeframe of the FTMO export.

Source code: none of the five EAs' .mq5 files could be read (mql5.com /code/download/ is robots-disallowed for the web reader and
mql5.com is blocked from the shell). Only one page publishes a complete rule set with every default:

GB4 "Gold Breakout EA for XAUUSD H4 +90 Percent in a 2020 to 2026 Backtest" (https://www.mql5.com/en/code/77691, RanaAli878,
24 Sep 2026), rules and inputs AS WRITTEN ON THE PAGE (default InpExitMode = C, fixed target; InpAllowShort = false):
  on each new bar, the bar that just closed (i): close[i] > highest high of the previous 20 bars (i-20..i-1), and the bar before did
  NOT (close[i-1] <= highest high of i-21..i-2), and close[i] > EMA(200) of closes -> buy at market (= the next bar's open);
  stop = fill - 2 x ATR(20) (MT5 ATR = simple average of true range, read on bar i), target = fill + 2R; one position at a time;
  skip when the spread > 10% of the stop distance; no entry in the last 15 minutes before the session closes; no Friday close.
  Money management (1% risk) only sets the stop distance -> R = P/L after costs / (2 x ATR).
Baselines per cell: (1) random entry bars, same side (long), same stop/target rule, same filters (the fair baseline for a long-only
rule, PROTOCOL 'daily baseline'); (2) coin = the same moments, short, same distances.
python3 bt/q75_web_mql.py [--symbols XAUUSD] [--groups gold,index] [--tfs H4] [--h4-offset 1] [--tag x]"""
import sys, os, time, zlib, argparse, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_web_common as C
U = C.U

OUT = "/home/claude/ywo-lab/results"
SCR = "/tmp/claude-0/-home-claude-ywo-lab/0f9104a2-35fd-5993-8aaf-c31d50623674/scratchpad"
TFS = ("M5", "M15", "M30", "H1", "H4", "D1")
RULE = "GB4 Gold Breakout H4 (page rules)"
MAXHOLD = 3650 * 1440 * C.NS          # no time exit in the EA: until stop, target or the end of the data


def mt5_atr(h, l, c, n):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))
    return pd.Series(tr).rolling(n).mean().values


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def gb4_signals(F, entry_bars=20, atr_n=20, stop_atr=2.0, ema_n=200):
    h, l, c = F.high.values, F.low.values, F.close.values
    hh = pd.Series(h).rolling(entry_bars).max().shift(1).values
    brk = c > hh                                   # NaN -> False
    prev = np.r_[False, brk[:-1]]
    sig = brk & ~prev & (c > ema(c, ema_n))
    sig[:max(ema_n, entry_bars + 2, atr_n + 1)] = False
    return sig, stop_atr * mt5_atr(h, l, c, atr_n)


def run(a):
    groups = [x for x in a.groups.split(",") if x] or None
    symbols = [x for x in a.symbols.split(",") if x] or None
    tfs = [x for x in a.tfs.split(",") if x] or list(TFS)
    tag = a.tag or (f"h4o{a.h4_offset}" if a.h4_offset else "")
    trd_dir = os.path.join(SCR, "q75_web_mql_trades" + (f"_{tag}" if tag else "")); os.makedirs(trd_dir, exist_ok=True)
    pool, pool_b = C.Pool(), C.Pool(); cells = []; t0 = time.time()
    for sym, grp, base_tf, d in C.datasets(groups, symbols, clean=a.clean):
        t = C.ns(d.index); o, h, l, c, sp = (d[k].values for k in ("open", "high", "low", "close", "sp"))
        comm = U.commission_of(sym); base_ns = C.TF_NS[base_tf]
        cal = C.swap_calendar(sym, t[0], t[-1])
        send = C.session_end(t, base_ns, (30 if base_tf in ("M1", "M5") else 45) * C.NS)
        fr = C.frames(d, base_tf, a.h4_offset, want=set(tfs))
        rows = []
        for tf in tfs:
            if tf not in fr or C.TF_NS[tf] < C.TF_NS[base_tf] or len(fr[tf]) < 300: continue
            F = fr[tf]; Ft = C.ns(F.index); sig, dist = gb4_signals(F)
            warm = 205

            def entries(idx):
                k0 = np.searchsorted(t, Ft[idx + 1]); k0c = np.minimum(k0, len(t) - 1)
                ok = (k0 < len(t)) & np.isfinite(dist[idx]) & (dist[idx] >= 2e-5 * np.abs(o[k0c]))
                ok &= (sp[k0c] / 1.2) <= 0.10 * np.nan_to_num(dist[idx], nan=0.0)          # spread filter (raw spread)
                ok &= (send[k0c] - t[k0c]) > 15 * C.NS                                     # not in the last 15 minutes
                return k0[ok], dist[idx][ok]

            i_sig = np.flatnonzero(sig[:-1])
            k0, ds = entries(i_sig)
            if len(k0):
                took, xi, xp, why = C.sim_bracket(t, o, h, l, c, k0.astype(np.int64), ds, np.full(len(k0), 2.0), 1, True, MAXHOLD)
                k0, ds, xi, xp, why = k0[took], ds[took], xi[took], xp[took], why[took]
            if len(k0) == 0:
                cells.append(dict(rule=RULE, asset=sym, group=grp, tf=tf, base_tf=base_tf, n=0)); continue
            t_out = np.where(why == 3, t[xi] + base_ns - 1, t[xi] + base_ns // 2)
            R, swR, nt = C.trade_R(sym, 1, o[k0], xp, ds, sp[k0], t[k0], t_out, cal, comm)
            # coin: same moments, short, same distances
            tk, cxi, cxp, cwhy = C.sim_bracket(t, o, h, l, c, k0.astype(np.int64), ds, np.full(len(k0), 2.0), -1, False, MAXHOLD)
            ct_out = np.where(cwhy == 3, t[cxi] + base_ns - 1, t[cxi] + base_ns // 2)
            Rc, _, _ = C.trade_R(sym, -1, o[k0[tk]], cxp[tk], ds[tk], sp[k0[tk]], t[k0[tk]], ct_out[tk], cal, comm)
            # random-entry baseline: long, same exits and filters
            rng = np.random.default_rng(zlib.crc32(f"{sym}|{tf}|{tag}".encode()))
            elig = np.arange(warm, len(F) - 1)
            m = int(min(2000, max(300, 3 * len(k0)), len(elig)))
            rb = np.sort(rng.choice(elig, m, replace=False)) if m > 0 else elig[:0]
            bk0, bds = entries(rb)
            Rb = np.array([])
            if len(bk0):
                btk, bxi, bxp, bwhy = C.sim_bracket(t, o, h, l, c, bk0.astype(np.int64), bds, np.full(len(bk0), 2.0), 1, False, MAXHOLD)
                bt_out = np.where(bwhy == 3, t[bxi] + base_ns - 1, t[bxi] + base_ns // 2)
                Rb, _, _ = C.trade_R(sym, 1, o[bk0[btk]], bxp[btk], bds[btk], sp[bk0[btk]], t[bk0[btk]], bt_out[btk], cal, comm)
            T = pd.DataFrame(dict(t=pd.to_datetime(t[k0]), t_out=pd.to_datetime(t_out), e=o[k0], x=xp, dist=ds, R=R, swapR=swR,
                                  nights=nt, why=why, hold_h=(t_out - t[k0]) / 3.6e12))
            st = C.cell_stats(T, base=Rb.mean() if len(Rb) else np.nan, coin=Rc.mean() if len(Rc) else np.nan)
            cells.append(dict(rule=RULE, asset=sym, group=grp, tf=tf, base_tf=base_tf, **st,
                              stop_pct=np.median(ds / o[k0]) * 100, tgt_hit=(why == 2).mean(), swapR=swR.mean()))
            T.insert(0, "tf", tf); rows.append(T)
            for key in ((tf, grp), ("ALL", grp), (tf, "ALL"), ("ALL", "ALL")) + (((tf, "ALL_ex_crypto"), ("ALL", "ALL_ex_crypto")) if grp != "crypto" else ()):
                pool.add(key, R); pool_b.add(key, Rb)
            IS = T.t < "2024-01-01"
            pool.add(("IS", "ALL"), R[IS.values]); pool.add(("OOS", "ALL"), R[~IS.values])
        if rows:
            TT = pd.concat(rows, ignore_index=True); TT.insert(0, "asset", sym); TT.insert(1, "group", grp)
            TT.to_pickle(os.path.join(trd_dir, f"{sym}.pkl"))
        done = [x for x in cells if x["asset"] == sym and x.get("n", 0) >= 10]
        print(f"{sym:12s} {base_tf} {d.index[0].date()}..{d.index[-1].date()} " +
              " ".join(f"{x['tf']}:{x['n']}/{x['avgR']:+.2f}" for x in done) + f"  ({time.time() - t0:.0f}s)", flush=True)
        del d, fr
    Cdf = pd.DataFrame(cells)
    P = pool.frame(["tf", "group"]); Pb = pool_b.frame(["tf", "group"]).rename(columns={"n": "n_base", "avgR": "base", "t": "t_base", "win": "win_base"})
    P = P.merge(Pb, on=["tf", "group"], how="left")
    sfx = f"_{tag}" if tag else ""
    if not (symbols or groups) or a.save:
        Cdf.to_csv(os.path.join(OUT, f"q75_web_mql_cells{sfx}.csv"), index=False)
        P.to_csv(os.path.join(OUT, f"q75_web_mql_pooled{sfx}.csv"), index=False)
    cc = Cdf.dropna(subset=["avgR"]) if "avgR" in Cdf else Cdf.iloc[:0]
    print(f"\n{RULE}: cells {len(cc)}, positive {(cc.avgR > 0).mean():.0%}, beat baseline {(cc.avgR > cc.base).mean():.0%}, "
          f"passing {int(cc.candidate.sum())} vs {0.025 * len(cc):.1f} by luck; {time.time() - t0:.0f}s")
    pd.set_option("display.width", 250)
    print(P.sort_values(["group", "tf"]).to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    show = cc[(cc.asset.str.startswith("XAUUSD")) | cc.candidate]
    print(show[["asset", "tf", "n", "avgR", "t", "win", "base", "coin", "is_", "oos", "last60", "worst", "yrs_pos", "by_year", "candidate"]]
          .to_string(index=False, float_format=lambda v: f"{v:+.3f}"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", default=""); ap.add_argument("--symbols", default=""); ap.add_argument("--tfs", default="")
    ap.add_argument("--h4-offset", type=int, default=0); ap.add_argument("--tag", default=""); ap.add_argument("--save", action="store_true")
    ap.add_argument("--clean", action="store_true", help="apply q75_web_common.clean_crypto to crypto symbols")
    run(ap.parse_args())
