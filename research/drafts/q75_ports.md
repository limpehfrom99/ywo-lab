# q75 ports: three existing rule scripts run unchanged on the FTMO export (log #75; backlog #43, #44, #22)

2026-10-10, 08:45-09:40 MYT. Rules are the originals (imported from `bt/breakout_retest.py`, `bt/value_area.py`, `bt/smc_grid.py`);
only data loading and the cost/exit model per symbol were changed. Every cell is in the results CSVs.

| idea (backlog) | cells | positive | pass the CANDIDATE bar | expected by luck (2.5%) | primary / confirm cell | verdict |
|---|---|---|---|---|---|---|
| #43 breakout-retest A/B/C (#38) | 1,120 | 80 (7%) | 0 | 28 | 36 primary A/B cells on US100/US500 M5/M15/H1: **0 positive** | **DEAD** |
| #44 value area V1-V3 (#43) | 84 | 12 (14%) | 0 | 2.1 | US100 RTH V3 on 5-min: **+0.001R** (t 0.0, 160 trades) | **DEAD** |
| #22 SMC timeframe grid (#31b) | 390 | 57 (15%) | 1 | 9.8 | none pre-registered. The one passing cell (US30 none/H1/M5/2R: p_alone 0.005, p_best 0.095 within US30, about 0.26 across the US grids) is contradicted by US500 (t -2.8) | **DEAD** (that cell WATCH at most) |

## What was ported, and what changed (all three)

- **Data**: `quant/universe.load` (the export fixes), cut to where each file is really intraday (`bt/xgrid.full_intraday_start`), days
  with < 50% of the usual bars dropped (as `xgrid.datasets_export`). Intraday history: US100/US500 2021-10-01 (both M1 and M5; before
  that the files are daily bars), US30 2019-02, US2000 2018-01, GER40 2022-01, UK100 2021-10, other indices 2019-02 to 2021-09 (DXY
  2024-11), metals 2015 (XPD/XPT 2017-04, XCU 2024-12), forex M15 2015-01.
- **Bars**: base = the finest file (M1 for US100/US500/XAUUSD, M5 for other indices and metals, M15 for forex); M5/M15/H1 resampled
  in UTC as in the originals; **H4 and D1 on FTMO's server clock** (`xgrid.frames`, PROTOCOL 22:54). The gold originals used UTC H4. Daily
  ATR: same definition (14 days, broker day, known before the day; `xgrid.daily_atr`).
- **Costs**: export spread x 1.2 at entry + commission per side (`universe.commission_of`: indices 0, forex 0.0025%, metals 0.0007%)
  + swap for every 17:00 New York rollover held (`universe.swap_per_night` with the spec sheet; triple Wednesday FX/metals, Friday CFDs).
  The originals had no swap (gold, short holds). Swap uses today's rates for every year.
- **Exits** on the finest bars. On 1-minute bars the exit is exactly the originals' (stop first). On coarser bars (M5 for indices other
  than US100/US500 and metals other than gold; M15 for forex) limit fills use PROTOCOL's conservative rule: in the fill bar the stop
  counts and the target doesn't, and the coin flip skips the fill bar. Time limits in bars are scaled to the same market time
  (5 x 1440 and 3 x 1440 one-minute bars).
- **Fidelity check**: run with the original gold M1 data and gold costs, the port's exit/cost code reproduces #38's six 1-hour A/B cells
  exactly. Same n and mean R in every cell, e.g. A follow-through 2R: 325 trades, -0.011R; B HTF: 1,112 trades, -0.011R.
- **Look-ahead audit (PROTOCOL "same-bar look-ahead")**: none found, so only one version is reported.
  - `rule_a` and `rule_b` check the fill before any cancel. A close below the stop, or a run to 2R, cancels only later bars.
  - The prior-high target uses only bars before the fill bar.
  - The follow-through order is placed after the follow-through close.
  - `rule_c` and `value_area` enter at the next open after a decision made on a close.
  - `smc_grid` enters at the close of the respected bar. Its zones and setups use completed bars only; a zone OB is live from the bar
    after its confirming close.
  - The only fill-bar ambiguity comes from the coarse exit bars in the port, and the conservative rule above handles it. With the
    originals' fill-bar handling on those same coarse bars, rules A+B would be +0.012R better on average, which changes nothing.
