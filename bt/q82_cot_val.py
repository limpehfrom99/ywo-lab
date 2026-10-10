"""Log #82 part 2: the Treasury-bond leg of Bernd's Valuation tool. #66's VAL rules (bt/bernd_daily.simulate, unchanged) rerun on
#66's universe with three references - the synthetic dollar index (DXY), a synthetic 10-year bond price from FRED DGS10 (BOND,
the ZB1! stand-in: 100 / (1 + y/200)^20) and gold (GOLD) - each alone (ROC reading and level reading, as #66) and combined:
  ALL  : every reference of the market's set beyond -0.75 (long) / +0.75 (short); entry the first day the joint condition holds.
         Sets: stocks and indices DXY + GOLD + BOND; energy DXY + GOLD (#66's set); forex/metals/crypto DXY only (= the DXY rule).
  2of3 : stocks and indices: at least two of the three beyond on one side, none beyond on the other.
The bond is aligned to each market's server dates (DGS10 of New York date D <-> the server day D, which closes 17:00 New York)
and forward-filled; like every input it is used from the next day on (bias known at the start of the day).
#66's numbers come from results/bernd_daily_trades.csv; the DXY and gold rules are rerun here and must reproduce #66's per-trade R.
python3 -I bt/q82_cot_val.py [--summary]"""
import os, sys, time
sys.path.insert(0, "/home/claude/ywo-lab/quant"); sys.path.insert(0, "/home/claude/ywo-lab/bt")
import numpy as np
import pandas as pd
import universe as U            # noqa: E402
import bernd_bias as BB         # noqa: E402
import bernd_daily as BD        # noqa: E402
import q82_cot_data as Q        # noqa: E402

RES = "/home/claude/ywo-lab/results"
THR = 0.75
GOLD66 = ("stock", "us_index", "index", "energy")          # #66 used gold for these groups only


def ref_sets(sym):
    g = U.group_of(sym)
    if g in ("stock", "us_index", "index"): return ("dxy", "gold", "bond")
    if g == "energy": return ("dxy", "gold")
    return ("dxy",)


def val_table(sym):
    d = BB.d1(sym)
    T = pd.DataFrame(index=d.index)
    bond = Q.bond_price()
    b = bond.reindex(d.index.normalize(), method="ffill"); b.index = d.index
    refs = {"dxy": BB.dxy(), "bond": b}
    if sym != "XAUUSD": refs["gold"] = BB.d1("XAUUSD").close
    for k, r in refs.items():
        T[f"val_{k}"] = BB.valuation_roc(d.close, r).reindex(d.index)
        T[f"lvl_{k}"] = BB.valuation(d.close, r).reindex(d.index)
    return T.shift(1)


def crossings(v):
    ent = []
    for i in range(1, len(v)):
        if not (np.isfinite(v[i]) and np.isfinite(v[i - 1])): continue
        if v[i] < -THR <= v[i - 1]: ent.append((i, 1))
        elif v[i] > THR >= v[i - 1]: ent.append((i, -1))
    return ent


def joint_entries(T, cols, mode):
    V = T[cols].values; fin = np.isfinite(V).all(axis=1)
    lo = (V < -THR).sum(axis=1); hi = (V > THR).sum(axis=1); k = len(cols)
    if mode == "all": L = fin & (lo == k); S = fin & (hi == k)
    else: L = fin & (lo >= 2) & (hi == 0); S = fin & (hi >= 2) & (lo == 0)
    ent = []
    for i in range(1, len(V)):
        if L[i] and not L[i - 1]: ent.append((i, 1))
        elif S[i] and not S[i - 1]: ent.append((i, -1))
    return ent


