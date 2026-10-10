# #75 "web" ideas: MQL5 CodeBase EAs (backlog #34) and freqtrade-strategies (backlog #38) on the FTMO export

Run 2026-10-10, 08:40-10:30 MYT. Pre-registration: research/log.md #75. Code: bt/q75_web_common.py (data, simulator, costs, stats),
bt/q75_web_mql.py (#34), bt/q75_web_ft.py (#38), bt/q75_web_perm.py (permutation test), bt/q75_web_extra.py (primary by year).
Results: results/q75_web_*.csv. Trade files (per symbol) in the session scratchpad, not in the repo.

## Verdicts

| Idea | Tested? | Primary cell (FTMO data and costs) | Verdict |
|---|---|---|---|
| #34 Gold Breakout EA XAUUSD H4 ("+90% 2020-2026") | yes, **page rules** (source unreadable) | XAUUSD H4: n 330, +0.18R, t 2.2; before 2024 +0.03R | **WATCH** |
| #34 Stochastic Daily Breakout for Gold ("+245%") | no: source unreadable, page rules incomplete | - | not tested |
| #34 ZoneUS30 (reversion + positive swap) | no: page describes no rules | - | not tested |
| #34 Nikkei "only buys when volume is quiet" | no: source unreadable, MACD/ATR periods missing | - | not tested |
| #34 ORB Risk Managed | no: source unreadable, no default values on page | - | not tested |
| #38 freqtrade Strategy001-005 | yes, from source | BTC/ETH M5 and M30: all 20 cells negative | **DEAD** (all five) |

## Method (both ideas)

- Data: the FTMO export (quant/universe), one symbol at a time, trimmed exactly as bt/xgrid.datasets_export (finest real intraday
  file, stock session only, thin days dropped). Exits run on the finest bars (M1: XAUUSD, NVDA, TSLA, US100, US500; M5: most; M15:
  forex). H4 and D1 candles on FTMO's server clock (17:00 New York).
- No look-ahead: signals on closed bars, market entry at the next bar's open. Stop counts first when a bar touches both levels; a bar
  that opens beyond the stop (or target) fills at that open.
- Costs per trade: spread x 1.2 at entry (round trip) + commission U.commission_of x (|entry| + |exit|) + swap for every 17:00 New
  York rollover held (x3 on the symbol's triple-swap weekday) from the export's spec sheet. Swaps quoted in points were turned into a
  percentage of the spec-sheet price and applied to the trade's own price: today's gold swap points on 2015 prices ($1,200 vs $4,190)
  would overstate old swaps 3.5x. Before this fix the gold primary cell read +0.08R instead of +0.18R, so swaps matter here.
- R = P/L after costs / initial risk (the strategy's own stop distance).
- Baselines: (1) random entry bars, same side, same exits, filters and costs (the fair baseline for long-only rules, PROTOCOL
  "daily baseline"); (2) coin = the same moments, other side, same distances (#34 only).
- Why a dedicated simulator (bt/q75_web_common.py) instead of bt/xrun.py: the harness charges no swaps, cannot hold one position
  at a time, and cannot do indicator exits or freqtrade's ROI table. The simulator reuses xgrid's data trimming and candle building.
- CANDIDATE bar: PROTOCOL rule 4 (n >= 200, t >= 2, mean >= +0.05R, both halves > 0, no year below -0.3R) and beats the
  random-entry baseline.

## #34 MQL5 CodeBase EAs

**Source access.** All five pages were found (MQL5 CodeBase, MT5 experts list). Each EA's code is only an attachment under
mql5.com/en/code/download/..., which the web reader refuses (robots.txt disallow). The shell cannot reach mql5.com, no page shows
code inline, GitHub search is not available in this session, and web search found no copy. So no rule could be read from source
code. As instructed, the EAs are skipped, with one exception: the Gold Breakout page publishes its complete logic and every input
default, and the port reproduces the author's trade count. It is tested and labelled "page rules, source not verified".

1. **Stochastic Daily Breakout for Gold, +245 Percent in a 2021-2026 Backtest**: https://www.mql5.com/en/code/77900 (Bruno Nunes
   Myrrha Ribeiro, 1 Oct 2026). Claim: XAUUSD H1, Jul 2021-Sep 2026, $1,000 deposit, fixed 0.01 lot, +$2,453 (+245%), profit
   factor 1.54, max equity drawdown 23.9%, 213 trades (116 buys at 66% winners, 97 sells at 51%). Page rules: an in-EA stochastic
   23/3/7 ("close-to-close range, SMMA smoothing") and BB(9, 2.0, weighted price). Buy stop at yesterday's high when the signal line
   peaked on the previous bar and the open three bars ago is below the upper band (sells mirrored). SL = TP = 1.9% of entry; orders
   expire after 9 bars. **Missing:** the stochastic formula, which number is K/D/slowing, the bar indices of the "peak", which bar's
   band is compared, and whether "yesterday" means D1. Not tested: these would have to be invented.
2. **Gold Breakout EA for XAUUSD H4 +90 Percent in a 2020 to 2026 Backtest**: https://www.mql5.com/en/code/77691 (Ali Akbar /
   RanaAli878, 24 Sep 2026). Tested below.
3. **ZoneUS30 - Reversion and Positive Swap on Your Side in US30**: https://www.mql5.com/en/code/77748 (Jose Isaac Almeida Da Silva,
   28 Sep 2026). Page: sell-only mean reversion after an upward extension; positions may stay open for days. The only inputs are Lot
   and Signal Timeframe; all other conditions are "internally defined". The text gives no performance figures (only an image named
   "Results 2023 - 2026"). Not tested. Side fact: FTMO does pay US30 shorts about +0.4%/yr, against -8.1%/yr charged on longs.
4. **87.8 Percent from 2021 to YTD at 8.5 Percent MaxDD. The Nikkei EA That Only Buys When Volume Is Quiet** ("JPN225 Quiet
   Drift"): https://www.mql5.com/en/code/78027 (Tomasz Wojciech Forszpaniak, 4 Oct 2026). Claim (author's own engine, 2022-Oct 2026,
   10k at 15 lots): +87.8%, max drawdown 8.5%, profit factor 1.68, 309 trades, 61.8% winners, every year positive (+15.6 / +18.1 /
   +22.3 / +16.4 / +15.4%). Page rules: M15, all on the closed bar: close > 34-bar mean + 0.5 SD; MACD histogram / ATR < 0.2; tick
   volume < 60% of its 20-day same-time average. Buy at the next open; stop 4 ATR, target 3.5 ATR; signals 11:00-14:59 server time
   (GMT+2/+3); flat by 17:00; long only. **Missing:** MACD periods and whether the "histogram" is MACD minus signal, the ATR period,
   and the SD window. Not tested. This is the most complete of the four; with the .mq5 file (downloadable in a browser or MetaEditor)
   it ports in minutes.
5. **ORB Risk Managed - Opening Range Breakout with Account Protection**: https://www.mql5.com/en/code/77967 (Matas Kerys, 3 Oct
   2026). No performance claim ("built and tested on US100"). Page: opening range from the 16:30 server (GMT+3) US open, OCO
   buy/sell stops, stop as a fraction of the range, target as an R multiple, an ATR filter, close-all before the session end. **No
   default values on the page.** Not tested (the lab's own US-index ORB tests are #70).

### GB4: Gold Breakout EA XAUUSD H4 (page rules, source not verified)

Rules, from the page text and its input table (InpEntryBars 20, InpATRPeriod 20, InpStopATR 2.0, InpUseTrend true, InpTrendEMA 200,
InpAllowLong true, InpAllowShort false, InpExitMode C = fixed target, InpTargetR 2.0, InpRiskPercent 1.0, InpMaxSpreadToRisk 0.10,
InpCloseFriday false):
- On each new bar, with bar i the bar that just closed: close[i] > highest high of bars i-20..i-1, AND the bar before did not break
  out (close[i-1] <= highest high of i-21..i-2), AND close[i] > EMA(200) of closes. Then buy at market (the next bar's open).
- Stop = fill - 2 x ATR(20) (MT5 ATR = simple mean of true range, read on bar i). Target = fill + 2R. No time exit, no Friday close.
- One position at a time. Skip when the spread exceeds 10% of the stop distance. No entry in the last 15 minutes before the session
  closes.
- How I resolved the gaps: "previous 20 bars" excludes the signal bar; ATR is read on the signal bar; the session close is the end
  of the symbol's continuous trading block in the data (next gap >= 30 min); the spread filter uses the entry bar's raw spread.
- **Reproduction check.** On the author's window (2020-01-01 to 2026-09-20) the port takes 197 trades (author 198) with 46.2% winners
  (author 46.97%). Per-year R matches the sign and size of the author's per-year %:

| Year | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Author, % at 1% risk (compounded) | +5.1 | -2.9 | +4.6 | +4.8 | +24.0 | +27.1 | +7.9 |
| FTMO data, sum of R (= % at 1% fixed risk) | +3.6 | -4.1 | +5.4 | +4.6 | +26.4 | +22.9 | +3.2 |

**Primary cell XAUUSD H4** (FTMO server-clock candles, 2015-01 to 2026-10, M1 exits):
- n 330 (29/yr), mean **+0.181R**, t 2.24, 42% winners. Before swaps +0.248R; swaps cost 0.067R/trade (median hold 66 h, about 3.9 nights).
- Before 2024: +0.031R (n 239). From 2024: +0.577R (n 91). Last 60 trades: +0.435R.
- By year: 2015 -0.04, 2016 +0.14, 2017 -0.03, 2018 -0.14, 2019 -0.03, 2020 +0.11, 2021 -0.21, 2022 +0.24, 2023 +0.16,
  2024 +0.85, 2025 +0.57, 2026 +0.16. Worst year -0.21R (2021); 7 of 12 years positive.
- Baselines: random long entries with the same exits, filters and costs earn +0.064R (990 entries) or +0.099R (4,000 entries,
  results/q75_web_mql_primary_years.csv). The rule's excess is +0.08 to +0.12R. Coin (short at the same moments) -0.274R.
- Excess over random long entries by period: 2015-19 -0.035R (rule -0.016, baseline +0.019); 2020-23 +0.066R; 2024-26 +0.218R
  (rule +0.577, baseline +0.359). In 2025 random long entries did as well as the rule (+0.62 vs +0.57).
- PROTOCOL rule 4: **passes, barely** (the before-2024 half is +0.03R).
- H4 grid starts at server hour +1 / +2 / +3: +0.219R (t 2.7) / +0.238R (t 2.9) / +0.174R (t 2.2). Positive at every start, but the
  bar **fails at all three** (worst years 2021 -0.50, 2015 -0.70, 2015 -0.42). Before 2024 the result stays at +0.003 to +0.061R.
- BCa 95% interval for the mean (20,000 resamples): +0.025 to +0.343R. The lower bound is above 0.
- Permutation test: 200 shuffles of the M1 bars within New York time-of-day slots (robust.permute_bars algorithm). The shuffles keep
  gold's drift: the null mean is +0.047R. **p_alone = 0.035** (t) / 0.040 (mean R). Within gold's own 5 cells with >= 200 trades,
  p_best = 0.040. Across the whole family of 308 cells, **p_best = 0.77** (see "Selection-aware permutation" below).

**Every symbol and timeframe** (510 cells with >= 10 trades; 474 without crypto; results/q75_web_mql_cells.csv, _pooled.csv):
- 33% of cells positive (34% without crypto); 50% beat their random-entry baseline.
- **9 cells pass the bar, against 12.8 expected by luck** (9 vs 11.9 without crypto). They are XAUUSD H4 plus 8 stock cells: AAPL
  M30, AMD M30, DIS M5, MSTR M5, NVDA M15, NVDA M30, QCOM M15, TSLA M15. Four of those (AMD, DIS, MSTR, QCOM) sit on the thin
  "second batch" stock histories (log #67).
- Pooled mean R by group and timeframe (trades pooled; the "vs base" row is the pooled rule minus pooled random-entry baseline):

| Group | M5 | M15 | M30 | H1 | H4 | D1 | All (n, t) |
|---|---|---|---|---|---|---|---|
| all | -0.065 | -0.105 | -0.090 | -0.056 | -0.042 | -0.020 | -0.082 (378,654, t -27.5) |
| all without crypto | -0.033 | -0.100 | -0.082 | -0.052 | -0.035 | -0.033 | -0.070 (349,968, t -26.9) |
| gold | -0.062 | -0.024 | -0.032 | +0.017 | +0.181 | +0.184 | -0.034 (13,246) |
| metal (ex gold) | -0.059 | -0.145 | -0.077 | -0.034 | -0.077 | +0.031 | -0.080 (6,119) |
| fx | - | -0.140 | -0.114 | -0.080 | -0.055 | -0.140 | -0.119 (171,025) |
| index | -0.051 | -0.058 | -0.044 | -0.025 | -0.060 | -0.162 | -0.050 (69,470) |
| stock | -0.009 | +0.028 | +0.015 | +0.028 | +0.033 | +0.137 | +0.007 (71,747, t 1.0) |
| energy | -0.045 | +0.011 | +0.033 | +0.034 | +0.037 | +0.364 | -0.007 (11,698) |
| soft | -0.052 | -0.038 | -0.027 | -0.042 | +0.046 | -0.041 | -0.041 (6,663) |
| crypto (raw data) | -0.283 | -0.196 | -0.239 | -0.113 | -0.120 | +0.172 | -0.229 (28,686) |
| crypto (cleaned, see #38) | -0.240 | -0.156 | -0.103 | -0.049 | -0.057 | +0.050 | -0.170 (26,523) |
| all without crypto, vs base | +0.019 | -0.042 | -0.029 | -0.013 | -0.009 | -0.039 | -0.026 |

- Before 2024 / from 2024, all cells pooled: -0.082R / -0.083R.

**Published claim vs FTMO.** The +90% claim (2020-01 to 2026-09, 1% risk, compounded) does reproduce on FTMO's data with FTMO's
spread, commission and swaps: +62R non-compounded in that window (about +85% if compounded at 1%), from 197 trades. But the window
was the good part. In 2015-2019, outside the author's test, the same rule made -0.016R/trade (133 trades). 2024-25 supplies about
80% of the window's profit (+49R of +62R). Random long entries with the same exits made +0.36R/trade in 2024-26, so most of the
gain is gold's trend, not the breakout timing. The author says as much: buys-only depends on gold's uptrend, and 2020-23 was modest.

**Verdict: WATCH.** On FTMO data and costs it is positive, beats its own permutation null (p_alone 0.035) and its random-entry
baseline, and has a BCa lower bound above 0. Against that:
- before 2024 the edge is about zero (2015-19 negative);
- the H4 phase check fails the bar at 3 of 4 candle starts;
- the excess over random long entries is only about +0.08R/trade;
- the cross-asset picture is luck-level (9 passes vs 12.8 expected, pooled -0.07R without crypto);
- the selection-aware permutation test fails: p_best 0.77 over the 308 cells;
- the source code is unverified.

What would change it: a readable .mq5 confirming the rules, and the excess over random long entries staying above 0 on new data
while gold is not trending. Paper-test only; no money.

## #38 freqtrade-strategies

Source: `git clone --depth 1 https://github.com/freqtrade/freqtrade-strategies` (commit f3340ce, 8 Sep 2026) into a new directory
under /tmp/claude-0/q75_web_src/. The .py files were read as text, never imported or run.

**Choice of five.** Strategy001-005 are the repo's original numbered reference strategies (author Gerald Lonlas), and the README's
own install and test examples use Strategy001. All five are long-only and use the 5m timeframe. GitHub stars exist per repo, not per
strategy, so "most starred" cannot be applied. The README publishes no performance figures (the results table it refers to has been
removed), so there is no claim to compare.

Indicators come from TA-Lib 0.8.1 (pip wheel; the same library and defaults freqtrade's talib.abstract calls). qtpylib's formulas are
re-implemented: heikinashi; typical price; bollinger_bands with pandas rolling std (ddof 1, min_periods 1); crossed_above (a > b and
a[-1] <= b[-1]).

**Common to all five:** timeframe 5m; stoploss -10%; no trailing stop; use_exit_signal True; exit_profit_only True (an exit signal
only counts while the trade is in profit after costs); ignore_roi_if_entry_signal False; one open trade per pair. ROI (minutes:
profit): S1-S4 {0: 5%, 20: 4%, 30: 3%, 60: 1%}; S5 {0: 5%, 20: 4%, 40: 3%, 80: 2%, 1440: 1%}.
- **S1 (Strategy001).** Enter: EMA20 crosses above EMA50, Heikin-Ashi close > EMA20, and the HA candle is green. Exit: EMA50
  crosses above EMA100, HA close < EMA20, and the HA candle is red.
- **S2 (Strategy002).** Enter: RSI14 < 30, STOCH slowK(5,3,3) < 20, the lower BB(20, 2) of typical price is above the close, and
  CDLHAMMER = 100. Exit: SAR(0.02, 0.2) > close and Fisher(RSI) > 0.3.
- **S3 (Strategy003).** Enter: 0 < RSI < 28, close < SMA40, Fisher(RSI) < -0.94, MFI14 < 16, (EMA50 > EMA100 or EMA5 crosses above
  EMA10), fastD > fastK, and fastD > 0 (STOCHF 5,3). Exit: SAR > close and Fisher(RSI) > 0.3.
- **S4 (Strategy004).** Enter: (ADX14 > 50 or ADX35 > 26), CCI14 < -100, the previous bar's fastK and fastD (STOCHF 5) < 20, the
  previous bar's slow fastK and fastD (STOCHF 50) < 30, previous fastK < previous fastD, fastK > fastD now, 12-bar mean volume > 0.75,
  and close > 1e-6. Exit: ADX35 < 25, (fastK > 70 or fastD > 70), previous fastK < previous fastD, and close > EMA5.
- **S5 (Strategy005)**, with its hyperopt buy_params / sell_params (freqtrade loads these over the IntParameter defaults). Enter:
  close > 2e-6, volume > 4 x its 150-bar mean, close < SMA40, fastD > fastK, RSI > 26, fastD > 1, and Fisher-RSI-normalised < 5.
  Exit (trigger "rsi-macd-minusdi"): RSI crosses above 74, MACD(12,26,9) < 0, and -DI14 > 4.

**Ambiguities and approximations:**
- FTMO tick volume stands in for exchange volume (S3's MFI, S4, S5). S4's "mean volume > 0.75" is always true on tick volume.
- Backtest order inside each bar follows freqtrade: the exit signal at the next candle's open, then the stoploss, then ROI by the
  trade's age (net of costs).
- Exits run on M5 bars for every timeframe.
- A bar that opens beyond the stop or the ROI level fills at its open.
- freqtrade skips an entry when the exit signal is set on the same candle; the port does not. This happens on 2 of about 25,000
  signal candles (S4, BTC and ETH M5), so it makes no difference.

**Primary cells:** BTCUSD and ETHUSD at M5 (the strategies' own timeframe) and M30 (the pre-registered cell). Also tested: every
crypto CFD in the export on M5 / M30 / H1 / H4.

**Crypto data repairs.** These were applied to every crypto rule and decided from data diagnostics; the uncleaned run is kept as
results/q75_web_ft_*_raw.csv.
- ETHUSD, LTCUSD and XRPUSD lose 2018-20: median spread 1-12% of price there (broken spread units) against 0.1-0.6% from 2021.
- About 600 LTCUSD bars quoted at 1/100 of the price around the rollover are dropped. In the raw run they made single trades of +900R.
- Bars with a spread above 5% of price are dropped (ADAUSD has single bars at 1,000%).
- BTCUSD keeps 2018+. SOLUSD has under 1.5 years and is excluded by the export trimming rule.
- The same artefacts sit in the crypto cells of the #34 run. Its cleaned crypto rerun is results/q75_web_mql_cells_clean_crypto.csv.

**Results** (cleaned; 6 coins x 4 timeframes; 99 cells with >= 10 trades; R = P/L / 10% of entry, so -0.04R = -0.4% per trade):

| Strategy | BTC M5 | ETH M5 | BTC M30 | ETH M30 | Pooled all cells (n, t) | Random-entry baseline | Before 2024 / from 2024 |
|---|---|---|---|---|---|---|---|
| S1 | -0.042 (1,412, t -4.1) | -0.033 (1,211) | -0.030 (592) | -0.036 (499) | -0.055 (12,790, t -15.2) | -0.060 | -0.050 / -0.060 |
| S2 | -0.038 (158) | -0.026 (114) | -0.101 (24) | -0.139 (20) | -0.064 (1,025, t -5.5) | -0.053 | -0.048 / -0.078 |
| S3 | -0.012 (233) | -0.010 (190) | -0.075 (46) | -0.056 (40) | -0.042 (1,490, t -4.6) | -0.049 | -0.060 / -0.026 |
| S4 | -0.024 (802) | -0.030 (640) | -0.033 (205) | -0.053 (162) | -0.035 (5,190, t -7.2) | -0.047 | -0.031 / -0.040 |
| S5 | -0.021 (167) | -0.003 (142) | -0.072 (29) | -0.101 (25) | -0.047 (1,241, t -3.6) | -0.068 | -0.027 / -0.069 |

- Pooled by timeframe (M5 / M30 / H1 / H4): S1 -0.049 / -0.058 / -0.061 / -0.089; S2 -0.049 / -0.112 / -0.152 / -0.087; S3 -0.036 /
  -0.074 / -0.050 / -0.011; S4 -0.033 / -0.053 / -0.032 / +0.001; S5 -0.043 / -0.020 / -0.178 / +0.025 (the H4 cells are tiny).
- Share of cells positive: S1 0%, S2 12%, S3 6%, S4 21%, S5 12%. **0 of 99 cells pass (2.5 expected by luck).** The best cell is S3
  ADAUSD H1 (+0.115R from 10 trades). No primary cell passes, so no permutation test was run.
- Why they lose: 84-88% winners, but wins are capped at +1% to +5% (ROI) against -10% stops. At a 1% ROI exit that needs about 91%
  winners before costs. FTMO's 0.065% round-trip commission, the spread (BTC 0.03%, ETH 0.12%, alts 0.2-0.5%) and 30%/yr swaps on
  both sides take the rest. Random entries with the same exits do about as badly (-0.05 to -0.07R).

**Verdict: DEAD**, all five, on every coin and timeframe.

## Selection-aware permutation (GB4, whose primary cell passed rule 4)

**Family:** every GB4 cell that could clear the bar (>= 200 trades in the real run). That is 308 cells on 87 symbols, or 282
without crypto.

**Method:** 200 shuffles. Each shuffle permutes every symbol's finest bars within New York time-of-day slots, using the
robust.permute_bars algorithm. bt/q75_web_perm.py re-implements it with precomputed slot groups for speed; it gives bit-identical
output for the same generator (checked on XAUUSD and DIS). Each shuffle then rebuilds every timeframe and reruns the rule with the
same filters, costs and swaps. Run through this code path, the real data reproduces the main run's cells exactly.

- **Primary XAUUSD H4: p_alone 0.035 (t) / 0.040 (mean R). p_best 0.77 (t).** The best of 308 shuffled cells averages t 2.52 (95th
  percentile 3.09) against the real 2.24, so skill is -0.28.
- Without crypto cells: p_best 0.71 (t) / 0.87 (mean R among cells with >= 200 trades). The null best mean averages +0.244R against
  the real +0.181R, so skill is -0.06R.
- The mean-R version over all 308 cells is unusable. Shuffled, the raw LTCUSD 1/100-price bars produce single trades of hundreds of
  R, and the null best mean averages +19.5R.
- The best real cell of the family (DIS M5, t 2.62) has p_best 0.34-0.37. **No cell of the idea survives selection.**
- PROTOCOL: p_alone <= 0.05 with p_best > 0.10 = **WATCH**.
- Files: results/q75_web_mql_perm.csv (all cells) and results/q75_web_mql_perm_excrypto.csv.

## Caveats

- No EA's source code was read. GB4 tests the page's description; the matching trade count (197 vs 198) and per-year profile
  suggest the description is faithful, but details such as ATR timing or the session filter could differ.
- Swaps use today's spec-sheet rates scaled to each trade's price; real historical swap rates differed (near-zero rates in
  2015-21), so old long-side swaps are probably overstated and GB4's early years slightly understated.
- Pending orders and spreads use bar data (the spread column is the bar's recorded spread x 1.2); no slippage beyond that.
- The crypto histories before 2021 (except BTC) are unusable for cost-sensitive tests; this affects any earlier crypto result that
  used them.

## Housekeeping

- TA-Lib 0.8.1 was pip-installed into the system Python as a binary wheel (version 0.6.4 had no wheel for Python 3.13).
- research/log.md and the Project doc were not updated, and nothing was committed, as instructed (new files only).
- Trade files are in the session scratchpad (q75_web_mql_trades*, q75_web_ft_trades*, q75_web_perm/), not in the repo.
