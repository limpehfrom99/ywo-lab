# #75 intraday: Dual Thrust (#30), R-Breaker (#31), Stocks in play (#35), run as pre-registered on the full FTMO export

Run 10 Oct 2026, 08:45-09:50 MYT. Pre-registration: research/log.md #75 and backlog items 30, 31 and 35. The rules were run
unchanged, nothing was tuned, and every cell is reported in the CSVs.

Code: `bt/q75_intraday.py` (Dual Thrust and R-Breaker engine plus runner), `bt/q75_intraday_perm.py` (permutation test),
`bt/q75_intraday_sip.py` (stocks in play).
Results: `results/q75_intraday_cells.csv` (one row per cell: n, mean R, t, win, halves, per-year, worst year, coin, pass flag,
sums for pooling), `q75_intraday_pooled.csv`, `q75_intraday_trades_primary.csv`, `q75_intraday_perm*.csv`,
`q75_intraday_sip*.csv`, `q75_intraday_cells_stock_spread_imputed.csv` (cost sensitivity).

## Common setup

- **Data.** The FTMO MT5 export (94 symbols) through 9 Oct 2026, loaded with `quant/universe.load` and cut into day x bar
  matrices with `quant/sessions.Session`.
- **Sessions.** Each symbol's `U.sessions_of` sessions. Gold also runs on the server day: 00:00-23:55 server time (17:00-16:55
  New York), with `edge_min=70` for the 17:00-18:00 New York pause, as in `quant/mcpt_wvb.py`. BTCUSD also runs on the UTC day
  (00:00-24:00).
- **Bar sizes.** M5 is primary and M15/M30/H1 are joined from M5. Forex has no M5 in the export, so for forex M15 is primary,
  then M30 and H1.
- **Costs.** Spread x 1.2 at entry (round trip, price units) plus commission x (|entry| + |exit|). No swap.
- **Fills.** Stop entries fill at the level, or at the bar's open if it gapped through. Exits at a level fill the same way.
- **CANDIDATE bar.** n >= 200, t >= 2, mean >= +0.05R, both halves (before 2024 / from 2024) > 0, no year below -0.3R (years
  with >= 10 trades), and beats its baseline. If a primary cell passes, it also needs p_best <= 0.10 and a BCa lower bound > 0.

**Decisions and deviations, all fixed before the results were seen except where marked:**

1. **Softs are not tested.** The 7 `.c` symbols have no session in `U.sessions_of`. That leaves 87 symbols and 130
   symbol-sessions.
2. **Joined bars start at the session open** (09:30-10:30 ...), not at clock hours. When the session length is not a multiple of
   the bar, the last partial bar is dropped and positions exit at the last full bar's close. This affects H1 on
   us/hk/eu/uk cash, nymex and london24, and M15/M30/H1 on the gold server day (last exits at 23:45 / 23:30 / 23:00 server):
   303 of 1,392 Dual Thrust cells. Joined-bar spread = the mean of its M5 spreads. Daily levels (the Dual Thrust range,
   R-Breaker pivots) always come from the full session.
3. **History starts late for some markets.** `Session` keeps only days with real intraday bars:
   - US/EU index and most stock histories start in 2021 (US100 has 1,255 sessions, from Aug 2021).
   - AAPL and MSFT have real M5 for 2015 to Sep 2019, then a gap until Aug 2021.
   - US30/US2000 start in 2018-19.
   - BTC's UTC day has almost no Friday or weekend sessions before 2022 (none at all in 2019-20): FTMO crypto closed for the
     weekend then, so those days fail the coverage rule.
4. **Dual Thrust same-bar rule, as instructed.** On a bar touching both triggers, the open position is closed at the opposite
   trigger and nothing is reversed on that bar. If flat, the first position is booked as stopped: the side the bar opened beyond,
   else a long. This applies to 0.6% of trades.
5. **R-Breaker same-bar rules (worst case):**
   - The stop is checked in the entry bar. A reversal trade's high/low-so-far stop counts only if the bar trades beyond it.
   - No new entry on a bar where a position was stopped.
   - A bar that triggers both sides while flat, where the open does not tell which came first, is booked as one loss on the worse
     side. That is 0.26% of trades, averaging -1.2R.
   - Reversal setups must be armed on an earlier bar.
