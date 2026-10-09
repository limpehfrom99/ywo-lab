"""Which backtest mistake inflates the Reddit ICT/OTE model? Same setups as ict_ote.py (n=3, any structure, with confluence,
Asia/London/NY AM), no costs. Each mistake switched on alone, then combined."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from ict_ote import detect, session, FILL_WIN, HOLD

def sim(setups, h, l, c, skip_entry_bar_stop=False, tp_first=False, fill_through_invalid=False, tp_on_entry_bar=False):
    N = len(h); R = np.full(len(setups), np.nan); stats = {"entry_bar_stop": 0, "sl_tp_same_bar": 0, "fill_and_invalid_same_bar": 0}
    for i, s in enumerate(setups):
        k, E, SL, TP = s["k"], s["E"], s["L"], s["H"]; risk = E - SL
        a, b = k + 1, min(k + 1 + FILL_WIN, N)
        if risk <= 0 or a >= b: continue
        fill = np.flatnonzero(l[a:b] <= E); inval = np.flatnonzero(h[a:b] > TP)
        if len(fill) == 0: continue
        f = fill[0]
        if len(inval) and inval[0] < f: continue
        if len(inval) and inval[0] == f:
            stats["fill_and_invalid_same_bar"] += 1
            if not fill_through_invalid: continue
        f += a
        if tp_on_entry_bar and h[f] >= TP: R[i] = (TP - E) / risk; continue
        if l[f] <= SL:
            stats["entry_bar_stop"] += 1
            if not skip_entry_bar_stop: R[i] = -1.0; continue
        a2, b2 = f + 1, min(f + 1 + HOLD, N)
        if a2 >= b2: continue
        st = np.flatnonzero(l[a2:b2] <= SL); tg = np.flatnonzero(h[a2:b2] >= TP)
        s0 = st[0] if len(st) else 10**9; t0 = tg[0] if len(tg) else 10**9
        if s0 == t0 and s0 < 10**9: stats["sl_tp_same_bar"] += 1
        if s0 == 10**9 and t0 == 10**9: R[i] = (c[b2 - 1] - E) / risk
        elif tp_first: R[i] = (TP - E) / risk if t0 <= s0 else -1.0
        else: R[i] = -1.0 if s0 <= t0 else (TP - E) / risk
    return R, stats

def frame(which):
    if which == "gold":
        g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl").loc["2012-01-01":"2023-12-31"]; d = g[["open","high","low","close"]]
        ny = d.index.tz_localize("UTC").tz_convert("America/New_York")
    else:
        d = load_export(glob.glob(f"/home/claude/data/assets/{which}_M1_*.csv")[0]); d.index = d.index - pd.Timedelta(hours=7)
        d.index = d.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT"); d = d[~d.index.isna()]; ny = d.index
    return d, (ny.hour * 60 + ny.minute).values

for which in ("US100.cash", "US500.cash", "gold"):
    d, nym = frame(which); h, l, o, c = (d[k].values.astype(float) for k in ("high", "low", "open", "close"))
    print(f"\n==== {which} 1-min ====")
    for look in (False, True):
        res = {}
        for mir in (False, True):
            H_, L_, O_, C_ = (h, l, o, c) if not mir else (-l, -h, -o, -c)
            st = [s for s in detect(H_, L_, O_, C_, 3, lookahead=look) if (s["fvg"] or s["ifvg"] or s["ob"]) and session(nym[s["k"]]) != "other"]
            for label, kw in (("honest", {}), ("stop ignored on the entry candle", dict(skip_entry_bar_stop=True)),
                              ("TP first when SL and TP share a candle", dict(tp_first=True)),
                              ("fill counted when the entry candle also breaks 0.0", dict(fill_through_invalid=True)),
                              ("TP counted on the entry candle", dict(tp_on_entry_bar=True)),
                              ("all four", dict(skip_entry_bar_stop=True, tp_first=True, fill_through_invalid=True, tp_on_entry_bar=True))):
                R, stt = sim(st, H_, L_, C_, **kw)
                r0 = res.setdefault(label, [[], {"entry_bar_stop": 0, "sl_tp_same_bar": 0, "fill_and_invalid_same_bar": 0}])
                r0[0].extend(R[~np.isnan(R)].tolist())
                for kk in stt: r0[1][kk] += stt[kk]
        for label, (R, stt) in res.items():
            R = np.array(R)
            extra = f"   [entry-candle stops {stt['entry_bar_stop']}, SL+TP same candle {stt['sl_tp_same_bar']}, fill+break same candle {stt['fill_and_invalid_same_bar']}]" if label == "honest" else ""
            print(f"  {'LOOK-AHEAD swings + ' if look else ''}{label:52s} n={len(R):6d} avgR={R.mean():+.3f} win={np.mean(R > 0):.1%}{extra}")