def main():
    t0 = time.time(); rng = np.random.default_rng(82); spec = U.specs(); cat = U.catalog()
    syms = sorted(s for s, tf in cat if tf == "D1" and U.group_of(s) not in ("soft",))
    out = []
    for sym in syms:
        d = BB.d1(sym)
        if d is None or len(d) < 900: continue
        T = val_table(sym); spy = BD.spread_year(sym); g = U.group_of(sym)
        rules = []
        for ref in ("dxy", "bond", "gold"):
            for kind, tag in (("val", ""), ("lvl", "_level")):
                col = f"{kind}_{ref}"
                if col not in T or T[col].notna().sum() < 250: continue
                in66 = ref == "dxy" or (ref == "gold" and g in GOLD66)
                rules.append((f"VAL_{ref}{tag}", crossings(T[col].values), in66))
        rs = ref_sets(sym)
        if len(rs) > 1:
            for kind, tag in (("val", ""), ("lvl", "_level")):
                cols = [f"{kind}_{r}" for r in rs]
                if any(c not in T for c in cols): continue
                rules.append((f"VAL_ALL{tag}", joint_entries(T, cols, "all"), False))
                if len(rs) == 3: rules.append((f"VAL_2of3{tag}", joint_entries(T, cols, "2of3"), False))
        for name, ent, in66 in rules:
            out += [dict(r, rule=name, in66=in66) for r in BD.simulate(sym, d, ent, spec, spy, rng)]
        print(f"{sym}: {sum(1 for r in out if r['symbol'] == sym)} trades ({time.time() - t0:.0f}s)", flush=True)
    R = pd.DataFrame(out); R["edge"] = R.R - R.base
    R.to_csv(os.path.join(RES, "q82_val_trades.csv"), index=False, float_format="%.6g")
    print(f"done in {time.time() - t0:.0f}s, {len(R)} trades")



# ---------------------------------------------------------------------------------------------------- summary (--summary)
def _t(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def _t_wk(x, day):
    x = np.asarray(x, float); m = np.isfinite(x); x = x[m]
    if len(x) < 3: return np.nan
    wk = (pd.to_datetime(np.asarray(day)[m]).values.astype("datetime64[D]").astype(np.int64) + 3) // 7
    e = pd.Series(x - x.mean()).groupby(wk).sum().values
    se = np.sqrt((e ** 2).sum()) / len(x)
    return x.mean() / se if se > 0 else np.nan


def summarize_rules(R, source):
    rows = []
    R = R.copy(); R["day"] = pd.to_datetime(R.day)
    for (rule, scope), x in list(R.groupby(["rule", "group"])) + [((r, "ALL"), x) for r, x in R.groupby("rule")]:
        cut = np.where(x.group.isin(["forex", "metal"]), x.day < "2018-01-01", x.day < "2023-01-01")
        rows.append(dict(source=source, rule=rule, scope=scope, n=len(x), R=x.R.mean(), t_R=_t(x.R), base=x.base.mean(),
                         edge=x.edge.mean(), t_edge=_t(x.edge), t_edge_wk=_t_wk(x.edge.values, x.day.values),
                         half1=x.edge[cut].mean(), half2=x.edge[~cut].mean(),
                         mkts_edge_pos=(x.groupby("symbol").edge.mean() > 0).mean(), n_mkts=x.symbol.nunique(),
                         R_long=x.R[x.side == 1].mean(), R_short=x.R[x.side == -1].mean(),
                         n_2025=int((x.day.dt.year == 2025).sum())))
    return pd.DataFrame(rows)


def summary():
    new = pd.read_csv(os.path.join(RES, "q82_val_trades.csv"))
    old = pd.read_csv(os.path.join(RES, "bernd_daily_trades.csv"))
    old = old[old.rule.str.startswith("VAL_")].copy()
    old["rule"] = old.rule.replace({"VAL_dxy_level": "VAL_dxy_level"})
    # reproduction check: #66 per-trade R vs the rerun (same symbol, day, side, rule)
    m = new[new.in66.astype(bool)].merge(old, on=["symbol", "day", "side", "rule"], suffixes=("", "_66"))
    rep = dict(n66=len(old), n_rerun=int(new.in66.astype(bool).sum()), matched=len(m),
               max_abs_dR=float((m.R - m.R_66).abs().max()) if len(m) else np.nan)
    S = pd.concat([summarize_rules(old, "#66 file"), summarize_rules(new, "#82 rerun")], ignore_index=True)
    S.to_csv(os.path.join(RES, "q82_val_summary.csv"), index=False, float_format="%.5g")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 300)
    print("reproduction:", rep)
    cols = ["source", "rule", "scope", "n", "R", "t_R", "base", "edge", "t_edge", "t_edge_wk", "half1", "half2", "mkts_edge_pos",
            "R_long", "R_short", "n_2025"]
    print(S[S.scope == "ALL"][cols].round(3).to_string(index=False))
    grp = S[(S.scope != "ALL") & (S.source == "#82 rerun")]
    print(grp[cols].round(3).to_string(index=False))
    return S, rep


if __name__ == "__main__":
    if "--summary" in sys.argv: summary()
    else:
        main(); summary()