6. **Coin baseline** = the same entry moment and price, opposite direction, protective stop at the same distance on the other
   side, out at the real exit moment unless stopped first. coin = (R + R_opposite) / 2.
7. **Spread data flag (found while running; not a rule change).** The export has **spread 0 and tick volume 0 on every
   cash-session bar of the second stock batch (AMD AVGO BA CVX DIS INTC JNJ JPM KO MSTR NKE PLTR QCOM XOM) from 2021 to 2025**.
   NVDA's spread is 0 in 2021-23 and MCD's in 2024-25. Stock spreads otherwise rose about 5x in 2025 (0.02 to ~0.10).
   The pre-registered run uses the export as is. A sensitivity run fills zero stock spreads with 0.02 (before 2025) or 0.10
   (from 2025): `run --impute-stock-spread`.

## #30 Dual Thrust: CANDIDATE on US100's cash session only (marginal); DEAD as a general rule

**Rule.** N = 4 previous sessions; Range = max(HH - LC, HC - LL); triggers = open ± k x Range, with k = 0.3 / 0.5 / 0.7.
Stop-and-reverse; flat at the close. R = P/L / (BT - ST). For US100 at k = 0.5, 1R is the trigger distance: median 402 points,
or 2.3% of price.

**Primary cells (k = 0.5) at every bar size.** Bar size barely matters: about 99% of trades never reverse and are held to the
close.

| cell | n | mean R | t | win | <2024 | >=2024 | worst yr | coin | passes | by year |
|---|---|---|---|---|---|---|---|---|---|---|
| XAUUSD server_day M5 | 1128 | +0.020 | 1.62 | 51% | +0.009 | +0.057 | 2017 -0.042 | -0.011 | no | 15:-0.018 16:+0.058 17:-0.042 18:+0.009 19:-0.027 20:+0.061 21:+0.058 22:-0.001 23:-0.018 24:+0.052 25:+0.077 26:+0.042 |
| XAUUSD server_day H1 | 1121 | +0.017 | 1.40 | 50% | +0.006 | +0.053 | 2017 -0.056 | -0.012 | no | (as M5) |
| **US100 us_cash M5** | **333** | **+0.060** | **3.10** | 57% | **+0.110** | **+0.019** | 2026 -0.030 | -0.001 | **yes** | 21:+0.116 22:+0.169 23:+0.064 24:+0.033 25:+0.041 26:-0.030 |
| US100 us_cash M15 / M30 | 333 | +0.060 | 3.11 | 57% | +0.110 | +0.019 | 2026 -0.030 | -0.001 | yes | (as M5) |
| US100 us_cash H1 | 316 | +0.060 | 3.19 | 57% | +0.102 | +0.026 | 2026 -0.007 | -0.002 | yes | 21:+0.132 22:+0.145 23:+0.065 24:+0.047 25:+0.027 26:-0.007 |
| US500 us_cash M5 | 353 | +0.032 | 1.33 | 51% | +0.066 | +0.005 | 2021 -0.096 | +0.000 | no | 21:-0.096 22:+0.130 23:+0.070 24:-0.014 25:+0.052 26:-0.032 |
| BTCUSD utc_day M5 | 973 | +0.032 | 2.02 | 47% | +0.048 | +0.009 | 2025 -0.013 | -0.025 | no | 18:+0.025 19:-0.008 20:+0.134 21:+0.109 22:-0.004 23:+0.051 24:+0.000 25:-0.013 26:+0.051 |

**Neighbouring k (M5):**

| cell | k = 0.3 | k = 0.7 |
|---|---|---|
| US100 | +0.039R (t 2.0) | +0.042R (t 1.7) |
| US500 | +0.001R | +0.054R (t 1.7) |
| Gold | +0.017R (t 1.3) | +0.023R (t 1.8) |
| BTC | +0.034R (t 2.0) | +0.028R (t 1.6) |

**US100 k = 0.5, M5 in detail:**
- Before 2024: +0.110R (t 4.7, n 149). From 2024: +0.019R (t 0.65, n 184). Last 60 trades: -0.005R.
- Shorts +0.081R (188 trades), longs +0.032R (145).
- Gross +0.062R, cost 0.003R.

