"""#38 freqtrade-strategies (log #75, backlog #38): Strategy001-005 ported from github.com/freqtrade/freqtrade-strategies
(commit f3340ce, 8 Sep 2026; read as text from a fresh clone, never imported). Indicators with TA-Lib 0.8.1 (the library freqtrade's
talib.abstract calls, same defaults) and qtpylib's formulas re-implemented (heikinashi, typical_price, bollinger_bands with
pandas rolling std ddof=1 and min_periods=1, crossed_above = a > b and a[-1] <= b[-1]).

Why these five: they are the repo's original numbered reference strategies (Strategy001-005, author Gerald Lonlas), the README's
own install/test examples use Strategy001, and all five are long-only with the repo's standard defaults. All five: timeframe 5m,
stoploss -10%, no trailing stop, use_exit_signal True, exit_profit_only True (an exit signal is honoured only while the trade is in
profit), ignore_roi_if_entry_signal False, one open trade per pair. ROI (minutes: profit): S1-S4 {0: 5%, 20: 4%, 30: 3%, 60: 1%};
S5 {0: 5%, 20: 4%, 40: 3%, 80: 2%, 1440: 1%}. S5 runs with its hyperopt buy_params / sell_params (freqtrade loads those over the
IntParameter defaults): volumeAVG 150, rsi 26, fastd 1, fishRsiNorma 5; sell trigger rsi-macd-minusdi with rsi 74, minusDI 4.
Volume = FTMO tick volume (CFDs carry no real volume): used by S3 (MFI), S4 (12-bar mean volume > 0.75: always true on tick
volume) and S5 (volume > 4 x its 150-bar mean).
Backtest semantics (q75_web_common.sim_ft): signals on closed candles, entry at the next candle's open; inside each bar (finest
bars of the symbol: M5 for crypto) exit signal at the open first, then stoploss (low), then ROI (high) by trade age.
R = P/L after FTMO costs / (10% of the entry price). Costs: spread x 1.2 at entry + 0.0325% commission per side + swaps.
Baseline per cell: random entry candles, same exits (stop, ROI table, the strategy's exit signals), long.
python3 bt/q75_web_ft.py [--symbols BTCUSD,ETHUSD] [--tfs M5,M30,H1,H4]"""
import sys, os, time, zlib, argparse, numpy as np, pandas as pd
import talib
sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_web_common as C
U = C.U

OUT = "/home/claude/ywo-lab/results"
SCR = "/tmp/claude-0/-home-claude-ywo-lab/0f9104a2-35fd-5993-8aaf-c31d50623674/scratchpad"
TFS = ("M5", "M30", "H1", "H4")
ROI_A = ([0, 20, 30, 60], [0.05, 0.04, 0.03, 0.01])
ROI_B = ([0, 20, 40, 80, 1440], [0.05, 0.04, 0.03, 0.02, 0.01])
MAXHOLD = 365 * 1440 * C.NS            # freqtrade has no time exit; cap at a year (never binds in practice)


def crossed_above(a, b):
    a = np.asarray(a, float); b = np.broadcast_to(np.asarray(b, float), a.shape)
    pa = np.r_[np.nan, a[:-1]]; pb = np.r_[np.nan, b[:-1]]
    with np.errstate(invalid="ignore"):
        return (a > b) & (pa <= pb)


def heikinashi(o, h, l, c):
    hc = (o + h + l + c) / 4
    ho = np.empty(len(c)); ho[0] = (o[0] + c[0]) / 2
    for i in range(1, len(c)): ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    return ho, hc


def fisher(rsi):
    r = 0.1 * (rsi - 50)
    return (np.exp(2 * r) - 1) / (np.exp(2 * r) + 1)


def bb_lower(h, l, c, window=20, stds=2):
    tp = pd.Series((h + l + c) / 3)
    return (tp.rolling(window, min_periods=1).mean() - tp.rolling(window, min_periods=1).std() * stds).values


