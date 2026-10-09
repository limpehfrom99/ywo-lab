"""Hedge-fund style view: each rule run as one diversified book across every symbol it applies to (equal risk per
symbol), the way a CTA runs trend-following on 50 markets. Many weak edges can add up even when no single cell passes.

Per rule (and per rule x group): daily R summed across symbols / number of symbols live that day -> Sharpe, return/vol,
max drawdown, share of positive months, separately in-sample and out-of-sample (same CUT as the cell tests).
Selection (fixed): in-sample Sharpe >= 0.8 with at least 3 symbols -> check out-of-sample Sharpe > 0.4.
"""
import os, sys, pickle
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from universe import group_of  # noqa: E402
from evaluate import CUT  # noqa: E402
from portfolio import book_dates  # noqa: E402

RES = os.path.join(HERE, "..", "results")


def book(trades, keys):
    parts = []
    for k in keys:
        tr = trades[k]
        s = pd.Series(tr.R.values, index=book_dates(k, tr)).groupby(level=0).sum()
        parts.append(s.rename("|".join(k[1:])))
    df = pd.concat(parts, axis=1, sort=True)
    live = pd.DataFrame({c: (df.index >= df[c].first_valid_index()) & (df.index <= df[c].last_valid_index()) for c in df}, index=df.index)
    cal = pd.bdate_range(df.index.min(), df.index.max())
    df = df.reindex(cal).fillna(0); live = live.reindex(cal).ffill().fillna(False)
    return df.sum(axis=1) / live.sum(axis=1).clip(lower=1)


def perf(r):
    if len(r) < 60 or r.std() == 0: return dict(sharpe=np.nan)
    eq = r.cumsum(); dd = (eq - eq.cummax()).min()
    m = r.groupby(r.index.to_period("M")).sum()
    return dict(sharpe=r.mean() / r.std() * np.sqrt(252), ann_R=r.mean() * 252, maxDD_R=dd, pos_months=(m > 0).mean(), days=len(r))


def main():
    trades = pickle.load(open("/home/claude/bt/battery_trades.pkl", "rb"))
    keys = list(trades)
    rows = []
    groupings = {}
    for k in keys:
        groupings.setdefault((k[0], k[3], "all"), []).append(k)
        groupings.setdefault((k[0], k[3], group_of(k[1])), []).append(k)
    for (kind, rule, grp), ks in groupings.items():
        if len(ks) < 3 and grp == "all": continue
        r = book(trades, ks)
        a, b = perf(r[r.index < CUT]), perf(r[r.index >= CUT])
        sel = (a.get("sharpe", np.nan) >= 0.8) and len(ks) >= 3
        rows.append(dict(kind=kind, rule=rule, group=grp, symbols=len(ks), sharpe_is=a.get("sharpe"), sharpe_oos=b.get("sharpe"),
                         annR_is=a.get("ann_R"), annR_oos=b.get("ann_R"), maxDD_R_oos=b.get("maxDD_R"), posm_oos=b.get("pos_months"),
                         verdict=("SURVIVOR" if sel and b.get("sharpe", -9) > 0.4 else "FAILED out of sample" if sel else "not selected")))
    df = pd.DataFrame(rows).sort_values(["verdict", "sharpe_oos"], ascending=[True, False])
    df.to_csv(os.path.join(RES, "battery_rule_books.csv"), index=False, float_format="%.3f")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
