# Cross-market battery

Every intraday and daily rule, on every symbol of the full FTMO export, with the selection bar fixed in advance.

| Step | Command | Output |
|---|---|---|
| 1. Unpack + check the export | `python3 -I quant/ingest.py exports_part*.zip` | `/home/claude/data/x`, `results/data_coverage.csv` |
| 2. Run all cells | `python3 quant/run_battery.py` (`--dry` = old 100k-bar data) | `results/battery_cells.csv`, `battery_groups.csv`, trades pickle |
| 3. Regime filters (selected cells only) | `python3 quant/conditions.py` | `results/battery_conditions.csv` |
| 4. Rule books (one rule across all symbols) | `python3 quant/rule_portfolios.py` | `results/battery_rule_books.csv` |
| 5. FTMO odds for the survivors | `python3 quant/portfolio.py --extra "intraday\|TSLA\|us_cash\|OC30;intraday\|US100.cash\|us_cash\|OC30"` | `results/battery_ftmo.csv` |
| 6. Report | `python3 quant/report.py` | `results/battery_report.md` |

Files: `universe.py` (symbols, sessions, costs, leverage, swaps, loaders), `sessions.py` (day x bar matrices per
exchange session), `intraday.py` (21 intraday variants + vectorised fills), `daily.py` (10 daily variants + 2
cross-sectional), `evaluate.py` (stats, selection rule, false-discovery arithmetic).

Selection rule (evaluate.py): in-sample before 2024-01-01; pass = 60+ trades, t >= 2.5, beats its baseline by 0.03R,
60% of years positive, positive at double spread. Out of sample: SURVIVOR (avg > 0, t >= 1.65, above baseline),
WATCH (avg > 0), FAILED. Baselines: random direction at the same times (intraday); same direction and holding time
from a random day (daily, so market drift doesn't count as skill).

Fill rules worth knowing: a bar that touches both stop and target is a loss; a bar that breaks both sides of an opening
range counts as a stopped trade (skipping those days inflated ORB by ~0.08R in the dry run); targets on stop-order entries
only count from the next bar; stops that gap fill at the open.
