# ywo-lab — "Your way out" trading research

Shen's lab for finding a mechanical, automatable edge that passes a prop-firm challenge (FTMO or
any reputable firm that allows EAs) or earns monthly income. Everything is tested the same way so
results are comparable: rules fixed first, FTMO costs on every trade, a baseline the idea must beat,
per-year tables, t-stats. See `research/PROTOCOL.md`.

Live: opening-candle strategy on TSLA / US100 (+0.10R per trade in 2022-2026), running as an EA on
the FTMO trial. Everything else tested so far is in `research/log.md` and the strategy map
(`research/strategy-map.html`).

## Layout
- `research/PROTOCOL.md` — how every idea is tested and logged.
- `research/backlog.md` — idea queue (first `[queued]` = next). `research/log.md` — all results.
- `lab/` — data loaders, FTMO rules and costs, pass-odds Monte Carlo (`ftmo_sim.py`), news calendar.
- `bt/` — backtest engines: `sr_diag.py` (levels, touches, confirmation entries, benchmarks),
  `period_levels.py`, `smc.py`, `ict.py`, `regimes.py`, `strategies_gold.py`, `period_open.py`.
- `data/` — gold 1-minute 2012-2026 (UTC, one parquet per year), FTMO 5-minute 2021-2026 for
  gold/TSLA/AAPL/US100/US500, raw broker exports (gzip), US news calendar.
- `results/` — result tables from finished runs.

## Fresh session (cloud or laptop)
```
git clone https://github.com/limpehfrom99/ywo-lab
cd ywo-lab && pip install pandas numpy pyarrow && python3 bt/bootstrap.py
```
`bootstrap.py` rebuilds `/home/claude/data/*.pkl`, `/home/claude/lab`, `/home/claude/bt`, which
is what the engines expect. Then follow `research/PROTOCOL.md`.

## Adding fresh prices
The laptop lab (`lab_app.py`, MT5) exports CSVs. Drop new FTMO exports into `data/raw/` (gzip) and
run `bt/pack_data.py` after rebuilding the pickles, or just commit the exports; the nightly run
picks up whatever is here.
