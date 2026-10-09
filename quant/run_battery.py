"""Cross-market battery: every intraday and daily rule on every symbol, fixed selection rule, reports.

python3 run_battery.py [--dry] [--symbols TSLA,US100.cash] [--flips 10] [--workers 2]
  --dry  use the data already in the lab (old 100k-bar exports + the MT4 gold history) to test the pipeline
Outputs: results/battery_cells.csv, results/battery_groups.csv, /home/claude/bt/battery_trades.pkl
"""
import os, sys, time, argparse, warnings, pickle
import numpy as np, pandas as pd
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
from universe import catalog, load, to_utc, sessions_of, group_of, commission_of, daily_bars, specs, NAME_RE  # noqa: E402
from sessions import Session  # noqa: E402
import intraday as ID  # noqa: E402
import daily as DL  # noqa: E402
from evaluate import cell_stats, verdict, false_discovery_note  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
TRADES = "/home/claude/bt/battery_trades.pkl"


def span_days(path):
    m = NAME_RE.match(os.path.basename(path))
    a, b = pd.Timestamp(m["a"][:8]), pd.Timestamp(m["b"][:8])
    return (b - a).days


def intraday_frame(sym, cat, dry=False):
    """Pick the intraday file covering the most days (finer timeframe on near-ties)."""
    cands = [(tf, cat[(sym, tf)]) for tf in ("M5", "M15", "M30") if (sym, tf) in cat]
    best = None
    for tf, p in cands:
        s = span_days(p)
        if best is None or s > best[1] * 1.05: best = (tf, s)
    d = load(sym, best[0], cat) if best else None
    if dry and sym == "XAUUSD" and os.path.exists("/home/claude/data/gold_m5.pkl"):
        g = pd.read_pickle("/home/claude/data/gold_m5.pkl")[["open", "high", "low", "close", "sp"]]
        g["tickvol"] = 1.0; d = to_utc(g, "utc"); best = ("M5(MT4)", 0)
    if d is not None:
        if "tickvol" not in d: d["tickvol"] = 1.0
        d = d[~d.index.duplicated()].sort_index()
    return d, (best[0] if best else None)


def run_symbol(args):
    sym, dry, flips = args
    t0 = time.time(); cat = catalog(); sp_df = specs()
    out_tr = {}; log = []
    d, tf = intraday_frame(sym, cat, dry)
    if d is not None and len(d) > 2000:
        for sess in sessions_of(sym):
            try: S = Session(d, sess)
            except Exception as e: log.append(f"{sym} {sess}: session error {e}"); continue
            if len(S.days) < 150: log.append(f"{sym} {sess}: only {len(S.days)} days"); continue
            for name, fn, kw, scope in ID.VARIANTS:
                if not ID.applies(scope, sess): continue
                if "minutes" in kw and kw["minutes"] % S.bar: continue
                try: tr = ID.run_variant(S, name, fn, kw, commission_of(sym), n_flip=flips)
                except Exception as e: log.append(f"{sym} {sess} {name}: {e!r}"); continue
                if tr is not None and len(tr): out_tr[("intraday", sym, sess, name)] = tr
            log.append(f"{sym} {sess}: {len(S.days)} days, {S.bar}-min bars, {S.days[0].date()}..{S.days[-1].date()}")
    D = daily_bars(sym, cat, intraday=d)
    if D is not None and len(D) > 300:
        x = DL.Daily(D, sym, sp_df if len(sp_df) else None)
        for name, fn, kw in DL.VARIANTS:
            if name in ("TOM", "HIGH52") and group_of(sym) in ("forex",): continue
            try: tr = x.run(fn(x, **kw), n_flip=flips)
            except Exception as e: log.append(f"{sym} daily {name}: {e!r}"); continue
            if len(tr): out_tr[("daily", sym, "D1", name)] = tr
        log.append(f"{sym} daily: {len(D)} days {D.index[0].date()}..{D.index[-1].date()}")
    log.append(f"{sym}: {len(out_tr)} cells in {time.time() - t0:.0f}s (intraday tf {tf})")
    return out_tr, log