def signals(name, F):
    o, h, l, c, v = (F[k].values.astype(float) for k in ("open", "high", "low", "close", "tickvol"))
    lt = lambda a, b: np.less(a, b, where=np.isfinite(a) & np.isfinite(b), out=np.zeros(len(c), bool))
    gt = lambda a, b: np.greater(a, b, where=np.isfinite(a) & np.isfinite(b), out=np.zeros(len(c), bool))
    if name == "S1":
        e20, e50, e100 = talib.EMA(c, 20), talib.EMA(c, 50), talib.EMA(c, 100)
        ho, hc = heikinashi(o, h, l, c)
        ent = crossed_above(e20, e50) & gt(hc, e20) & (ho < hc)
        ex = crossed_above(e50, e100) & lt(hc, e20) & (ho > hc)
    elif name == "S2":
        slowk, _ = talib.STOCH(h, l, c); rsi = talib.RSI(c); fr = fisher(rsi)
        ham = talib.CDLHAMMER(o, h, l, c); sar = talib.SAR(h, l)
        ent = lt(rsi, 30) & lt(slowk, 20) & gt(bb_lower(h, l, c), c) & (ham == 100)
        ex = gt(sar, c) & gt(fr, 0.3)
    elif name == "S3":
        mfi = talib.MFI(h, l, c, v); fastk, fastd = talib.STOCHF(h, l, c); rsi = talib.RSI(c); fr = fisher(rsi)
        e5, e10, e50, e100 = (talib.EMA(c, n) for n in (5, 10, 50, 100)); sar = talib.SAR(h, l); sma = talib.SMA(c, 40)
        ent = (lt(rsi, 28) & gt(rsi, 0) & lt(c, sma) & lt(fr, -0.94) & lt(mfi, 16.0) & (gt(e50, e100) | crossed_above(e5, e10))
               & gt(fastd, fastk) & gt(fastd, 0))
        ex = gt(sar, c) & gt(fr, 0.3)
    elif name == "S4":
        adx, sadx, cci = talib.ADX(h, l, c, 14), talib.ADX(h, l, c, 35), talib.CCI(h, l, c, 14)
        fk, fd = talib.STOCHF(h, l, c, 5); sk, sd = talib.STOCHF(h, l, c, 50)
        fkp, fdp, skp, sdp = (np.r_[np.nan, x[:-1]] for x in (fk, fd, sk, sd))
        e5 = talib.EMA(c, 5); mv = pd.Series(v).rolling(12).mean().values
        ent = ((gt(adx, 50) | gt(sadx, 26)) & lt(cci, -100) & lt(fkp, 20) & lt(fdp, 20) & lt(skp, 30) & lt(sdp, 30) & lt(fkp, fdp)
               & gt(fk, fd) & gt(mv, 0.75) & (c > 0.00000100))
        ex = lt(sadx, 25) & (gt(fk, 70) | gt(fd, 70)) & lt(fkp, fdp) & gt(c, e5)
    elif name == "S5":
        macd, _, _ = talib.MACD(c); mdi = talib.MINUS_DI(h, l, c); rsi = talib.RSI(c); fn = 50 * (fisher(rsi) + 1)
        fk, fd = talib.STOCHF(h, l, c); sma = talib.SMA(c, 40); vm = pd.Series(v).rolling(150).mean().values * 4
        ent = (c > 0.00000200) & gt(v, vm) & lt(c, sma) & gt(fd, fk) & gt(rsi, 26) & gt(fd, 1) & lt(fn, 5)
        ex = crossed_above(rsi, 74) & lt(macd, 0) & gt(mdi, 4)
    else:
        raise ValueError(name)
    return ent, ex


STRATS = {"S1": ("Strategy001 EMA20/50 cross + Heikin-Ashi", ROI_A), "S2": ("Strategy002 RSI/Stoch/BB + hammer", ROI_A),
          "S3": ("Strategy003 RSI/MFI/Fisher dip", ROI_A), "S4": ("Strategy004 ADX/CCI/StochF", ROI_A),
          "S5": ("Strategy005 volume spike + Fisher RSI (hyperopt params)", ROI_B)}


