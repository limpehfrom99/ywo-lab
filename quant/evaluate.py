"""Cell statistics, the fixed selection rule, and the multiple-testing arithmetic.

Selection rule (fixed before running; nothing is tuned afterwards):
  In-sample = before CUT, out-of-sample = from CUT on. "coin" = the baseline: random direction at the same times for
  intraday rules; for daily rules the same direction and holding time from a random entry day (so plain market drift,
  e.g. stocks rising, doesn't count as an edge).
  A cell passes in-sample when: at least 60 trades, t >= 2.5, avg R beats its coin flip by >= 0.03 R, at least 60% of the
  in-sample years (with 10+ trades) are positive, and it is still positive with double the spread.
  Out-of-sample verdict for those: SURVIVOR = avg R > 0, t >= 1.65 and above its coin flip; WATCH = avg R > 0 but weaker;
  FAILED = avg R <= 0. Everything else: not selected.
Expected false passes if nothing works: P(t >= 2.5) = 0.6% of the cells in-sample, and 5% of those survive out of sample.
"""
import numpy as np, pandas as pd
from math import erf, sqrt

CUT = pd.Timestamp("2024-01-01")
IS_RULE = dict(n=60, t=2.5, edge=0.03, years=0.6)


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 3 or x.std() == 0: return np.nan
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def p_one_sided(t):
    return 0.5 * (1 - erf(t / sqrt(2)))


def cell_stats(tr, cut=CUT):
    tr = tr.dropna(subset=["R"])
    day = pd.DatetimeIndex(tr.day)
    out = dict(n=len(tr))
    if len(tr) == 0: return out
    span_y = max((day.max() - day.min()).days / 365.25, 0.25)
    bcol = "base" if "base" in tr and tr["base"].notna().any() else "coin"     # daily rules: random-timing baseline
    out.update(per_year=round(len(tr) / span_y, 1), avgR=tr.R.mean(), t=tstat(tr.R), win=(tr.R > 0).mean(),
               coin=tr[bcol].mean(), R2x=tr.R2x.mean(), first=day.min().date(), last=day.max().date(), baseline=bcol)
    if "long_only" in tr: out["long_only"] = tr.long_only.mean()
    for tag, m in (("is", day < cut), ("oos", day >= cut)):
        x = tr[m]
        out[f"n_{tag}"] = len(x)
        out[f"avg_{tag}"] = x.R.mean() if len(x) else np.nan
        out[f"t_{tag}"] = tstat(x.R) if len(x) > 2 else np.nan
        out[f"coin_{tag}"] = x[bcol].mean() if len(x) else np.nan
        out[f"R2x_{tag}"] = x.R2x.mean() if len(x) else np.nan
        yr = x.groupby(pd.DatetimeIndex(x.day).year).R.agg(["mean", "size"])
        yr = yr[yr["size"] >= 10]
        out[f"years_{tag}"] = len(yr)
        out[f"pos_years_{tag}"] = (yr["mean"] > 0).mean() if len(yr) else np.nan
    yr = tr.groupby(day.year).R.mean()
    out["by_year"] = " ".join(f"{y % 100:02d}:{v:+.2f}" for y, v in yr.items())
    return out


def verdict(s):
    if s.get("n_is", 0) < IS_RULE["n"]: return "too few in-sample"
    ok = (s["t_is"] >= IS_RULE["t"] and s["avg_is"] - s["coin_is"] >= IS_RULE["edge"]
          and (s["pos_years_is"] if np.isfinite(s["pos_years_is"]) else 0) >= IS_RULE["years"] and s["R2x_is"] > 0)
    if not ok: return "not selected"
    if s.get("n_oos", 0) < 20: return "selected, no OOS yet"
    if s["avg_oos"] > 0 and s["t_oos"] >= 1.65 and s["avg_oos"] > s["coin_oos"]: return "SURVIVOR"
    if s["avg_oos"] > 0: return "WATCH"
    return "FAILED out of sample"


def false_discovery_note(n_cells):
    p_is = p_one_sided(IS_RULE["t"])
    exp_is = n_cells * p_is
    return (f"{n_cells:,} cells had enough in-sample trades. If none had any edge, about {exp_is:.0f} would still pass the "
            f"in-sample bar by luck (t >= {IS_RULE['t']}: {p_is:.2%} each), and about {exp_is * 0.05:.1f} of those would also "
            f"pass out of sample (5%). Survivor counts well above that are signal; counts near it are luck.")