def cross_sectional(syms, dry):
    cat = catalog(); sp_df = specs(); xs = {}
    stocks = [s for s in syms if group_of(s) == "stock"]
    dl = {}
    for s in stocks:
        d, _ = intraday_frame(s, cat, dry)
        D = daily_bars(s, cat, intraday=d)
        if D is not None and len(D) > 300: dl[s] = DL.Daily(D, s, sp_df if len(sp_df) else None)
    if len(dl) < 8: return xs
    for kind in ("xsmom", "xsrev"):
        for s, tr in DL.cross_section(dl, kind).items(): xs[("xsec", s, "D1", kind.upper())] = tr
    return xs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--symbols", default="")
    ap.add_argument("--flips", type=int, default=10); ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    cat = catalog()
    syms = sorted({k[0] for k in cat}) if not a.symbols else a.symbols.split(",")
    print(f"{len(syms)} symbols: {' '.join(syms)}", flush=True)
    trades, logs = {}, []
    t0 = time.time()
    with Pool(a.workers) as pool:
        for tr, log in pool.imap_unordered(run_symbol, [(s, a.dry, a.flips) for s in syms]):
            trades.update(tr); logs += log
            print(log[-1], f"| {(time.time() - t0) / 60:.1f} min", flush=True)
    trades.update(cross_sectional(syms, a.dry))
    pickle.dump(trades, open(TRADES, "wb"))
    rows = []
    for (kind, sym, sess, name), tr in trades.items():
        s = cell_stats(tr); s.update(kind=kind, symbol=sym, group=group_of(sym), session=sess, rule=name)
        s["verdict"] = verdict(s); rows.append(s)
    cells = pd.DataFrame(rows)
    lead = ["kind", "group", "symbol", "session", "rule", "verdict", "n", "per_year", "avgR", "t", "coin", "R2x", "win",
            "n_is", "avg_is", "t_is", "coin_is", "n_oos", "avg_oos", "t_oos", "coin_oos", "pos_years_is", "by_year", "first", "last"]
    cells = cells[[c for c in lead if c in cells] + [c for c in cells if c not in lead]]
    os.makedirs(RESULTS, exist_ok=True)
    cells.to_csv(os.path.join(RESULTS, "battery_cells.csv"), index=False, float_format="%.4f")
    # pooled by rule x group x session: is the effect broad?
    pooled = []
    for (kind, grp, sess, name), keys in pd.Series(list(trades.keys())).groupby(
            [[k[0] for k in trades], [group_of(k[1]) for k in trades], [k[2] for k in trades], [k[3] for k in trades]]):
        tr = pd.concat([trades[k] for k in keys], ignore_index=True)
        s = cell_stats(tr); s.update(kind=kind, group=grp, session=sess, rule=name, symbols=len(keys)); s["verdict"] = verdict(s)
        pooled.append(s)
    groups = pd.DataFrame(pooled)
    groups = groups[[c for c in ["kind", "group", "session", "rule", "symbols", "verdict"] + lead[6:] if c in groups]]
    groups.to_csv(os.path.join(RESULTS, "battery_groups.csv"), index=False, float_format="%.4f")
    enough = int((cells.n_is >= 60).sum())
    print("\n" + false_discovery_note(enough))
    print(cells.verdict.value_counts().to_string())
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    show = ["kind", "symbol", "session", "rule", "verdict", "n", "avgR", "t", "coin", "n_is", "avg_is", "t_is", "n_oos", "avg_oos", "t_oos"]
    top = cells[cells.verdict.isin(["SURVIVOR", "WATCH", "FAILED out of sample"])].sort_values("t_oos", ascending=False)
    print("\nSelected in-sample:\n" + (top[show].round(3).to_string(index=False) if len(top) else "none"))
    print("\nPooled groups selected in-sample:\n" + groups[groups.verdict.isin(["SURVIVOR", "WATCH", "FAILED out of sample"])]
          [["kind", "group", "session", "rule", "symbols", "verdict", "n", "avgR", "t", "avg_is", "t_is", "avg_oos", "t_oos"]].round(3).to_string(index=False))
    with open(os.path.join(RESULTS, "battery_log.txt"), "w") as f: f.write("\n".join(logs))
    print(f"\ndone in {(time.time() - t0) / 60:.1f} min; {len(cells)} cells")


if __name__ == "__main__":
    main()
