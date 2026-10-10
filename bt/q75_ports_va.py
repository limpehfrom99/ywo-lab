"""q75 port of #43's value-area rules V1-V3 (bt/value_area.py) to the FTMO export — backlog #44, log #75.

value_area.run / va_of / prep are the original functions (imported, not copied). Changes, data only:
  - bars: the export's 5-minute file of each index from where it is really intraday (xgrid.full_intraday_start); profile from
    5-minute TICK volume; the 30-minute decision bars are resampled from those 5-minute bars (as the original did for gold);
    exits on 5-minute bars (run(px=5-min, dec=30-min)); daily ATR from the 5-minute bars (prep), copied to the 30-minute bars.
  - RTH = each index's own cash session (quant/universe SESSIONS; US indices 09:30-16:00 New York = the original); ETH = broker
    day (unchanged). value_area.sessions is replaced at run time to read that session mask.
  - costs: export spread x 1.2 at entry + commission (0 on indices); trades are flat by the session end -> no swap.
Bridge rows (not counted as cells): the original 30-minute configuration (profile, decisions and exits on 30-minute bars
resampled from the export) on US100/US500, to separate resolution effects from data effects.
Pre-registered confirm cell (backlog #44): US100 RTH V3 (+0.096R, t 2.3, 191 trades on 30-minute bars 2021-26); verdict rule:
dead unless US100 RTH V3 holds before 2021 AND US500 RTH V3 turns positive.
Usage: python3 bt/q75_ports_va.py [SYMBOL ...]"""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q75_ports_common as C                              # noqa: E402
import value_area as VA                                   # noqa: E402

OUT = os.path.join(C.RES, "q75_ports_va_cells.csv")
TRD = os.path.join(C.SCR, "va"); os.makedirs(TRD, exist_ok=True)
FIRST = ["US100.cash", "US500.cash", "US30.cash", "GER40.cash", "UK100.cash"]
AGG30 = {"open": "first", "high": "max", "low": "min", "close": "last", "vol": "sum", "sp": "mean"}


def sessions(df, kind):
    sel = df if kind == "ETH" else df[df.rth.values]
    return {k: g for k, g in sel.groupby("day")}


VA.sessions = sessions


def rth_mask(idx, sym):
    tz, a, b = C.U.SESSIONS[C.U.sessions_of(sym)[0]]
    loc = idx.tz_localize("UTC").tz_convert(tz); mins = loc.hour * 60 + loc.minute
    a = int(a[:2]) * 60 + int(a[3:]); b = int(b[:2]) * 60 + int(b[3:])
    return np.asarray((mins >= a) & (mins < b))


def frames(sym):
    d, tf = C.load_base(sym, ("M5",), cols=("open", "high", "low", "close", "sp", "tickvol"))
    if d is None: return None, None
    d = d.rename(columns={"tickvol": "vol"})
    comm = C.U.commission_of(sym)
    px = VA.prep(d, comm); px["rth"] = rth_mask(px.index, sym)
    d30 = d.resample("30min", label="left", closed="left").agg(AGG30).dropna()
    dec = VA.prep(d30, comm); dec["atr"] = px.groupby("day").atr.first().reindex(dec.day).values
    dec["rth"] = rth_mask(dec.index, sym)
    return px, dec


def run_symbol(sym, bridge=False):
    t0 = time.time(); px, dec = frames(sym)
    if px is None: print(f"{sym}: no 5-minute data", flush=True); return []
    cells = []; trades = []
    for kind in ("ETH", "RTH"):
        r = VA.run(px, dec, kind)
        if bridge:
            b = VA.run(dec, dec, kind); b["cell"] = b.cell + " (30-min bridge)"; r = pd.concat([r, b], ignore_index=True)
        r["kind"] = kind; trades.append(r)
        for cell, x in r.groupby("cell"):
            x = x.rename(columns={"R_flip": "R_coin"})
            s = C.cell_stats(x, idea="#44 value-area", sym=sym, group=C.U.group_of(sym), tf=kind, cell=cell, exit_bars="M5" if "bridge" not in cell else "M30",
                             primary=bool(sym == "US100.cash" and kind == "RTH" and cell == "V3"))
            s.update(hit=x.hit.mean(), rr_med=x.rr.median(), bridge="bridge" in cell)
            cells.append(s)
    pd.concat(trades, ignore_index=True).to_pickle(os.path.join(TRD, f"{sym}.pkl"))
    C.append_csv(cells, OUT)
    print(f"{sym:12s} 5-min {px.index[0].date()}..{px.index[-1].date()} ({time.time() - t0:.0f}s)", flush=True)
    for s in cells:
        if s["n"] >= 10:
            print(f"   {s['tf']} {s['cell']:20s} n={s['n']:5d} mean={s['mean']:+.3f} t={s['t']:+.1f} win={s['win']:.0%} hit={s['hit']:.0%} "
                  f"rr={s['rr_med']:.2f} coin={s['coin']:+.3f} <24 {s['mean_is']:+.3f} 24+ {s['mean_oos']:+.3f} yrs {s['years']}"
                  f"{'  << CANDIDATE' if s['candidate'] else ''}", flush=True)
        else:
            print(f"   {s['tf']} {s['cell']:20s} n={s['n']}", flush=True)
    return cells


if __name__ == "__main__":
    syms = sys.argv[1:] or (FIRST + [s for s in C.INDICES if s not in FIRST])
    for s in syms:
        try: run_symbol(s, bridge=s in ("US100.cash", "US500.cash"))
        except Exception as ex: print(f"{s}: ERROR {ex!r}", flush=True)
    print("done", flush=True)
