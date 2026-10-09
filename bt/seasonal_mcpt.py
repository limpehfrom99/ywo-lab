"""Log #64 follow-up: what the seasonal-window result is made of, and a permutation test of the calendar.
Same windows, selection and costs as bt/seasonal_fx.py (#64 pre-registration). Adds:
  gross   = the same trades before spread and swap;
  carry   = trades split by the sign of today's swap for the chosen side (earning vs paying carry);
  MCPT    = the calendar is the claimed pattern, so each shuffle shifts every HISTORY year by its own random number of window
            starts (circularly within the year) before the 80% selection; the test-year trades stay real. If the windows carry
            seasonal information, misaligned history should do worse. p = share of 300 shuffles with an edge >= the real one.
  baseline = for each traded window: the mean of the same side and length over every start of that test year (all 73 starts).
python3 bt/seasonal_mcpt.py"""
import os, sys, time, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "quant"))
sys.path.insert(0, os.path.join(ROOT, "lab"))
import universe as U
from ftmo_data import load_any
from seasonal_fx import STARTS, LENS, YEARS, LOOK, spread_by_year

NS = len(STARTS)


def build(sym, cat, spec):
    D = load_any(cat[(sym, "D1")])[["open", "high", "low", "close", "sp"]]
    D = D[D.index.weekday < 5]; D = D[~D.index.duplicated()].sort_index()
    c = D.close.values; dates = D.index; n = len(c)
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(D.high.values - D.low.values, np.maximum(np.abs(D.high.values - pc), np.abs(D.low.values - pc)))
    atr = pd.Series(tr).rolling(20).mean().values
    spy = spread_by_year(sym, cat); d1sp = D.sp.values * 2.0
    doy = dates.dayofyear.values; yr = dates.year.values
    ys = np.arange(yr.min(), yr.max() + 1)
    raw = np.full((len(ys), NS, len(LENS)), np.nan)                     # raw price change of each window (history)
    net = np.full((len(ys), NS, len(LENS), 2), np.nan)                  # test-year trades in ATR units: [.., side 0=long 1=short]
    gross = np.full_like(net, np.nan); swp = np.full((len(ys), NS, len(LENS), 2), np.nan)
    for a, y in enumerate(ys):
        ii = np.flatnonzero(yr == y)
        if not len(ii): continue
        dd = doy[ii]
        for b, s in enumerate(STARTS):
            k = np.searchsorted(dd, s)
            if k >= len(ii): continue
            i = ii[k]
            for l, L in enumerate(LENS):
                j = i + L
                if j >= n: continue
                raw[a, b, l] = c[j] - c[i]
                if y < YEARS[0] or not np.isfinite(atr[i]) or atr[i] <= 0: continue
                sp = (spy.get(dates[i].year, d1sp[i]) + spy.get(dates[j].year, d1sp[j])) / 2
                nights = (dates[j] - dates[i]).days + 2 * sum(1 for kk in range(i, j) if dates[kk].weekday() == 2)
                for si, side in enumerate((1, -1)):
                    sw = U.swap_per_night(sym, c[i], side, spec) * nights
                    gross[a, b, l, si] = side * (c[j] - c[i]) / atr[i]
                    swp[a, b, l, si] = sw / atr[i]
                    net[a, b, l, si] = (side * (c[j] - c[i]) - sp - sw) / atr[i]
    return ys, raw, net, gross, swp