**Pooled, mean R per trade (t), all cells in the group.** A dash means no cell: forex has no M5.

| k | group | M5 | M15 | M30 | H1 |
|---|---|---|---|---|---|
| 0.5 | crypto | -0.131 (-14.9) | -0.129 | -0.127 | -0.133 |
| 0.5 | energy | -0.038 (-3.1) | -0.038 | -0.038 | -0.027 |
| 0.5 | forex | - | -0.018 (-10.0) | -0.018 | -0.017 |
| 0.5 | index (non-US) | -0.024 (-3.9) | -0.024 | -0.024 | -0.026 |
| 0.5 | metal | -0.043 (-9.0) | -0.045 | -0.046 | -0.049 |
| 0.5 | stock | -0.003 (-0.9) | -0.003 | -0.003 | -0.000 |
| 0.5 | us_index | +0.012 (1.3) | +0.012 | +0.011 | +0.014 (1.5) |
| 0.5 | ALL | -0.044 (-15.9) | -0.029 | -0.029 | -0.028 |
| 0.5 | ALL without crypto | -0.018 (-7.3) | -0.018 (-12.5) | -0.018 | -0.017 |
| 0.3 | ALL / without crypto | -0.072 / -0.034 | -0.049 / -0.033 | -0.048 / -0.033 | -0.048 / -0.032 |
| 0.7 | ALL / without crypto | -0.038 / -0.013 | -0.022 / -0.011 | -0.022 / -0.011 | -0.022 / -0.010 |

US indices are the only group above zero at every k and bar, at +0.001 to +0.023. US stocks and US indices pooled on the cash
session at M5, k = 0.5, give -0.001R (t -0.35). Full group x bar tables for every k are in `q75_intraday_pooled.csv`.

**Cells.**
- 1,392 cells and 1.04M trades; 33.5% of cells are positive (k = 0.3: 29%, 0.5: 38%, 0.7: 34%).
- 18 of the 1,159 cells with n >= 200 pass the bar, against ~29 expected by luck (2.5%).
- The 18 are only 6 distinct symbol x k effects, because bar sizes duplicate each other:
  - US100 k = 0.5 (all 4 bars) and k = 0.3 (H1 only)
  - TSLA k = 0.5
  - MSTR k = 0.3 and k = 0.5
  - DIS k = 0.5
- MSTR and DIS are second-batch stocks that paid no spread before 2026. With spreads imputed:
  - DIS falls to +0.043R and fails.
  - MSTR k = 0.3 fails; MSTR k = 0.5 holds at +0.054R (t 2.55).
  - 12 passing cells remain.

**Selection-aware permutation test.** 200 shuffles; on each, all 1,392 cells are rerun. The shuffle is `permute_session`'s
algorithm compiled with numba and checked against it to 1e-13. Each symbol-session is shuffled independently on M5 (M15 for
forex), and joined bars are rebuilt from the shuffled bars.
- **Real best cell:** US100 H1 k = 0.5, t 3.19. Shuffled best t: median 2.32, 90th percentile 2.99, 95th 3.27. **p_best 0.065.**
- **Primary US100 M5 k = 0.5:**
  - p_alone 0.005 (no shuffle reached its t or mean). Its own shuffled mean is +0.000.
  - **p_best 0.080.**
  - **Masters skill +0.020R:** the real +0.060 minus +0.040 for the average best shuffled cell.
  - **BCa 95% lower bound +0.024R** (90%: +0.030).
- **The other primaries.** Each has p_alone 0.005 against its own shuffles, mostly because the shuffles lose to costs. But:

| primary | p_best | BCa 95% lower bound | other reason it fails |
|---|---|---|---|
| Gold server day | 0.97 | -0.004 | |
| US500 | 1.00 | -0.011 | |
| BTC UTC day | 0.79 | +0.002 | mean +0.032 is below the +0.05 bar |