- **Additions, flagged**: H4 as an entry timeframe for #43 (asked for). Rule B's HTF filter on H4 uses D1, because the script defines no
  HTF for H4. For non-US indices in #44, RTH = their own cash session (`universe.SESSIONS`); the original defined RTH for US indices only.

## #43: #38 rules A, B (and C) on the trader's own markets and everywhere else

Cells as in the script: A (two-wick level, big-body break, limit retest) with follow-through on/off x 2R / prior-high target; B (trend
candle 0.382 retest) with the HTF filter on/off; C (equal-high sweep, reverse). Symbols: 14 indices, 5 metals, 28 forex pairs. Timeframes:
M5/M15/H1/H4 (forex M15/H1/H4). 1,120 cells and 1.67M trades.

**Primary cells (US100 = NQ, US500 = ES, 2021-10 to 2026-10, M1 exits): mean R (t) [trades]**

| cell | US100 M5 | US100 M15 | US100 H1 | US500 M5 | US500 M15 | US500 H1 |
|---|---|---|---|---|---|---|
| A noFT 2R | -0.077 (-4.0) [5280] | -0.068 (-2.1) [1809] | -0.193 (-2.6) [335] | -0.144 (-6.7) [4333] | -0.100 (-2.8) [1562] | -0.151 (-2.0) [314] |
| A noFT HIGH | -0.078 (-2.0) [1216] | -0.174 (-3.0) [650] | -0.290 (-2.7) [143] | -0.175 (-3.9) [988] | -0.223 (-3.8) [576] | -0.239 (-1.8) [121] |
| A FT 2R | -0.049 (-1.6) [2109] | -0.077 (-1.5) [738] | -0.105 (-0.8) [118] | -0.088 (-2.5) [1574] | -0.143 (-2.6) [625] | -0.149 (-1.1) [96] |
| A FT HIGH | -0.063 (-1.3) [824] | -0.122 (-1.8) [451] | -0.249 (-1.8) [95] | -0.145 (-2.5) [651] | -0.256 (-3.5) [384] | -0.243 (-1.3) [66] |
| B noHTF 2R | -0.083 (-5.5) [8587] | -0.010 (-0.4) [3086] | -0.024 (-0.5) [852] | -0.140 (-9.0) [8123] | -0.078 (-3.0) [3064] | -0.084 (-1.8) [850] |
| B HTF 2R | -0.046 (-2.1) [4397] | -0.028 (-0.8) [1559] | -0.089 (-1.3) [419] | -0.113 (-5.2) [4144] | -0.058 (-1.6) [1560] | -0.115 (-1.7) [413] |
| C sweep-reverse 2R | -0.070 (-4.5) [8482] | -0.097 (-3.5) [2602] | -0.072 (-1.1) [421] | -0.096 (-5.4) [6393] | -0.094 (-3.2) [2246] | -0.117 (-1.6) [389] |

- All 36 A/B primary cells are negative, and the coin flip does better than the rule in 25 of them.
- Only 2 cells are positive before 2024 and only 1 from 2024.
- Win rates are 26-38%, far from the "very high win rate" claimed in the video.

Per-cell win %, halves, per-year means, worst year, coin and last 60 trades are in `results/q75_ports_br_cells.csv`.

**Pooled by asset group x timeframe** (all trades; then without the 0.08% of trades below -10R, whose stop was a fraction of the spread,
mostly XPDUSD and AUS200 around the rollover; then the median cell):

