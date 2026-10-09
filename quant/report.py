"""Compile results/battery_*.csv into results/battery_report.md (plain-language summary + tables)."""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from evaluate import false_discovery_note, CUT  # noqa: E402

RES = os.path.join(HERE, "..", "results")


def md(df, cols, fmt=None):
    if df is None or not len(df): return "_none_\n"
    d = df[cols].copy()
    for c in d:
        if d[c].dtype.kind == "f": d[c] = d[c].map(lambda v: "" if pd.isna(v) else (fmt or {}).get(c, "{:+.3f}").format(v))
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(v) for v in r) + " |\n" for r in d.values)


def main():
    cells = pd.read_csv(os.path.join(RES, "battery_cells.csv"))
    groups = pd.read_csv(os.path.join(RES, "battery_groups.csv"))
    out = [f"# Cross-market battery — {pd.Timestamp.now():%Y-%m-%d %H:%M}\n",
           f"In-sample = before {CUT.date()}, out-of-sample = from {CUT.date()} on. Rules and the selection bar were fixed before "
           "running (quant/evaluate.py). Costs: spread x1.2 + commission (+ swap on multi-day trades). R = profit after costs / "
           "amount risked.\n"]
    out.append("## Verdicts\n")
    vc = cells.verdict.value_counts()
    out.append(md(vc.rename_axis("verdict").reset_index(name="cells"), ["verdict", "cells"]))
    out.append("\n" + false_discovery_note(int((cells.n_is >= 60).sum())) + "\n")
    cols = ["kind", "symbol", "session", "rule", "n", "per_year", "avgR", "t", "coin", "R2x", "avg_is", "t_is", "avg_oos", "t_oos", "by_year"]
    fm = {"t": "{:+.1f}", "t_is": "{:+.1f}", "t_oos": "{:+.1f}", "per_year": "{:.0f}"}
    for v, title in (("SURVIVOR", "Survivors (passed in-sample, then held up out of sample)"),
                     ("WATCH", "Watch (passed in-sample, positive but weak out of sample)"),
                     ("FAILED out of sample", "Looked good in-sample, failed afterwards (what overfitting looks like)")):
        x = cells[cells.verdict == v].sort_values("t_oos" if v != "FAILED out of sample" else "t_is", ascending=False)
        out.append(f"\n## {title}: {len(x)}\n"); out.append(md(x.head(40), cols, fm))
    gcols = ["kind", "group", "session", "rule", "symbols", "verdict", "n", "avgR", "t", "avg_is", "t_is", "avg_oos", "t_oos"]
    g = groups[groups.verdict.isin(["SURVIVOR", "WATCH", "FAILED out of sample"])].sort_values("t", ascending=False)
    out.append("\n## Pooled across symbols of a group (is an effect broad?)\n"); out.append(md(g, gcols, fm))
    # breadth: per rule, share of symbols positive in each period
    b = cells.groupby(["kind", "rule"]).agg(symbols=("symbol", "nunique"), pos_is=("avg_is", lambda s: np.mean(s > 0)),
                                             pos_oos=("avg_oos", lambda s: np.mean(s > 0)), med_is=("avg_is", "median"),
                                             med_oos=("avg_oos", "median")).reset_index().sort_values("med_oos", ascending=False)
    out.append("\n## Breadth per rule (share of symbol-sessions with avg R > 0; median avg R)\n")
    out.append(md(b, ["kind", "rule", "symbols", "pos_is", "pos_oos", "med_is", "med_oos"], {"pos_is": "{:.0%}", "pos_oos": "{:.0%}"}))
    p = os.path.join(RES, "battery_conditions.csv")
    if os.path.exists(p):
        c = pd.read_csv(p); c = c[c.adopted]
        out.append("\n## Regime filters adopted in-sample (confirmed = also better out of sample)\n")
        out.append(md(c, ["cell", "filter", "n_is", "avg_is", "base_is", "n_oos", "avg_oos", "base_oos", "confirmed"]))
    p = os.path.join(RES, "battery_walkforward.csv")
    if os.path.exists(p):
        w = pd.read_csv(p)
        a = w.groupby(["kind", "family"]).agg(cells=("symbol", "size"), fwd_pos=("fwd_avgR", lambda s: np.mean(s > 0)),
                                              fwd_med=("fwd_avgR", "median"), mix_med=("mix_avgR", "median")).reset_index()
        out.append("\n## Walk-forward: each year pick the variant that did best in the previous 3 years, trade it the next year\n")
        out.append("fwd = forward result of that yearly pick; mix = trading every variant (no picking). Picking only helps where fwd beats mix.\n")
        out.append(md(a, ["kind", "family", "cells", "fwd_pos", "fwd_med", "mix_med"], {"fwd_pos": "{:.0%}"}))
    p = os.path.join(RES, "battery_ftmo.csv")
    if os.path.exists(p):
        f = pd.read_csv(p)
        out.append("\n## FTMO odds for the survivor portfolio (2-step, 10-day block resampling)\n")
        cols_f = [c for c in ["risk", "edge", "pass 1m", "pass 2m", "pass 3m", "pass 4m", "pass 12m", "fail", "median months",
                              "hist_maxDD", "worst_day", "avg_month", "keep12m", "payout_10k"] if c in f]
        out.append(md(f, cols_f, {c: "{:.2f}" for c in cols_f}))
    open(os.path.join(RES, "battery_report.md"), "w").write("\n".join(out))
    print("\n".join(out)[:6000])


if __name__ == "__main__":
    main()