**Verdict.** **CANDIDATE, by the letter of the bar, for US100's cash session at k = 0.5 only.** It passes rule 4, beats the
coin, has p_best 0.080 <= 0.10 and a BCa lower bound > 0. But it is marginal:
- With 200 shuffles, p_best carries about ±0.02 of Monte Carlo error.
- The skill is a third of the backtest mean.
- The from-2024 half is flat: +0.019R, t 0.65, with 2026 at -0.030R.
- The rule is effectively "break the open by half the 4-day range, hold to the close". That is a cousin of the US-index ORB30
  WATCH (#70) and the Williams breakout (#50/#71), and it is likely correlated with the live US100 opening candle; that overlap
  was not measured here.
- US500 (+0.032R) and the US stock cross-section (-0.001R) do not confirm it.

Everywhere else, Dual Thrust is **DEAD**: pooled negative in every group except US indices, and fewer passes than luck.
Size on skill (+0.02R), not on +0.06R.

**What would change the verdict:**
- **Down to WATCH or DEAD:** 1,000 shuffles putting p_best above 0.10, or the 2026 forward half staying <= 0.
- **Up:** US100 from 2024 back above +0.05R with t >= 2 on new data.

## #31 R-Breaker: DEAD

**Rule.** As pre-registered (six levels from yesterday's session H/L/C; trend entries at the break levels with the stop at P;
reversal entries after the setup level; at most one long and one short per day; SAR on reversal signals; flat at the close).

| cell | n | mean R | t | <2024 | >=2024 | worst yr | coin | passes |
|---|---|---|---|---|---|---|---|---|
| XAUUSD server_day M5 | 831 | +0.000 | 0.01 | -0.006 | +0.022 | 2021 -0.278 | -0.010 | no |
| US100 us_cash M5 | 452 | +0.030 | 0.87 | -0.005 | +0.052 | 2021 -0.027 | -0.004 | no |
| US500 us_cash M5 | 468 | +0.036 | 0.68 | +0.017 | +0.050 | 2026 -0.186 | +0.008 | no |
| (H1 versions) | | gold -0.002, US100 -0.042, US500 -0.008 | | | | | | no |

**Pooled, mean R per trade (t):**

| group | M5 | M15 | M30 | H1 |
|---|---|---|---|---|
| crypto | -0.348 | -0.347 | -0.344 | -0.354 |
| energy | -0.080 | -0.086 | -0.107 | -0.124 |
| forex | - | -0.062 | -0.070 | -0.084 |
| index (non-US) | -0.060 | -0.058 | -0.063 | -0.077 |
| metal | -0.152 | -0.159 | -0.161 | -0.169 |
| stock | -0.016 | -0.024 | -0.032 | -0.046 |
| us_index | +0.021 (t 1.2) | +0.012 | -0.000 | -0.035 |
| ALL | -0.141 | -0.097 | -0.103 | -0.116 |
| ALL without crypto | -0.063 | -0.064 | -0.072 | -0.086 |

**By leg** (mean R; without crypto in brackets):
- Trend legs: -0.077R (-0.052).
- Reversal legs: -0.146R (-0.094).

**Cells.**
- 464 cells; 15.3% positive.
- 3 pass against ~11 expected by luck, all INTC at M5/M15/M30. INTC is a second-batch stock with zero spread before 2026. With
  spreads imputed it falls to +0.008R (from 2024: -0.02R), leaving **0** passes.
- No primary passed, so no permutation test was run.

**Verdict: DEAD** on every market and bar size. Coarser bars make it worse, as the worst-case same-bar fills bite more.

## #35 Stocks in play (Zarattini & Aziz 2023): DEAD

**Rule.**
- Relative volume (RV) = the first 5-minute bar's tick volume / its average over the previous 14 sessions.
- Each day, take the top 20% of stocks with an RV (round(0.2 x count), at least 1).
- Trade the first candle's direction at the next bar's open; skip a doji.
- Stop = 0.1 x ATR(14); out at 16:00 New York. Costs as above (0.002% per side).
- Baselines: ALL stocks, a random 20% (1,000 draws), and the opposite direction.

**Data limits.**
- Before Aug 2021 only AAPL and MSFT have real intraday bars, so 2015-19 is a pick between two stocks. There is nothing
  from Oct 2019 to Jul 2021.
- The second batch has tick volume 0 until 2026, so it gets an RV on only ~175 days in 2026.
- A real cross-section exists from Aug 2021: 14-16 stocks with an RV per day (median 14).

| universe | set | n | mean R | t | win | <2024 | >=2024 | worst yr |
|---|---|---|---|---|---|---|---|---|
| all 30 | **TOP 20% by RV** | 5,474 | **-0.253** | -6.2 | 15% | -0.038 | -0.498 | 2026 -0.586 |
| all 30 | ALL stocks | 24,085 | -0.284 | -15.4 | 16% | -0.096 | -0.438 | 2025 -0.579 |
| all 30 | RANDOM 20% | ~5,460 | -0.229 (5-95%: -0.279 to -0.179) | | | | | |
| all 30 | TOP, opposite direction | 5,474 | -0.287 | -7.3 | 14% | -0.097 | -0.502 | |
| without batch 2 | **TOP 20% by RV** | 4,951 | **-0.248** | -5.8 | 15% | -0.038 | -0.547 | 2026 -0.844 |
| without batch 2 | ALL / RANDOM / opposite | | -0.277 / -0.213 / -0.279 | | | | | |

- **Against the random-20% baseline:** p_random 0.78 for all 30 stocks and 0.86 without batch 2. Picking by relative volume adds
  nothing over a random pick.
- **TOP by year (all 30):** 15:+0.18 16:-0.09 17:-0.02 18:+0.26 19:-0.10 21:+0.08 22:-0.07 23:-0.20 24:-0.29 25:-0.57 26:-0.59.
- **Costs explain the loss:**
  - Before costs, TOP makes +0.025R and ALL +0.010R per trade. Spread costs average 0.26R a trade because the stop (0.1 ATR) is
    tiny, and 84% of trades exit at the stop.
  - From 2025, when stock spreads went from ~0.02 to ~0.10, TOP loses -0.58R a trade; in 2021-24 it lost -0.16R.
  - The zero-spread data flag (NVDA 2021-23, MCD 2024-25) only flatters these numbers.
- **M1 exit check:**
  - TSLA, all days: M5 +0.166R vs M1 +0.151R (n 1,266). Selected days: +0.233 vs +0.219 (n 190).
  - NVDA, all days: M5 -0.011 vs M1 -0.018 (n 1,251). Selected days: +0.247 vs +0.239 (n 174).
  - So M5 exits overstate by about 0.01R, which changes nothing.
  - TSLA alone is positive, which echoes the live TSLA opening candle, but NVDA's selected-day result sits in its zero-spread
    years.

**Verdict: DEAD**, with or without batch 2. It loses -0.25R a trade after FTMO costs and does not beat a random 20% pick.

## Caveats

- **Pooled t-statistics are overstated.** Bar sizes are near-duplicates (Dual Thrust M5/M15/M30 are almost identical), and
  stocks or indices trade on the same days. The luck count of 2.5% x cells is a rough upper bound on independent chances.
- **Crypto.** Here crypto does not produce huge-R outliers: the Dual Thrust R unit is a 4-day range. Crypto pools strongly
  negative instead (-0.13 to -0.20R), mostly costs on altcoins. BTC alone is +0.03R.
- **The second stock batch should not be trusted for any intraday test before 2026:** zero spread and zero tick volume.
  Excluding it, or imputing its spreads, should be standard. The universe loader does not currently flag the zero spreads.
- **Index histories start in 2021.** US100 has 5 years of real intraday bars, so its CANDIDATE rests on 333 trades, 149 of them
  before 2024.

## Reproduce

```
nice -n 15 python3 bt/q75_intraday.py run          # 87 symbols, 1,856 cells, ~3 min
nice -n 15 python3 bt/q75_intraday.py summary
nice -n 15 python3 bt/q75_intraday.py run --impute-stock-spread   # stock cost sensitivity
nice -n 15 python3 bt/q75_intraday_perm.py --verify   # numba shuffle vs quant/permute.permute_session
nice -n 15 python3 bt/q75_intraday_perm.py run 200    # ~22 min with other jobs running
nice -n 15 python3 bt/q75_intraday_perm.py summary && nice -n 15 python3 bt/q75_intraday_perm.py skill
nice -n 15 python3 bt/q75_intraday_sip.py             # ~1 min
```