| group | tf | cells | cells > 0 | trades | pooled R (t) | coin | pooled R without < -10R trades | median cell |
|---|---|---|---|---|---|---|---|---|
| us_index | M5 | 28 | 0% | 150,589 | -0.146 (-40) | -0.118 | -0.145 (-40) | -0.092 |
| us_index | M15 | 28 | 0% | 54,429 | -0.117 (-19) | -0.086 | -0.117 (-19) | -0.107 |
| us_index | H1 | 28 | 14% | 12,085 | -0.090 (-7) | -0.042 | -0.090 (-7) | -0.097 |
| us_index | H4 | 28 | 39% | 3,002 | -0.106 (-4) | -0.027 | -0.106 (-4) | -0.096 |
| index | M5 | 70 | 0% | 188,521 | -0.462 (-85) | -0.426 | -0.394 (-111) | -0.395 |
| index | M15 | 70 | 0% | 67,637 | -0.306 (-47) | -0.277 | -0.278 (-48) | -0.259 |
| index | H1 | 70 | 4% | 15,950 | -0.213 (-18) | -0.159 | -0.208 (-18) | -0.235 |
| index | H4 | 70 | 21% | 3,883 | -0.125 (-5) | -0.064 | -0.125 (-5) | -0.162 |
| metal | M5 | 35 | 0% | 261,150 | -1.643 (-5) | -1.584 | -0.993 (-293) | -0.826 |
| metal | M15 | 35 | 0% | 91,595 | -2.473 (-2) | -2.463 | -0.737 (-136) | -0.594 |
| metal | H1 | 35 | 3% | 18,987 | -0.416 (-38) | -0.469 | -0.414 (-38) | -0.331 |
| metal | H4 | 35 | 23% | 4,457 | -0.263 (-12) | -0.276 | -0.263 (-12) | -0.231 |
| forex | M15 | 196 | 0% | 622,399 | -0.261 (-94) | -0.238 | -0.248 (-135) | -0.237 |
| forex | H1 | 196 | 1% | 144,400 | -0.167 (-39) | -0.159 | -0.156 (-41) | -0.165 |
| forex | H4 | 196 | 18% | 31,434 | -0.145 (-8) | -0.093 | -0.126 (-16) | -0.128 |

- Every group x timeframe pool is negative.
- 0 of 1,120 cells pass, against 28 expected by luck; dropping the tiny-stop trades still leaves 0.
- The best cell with >= 200 trades is XAUUSD H4 B no-filter: +0.060R, t 0.95, 507 trades.
- On FTMO's gold M1 the M5-H1 cells repeat #38 (-0.05 to -0.28R).

