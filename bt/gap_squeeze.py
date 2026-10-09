"""#46 — RedNote repost (油管中文配音檔案館) of a Jesse Rogers NQ live session (22.7 min): a huge gap down, everyone bearish; instead
of selling, wait for the open to prove it; sellers failed to follow through, buyers got accepted above the day's value -> long
"squeeze" toward the gap / prior high, stop under the value-area high, trailed fast near the round number. Order flow and the
heatmap can't be tested on bars; the testable core: on a big-gap day, when the open fails to continue the gap, trade the gap fill.
Fixed before running (stock-session bars 09:30-16:00 New York, FTMO 30-minute bars, Jan 2022 - Oct 2026):
  gap = 09:30 open - the previous session's close; big gap = |gap| >= 0.5 x ATR(14) of session ranges (known before the day).
  "Squeeze" = the first 30-minute candle closes against the gap (gap down and an up candle, or the mirror) -> at 10:00 trade in
  the candle's direction; stop at the candle's far end; target = the previous close (gap fill), only if beyond the entry;
  flat at 16:00. For reference: the same days without the target (= the opening-candle rule), and big-gap days where the first
  candle went with the gap.
Markets: US100, US500, TSLA, AAPL; exits on 30-minute bars (stop first); FTMO spread x 1.2 + commission (stocks 0.002% per side)."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc_grid import exit_nb, tstat
from ftmo_data import load_export

COMM = {"US100.cash": 0.0, "US500.cash": 0.0, "TSLA": 0.00002, "AAPL": 0.00002}


def session(path):
    d = load_export(path); ny = d.index - pd.Timedelta(hours=7)
    d = d.copy(); d["nyd"] = ny.normalize(); d["nym"] = ny.hour * 60 + ny.minute
    s = d[(d.nym >= 570) & (d.nym < 960)].loc["2021-12-01":]
    return s


def run(sym):
    s = session(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0]); s = s.copy(); s["sp"] = s.sp * 1.2
    day = s.groupby("nyd").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), n=("open", "size"))
    pc = day.c.shift(1)
    day["atr"] = pd.concat([day.h - day.l, (day.h - pc).abs(), (day.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    day["pc"] = pc; rows = []; comm = COMM[sym]
    for nyd, g in s.groupby("nyd"):
        if nyd < pd.Timestamp("2022-01-01") or nyd not in day.index: continue
        atr, prev = day.at[nyd, "atr"], day.at[nyd, "pc"]
        if not (np.isfinite(atr) and np.isfinite(prev)) or len(g) < 3 or g.nym.iloc[0] != 570: continue
        o0 = g.open.iloc[0]; gap = o0 - prev
        if abs(gap) < 0.5 * atr: continue
        c0, h0, l0 = g.close.iloc[0], g.high.iloc[0], g.low.iloc[0]
        if c0 == o0: continue
        d = 1 if c0 > o0 else -1; against = (np.sign(gap) == -d)
        H, L, C = g.high.values[1:], g.low.values[1:], g.close.values[1:]; e = g.open.values[1]; sp = g.sp.values[1]
        stop = l0 if d == 1 else h0; risk = d * (e - stop)
        if risk <= 0: continue
        n = len(H)
        for kind, tgt in (("gap fill", prev), ("no target", e + d * 1e9)):
            if kind == "gap fill" and (not against or d * (prev - e) <= 0): continue
            X = exit_nb(H, L, C, 0, n, stop, tgt, d); cost = sp + comm * (abs(e) + abs(X))
            Xf = exit_nb(H, L, C, 0, n, e + d * risk, (2 * e - tgt) if kind == "gap fill" else e - d * 1e9, -d)
            rows.append((kind, "against the gap" if against else "with the gap", nyd, d, (d * (X - e) - cost) / risk,
                         (-d * (Xf - e) - cost) / risk, d * (tgt - e) / risk if kind == "gap fill" else np.nan, X == tgt))
    return pd.DataFrame(rows, columns=["kind", "dir", "day", "d", "R", "R_flip", "rr", "hit"]).assign(sym=sym)


if __name__ == "__main__":
    r = pd.concat([run(s) for s in COMM])
    for (kind, dr), x in r.groupby(["kind", "dir"]):
        IS = x.day < "2024-01-01"
        per = " ".join(f"{s.split('.')[0]} {v:+.2f}({n})" for s, (v, n) in x.groupby("sym").R.agg(["mean", "size"]).iterrows())
        extra = f" | gap filled {x.hit.mean():.0%}, rr {x.rr.median():.2f}" if kind == "gap fill" else ""
        print(f"{dr:16s} {kind:10s} n={len(x):4d} avgR={x.R.mean():+.3f} t={tstat(x.R):+.1f} win={np.mean(x.R>0):.0%} coin={x.R_flip.mean():+.3f} "
              f"| <24 {x.R[IS].mean():+.3f} 24+ {x.R[~IS].mean():+.3f} | {per}{extra}")
    r.to_pickle("/home/claude/bt/gap_squeeze_trades.pkl")
