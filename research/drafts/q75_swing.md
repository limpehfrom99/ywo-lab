# #75 swing ideas — pre-holiday (#32), Bollinger squeeze (#33), metal/index ratios (#36), Clenow trend (#37), trend exit grid (#39)

Run 2026-10-10 08:45-09:30 MYT on the FTMO MT5 export (94 symbols), every asset and timeframe, rules as pre-registered in log #75.
Code: `bt/q75_swing_common.py` (data, costs, stats), `q75_swing_holiday.py`, `q75_swing_squeeze.py`, `q75_swing_ratio.py`,
`q75_swing_trend.py` (#37 + #39), `q75_swing_report.py` (aggregation), `q75_swing_perm.py` (#39 permutation test),
`q75_swing_costs.py` (cost breakdown), `q75_swing_phase.py` (#39 day-start check). Results: `results/q75_swing_*.csv`.
Kernels were checked against slow re-implementations (squeeze on gold D1/H4, the five trend exits and Clenow on EURUSD D1, the
ratio rule on XAU/XAG D1): identical trades.

**Bottom line: four ideas are DEAD. In #39, one crypto cell passes the bar and the permutation test by the letter of the rules. Its edge
comes from 2011-17, so I rate it WATCH, not something to trade.**

| Idea | Primary cell | n | mean R | t | <2024 / 2024+ | baseline | Cells (share > 0) | Passing vs luck | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| #32 pre-holiday | US500 + US100 D1 | 166 | -0.142 | -2.39 | -0.130 / -0.165 | other days +0.012 | 44 (30%) | 0 vs 1.1 | DEAD |
| #33 squeeze | gold D1 / gold H4 / indices D1 | 42 / 131 / 202 | +0.186 / +0.031 / -0.071 | 1.38 / 0.41 / -1.41 | see below | coin -0.16 / -0.04 / +0.04 | 536 (19%) | 0 vs 13.4 | DEAD |
| #36 ratio | XAU/XAG D1 | 93 | -0.690 | -2.64 | -0.762 / -0.342 | coin -0.04, random -0.36 | 78 (9%) | 0 vs 2.0 | DEAD |
| #37 Clenow | D1 group portfolios | 70-2,718 | -0.192 .. +0.135 | -7.8 .. +1.4 | see table | random entries | 282 (26%); groups 8 (62%) | 1 vs 7.1; groups 0 vs 0.2 | DEAD |
| #39 exit grid | D1 pooled by group | 112 cells | crypto N55_chand2 +0.256 | 3.87 | +0.305 / +0.129 | -0.006 | 2,632 (22%); groups 112 (19%) | 1 vs 65.8; groups 2 vs 2.8 | formally CANDIDATE (one crypto cell), rated WATCH; everything else DEAD |

## Common implementation (all five ideas)
- **Bars.** The intraday base is the M5 file (66 symbols) or the M15 file (28 forex pairs). The 5 symbols that also have an M1 file
  use M5, which gives the same M15-D1 bars. The base is cut with `xgrid.full_intraday_start`, days with fewer than 50% of the usual
  bars are dropped, and stocks keep 9:30-16:00 New York only. M15, M30 and H1 are resampled on the UTC clock and H4 on the server
  clock (New York + 7 h, as in `xgrid.frames`). D1 is the export's D1 file with its full history: forex from 2000, gold 2004,
  AAPL/MSFT 2007, BTC/LTC 2011, most stocks 2019-20, indices 2017-20.
- **Costs per trade.** Spread x 1.2 at entry, plus commission x (|entry| + |exit|), plus swap for every 17:00 New York rollover held
  (x3 on the symbol's triple day; crypto pays every calendar night x1, the lab's existing convention).
- **Data problems found and how they were handled** (each one is a deviation, stated here):
  1. *Zero spreads.* The export's spread is 0 on many old bars: stocks before 2022, the second stock batch until 2026, D1 files
     before 2021. Left alone, those trades would cost nothing. Each zero is replaced by that year's median non-zero spread
     relative to price, taken from the nearest year where at least 10% of bars have a spread. A resampled bar uses the spread of
     its first 5- or 15-minute bar (the moment of entry). A D1 bar uses that day's median intraday spread.
  2. *Swaps quoted in points.* Today's swap sheet gives a fixed amount in price units. Applied to old or split-adjusted prices
     it would charge absurd amounts (about 2% a night on AAPL in 2009). It is converted to a % of price per night at the latest
     close and charged on each trade's entry price. Today's rates are still applied to the whole history, which overstates
     2009-21 financing. The cost breakdowns below show that no verdict depends on this.
  3. *Unadjusted splits.* AAPL's D1 file contains the 7:1 split of 2014-06-09 and the 4:1 split of 2020-08-31 as -86% and -75%
     moves. Stock prices are split-adjusted wherever an open/previous-close ratio is within 3% of 1/k (k = 2..30). Only AAPL's
     two splits triggered this.
  4. *Data holes.* Several files have long gaps: AAPL/MSFT intraday 2019-10 to 2021-08, N25 (3 gaps of 77-474 days), GER40 D1
     in 2018 (199 days), FX D1 in 2006-08, AUS200/US30 in 2019. Each series is cut at gaps longer than 10 days and the rules run
     on each piece separately, so no trade spans a hole.
  5. *Price glitches.* LTCUSD D1 in 2011-12 has bars at half or double the true price. They were not fixed, but the #39 result
     does not depend on them (checked below).
- **Stats.** Per-trade stats follow PROTOCOL rule 4, with halves split at 2024-01-01. Pooled t-stats treat trades on different
  symbols as independent. They are not (coins trend together, US indices close together), so where it matters an
  event-clustered or monthly-sum t is shown next to them.

## #32 Pre-holiday (Ariel 1990)
**Rule as run:** long at the cash close of the last trading day before an exchange holiday, out at the cash close of the first
trading day after it; consecutive closed weekdays count as one holiday; no stop.
- **R unit.** The pre-registration left it open. R = P/L after costs / ATR(14) of daily bars known at entry, as in the lab's
  earlier no-stop daily rules (#4, #7).
- **US calendar.** NYSE holidays from `pandas_market_calendars`. The cash close is 16:00, or 13:00 on early-close days. The
  Hurricane Sandy closure (2012-10-29/30) is excluded because nobody knew about it at the previous close. The mourning days of
  2018-12-05 and 2025-01-09 are included.
- **Close prices (which source).** Where the export is really intraday, the close of the last 5-minute bar ending at the cash
  close: US500/US100 from 2021-11 (59% of events), US30 from 2019-11, US2000 from 2018-03, stocks from 2021-22 (AAPL/MSFT also
  2015-19). Before that, the D1 close, which for index CFDs is 17:00 New York, one hour after the cash close. Each trade uses a
  single source for both ends.
- **Other indices.** Holidays are taken from each index's own data: a weekday with no bar in the local cash session, in runs of
  at most 4 weekdays. Deviation: market-wide closures such as Dec 25 and Jan 1, when FX is shut too, count as holidays, as they do
  on the NYSE side. The detected dates are in `q75_swing_holiday_calendar.csv` and look like real exchange calendars (EU about 5-6
  a year, HK50 about 14 including Lunar New Year). JP225's CFD trades through Japanese holidays, so its data only shows Western
  ones.
- **Baseline.** Every other day of the same symbol, with the same close-to-close hold and the same costs, paired by calendar year.

**Primary result.**
- US500: n=83, -0.207R, t -2.40, 0 of 9 years positive (other days +0.003).
- US100: n=83, -0.077R, t -0.94, 3 of 9 years positive (other days +0.021).
- Pooled US500+US100: n=166, -0.142R, t -2.39, before 2024 -0.130 / from 2024 -0.165, worst year 2023 -0.28. By year: 18 -0.05,
  19 -0.03, 20 -0.18, 21 +0.01, 22 -0.21, 23 -0.28, 24 -0.21, 25 -0.11, 26 -0.19. BCa 95% lower bound -0.261.
- Before costs the result is already negative: -0.14 ATR (US500) and -0.03 (US100) per event. These trades hold about 3.2 nights
  of swap, against 1.4 for an ordinary day.

**Pooled.**
| Group | n | mean R | t | Notes |
|---|---|---|---|---|
| US indices | 319 | -0.185 | -4.4 | event-clustered t -2.4 |
| US stocks | 2,082 | -0.083 | -4.4 | per event day +0.016 (t +0.3); without the second batch -0.053 (1,266) |
| Other indices (own holidays) | 325 | +0.006 | +0.1 | per event day -0.089 |

Cells: 44 (one per symbol), 30% positive, 0 passing vs 1.1 expected by luck. The best are N25 +0.40 (n=13) and JP225 +0.13 (n=20).

**Verdict: DEAD.** The published effect from 1963-2000s data is not there in FTMO's index or stock CFDs in 2007-2026.

## #33 Bollinger squeeze breakout
**Rule as run:**
- **Signal.** BB(20, 2) on closes with population std. BandWidth = (upper - lower) / middle. A squeeze is BandWidth at its lowest
  of the last 125 bars, current bar included. Within the next 20 bars, the first close outside the bands triggers entry at the
  next open. A close outside while the window is armed always disarms it, so it really is the *first* close outside.
- **Stop.** The middle band of the signal bar, fixed. It is checked first on every bar and fills at the stop, or at the open if
  the bar gaps through.
- **Exit.** The next open after a close back inside the bands.
- **Skipped trades.** Trades whose entry open is already through the stop are skipped (rare: 18 of 6,153 on gold M5). So are stops
  closer than 0.2 bp (the `xgrid` data-artefact rule).
- **Coin flip.** Same entry, opposite side, same stop distance, exits at the same "close back inside" moment unless its own stop
  hits first. A literal mirror (exit once the close is back above the lower band) would close the coin after one bar every
  time, because price sits above the upper band at entry.
- **Bars.** M5 (66 symbols), M15 to H4 from the intraday base, D1 from the export file. Forex has no M5 cell.

**Primary cells.**
| Cell | n | mean R | t | <2024 | 2024+ | Worst year | Coin |
|---|---|---|---|---|---|---|---|
| Gold D1 (2004-26) | 42 | +0.186 | 1.38 | +0.220 | -0.068 | -1.03 | -0.162 |
| Gold H4 | 131 | +0.031 | 0.41 | +0.005 | +0.100 | -0.46 | -0.042 |
| Indices D1 pooled | 202 | -0.071 | -1.41 | -0.050 | -0.107 | -0.42 | +0.036 |

Gold D1 has a BCa lower bound of -0.028. None of the three meets the bar (n >= 200 with t >= 2).

**Pooled by timeframe, without crypto.**
| Timeframe | n | mean R | Coin | Median cost per trade |
|---|---|---|---|---|
| M5 | 97,382 | -1.19 | -1.17 | 0.34R (stop = middle band, about 20 bp away) |
| M15 | 84,870 | -0.49 | -0.41 | 0.19R |
| M30 | 45,397 | -0.26 | -0.23 | 0.12R |
| H1 | 23,105 | -0.15 | -0.14 | 0.07R |
| H4 | 6,010 | -0.09 | -0.09 | 0.05R |
| D1 | 2,102 | -0.009 (t -0.5) | -0.076 | 0.03R |

D1 by group: stocks +0.031 (364), metals +0.042 (115), energy +0.033 (44), forex -0.012 (1,349), indices -0.08 / US indices
-0.05. Every intraday group x timeframe cell is negative. Stocks without the second batch: D1 +0.033, H4 -0.012.

Cells: 536, 19% positive, 0 passing vs 13.4 expected by luck. Without crypto: 494, 19% positive, 0 vs 12.4.

**Verdict: DEAD.** The breakouts are no better than a coin flip before costs. Costs decide every intraday timeframe.

## #36 Gold/silver ratio (and every pair within metals, US indices, EU indices)
**Rule as run:**
- **Signal.** z = (log(A/B) - 60-bar mean) / 60-bar std on closes, taken on bars where both legs trade. z > 2 means short A and
  long B; z < -2 means long A and short B. Both legs enter at the next opens with equal notional.
- **Exit.** The next open after z crosses 0, or 20 bars after entry, whichever comes first. One position per pair; data holes
  longer than 10 days split the series.
- **Return.** Long-leg % plus short-leg % of one leg's notional, after both legs' spread x 1.2, commissions and their own swaps.
- **R unit.** Our choice, stated here: R = that return / the 60-bar std of the log ratio at the signal bar. That std is the z unit,
  so entering at z = 2 and exiting at z = 0 earns about +2R if the mean stays put.
- **Baselines.** Coin = the opposite trade on the same bars. Random timing = same direction and holding time from 20 random entry
  bars. A cell must beat both.

**Primary: XAU/XAG D1, 2009-2026.**
- n=93, -0.690R, t -2.64, before 2024 -0.762 / from 2024 -0.342, worst year 2020 -3.29R.
- -1.23% of one leg's notional per trade: -0.43% gross plus 0.80% costs. Average -6.4% a year. By year (%): 10 -34.9, 15 +15.9,
  20 -41.9, 22 +10.6, 23 +12.6, 25 -50.2, 26 +34.5.
- Baselines: coin -0.038R, random timing -0.362R. H4: -0.63R (n=382). H1: -0.77R (n=1,443).

**Pooled by group and timeframe (mean R).**
| Pairs | D1 | H4 | H1 |
|---|---|---|---|
| Metals | -0.52 (n=442) | -0.52 | -0.79 |
| US indices | -0.54 | -0.29 | -0.19 |
| EU indices | -0.40 | -0.33 | -0.38 |

Gross results are near 0 per trade (-0.03% to +0.10% of one leg). Costs run 0.05-1.3%: two spreads (platinum, palladium and
silver are wide) and a long leg paying about 0.02-0.03% a night on metals and index CFDs.

Cells: 78, 9% positive, 0 passing vs 2.0 expected by luck. The best, XAU/XCU D1 +0.48R, has n=11.

**Verdict: DEAD.**

## #37 Clenow trend
**Rule as run:**
- **Signal.** EMA50 > EMA100 and the close is the highest close of the last 50 bars: long at the next open. The short side is the
  mirror. One position per symbol.
- **Stop.** A 3 x ATR(20) trailing stop. ATR(20) is a simple 20-bar mean of the true range, taken at the signal bar and fixed. The
  stop is the best close since entry minus 3 ATR; the entry price counts as the first "best", so the initial stop is entry - 3 ATR
  and the stop never loosens. It works intrabar, and a gap through it fills at the open.
- **R.** P/L after costs and swaps / (3 ATR at entry).
- **Baseline.** Five random entry bars per trade, same direction, same exit.
- **Portfolio.** Each group's D1 trades at equal risk, marked to market daily and summed.

**Primary: D1 group portfolios.**
| Group | n | mean R/trade | t | <2024 | 2024+ | Worst year | Random | Portfolio R/yr | Daily t |
|---|---|---|---|---|---|---|---|---|---|
| stocks | 828 | +0.020 | 0.47 | +0.001 | +0.047 | -0.59 | +0.019 | +0.9 | 0.28 |
| metals | 255 | +0.044 | 0.56 | -0.024 | +0.285 | -0.58 | -0.043 | +0.5 | 0.43 |
| US indices | 119 | +0.021 | 0.23 | -0.013 | +0.098 | -0.35 | -0.074 | +0.3 | 0.11 |
| softs | 81 | +0.058 | 0.43 | +0.145 | +0.048 | -0.48 | -0.089 | +1.4 | 0.40 |
| crypto | 338 | +0.135 | 1.42 | +0.245 | -0.131 | -0.46 | +0.059 | +1.4 | 0.62 |
| forex | 2,718 | -0.152 | -7.82 | -0.143 | -0.218 | -0.41 | -0.124 | -15.8 | -3.28 |
| other indices | 258 | -0.192 | -3.38 | -0.254 | -0.089 | -0.57 | -0.130 | -5.9 | -1.52 |
| energy | 70 | -0.189 | -0.98 | +0.102 | -0.576 | -1.14 | -0.390 | -1.3 | -1.01 |

- No group passes; 5 of 8 are positive, 0 passing vs 0.2 expected by luck.
- Pooled without crypto: D1 -0.102 (t -6.1, n=4,329), H4 -0.082, H1 -0.097.
- Stocks without the second batch, D1: +0.075 (n=481, t 1.3).
- Symbol cells: 282, 26% positive. One passes (gold H1) against 7.1 expected by luck.
- **Cost breakdown, D1 without crypto:** gross +0.008R, spread + commission -0.011, swaps -0.098. The entries make nothing before
  costs, and swaps (forex above all) make the result clearly negative. Even at cheaper historic swap rates it would stay at about
  zero.

**Verdict: DEAD.**

## #39 Trend exit grid
**Rule as run:**
- **Entries.** A close beyond the previous N-bar high or low (N = 20 or 55) enters at the next open, long or short.
- **Exits, one per cell, with no other stop.**
  - chand2/3/4: k x ATR(20) below the highest high since entry. ATR is fixed at entry and the entry price counts as the first
    high. Intrabar, with gaps filling at the open.
  - chan10: a close beyond the opposite 10-bar channel (previous 10 bars), out at the next open.
  - sma50: a close beyond the 50-bar SMA, out at the next open.
  - time20 / time60: out at the open 20 or 60 bars after entry.
- **R.** 2 x ATR(20) at entry in every cell, as pre-registered.
- **Baseline.** Five random entry bars per trade, same direction, same exit rule.
- **Timeframes.** D1 (export file) and H4 (server clock); 94 symbols x 14 cells x 2 timeframes = 2,632 symbol cells.

**Primary: D1 pooled by group (112 cells).** 19% positive; 2 pass the bar against 2.8 expected by luck, and both are crypto:

| Cell | n | mean R | t | <2024 | 2024+ | Worst year | Random | BCa 95% low |
|---|---|---|---|---|---|---|---|---|
| crypto N55_chand2 | 467 | +0.256 | 3.87 | +0.305 | +0.129 | 2018, -0.16 | -0.006 | +0.134 |
| crypto N20_chand2 | 813 | +0.105 | 2.20 | +0.141 | +0.024 | -0.24 | -0.011 | +0.017 |

- **Without crypto every group x exit cell is negative.** The best are metals N20_chand2 +0.023 (678) and US indices N20_chand4
  +0.176 (121, t 1.1).
- **Pooled over all groups without crypto,** by exit: chand2 -0.074 (N20) / -0.083 (N55) is least bad; time60 -0.33 is worst.
  Every cell has t below -5.
- **H4:** the 112 group cells are 3% positive, none passes.
- **All 2,632 symbol cells:** 22% positive, 1 passing (gold D1 N20_chand2) against 65.8 expected by luck.
- **Stocks:** D1 -0.111, or -0.074 without the second batch.
- **Cost breakdown, D1 without crypto:** gross -0.05 to +0.03R per cell; swaps cost -0.05R (chand2) to -0.34R (time60).
- **Walk-forward exit choice** (best exit of the previous 3 years, per group, timeframe and N):
  - Pooled D1 -0.055R (t -3.1, n=15,172); without crypto -0.105 (t -10.3).
  - H4 -0.090; without crypto -0.098.
  - It never beats the best fixed exit chosen with hindsight. Crypto's walk-forward of +1.21R (N20) and +0.64R (N55) rests on
    outlier years (2017, 2020, 2024). Picks are in `q75_swing_summary_exitgrid_wf_picks.csv`.

**Selection-aware permutation test (`bt/q75_swing_perm.py`).**
- **Setup.** 200 shuffles. In each, every symbol cell's trades are replaced by the same number of random-bar entries, same
  directions, same exit rule. All 224 group cells (D1 + H4) are recomputed, and the statistic is the pooled t, as in #70.
- **Null distribution.** The best cell's t has a median of 2.12, a 95th percentile of 2.76 and a 99th of 3.03. The real best is
  crypto D1 N55_time20 at t 4.12, which fails the bar because 2018 lost -0.55.
- **N55_chand2:** p_alone 0.005, p_best 0.005, skill +1.7 t.
- **N20_chand2:** p_alone 0.005, p_best 0.378, so it fails.

**Checks on N55_chand2 (`bt/q75_swing_phase.py`).**
- **Where the money was made.** 2011-17 was positive every year (+0.17 to +1.34R). 2018-26 ran -0.16, -0.05, +0.46, +0.20, -0.10,
  -0.08, +0.10, -0.06, +0.50. From 2018 only: n=326, +0.077R.
- **Correlation.** Summed by month (coins trend together), t is 2.86 for 2011-26 but only 0.82 for 2018-26.
- **Day-start phase.** Using daily bars rebuilt from the 5-minute files (2018+, the only intraday history) with the day starting
  0, 1, 2, 3, 6 or 12 hours after server midnight: +0.05 to +0.12R, t 0.7-1.6. The sign holds on every phase, but nothing is
  significant.
- **By coin:** BTC +0.37 (152 trades), ETH +0.31 (96), LTC +0.32 (83), ADA +0.12, XRP +0.07, DOGE -0.01, SOL 0.00.
- **Robustness:** without LTC 2011-12, +0.256; without the top 1% of trades, +0.18.

**Verdict.**
- By the letter of PROTOCOL (bar + p_best <= 0.10 + BCa > 0), crypto D1 "close above the 55-day high, 2-ATR chandelier" is a
  **CANDIDATE**.
- I rate it **WATCH**. The edge is the 2011-17 crypto history, before FTMO listed crypto CFDs, on thin early data. Since 2018 it is
  +0.08R per trade with t below 1 on every day-start. FTMO crypto also means 1:1 leverage and swaps of 30% a year (already
  charged).
- What would change this: +0.10R or more over the next 100+ trades from 2026-10 on.
- The other 223 group cells and the walk-forward: **DEAD**.

## Caveats common to all five
- Today's swap sheet is applied to 2000-2026. That overstates the cost of long FX, metal and index holds before 2022. The gross
  columns above show the conclusions do not depend on it: trend and ratio entries make about 0 before costs everywhere except
  crypto.
- Pooled t-stats across correlated symbols are optimistic (see the event and monthly versions above).
- Crypto D1 history from 2011-17 predates FTMO's crypto CFDs, and the export's early bars are thin (LTC 2011-12 glitches).

## Files
- `results/q75_swing_{holiday,squeeze,ratio,clenow,exitgrid}_years.csv`: per symbol x timeframe x cell x year (n, sum, sum of
  squares, wins, baseline).
- `results/q75_swing_*_cells.csv`: per-cell statistics.
- Trades: `q75_swing_holiday_trades.csv`, `q75_swing_squeeze_primary_trades.csv`, `q75_swing_ratio_trades.csv`,
  `q75_swing_clenow_d1_trades.csv`, `q75_swing_exitgrid_perm_trades.csv`.
- `q75_swing_clenow_portfolio_daily.csv`: daily mark-to-market R per group.
- `q75_swing_holiday_calendar.csv`: holidays detected from the data.
- Summaries: `q75_swing_summary_{luck,pooled,primary,groups,clenow_portfolio,exitgrid_wf,exitgrid_wf_picks}.csv`,
  `q75_swing_costs_d1.csv`, `q75_swing_exitgrid_perm.csv`, `q75_swing_phase.csv`.
