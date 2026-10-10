# #82 Bernd's COT tool and the bond leg of his Valuation tool, on every market the data covers

Pre-registration: research/log.md #82 (10 Oct 2026 10:25 MYT). Code: `bt/q82_cot_data.py` (data layer, reusable COT rule),
`bt/q82_cot.py` (part 1 + part 4), `bt/q82_cot_val.py` (part 2, bond leg), `bt/q82_cot_conf.py` (part 3, confluence + COT filter).
Results: `results/q82_*.csv`. Data checks: `bt/q82_cot_checks.py`.

**Bottom line: DEAD.** Bernd's COT setting (commercials, 3-year index, 80/20) loses on the 15 commodity CFDs at every hold:
-0.19 / -0.64 / -1.43 ATR a trade at 1 / 4 / 8 weeks, t -4.5 to -5.1. It is still negative with swaps removed. It does pick better weeks
than random weeks of the same year on the same side (+0.12 to +0.39 ATR, t 1.5-3.2), but it loses to plain always-long. 0 of 54
commodity cells make money. The US-index version (calendar large speculators) is positive at 4 and 8 weeks on 30-50 trades
(t <= 0.6), inside luck. The bond leg reproduces #66's pattern: timing information, no money after costs. It adds nothing over
#66's gold reference. Bernd's full confluence can't be tested: seasonality needs 12+ years of prices, which only gold and silver
have, and the strict version leaves 1 trade. As a filter on #66's trades, COT agreement does not improve R. A bug was found in
`bt/bernd_bias.seasonal` (it affected 66% of #66's SEAS trades), but #66's SEAS verdict does not change.

| Part | What | n | mean R after costs | vs baselines | Verdict |
|---|---|---|---|---|---|
| 1 | COT primary, commodities, hold 4 w | 529 | -0.635 ATR (t -4.46) | random-week -0.944, always-long -0.073 | DEAD (fails rule 4; loses to always-long) |
| 1 | same, hold 1 / 8 w | 1,697 / 307 | -0.188 / -1.429 | beats random, loses to always-long | DEAD |
| 1 | US-index COT (large specs), 157, 80/20, 4 w | 50 | +0.286 (t 0.59) | random -0.204, always-long -0.094 | formally WATCH (n 50); no evidence |
| 2 | VAL vs bonds (ROC / level), every market | 3,331 / 1,551 | -0.109 / -0.179 R | edge vs random +0.048 / +0.067 | DEAD as trades (as #66) |
| 2 | VAL combination ALL (stocks/indices/energy) | 542 / 341 | -0.074 / -0.226 R | edge +0.149 / +0.238 | DEAD as trades; timing like #66's gold leg |
| 3 | COT + VAL + SEAS confluence | 1 (strict) / 18 (cheap side) | -1.08 ATR (cheap) | - | untestable on FTMO history |
| 3 | COT filter on #66 trades | 848 kept of 5,321 | kept -0.147 vs rest -0.109 R | - | no improvement |
| 4 | permutation test | - | - | gate not met | not run (diagnostic only, below) |

## Rules as implemented (written 10:27 MYT, before any result was computed)

Details the log entry left open, fixed here before running:

1. **COT data.** CFTC Disaggregated Futures-Only, 2006-06-13 to 2026-10-06, read with pandas only. Markets mapped by
   CFTC_Contract_Market_Code (names change in 2007, 2013 and 2022). Net = long - short per group (spread positions cancel).
   Commercials = producer/merchant + swap dealers; large speculators = managed money + other reportables (index inverted);
   small speculators = non-reportables (index inverted). COT index = 100 x (net - min) / (max - min) over the last N reports,
   current report included, a full window required.
2. **Release times.** The MT5 calendar's "CFTC Gold Non-Commercial Net Positions" equals the Disaggregated gold managed money +
   other reportables net to +-0.05k, so each calendar release (2012+) is matched to its as-of date by value; crude oil gives the
   same matching (763 of 764 weeks; the one disagreement takes the later time). Weeks with no calendar match (2006-2011 and 5
   later weeks) use the rule "Friday 15:30 New York; next business day if a federal holiday falls on Wednesday-Friday". Where
   both exist (2012-26, outside the catch-ups), the rule matches the calendar in 98% of weeks, is later in 12 holiday weeks of
   2012-14 and earlier in one (the 5 Dec 2018 day of mourning), so pre-2012 timing is right or slightly late.
3. **Skipped reports** (no signal; they still count in later index windows): as-of 2013-10-01..2013-11-12 (2013 shutdown; the
   calendar's Friday times for those weeks are back-filled), 2018-12-24..2019-02-26 (catch-up releases 1 Feb-5 Mar 2019),
   2025-09-30..2025-12-16 (catch-up 19 Nov-23 Dec 2025) and, found while checking, 2023-01-31..2023-03-07 (the ION cyber
   incident delayed those reports by 2-4 weeks; same reason as the shutdowns, so treated the same way). 35 reports in all.
4. **Entry/exit.** Entry at the open of the first FTMO D1 bar that opens after the release (Friday release -> Sunday-evening
   open; Monday release -> Monday-evening open). Exit at the open of the first D1 bar >= 7 x hold days later. No stop.
   **Non-overlapping per market** (a signal while a trade is open is ignored) - this is the tradeable rule and gives honest
   n and t; the overlapping "every signal week" mean is reported beside it.
5. **R** = (side x move - costs) / ATR(20) of the 20 daily bars before entry. Costs as bt/q75_swing_common: spread x 1.2 (the
   entry day's median intraday spread), commission x (|entry| + |exit|), swap for every 17:00 New York rollover held (today's
   sheet converted to % of price, x3 on the triple day).
6. **Baselines** per trade: (a) mean R of the same side and hold from 20 random report weeks of the same market and calendar
   year (without replacement); (b) always-long = mean R of a long with the same hold from every report week of the same market
   and year. "Beats both" = mean R above both baseline means.
7. **Rule 4 halves** = the cell's trades split in two by entry date (earlier half / later half); before/after 2024 shown too.
   t = plain t of per-trade R; a t clustered by entry week (markets entering the same week are correlated) is shown beside it.
8. **US500/US100.** The calendar series is non-commercial net = large speculators (contrarian) only, so the index grid is
   large x N x thresholds x hold; index primary = large, 157, 80/20, 4 weeks. Releases with as-of dates in the skip windows are
   skipped. Prices: FTMO D1 from 2017-12-29.
9. **Permutation test (only if the commodity primary passes).** Each market's weekly signal series is circularly shifted by a
   random offset (>= 52 weeks), the same offset for all of that market's cells (keeps the signals' persistence; destroys their
   timing); all pooled cells (54 commodity + 18 index) rerun; statistic = pooled t; 500 shuffles; p_alone and p_best
   (bt/robust.mcpt_select); BCa lower bound of the primary's mean R (bt/robust.bca_bounds, 20,000 resamples).
10. **Part 2 (bond leg).** Bond price = 100 / (1 + y/200)^20 from DGS10, forward-filled over every calendar day, used as a
    reference exactly like the dollar index in bt/bernd_bias (ROC reading and level reading, 480 days, +-0.75). #66's VAL rule
    and engine (bt/bernd_daily.simulate, unchanged: next-open entry, 20-day or 2-ATR exit, #66's costs, 20 random same-year
    days as baseline) on #66's universe (every export symbol with >= 900 D1 bars, softs excluded as in #66), with each reference
    alone (DXY, BOND, GOLD; gold on every market but XAUUSD) and in combination. **Combination** = #66's reference set per
    market plus the bond where Bernd uses it: stocks and indices DXY + GOLD + BOND (his "undervalued versus gold, dollar and
    treasury bonds"), energy DXY + GOLD, forex/metals/crypto DXY only (= the DXY rule, not repeated). Signal "ALL" = every
    reference of the set beyond -0.75 (long) / +0.75 (short), entry on the first day the joint condition holds; "2of3"
    (stocks/indices) = at least two of the three beyond on one side and none beyond on the other. #66's numbers are taken from
    results/bernd_daily_trades.csv; the rerun is checked to reproduce #66's per-trade R for the DXY and gold rules.
11. **Part 3 (confluence).** At each report week's entry bar: COT primary (commercials, 157, 80/20), valuation vs DXY, BOND and
    GOLD (gold itself: DXY + BOND; ROC reading, known at the start of the entry day) and True Seasonality (seas30: mean 30-day
    log return from the same date over the 15 previous years, >= 12 years needed) all on the same side -> trade, hold 4 weeks,
    part 1's engine and baselines. Valuation "agrees" two ways, both reported: strict (every reference beyond +-0.75) and
    cheap side (every reference on the correct side of 0). Seasonality needs 12+ years of FTMO daily data, which only gold
    (from 2016) and silver (from 2020-11) have. COT as a filter on #66's trades: each #66 VAL/SEAS trade on a market with COT
    data (commodities: commercials 157 80/20; US500/US100: large 157 80/20) is kept if the COT bias known at its entry agrees
    with its side; kept vs dropped vs all compared on R and on #66's edge over random days.

One change after the first run: part 3's first pass took seasonality from `bt/bernd_bias.seasonal`, which gave "15-year"
seasonals for every market (the bug below). Item 11 intends the 12-real-years rule, so part 3 was rerun with a fixed copy
(`q82_cot_conf.seasonal_fixed`). Only the fixed numbers are reported.

## Data: mapping and checks

| FTMO symbol | CFTC code | Disaggregated market name(s) | reports | FTMO D1 from | tradable report weeks (4 w) |
|---|---|---|---|---|---|
| XAUUSD | 088691 | GOLD - COMMODITY EXCHANGE INC. | 1,061 | 2004-06 | 1,056 |
| XAGUSD | 084691 | SILVER - COMMODITY EXCHANGE INC. | 1,061 | 2008-11 | 927 |
| XPTUSD | 076651 | PLATINUM - NYMEX | 1,061 | 2015-01 | 597 |
| XPDUSD | 075651 | PALLADIUM - NYMEX | 1,061 | 2015-01 | 593 |
| XCUUSD | 085692 | COPPER-GRADE #1 (to 2022-02-01) -> COPPER- #1 - COMEX | 1,061 | 2024-12 | 89 |
| USOIL.cash | 067651 | CRUDE OIL, LIGHT SWEET - NYMEX (to 2022-02-01) -> WTI-PHYSICAL | 1,061 | 2020-12 | 293 |
| UKOIL.cash | 06765T | BRENT CRUDE OIL LAST DAY (to 2022-02-01) -> BRENT LAST DAY - NYMEX | 771 (from 2011-10-18) | 2016-04 | 538 |
| NATGAS.cash | 023651 | NATURAL GAS - NYMEX (to 2022-02-01) -> NAT GAS NYME | 1,061 | 2024-10 | 94 |
| WHEAT.c | 001602 | WHEAT - CBOT (to 2013-12-10) -> WHEAT-SRW - CBOT | 1,061 | 2023-03 | 176 |
| CORN.c | 002602 | CORN - CBOT | 1,061 | 2023-03 | 176 |
| SOYBEAN.c | 005602 | SOYBEANS - CBOT | 1,061 | 2023-08 | 158 |
| SUGAR.c | 080732 | SUGAR NO. 11 - NYBOT (to 2007-08-28) -> ICE FUTURES U.S. | 1,061 | 2024-11 | 89 |
| COFFEE.c | 083731 | COFFEE C - NYBOT -> ICE FUTURES U.S. | 1,061 | 2023-01 | 187 |
| COCOA.c | 073732 | COCOA - NYBOT -> ICE FUTURES U.S. | 1,061 | 2023-01 | 187 |
| COTTON.c | 033661 | COTTON NO. 2 - NYBOT -> ICE FUTURES U.S. | 1,061 | 2024-11 | 89 |
| US500.cash | calendar | CFTC S&P 500 Non-Commercial Net Positions (MT5) | 605 releases 2015-02.. | 2017-12 | 446 |
| US100.cash | calendar | CFTC Nasdaq 100 Non-Commercial Net Positions (MT5) | 370 releases 2019-08.. | 2017-12 | 366 |

Checks (results/q82_cot_mapping.csv, q82_cot_xcheck.csv, q82_cot_schedule.csv):
- **Continuity.** Every mapped series is weekly and unbroken from 2006-06-13 to 2026-10-06. The 6-8-day gaps are holiday
  shifts of the as-of day. One exception: Brent last day (06765T) starts 2011-10-18 and has one 77-day hole (Nov 2011 - Jan 2012).
  Name changes (NYBOT -> ICE in 2007, wheat -> SRW in 2013, the CFTC renaming of 8 Feb 2022) keep the same code, and the
  series run straight through them. No duplicate dates. On every row the long side of all categories (spreads included) sums
  to open interest, and so does the short side. The largest weekly open-interest change is 12-28%: no contract-size breaks.
- **Calendar cross-check.** On every matched week, the MT5 "non-commercial net" for gold and crude equals Disaggregated managed
  money + other reportables to +-0.05k (rounding). Matched: gold 764 of 766 releases, crude 766 of 766. With a plain "release
  date - 3 days" alignment, 97% of weeks match exactly; the rest are holiday and catch-up weeks. Level correlation is 0.999 and
  weekly-change correlation 0.97-0.98. So for these two markets the Legacy non-commercial category = managed money + other
  reportables, which is the "large speculators" group used here.
- **Release schedule.** 764 weeks are timed from the calendar (+2 from crude only), and 295 by rule (2006-2011 plus 5 weeks).
  35 reports are skipped as delayed (2013: 7, 2018-19: 10, 2023 ION incident: 6, 2025: 12). The S&P series has 25 skipped
  releases and the Nasdaq series 15.
- **Prices.** The FTMO commodity CFDs have no futures-roll gaps. Opens more than 1.5 ATR from the previous close happen 0-1
  times a year, and all are real weekend moves. Price history is the binding limit: 9 of the 15 commodities start in 2023-24 and WTI in 2021,
  so about 60% of the commodity trades are metals (gold and silver back to 2009, platinum and palladium from 2015).
- **Engine check.** Three trades (gold, Brent, US500) were recomputed by hand from the raw D1 bars, the release time and the
  swap sheet. R matched to 4 decimals, and each entry bar was the first bar opening after its release.

## Part 1 - COT index rules

### Primary cell: commercials, 157 reports, 80/20, the 15 commodities pooled

| hold | n | mean R | t (week-clustered) | halves | < 2024 / 2024+ | years > 0 | worst year | last 60 | random-week base | always-long base | edge vs random (t) | longs / shorts R | R without swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 w | 1,697 | -0.188 | -5.09 (-4.33) | -0.135 / -0.241 | -0.097 / -0.342 | 4/18 | -0.70 (2010) | -0.273 | -0.306 | -0.128 | +0.118 (3.2) | -0.120 / -0.304 | -0.113 |
| 4 w | 529 | -0.635 | -4.46 (-4.25) | -0.601 / -0.670 | -0.527 / -0.818 | 3/18 | -2.24 (2010) | +0.107 | -0.944 | -0.073 | +0.308 (2.3) | -0.225 / -1.322 | -0.314 |
| 8 w | 307 | -1.429 | -4.68 (-4.48) | -1.331 / -1.527 | -1.150 / -1.930 | 3/18 | -5.24 (2010) | -1.462 | -1.818 | -0.094 | +0.389 (1.5) | -0.559 / -2.823 | -0.741 |

Hold 4 w by year: 09 -1.09, 10 -2.24, 11 -0.53, 12 +0.29, 13 -1.24, 14 +1.96, 15 -0.62, 16 -0.10, 17 -0.25, 18 -0.77, 19 -0.26,
20 -0.88, 21 -0.97, 22 -0.84, 23 -0.29, 24 -1.01, 25 -1.50, 26 +0.20. Swaps alone cost 0.32 ATR a trade on average (removed in the last column).
The overlapping "every signal week" version has the same picture: 1,846 signal weeks at 4 w, mean -0.613.

Hold 4 w per market (n, R, R without swaps, edge vs random): gold 91, -0.84, -0.67, +0.20; silver 81, -0.15, -0.00, +0.75;
platinum 49, -0.11, +0.30, +0.83; palladium 82, -0.63, -0.35, +0.14; copper 9, -0.44; WTI 35, +0.79, +0.36, +0.15;
Brent 43, -1.54, -0.30, -0.34; natural gas 12, -0.87; wheat 17, +0.24; corn 23, -0.99; soybeans 18, -0.83; sugar 14, -1.43;
coffee 18, -1.63; cocoa 21, -1.84; cotton 16, -1.01. Two of 15 markets are positive (WTI, all longs; wheat).

### Pooled by market group x hold (primary setting) and over all cells

| group | hold | n | mean R | t | R w/o swaps | random base | always-long base | edge (t) | longs R / shorts R |
|---|---|---|---|---|---|---|---|---|---|
| metals | 1 / 4 / 8 | 1,033 / 312 / 184 | -0.147 / -0.479 / -0.968 | -3.2 / -2.8 / -2.9 | -0.09 / -0.25 / -0.51 | -0.30 / -0.91 / -1.65 | -0.13 / -0.15 / -0.27 | +0.15 (3.3) / +0.43 (2.6) / +0.68 (2.2) | -0.12/-0.19, -0.23/-0.86, -0.35/-1.88 |
| energy | 1 / 4 / 8 | 263 / 90 / 52 | -0.081 / -0.546 / -1.176 | -0.8 / -1.2 / -1.3 | +0.02 / -0.02 / +0.06 | -0.17 / -0.46 / -1.21 | -0.01 / +0.36 / +0.74 | +0.09 / -0.08 / +0.04 | +0.12/-0.78, +0.59/-3.34, +1.01/-5.68 |
| grains | 1 / 4 / 8 | 182 / 58 / 33 | -0.137 / -0.577 / -1.734 | -1.4 / -1.8 / -2.4 | -0.02 / -0.12 / -0.81 | -0.31 / -1.24 / -2.14 | -0.29 / -0.70 / -1.25 | +0.17 / +0.67 (2.0) / +0.40 | -0.20/-0.01, -0.88/+0.10, -2.45/-0.08 |
| softs | 1 / 4 / 8 | 219 / 69 / 38 | -0.553 / -1.510 / -3.745 | -5.3 / -4.3 / -3.0 | -0.46 / -1.13 / -2.89 | -0.49 / -1.48 / -3.21 | -0.13 / +0.23 / +0.61 | -0.06 / -0.03 / -0.54 | -0.45/-0.67, -0.87/-2.29, -2.18/-5.68 |

All 54 commodity cells (3 groups x 3 N x 2 thresholds x 3 holds, pooled over the 15): **0 have a positive mean R**. The median
is -0.13 / -0.42 / -0.75 at 1 / 4 / 8 weeks. Every cell beats its random-week baseline (edge > 0 in 94-100% of cells; median
+0.13 / +0.43 / +0.76). At 4 and 8 weeks no cell beats always-long, and at 1 week 22% do. By group, 0-28% of cells are positive
(metals 6-22%, grains 0-28%, energy 0-11%, softs 0-11%). No cell passes rule 4.

The baselines explain the pattern. The rule is short ~40% of the time, and shorting commodities over 2009-2026 lost: shorts
-1.32 ATR at 4 w, -0.94 without swaps. Today's swap sheet also charges oil shorts ~25 bp a night, because the oil curve is
steeply backwardated now. The random-week baseline uses the same sides, so it carries the same handicap. That is why the rule
"beats" it while losing to always-long.

### US500 / US100 (calendar large speculators, contrarian)

| cell | n | mean R | t | random base | always-long base | longs / shorts |
|---|---|---|---|---|---|---|
| index primary, 157, 80/20, 1 / 4 / 8 w (pooled) | 143 / 50 / 30 | +0.002 / +0.286 / +0.278 | 0.02 / 0.59 / 0.37 | -0.007 / -0.204 / -0.681 | -0.072 / -0.094 / -0.146 | 55/88, 18/32, 10/20 |
| US500, 4 w | 30 | +0.756 | 1.12 | -0.011 | -0.588 | 14 / 16 (signals end Nov 2024) |
| US100, 4 w | 20 | -0.419 | -0.62 | -0.494 | +0.647 | 4 / 16 |

Over the 18 index cells, 4 are positive (all N = 157). The halves are +0.85 / -0.28 at 4 w, and 2024-26 is negative. By
PROTOCOL wording this is "positive but n too small" = WATCH, but there is nothing to act on: 50 trades, t 0.6, US100 negative,
and the diagnostic below puts it inside luck (p_best 0.48).

## Part 2 - the bond leg of the Valuation tool vs #66

#66's VAL engine, unchanged, on #66's universe (D1 symbols with >= 900 bars, softs excluded; 82 symbols trade). **Reproduction:** the rerun's
DXY and gold rules give the same 8,338 trades as results/bernd_daily_trades.csv, with the same per-trade R (max |dR| 4e-5).
Only the random-day baselines were redrawn (VAL_dxy edge +0.012 vs #66's +0.010).

| rule (R = 2-ATR stop) | source | n | R after costs (t) | edge vs random days (t; week-clustered t) | halves | markets edge > 0 | longs / shorts R |
|---|---|---|---|---|---|---|---|
| VAL vs DXY, ROC | #66 | 4,503 | -0.135 (-7.4) | +0.010 (0.6; 0.3) | -0.006 / +0.032 | 54% | -0.04 / -0.24 |
| VAL vs DXY, level | #66 | 1,957 | -0.195 (-7.3) | +0.073 (2.8; 2.5) | +0.062 / +0.086 | 62% | -0.14 / -0.24 |
| VAL vs gold, ROC (indices, stocks, oil) | #66 | 1,304 | -0.058 (-1.4) | +0.165 (4.1; 1.9) | +0.178 / +0.156 | 61% | +0.21 / -0.35 |
| VAL vs gold, level (same) | #66 | 574 | -0.156 (-2.7) | +0.156 (2.8; 2.3) | +0.019 / +0.233 | 59% | -0.03 / -0.36 |
| **VAL vs BOND, ROC (every market)** | #82 | 3,331 | -0.109 (-4.9) | +0.048 (2.1; 1.2) | +0.061 / +0.040 | 62% | -0.00 / -0.22 |
| **VAL vs BOND, level** | #82 | 1,551 | -0.179 (-6.0) | +0.067 (2.3; 2.0) | +0.034 / +0.088 | 62% | -0.02 / -0.27 |
| VAL vs gold, ROC (every market) | #82 | 4,398 | -0.117 (-5.9) | +0.043 (2.2; 1.1) | +0.028 / +0.058 | 62% | +0.03 / -0.30 |
| VAL vs gold, level (every market) | #82 | 1,708 | -0.089 (-2.9) | +0.100 (3.4; 2.8) | +0.070 / +0.132 | 59% | -0.01 / -0.26 |
| **Combination ALL, ROC** | #82 | 542 | -0.074 (-1.4) | +0.149 (2.6; 1.5) | +0.159 / +0.137 | 61% | +0.11 / -0.28 |
| **Combination ALL, level** | #82 | 341 | -0.226 (-3.0) | +0.238 (3.6; 3.4) | +0.150 / +0.329 | 77% | +0.18 / -0.46 |
| Combination 2 of 3, ROC (stocks/indices) | #82 | 948 | -0.084 (-1.9) | +0.138 (3.1; 1.5) | +0.132 / +0.144 | 64% | +0.10 / -0.26 |
| Combination 2 of 3, level | #82 | 484 | -0.230 (-4.1) | +0.128 (2.4; 2.1) | +0.185 / +0.099 | 60% | +0.11 / -0.37 |

Halves split as in #66: forex/metals at 2018, the rest at 2023. Bond leg by group (ROC): stocks edge +0.144 (t 2.8, R -0.135);
non-US indices +0.240 (t 2.3, R +0.099, 222 trades); US indices +0.111 (t 1.3, R -0.074); forex +0.061 (R -0.101); crypto
-0.408. Gold on the same trades of #66's groups: stocks +0.170, indices +0.235, US indices +0.209.
- On stocks and indices the bond is a near-copy of the gold reference. Both read "the asset fell against a defensive asset",
  and the edges are about the same. Adding it (ALL, 2 of 3) neither raises the edge above #66's gold leg (ROC) nor turns R
  positive.
- Every rule in this table loses after costs and swaps, as in #66. The only positive slices are longs (buy after a slump
  against the references: ALL longs +0.11, ALL-level longs +0.18) and non-US indices vs bonds (+0.099, t 0.9). These are
  the same long-only equity-rebound effect #66 found against gold, which leans on the 2025 crash (208 of the 948 2-of-3 trades
  are in 2025).
- The largest timing number in this battery is the combination ALL, level reading: edge +0.238, week-clustered t 3.4, 77% of
  markets. It passes #66's edge bar, as did #66's level/DXY and gold rules. As a trade it loses -0.226R.

## Part 3 - Bernd's confluence, and COT as a filter

Confluence (hold 4 weeks; part 1 engine; commodities):

| variant | n | mean R | t | random base | always-long base | edge (t) | markets |
|---|---|---|---|---|---|---|---|
| COT + VAL strict (all refs beyond +-0.75) + SEAS | 1 | +2.52 | - | - | - | - | silver |
| COT + VAL cheap side (all refs on the right side of 0) + SEAS | 18 | -1.079 | -1.24 | -1.264 | +0.736 | +0.19 (0.2) | gold 9, silver 9 |
| COT + VAL strict (no SEAS) | 11 | +0.300 | 0.37 | -0.391 | +0.319 | +0.69 (0.8) | 6 |
| COT + VAL cheap side (no SEAS) | 245 | -0.342 | -1.59 | -0.755 | -0.061 | +0.41 (2.0) | 15 |
| COT + SEAS (no VAL) | 36 | -1.111 | -1.83 | -1.440 | +0.820 | +0.33 (0.6) | gold, silver |
| COT only (= primary) | 529 | -0.635 | -4.46 | -0.940 | -0.073 | +0.31 (2.4) | 15 |

Seasonality has 12+ real years only for gold (from 2016) and silver (from 2020-11) on FTMO's daily data. The other 13
commodities have no valid seasonal, so the three-tool confluence exists on 2 markets, and the strict reading has 1 trade.
Untestable. The valuation filter on its own (COT + cheap side) improves the COT rule from -0.64 to -0.34R, which is still
negative and below always-long.

COT as a filter (results/q82_cotfilter.csv): every #66 trade on a market with COT data (gold, silver, platinum, palladium,
WTI, Brent, US500, US100; copper, natural gas and the softs are not in #66), labelled by the COT bias known when it opened.

| trades | all | COT agrees | COT against | COT neutral | agrees minus rest (t) |
|---|---|---|---|---|---|
| #66, all rules | 5,321: -0.115R | 848: -0.147R (edge +0.091) | 760: -0.037R | 3,713: -0.123R | -0.038 (-0.9) |
| #66 VAL vs DXY (ROC) | 397: -0.189 | 65: -0.023 | 64: -0.056 | 268: -0.261 | +0.199 (1.3) |
| #66 VAL vs gold (ROC) | 153: -0.012 | 20: -0.467 | 16: -0.778 | 117: +0.171 | -0.524 (-1.7) |
| #66 SEAS, valid seasonals (gold, silver) | 766: -0.091 | 93: -0.412 | 131: +0.262 | 542: -0.121 | -0.365 (-3.7) |
| #82 part 2 new VAL rules on these markets | 915: -0.195 | 166: -0.167 | 125: -0.263 | 624: -0.188 | +0.034 (0.3) |

Keeping only trades the COT bias agrees with does not help. On gold and silver seasonal trades it hurts (t -3.7). This fits
the diagnostic below: the 3-year commercial index sat on the wrong side of the metals' bull years.

## Part 4 - permutation test and BCa

The pre-registered gate was not met: the primary fails rule 4 and loses to always-long. **The selection-aware permutation
test is therefore not part of the verdict.** It was run anyway as a diagnostic of timing information (`--force-perm`, 500
circular shifts of each market's weekly signal series, all 72 pooled cells, statistic = pooled t of R; results/q82_cot_perm.csv).
- Primary (commodities, comm 157 80/20, 4 w): real t -4.46 vs shifted-signal mean -2.13 -> p_alone 0.98. The 3-year commercial
  index is *worse* than its own signals moved to random dates. It was short in the years commodities rose. The same holds at 1 w
  (p 0.92) and 8 w (p 1.00). The positive edge vs same-year random weeks reflects better timing within the year (buying
  dips); it is not a better yearly direction.
- The faster indices carry timing. 13 of 54 commodity cells have p_alone <= 0.05, and all have N = 26 or 52 (best: comm 26
  90/10 at 4 w, p 0.004). All 13 still lose money (t -0.55 to -2.6).
- Best cell of all 72: US indices, large 157 80/20, 4 w (t +0.59). p_alone 0.038, but p_best 0.48.
- BCa (20,000 resamples): primary mean -0.635 ATR, 95% lower bound -0.92.

## Side finding: `bt/bernd_bias.seasonal` reuses the first window for missing years

`np.searchsorted(dates, past)` returns 0 for any date before a series starts. Each missing year then adds the series' first
N-day return again, and a short history passes the 12-of-15-years test from its second year on. Platinum (data from 2015), for
example, gets a "15-year seasonal" in 2016. In #66, 34,984 of 53,331 SEAS trades (66%) used such seasonals: every index, energy,
platinum and palladium trade, almost every stock trade (AAPL/MSFT from 2019 are valid), most crypto, forex 2001-12 and gold
2005-16. On the valid trades only (34 markets), #66's
conclusion stands: SEAS10/20/30 edge +0.011 (t 1.2) / +0.007 / +0.007, on contaminated trades -0.001 / -0.000 / -0.010. So
the "no timing information" verdict holds. #67's seasonal filters went through the same function. `q82_cot_conf.seasonal_fixed`
is a corrected copy; bernd_bias.py was not edited (instructions: no edits to existing files).

## Verdict

**DEAD.** Under the pre-registered bar the primary cell fails rule 4 at every hold: mean -0.19 to -1.43 ATR, t -4.5 to -5.1,
both halves negative, 3-4 of 18 years positive. It beats the random-week baseline but not always-long, so the selection-aware
test does not apply. 0 of 54 commodity cells are positive. The US-index large-speculator version is positive on 50 trades
(t 0.6): "WATCH" by the letter, with no evidence behind it. The bond leg of the Valuation tool does what #66's legs did:
timing information against random days, but no trade that makes money after FTMO costs, and nothing beyond the gold
reference. The confluence can't be tested on FTMO history, and the COT filter does not improve #66's trades.

What would change it: the Legacy report (forex, indices, bonds, with commercials; Bernd's own markets) showing the commercial
index working there; or futures price history long enough (15+ years) to test the confluence on all 15 commodities.

## Caveats

- **Disaggregated vs Legacy categories.** Bernd's indicator runs on the Legacy report (commercials vs non-commercials vs
  non-reportables). Here commercials = producer/merchant + swap dealers. In Legacy, some swap dealers and other reportables
  sit in different buckets, so the commercial net differs, mostly in metals, where swap dealers are large. For gold and
  crude, Legacy non-commercial = managed money + other reportables exactly (cross-check above), so the "large" group matches
  Legacy. The index side (US500/US100) has only the non-commercial series, so Bernd's primary group (commercials) is untested
  on indices until the Legacy file arrives (`q82_cot_data.LEGACY_GROUPS` / `load_report("legacy")` are ready).
- **Short price history.** 9 of 15 commodities have FTMO prices only from 2023-24 (9-23 trades each at 4 w), WTI from 2021.
  The pooled result is mostly metals 2009-26 and Brent 2016-26.
- **Swaps.** Today's swap sheet is applied to 2009-26, converted to % of price. It charges oil shorts ~25 bp/night (today's
  backwardation) and grain/soft longs 3-8 bp/night (today's contango), which history did not always have. Without swaps the
  primary is still negative (-0.11 / -0.31 / -0.74).
- **Timing.** Release times before 2012 come from the holiday rule (right or slightly late where it can be checked). The 2013
  skip window is a date range, because the calendar's 2013 times are back-filled. FTMO CFD entry at the Sunday-evening open
  carries that day's median spread; real Sunday-open spreads are wider (this works against the rule, which loses anyway).
- **Statistics.** Trades across markets in the same week are correlated; week-clustered t is shown and changes nothing. The
  COT index uses the plain net position (not % of open interest), as pre-registered.
- **Bernd's discretion.** He uses COT as one of three "stars" plus a supply/demand entry (#58/#67: dead) and reads near-misses
  of thresholds as agreement; a mechanical test can only take the stated thresholds.

## Files

- Code: `bt/q82_cot_data.py` (COT loader, release schedule, `cot_signal()` for any report/group/N/thresholds, bond price),
  `bt/q82_cot.py`, `bt/q82_cot_val.py`, `bt/q82_cot_conf.py`, `bt/q82_cot_checks.py`.
- Results: `results/q82_cot_cells.csv` (1,134 rows: every cell x pooled/group/market scope), `q82_cot_trades.csv.gz`,
  `q82_cot_perm.csv`, `q82_cot_mapping.csv`, `q82_cot_xcheck.csv`, `q82_cot_schedule.csv`, `q82_val_trades.csv`,
  `q82_val_summary.csv`, `q82_conf_cells.csv`, `q82_conf_trades.csv`, `q82_conf_coverage.csv`, `q82_cotfilter.csv`,
  `q82_cotfilter_trades66.csv`.
- Run: `nice -n 15 python3 -I bt/q82_cot_checks.py; ... bt/q82_cot.py [--force-perm]; ... bt/q82_cot_val.py; ... bt/q82_cot_conf.py`
  (about 1, 1, 2 and 1 minute).