def trade(ys, raw, net, gross, swp, shift=None):
    """Selection from history (optionally misaligned by per-year shifts) -> list of (year, start, L, side_idx, net, gross, swap, base)."""
    out = []
    for a, Y in enumerate(ys):
        if Y not in YEARS: continue
        hist_idx = [k for k in range(a - LOOK, a) if k >= 0]
        if len(hist_idx) < 12: continue
        H = raw[hist_idx]                                               # years x starts x L
        if shift is not None:
            H = np.stack([np.roll(H[q], shift[hist_idx[q]], axis=0) for q in range(len(hist_idx))])
        cnt = np.isfinite(H).sum(0)
        up = (H > 0).sum(0) / np.maximum(cnt, 1); dn = (H < 0).sum(0) / np.maximum(cnt, 1)
        for b in range(NS):
            for l in range(len(LENS)):
                if cnt[b, l] < 12 or max(up[b, l], dn[b, l]) < 0.8: continue
                si = 0 if up[b, l] >= 0.8 else 1
                v = net[a, b, l, si]
                if not np.isfinite(v): continue
                base = np.nanmean(net[a, :, l, si])
                out.append((Y, b, l, si, v, gross[a, b, l, si], swp[a, b, l, si], base))
    return out


def nonoverlap(rows):
    keep = []; last = {}
    for r in sorted(rows, key=lambda r: (r[0], r[1], r[2])):
        Y, b, l = r[0], r[1], r[2]
        start = b * 5; end = start + LENS[l] * 7 / 5                  # calendar-day approximation of the window
        if Y in last and start < last[Y]: continue
        keep.append(r); last[Y] = end
    return keep


def main():
    cat = U.catalog(); spec = U.specs(); t0 = time.time(); rng = np.random.default_rng(63)
    syms = sorted(s for s, tf in cat if tf == "D1" and (U.group_of(s) == "forex" or s in ("XAUUSD", "XAGUSD")))
    data = {s: build(s, cat, spec) for s in syms}
    print(f"built {len(data)} markets ({time.time() - t0:.0f}s)", flush=True)

    def run(shifted):
        allr = []
        for s, (ys, raw, net, gross, swp) in data.items():
            sh = {k: int(rng.integers(0, NS)) for k in range(len(ys))} if shifted else None
            rows = nonoverlap(trade(ys, raw, net, gross, swp, sh))
            allr += [(s,) + r for r in rows]
        return pd.DataFrame(allr, columns=["symbol", "year", "start", "L", "side", "net", "gross", "swap", "base"])

    R = run(False); R["edge"] = R.net - R.base
    t = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x))
    print(f"real, non-overlapping: n={len(R)} net {R.net.mean():+.3f} ATR (t {t(R.net):+.2f}) | gross {R.gross.mean():+.3f} | swap "
          f"{R.swap.mean():+.3f} | baseline (all starts, same side/length) {R.base.mean():+.3f} | edge {R.edge.mean():+.3f} (t {t(R.edge):+.2f})")
    for lab, x in (("earning carry (swap <= 0)", R[R.swap <= 0]), ("paying carry (swap > 0)", R[R.swap > 0])):
        print(f"  {lab:28s} n={len(x):5d} net {x.net.mean():+.3f} (t {t(x.net):+.2f}) gross {x.gross.mean():+.3f} edge {x.edge.mean():+.3f}")
    for lab, x in (("2015-20", R[R.year <= 2020]), ("2021-26", R[R.year >= 2021])):
        print(f"  {lab:28s} n={len(x):5d} net {x.net.mean():+.3f} gross {x.gross.mean():+.3f} edge {x.edge.mean():+.3f}")
    perms = []
    for k in range(300):
        P = run(True); P["edge"] = P.net - P.base; perms.append((P.edge.mean(), P.gross.mean(), P.net.mean()))
        if (k + 1) % 50 == 0: print(f"  {k + 1} shuffles ({time.time() - t0:.0f}s)", flush=True)
    pe = np.array(perms)
    for lab, col, real in (("edge", 0, R.edge.mean()), ("gross", 1, R.gross.mean()), ("net", 2, R.net.mean())):
        p = (1 + (pe[:, col] >= real).sum()) / (1 + len(pe))
        print(f"MCPT {lab}: real {real:+.3f} vs shuffled mean {pe[:, col].mean():+.3f}, 95th {np.percentile(pe[:, col], 95):+.3f} -> p = {p:.3f}")
    R.to_csv(os.path.join(ROOT, "results", "seasonal_mcpt_trades.csv"), index=False)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