**Verdict: DEAD**, on ES/NQ (the trader's own markets) and on every other index, metal and forex pair. The H4 cells show a higher
share positive (18-39%), but on few trades and still with negative pools.

## #44: #43 value-area rules V1-V3 on 5-minute index data

The 14 indices from where their 5-minute data is intraday, ETH (broker day) and RTH (own cash session). Profile from 5-minute tick
volume; 30-minute decisions resampled from the 5-minute bars; exits on 5-minute bars; flat at the session end (no swap). 84 cells.
A **30-minute bridge** run (the original's resolution: profile, decisions and exits on 30-minute bars, on the export) is shown next to
it for US100/US500. It is not counted as a cell.

| sym | session | rule | 5-min port: mean R (t) [n] win | 30-min bridge (original resolution) |
|---|---|---|---|---|
| US100 | ETH | V1 | +0.036 (+0.6) [404] 49% | +0.062 (+1.0) [393] 50% |
| US100 | ETH | V2 | +0.040 (+0.7) [368] 50% | -0.016 (-0.3) [366] 50% |
| US100 | ETH | V3 | +0.013 (+0.3) [332] 61% | +0.004 (+0.1) [317] 61% |
| US100 | RTH | V1 | -0.030 (-0.7) [249] 61% | +0.000 (+0.0) [261] 61% |
| US100 | RTH | V2 | -0.004 (-0.1) [236] 61% | -0.003 (-0.1) [240] 61% |
| **US100** | **RTH** | **V3 (confirm cell)** | **+0.001 (+0.0) [160] 70%** | +0.085 (+1.9) [178] 75% |
| US500 | ETH | V1 | -0.058 (-1.0) [435] 47% | -0.059 (-1.1) [430] 47% |
| US500 | ETH | V2 | +0.013 (+0.2) [371] 53% | -0.015 (-0.3) [369] 52% |
| US500 | ETH | V3 | -0.041 (-0.8) [350] 57% | -0.071 (-1.4) [353] 57% |
| US500 | RTH | V1 | +0.010 (+0.2) [245] 58% | +0.041 (+0.7) [245] 59% |
| US500 | RTH | V2 | +0.044 (+1.1) [235] 63% | +0.044 (+1.1) [225] 62% |
| US500 | RTH | V3 | +0.009 (+0.2) [163] 66% | -0.020 (-0.4) [169] 65% |

**The confirm cell, against the verdict rule written in the backlog ("dead unless US100 RTH V3 holds before 2021 AND US500 RTH V3
turns positive"):**

- On the pre-registered 5-minute spec the cell is +0.001R (t 0.0, 160 trades). Before 2024 it is +0.040R; from 2024 it is -0.034R.
- The bridge reproduces the logged number (+0.085R, t 1.9 vs +0.096R, t 2.3 with the old M30 file and costs without the x1.2). So the
  old result depends on building the profile and exits from 30-minute bars, and is gone at 5-minute resolution.
- **"Before 2021" cannot be tested on US100.** The export's US100 history (M5 and M1) is daily bars before 2021-10-01.
- The nearest evidence is the same rule on the US indices that do have earlier intraday history:
  - US30, 2019-20: -0.014R (74 trades)
  - US2000, 2018-20: -0.118R (105 trades)
  - pooled: -0.075R (t -1.7, 179 trades)
- US500 RTH V3 is +0.009R (t 0.2): positive only in the third decimal.
- The rule's first condition is unconfirmed and its proxy is negative. The cell itself is zero.

**Pooled** (5-minute port):

| group | session | cells | cells > 0 | trades | pooled R (t) | coin |
|---|---|---|---|---|---|---|
| us_index | ETH | 12 | 50% | 5,980 | -0.040 (-2.9) | -0.069 |
| us_index | RTH | 12 | 33% | 3,532 | -0.033 (-3.0) | -0.029 |
| index | ETH | 30 | 0% | 10,855 | -0.207 (-17.2) | -0.172 |
| index | RTH | 30 | 7% | 6,927 | -0.090 (-10.5) | -0.111 |

Per rule: V1 -0.149 / -0.079R, V2 -0.134 / -0.046R, V3 -0.160 / -0.093R (ETH / RTH). 0 of 84 cells pass, against 2.1 expected by
luck. Dalton's "80%": in V1/V2 trades price reached the far side of value 34-55% of the time (median 43%; the `hit` column), not 80%.

**Verdict: DEAD.** This closes the WATCH from log #43.

## #22: #31b SMC timeframe grid on US indices and the 28 forex pairs

Every nesting the script defines that the data allows (zone D1/H4/none > structure H4/H1/M15 > entry M15/M5/M1; IDM or 2R target;
entries 08:00-16:00 New York):

- **US100 and US500**: 42 cells each, M1 entries from 2021-10.
- **US30**: 26 cells, M5/M15 entries, M5 exits, from 2019-02. Its 5-minute file is really intraday from then; the backlog's "from
  2021-09" was the expected start of the index files.
- **Each of the 28 forex pairs**: 10 cells, M15 entries, H1/H4 structure, D1/H4/no zone, 2015-26, M15 exits.

All 28 pairs ran: 390 cells, 50,603 trades.

| group | entry | cells | cells > 0 | trades | pooled R (t) | coin | passing | luck |
|---|---|---|---|---|---|---|---|---|
| us_index | M1 | 32 | 28% | 8,333 | -0.095 (-4.4) | -0.082 | 0 | 0.8 |
| us_index | M5 | 48 | 27% | 7,995 | -0.067 (-3.3) | -0.106 | 1 | 1.2 |
| us_index | M15 | 30 | 43% | 2,072 | -0.032 (-0.8) | -0.029 | 0 | 0.8 |
| forex | M15 | 280 | 8% | 32,203 | -0.309 (-29.3) | -0.309 | 0 | 7.0 |

- **By symbol**: US100 -0.033R (t -1.4), US500 -0.145R (t -6.3), US30 -0.038R (t -1.5).
- **Forex**: all 10 nestings are negative (-0.23 to -0.39R). Only 28 of the 280 cells have >= 200 trades, and the best t is +1.9.
- **The one cell that passes the per-cell bar: US30 none/H1/M5/2R.**
  - +0.158R, t 2.3, 474 trades (62 a year), win 40%, coin -0.209R.
  - Before 2024 +0.077R, from 2024 +0.288R. Every year from 2019 to 2026 is >= +0.015R. Longs +0.24R, shorts +0.07R.
  - BCa 95% lower bound: +0.028R.
- **Why it doesn't count:**
  - It is 1 of 390 cells, where luck predicts about 10.
  - The same cell is +0.038R (t 0.5) on US100 and **-0.221R (t -2.8)** on US500.
  - Its forex counterpart (none/H1/2R, M15 entries) is negative on all 28 pairs.
  - Most of the cell's edge comes from 2024-26 (about +0.29R a year) against +0.02 to +0.15R before, so it looks like a recent-trend
    effect.
- **Permutation check** (`bt/q75_ports_perm.py`). Not triggered by the task's rule, since no primary cell passed. The full test over
  all 390 cells would take hours, so this is the affordable part. US30's 5-minute bars were shuffled across days within their New York
  time-of-day slot, all 26 US30 cells were re-run per shuffle, and the statistic is the cell t. After 200 shuffles:
  - p_alone is **0.005**: the cell beats its own shuffled null.
  - p_best over US30's 26 cells is **0.095**. The best shuffled cell's t averages +1.51 (95th percentile +2.53); skill is +0.83 in t.
  - With mean R as the statistic, p_alone is 0.005 and p_best is 0.97, because cells with few trades produce extreme shuffled means.
  - The cell was found among 390 cells, not 26. Counting only the similar-sized US100 and US500 grids, the selection-corrected p_best is
    about 1 - (1 - 0.095)^3 ≈ 0.26, if the three grids are independent.
  - So by PROTOCOL's labels this cell is at most **WATCH** (p_alone <= 0.05, p_best > 0.10), not CANDIDATE.

**Verdict: DEAD as an idea.** As on gold (#31b), the SMC sequence has no edge at any nesting on the US indices or forex after costs.
The US30 none/H1/M5/2R cell is a single-market WATCH at most. It beats shuffled US30 data, but the identical rule loses on US500
(t -2.8) and does nothing on US100. It is not tradeable; recheck it only on data after Oct 2026.

## Caveats

- **Swaps**: today's FTMO swap rates are applied to every year. US100 longs pay about 0.023% a night today, probably more than in the
  near-zero-rate years. This matters only for the multi-day H1/H4 trades; the mean swap per trade is in the cells files.
- **Spread**: the cost is the bar's recorded spread x 1.2. Rollover spikes make a few tiny-stop trades cost tens of R. The robustness
  column above drops them, and no verdict changes.
- **History length**: the primary markets have only 5 years of intraday history in this export (2021-10 to 2026-10), against 2015+
  for metals and forex.
- **H4**: H4 cells use FTMO's server clock only. No H4 phase check was run, since nothing on H4 passed.
- **Short histories**: DXY (from 2024-11) and XCUUSD (from 2024-12) have no before-2024 half, so they cannot pass the bar.

Files:

- Code: `bt/q75_ports_common.py`, `bt/q75_ports_br.py`, `bt/q75_ports_va.py`, `bt/q75_ports_smc.py`, `bt/q75_ports_summary.py`,
  `bt/q75_ports_perm.py`
- Cells: `results/q75_ports_br_cells.csv`, `results/q75_ports_va_cells.csv` (bridge rows flagged), `results/q75_ports_smc_cells.csv`
- Summaries: `results/q75_ports_summary.csv` (pooled tables), `results/q75_ports_br_pooled_robust.csv`
- Trades: `results/q75_ports_primary_trades.csv` (every trade of the #43 / #44 US100-US500 cells and of the US30 SMC cell)
- Permutation: `results/q75_ports_perm_smc_us30.csv` (null statistics per shuffle and cell)