def run(a):
    symbols = [x for x in a.symbols.split(",") if x] or None
    tfs = [x for x in a.tfs.split(",") if x] or list(TFS)
    names = [x for x in a.strats.split(",") if x] or list(STRATS)
    trd_dir = os.path.join(SCR, "q75_web_ft_trades"); os.makedirs(trd_dir, exist_ok=True)
    pool, pool_b = C.Pool(), C.Pool(); cells = []; t0 = time.time()
    for sym, grp, base_tf, d in C.datasets(["crypto"], symbols, clean=not a.raw):
        t = C.ns(d.index); o, h, l, c, sp = (d[k].values for k in ("open", "high", "low", "close", "sp"))
        comm = U.commission_of(sym); base_ns = C.TF_NS[base_tf]; cal = C.swap_calendar(sym, t[0], t[-1])
        fr = C.frames(d, base_tf, 0, want=set(tfs)); rows = []
        for tf in tfs:
            if tf not in fr or C.TF_NS[tf] < C.TF_NS[base_tf] or len(fr[tf]) < 500: continue
            F = fr[tf]; Ft = C.ns(F.index); nF = len(F)
            kF = np.searchsorted(t, Ft)                         # first finest bar of each frame bar
            for nm in names:
                label, (rmin, rval) = STRATS[nm]
                ent, ex = signals(nm, F)
                ent[:200] = False                               # indicator warm-up (freqtrade startup candles)
                exit_open = np.zeros(len(t), np.bool_)
                xs = np.flatnonzero((ex & ~ent)[:-1]); exit_open[kF[xs + 1]] = True
                roi_ns = np.array(rmin, np.int64) * C.NS; roi_v = np.array(rval, float)

                def go(idx, one_pos):
                    k0 = kF[idx + 1].astype(np.int64)
                    tk, xi, xp, why = C.sim_ft(t, o, h, l, c, sp, k0, 0.10, roi_ns, roi_v, exit_open, comm, True, one_pos, MAXHOLD)
                    k0, xi, xp, why = k0[tk], xi[tk], xp[tk], why[tk]
                    t_out = np.where(why == 4, t[xi], np.where(why == 3, t[xi] + base_ns - 1, t[xi] + base_ns // 2))
                    R, swR, nt = C.trade_R(sym, 1, o[k0], xp, 0.10 * o[k0], sp[k0], t[k0], t_out, cal, comm)
                    return k0, xp, why, t_out, R, swR, nt

                i_sig = np.flatnonzero(ent[:-1])
                k0, xp, why, t_out, R, swR, nt = go(i_sig, True)
                rng = np.random.default_rng(zlib.crc32(f"{sym}|{tf}|{nm}".encode()))
                elig = np.arange(200, nF - 1); m = int(min(3000, max(500, 2 * len(k0)), len(elig)))
                _, _, _, _, Rb, _, _ = go(np.sort(rng.choice(elig, m, replace=False)), False)
                rule = f"{nm} {label}"
                if len(k0) == 0:
                    cells.append(dict(rule=rule, asset=sym, group=grp, tf=tf, n=0, base=Rb.mean())); continue
                T = pd.DataFrame(dict(t=pd.to_datetime(t[k0]), t_out=pd.to_datetime(t_out), e=o[k0], x=xp, R=R, swapR=swR, nights=nt,
                                      why=why, hold_h=(t_out - t[k0]) / 3.6e12))
                st = C.cell_stats(T, base=Rb.mean() if len(Rb) else np.nan)
                cells.append(dict(rule=rule, asset=sym, group=grp, tf=tf, **st, ret_pct=(R * 10).mean(),
                                  exit_stop=(why == 1).mean(), exit_roi=(why == 2).mean(), exit_sig=(why == 4).mean()))
                T.insert(0, "rule", nm); T.insert(1, "tf", tf); rows.append(T)
                for key in ((nm, tf, "crypto"), (nm, "ALL", "crypto")):
                    pool.add(key, R); pool_b.add(key, Rb)
                IS = (T.t < "2024-01-01").values
                pool.add((nm, "IS", "crypto"), R[IS]); pool.add((nm, "OOS", "crypto"), R[~IS])
        if rows:
            TT = pd.concat(rows, ignore_index=True); TT.insert(0, "asset", sym); TT.to_pickle(os.path.join(trd_dir, f"{sym}.pkl"))
        print(f"{sym} {base_tf} {d.index[0].date()}..{d.index[-1].date()} done ({time.time() - t0:.0f}s)", flush=True)
    Cdf = pd.DataFrame(cells)
    P = pool.frame(["strategy", "tf", "group"]).merge(
        pool_b.frame(["strategy", "tf", "group"]).rename(columns={"n": "n_base", "avgR": "base", "t": "t_base", "win": "win_base"}),
        on=["strategy", "tf", "group"], how="left")
    if not symbols or a.save:
        sfx = "_raw" if a.raw else ""
        Cdf.to_csv(os.path.join(OUT, f"q75_web_ft_cells{sfx}.csv"), index=False); P.to_csv(os.path.join(OUT, f"q75_web_ft_pooled{sfx}.csv"), index=False)
    pd.set_option("display.width", 250)
    cc = Cdf.dropna(subset=["avgR"])
    for nm, x in cc.groupby(cc.rule.str[:2]):
        print(f"{nm}: cells {len(x)}, positive {(x.avgR > 0).mean():.0%}, beat baseline {(x.avgR > x.base).mean():.0%}, "
              f"passing {int(x.candidate.sum())} vs {0.025 * len(x):.1f} by luck")
    print(P.sort_values(["strategy", "tf"]).to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
    print(cc[["rule", "asset", "tf", "n", "avgR", "t", "win", "base", "is_", "oos", "worst", "yrs_pos", "ret_pct", "exit_stop", "exit_roi",
              "exit_sig", "candidate"]].to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=""); ap.add_argument("--tfs", default=""); ap.add_argument("--strats", default="")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--raw", action="store_true", help="skip q75_web_common.clean_crypto (broken 2018-20 spreads, 1/100 price bars)")
    run(ap.parse_args())
