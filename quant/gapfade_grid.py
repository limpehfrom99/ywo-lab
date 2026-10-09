"""Log #72: robustness grid for the index opening-gap fade (#70). See research/log.md #72 for the pre-registered grid.
python3 quant/gapfade_grid.py -> results/gapfade_grid.csv"""
import os, sys, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "bt"))
import universe as U, intraday as ID
from sessions import Session
from run_battery import intraday_frame
import robust as RB

MAIN = {"GER40.cash": "eu_cash", "EU50.cash": "eu_cash", "FRA40.cash": "eu_cash", "SPN35.cash": "eu_cash", "N25.cash": "eu_cash",
        "US100.cash": "us_cash", "US500.cash": "us_cash", "US30.cash": "us_cash", "US2000.cash": "us_cash"}
OTHER = {"UK100.cash": "uk_cash", "JP225.cash": "jp_cash", "HK50.cash": "hk_cash", "AUS200.cash": "au_cash"}
CUT = pd.Timestamp("2024-01-01")


def gapfade(S, min_gap, target, stop_mode, comm):
    g = (S.open - S.prev_close) / S.atr
    ok = np.isfinite(g) & (np.abs(g) >= min_gap)
    sg = np.sign(np.nan_to_num(g)).astype(int); size = np.abs(S.open - S.prev_close)
    d = -sg; e_px = S.open; e_col = np.where(ok, S.first, -1)
    tgt = S.prev_close if target == "close" else S.open - sg * 0.5 * size
    stop = S.open + sg * size if stop_mode == "gap" else S.open + sg * S.atr
    R = ID.simulate(S, e_col, e_px, d, stop, tgt, None, comm, 1.2, False)[0]
    m = np.isfinite(R)
    return pd.DataFrame({"day": S.days[m], "R": R[m]})


def load(symbols):
    cat = U.catalog(); out = {}
    for s, sess in symbols.items():
        d, _ = intraday_frame(s, cat); out[s] = (Session(d, sess), U.commission_of(s))
    return out


def main():
    SS = load(MAIN); SO = load(OTHER)
    cells = list(itertools.product((0.75, 1.0, 1.5), ("close", "half"), ("gap", "atr")))
    rows = []; daily = {}
    for c in cells:
        T = pd.concat([gapfade(S, *c, comm).assign(sym=s) for s, (S, comm) in SS.items()])
        T["day"] = pd.to_datetime(T.day); R = T.R.values
        t = R.mean() / R.std(ddof=1) * np.sqrt(len(R))
        rows.append(dict(min_gap=c[0], target=c[1], stop=c[2], n=len(T), avgR=R.mean(), t=t, is_=T.R[T.day < CUT].mean(),
                         oos=T.R[T.day >= CUT].mean(), win=(R > 0).mean()))
        daily[c] = T.groupby("day").R.sum()
    D = pd.DataFrame(rows); pd.set_option("display.width", 200)
    print(D.round(3).to_string(index=False))
    pick = D.loc[D.is_.idxmax()]
    print(f"\npicked on data before 2024: gap {pick.min_gap} target {pick.target} stop {pick.stop}: before 2024 {pick.is_:+.3f} -> from 2024 {pick.oos:+.3f}")
    M = pd.concat([daily[c].rename(str(c)) for c in cells], axis=1).fillna(0.0).sort_index()
    cs = RB.cscv_pbo(M.values, n_blocks=10)
    print(f"CSCV over 12 cells: PBO {cs['pbo']:.0%}, in-sample winner {cs['is_best']:+.3f}R/day -> out of sample {cs['oos_best']:+.3f} "
          f"(median cell {cs['oos_median']:+.3f}), winner loses out of sample in {cs['p_oos_loss']:.0%} of splits")
    base = (1.0, "close", "gap")
    Tb = pd.concat([gapfade(S, *base, comm).assign(sym=s) for s, (S, comm) in SS.items()]); Tb["day"] = pd.to_datetime(Tb.day)
    b = RB.bca_bounds(Tb.R.values, B=20000, rng=1); bd = RB.bca_bounds(Tb.groupby("day").R.mean().values, B=20000, rng=1)
    print(f"base cell BCa 95% lower bound: per trade {b['low'][0.025]:+.3f}, per day {bd['low'][0.025]:+.3f} (mean {b['theta']:+.3f})")
    cal = pd.bdate_range(Tb.day.min(), Tb.day.max())
    x = (Tb.groupby("day").R.sum() * 0.005).reindex(cal).fillna(0.0).values
    for nf, lab in ((63, "3 months"), (252, "12 months")):
        naive, bound = RB.drawdown_bound(x, nf, q=0.95, conf=0.90, n_outer=200, n_inner=1000, rng=2, mode="start")
        print(f"gap fade alone at 0.5%/trade: loss below start, 95th pct over {lab}: {naive * 100:.1f}% (90%-confidence bound {bound * 100:.1f}%)")
    print(f"trades per year: {len(Tb) / ((Tb.day.max() - Tb.day.min()).days / 365.25):.0f}")
    oth = pd.concat([gapfade(S, *base, comm).assign(sym=s) for s, (S, comm) in SO.items()]); oth["day"] = pd.to_datetime(oth.day)
    print(f"\nindices never used for selection (UK100, JP225, HK50, AUS200), base cell: n {len(oth)}, mean {oth.R.mean():+.3f}, "
          f"t {oth.R.mean() / oth.R.std(ddof=1) * np.sqrt(len(oth)):+.2f}; by index {oth.groupby('sym').R.agg(['mean', 'size']).round(3).to_dict('index')}")
    D.to_csv(os.path.join(HERE, "..", "results", "gapfade_grid.csv"), index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
