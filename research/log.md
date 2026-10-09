# Research log (overnight loop, started 2026-10-09 03:00 MYT)

## code (for rebuilds)
bt/gold_m1.py, bt/smc_data.py, bt/sr_diag.py, bt/period_levels.py live in /home/claude/bt; the
skill scripts in /mnt/skills/plugins/ftmo-strategy-lab/scripts are the originals of /home/claude/lab.

## results

### 1. Period open/close levels (Shen) — DEAD   [2026-10-09 03:50 MYT]
Rule (fixed before running): every past weekly open & close (alive 12 weeks) and monthly / quarterly /
half-year / yearly open & close (alive 1-3 years) is a level, both sides. Zone ±0.05 daily ATR(14).
Touch from either side -> first 1/5/15-minute close back beyond the level -> stop beyond the touch
extreme (+0.02 ATR), target 3R, 24h limit. Costs: spread by year + commission. Benchmarks: same rules
on FAKE levels (every level +0.37 ATR) and the pure reaction test (0.2 ATR away before 0.2 ATR through).
Gold M1 2012-2026 (bt/period_levels.py, run_period_tf.py):
  1m  real n=48391 avgR -0.247 (gross -0.110) win 22% | fake -0.223.  Negative all 15 years.
  5m  real n=19751 avgR -0.182 (gross -0.085) | fake -0.164.  15m real n=11049 -0.110 (gross -0.042) | fake -0.099.
  By level: W -0.24/-0.18/-0.11, M -0.28/-0.20/-0.12, Q -0.29/-0.24/-0.12, H -0.28/-0.19/-0.18, Y -0.22/-0.01/+0.10 (n=110, t=0.6).
  Reaction odds: real 61-62% "respect", fake 62%, random-walk geometry 62.5%. The lines do nothing.
Indices/stocks (run_period_idx.py, M5 2021-26 for TSLA/AAPL, 2025-26 only for US100/US500):
  US100 5m +0.159 (n=1616, t=3.5) and 15m +0.180 vs fake ~0  <- 17 months only, bulk (weekly, n=1185) +0.04,
  the big numbers sit in M/Q/H levels with n=68-254. Extended to M30 2017-2026: US100 +0.020 vs fake +0.043;
  US500 -0.024 vs fake +0.051; by side longs > shorts (bull market), not a level effect.
  US500 5m -0.10, TSLA 5m -0.03 / 15m +0.02 (fake -0.05/-0.04), AAPL -0.10/-0.06.
Verdict: DEAD on gold at every timeframe and level rank; indices no better than fake lines over 9 years.
What would change it: a 2017-2026 5-minute index test showing real > fake by >= 0.1R with t >= 2 in both halves
(needs older M5 data; the broker export only goes back to 2025-05 for US100/US500).
Note: the container restarted between wake-ups and killed the background run; long jobs must finish within a turn.

### 2. Weekly-open bias — DEAD   [2026-10-09 04:05 MYT]
Rule: (a) sign of (Monday 17:00 NY close - weekly open) vs rest-of-week return (Mon close -> Fri close), in ATR;
(b) each day's open above/below the weekly open vs that day's return. Gold M1 2012-26 (758 weeks), US100/US500 M30 2017-26 (453 weeks).
  gold: above -> rest-of-week +0.16 ATR, below +0.04 ATR, corr 0.04 (the uptrend, not a signal); day-level above +0.035 vs below 0.00 ATR,
  first half of the sample has the opposite sign.  US100: corr -0.06 (inverted).  US500: corr 0.00.
Verdict: DEAD. No consistent sign across markets or halves. (bt/weekly_open.py)

### 3. Weekly-open magnet ("price revisits the weekly open 70-80% of weeks") — TRUE BUT USELESS, DEAD as a trade   [04:05 MYT]
Rule: after price first moves 0.5 ATR away from the weekly open, does it come back within 0.05 ATR before the week ends?
  gold 73% of weeks, US100 70%, US500 71%  — but a FAKE open (+0.37 ATR) is revisited 74% / 75% / 76%. Prices wander; any
  line gets revisited that often.  Fade rule (first 1-ATR move from the weekly open, target the open, stop 1 ATR further):
  gold n=667 -0.08R t=-2.4; US100 n=377 +0.01R t=+0.3; US500 n=367 -0.04R. Verdict: DEAD.

### 4. Turn-of-the-month rule — DEAD (watch-list item removed)   [2026-10-09 04:15 MYT]
Rule: buy at the close of T-1 (second-to-last trading day of the month), exit at the close of T+3 or at a stop 1 daily
ATR below entry; R = P&L/ATR; costs = spread twice + commission + swap 0.01%/night. Baseline = the same 4-day hold
started on every other day. Gold M1 2012-26, US100/US500 M30 2017-26 (bt/tom.py).
  gold  n=175 +0.084R t=+0.8, halves -0.15 / +0.32 | any-day baseline +0.087R -> no advantage.
  US100 n=105 -0.012R t=-0.1 | any-day +0.145R.   US500 n=105 +0.007R t=+0.1 | any-day +0.113R.
Verdict: DEAD. The earlier watch-list numbers (+0.3-0.55% per window) were raw window returns; as a rule with a stop and
costs the window is no better than any other 4 days. What would change it: nothing on these markets.

### Correction to #1-#4: the US100/US500 "M30 2017-2026" export has only ONE bar per day before 2021-09 (daily bars),
30-minute bars from 2021-09-14. Daily-level tests (weekly open, TOM, reversal, Donchian) are fine; the intraday
tests on indices (period levels 30m, gap fade, overnight, pre-FOMC) effectively cover 2021-09 .. 2026-10 only.

### 5. Opening-gap fade US100/US500 — DEAD   [2026-10-09 04:40 MYT]
Rule: gap = 9:30 open - prior 16:00 close; if 0.3 <= |gap| <= 1.0 ATR, trade toward the prior close at the open,
target the prior close, stop 1 gap beyond the open, exit 11:00. R = P&L/|gap|. 30-min bars 2021-09..2026-10.
  US100 n=528 -0.010R t=-0.3, fill rate 23%.  US500 n=540 -0.027R t=-0.8.  Gaps > 1 ATR: +0.04R (n=52/55).
Verdict: DEAD. Gaps on these CFDs do not fill more than chance within the morning. (bt/index_ideas.py)

### 6. Overnight return (15:30 close -> next 9:30 close) — DEAD for a prop account   [04:40 MYT]
  US100 +0.015 ATR/night (t=1.0, 54% up nights), intraday +0.007. US500 +0.010 / -0.003. Swap 0.01%/night included.
  The academic overnight premium exists but is ~+0.015 ATR per night: at 0.5% risk per ATR that is ~+0.3%/year.
Verdict: DEAD as a strategy (far too small). 

### 7. Pre-FOMC drift (long from the 15:30 close the day before to the 13:30 close on FOMC day) — WATCH   [04:40 MYT]
  US100 n=41 +0.176 ATR per event, t=+2.3, 63% up, halves +0.16/+0.19, 5 of 6 years positive (2021-26).
  US500 n=41 +0.113, t=+1.6, 5 of 6 years. Baseline (same window, every other day): +0.025 / +0.022.
  Known effect (Lucca & Moench 2015 "pre-FOMC announcement drift"). 8 events a year; with a 1-ATR stop that is
  about +1.4R a year on US100 — real-looking but too small to pass a challenge on its own; a cheap add-on at most.
  Would conflict with the opening-candle EA's one-position-per-symbol logic on FOMC days (which it skips anyway).
Verdict: WATCH (re-check after 20 more events; add to the lab's watch list).

### 8. Short-term index reversal (daily, 2018-2026) — DEAD   [04:50 MYT]
Rule: after 3 consecutive lower closes buy at the close, exit at the first up close or 5 days, stop 1.5 ATR; mirror
for shorts. US100: both sides n=338 ~+0.02R; longs +0.08 (t=1.0), shorts -0.01. US500: -0.01; longs +0.06, shorts -0.06.
Baseline: an unconditional 5-day hold makes +0.18 / +0.14 ATR -> the reversal entry is WORSE than just holding.
Verdict: DEAD. (bt/daily_ideas.py)

### 9. Multi-day trend following, gold (daily 2012-2026, Donchian breakout, 2-ATR trailing stop) — WATCH   [04:55 MYT]
Rule: long on a close above the 20-day high, exit on a close below the 10-day low or the trailing stop; mirror for
shorts; swap 0.01%/night; R = P&L / ATR (stop = 2 ATR, so divide by 2 for R-per-risk).
  20/10: n=167 avgR +0.44 ATR (t=2.0), 11/15 years positive, longs +0.80 (t=2.4), shorts +0.01, avg hold 12.6 days.
  Fixed grid: 10/5 +0.19 (t=1.2), 20/10 +0.44, 55/20 +0.63 (t=2.0), 100/50 +0.73 (t=2.0). 2012-2024 only: +0.08..+0.35, t~1.1.
  Indices: US100 longs +0.48 ATR (t=1.5), both sides -0.06; US500 longs +0.27, both sides -0.29.
Verdict: WATCH. A real-looking but slow, long-biased effect (gold's uptrend; 2025-26 contribute most). ~11 trades
a year, +0.22R per unit of risk -> about +1.2%/year at 0.5% risk: not a challenge strategy, a diversifier at best.

### 10. Crypto weekend effect, BTCUSD (30-min bars 2021-09..2026-10) — DEAD   [2026-10-09 05:35 MYT]
  Weekend return (Fri 21:00 -> Mon 00:00 UTC): +0.057 ATR per weekend, t=1.2, 53% up, 2 of 6 years negative; weekday day
  return +0.024 ATR. Monday breakout of the weekend range (stop at the range mid, exit Monday close): n=220 +0.06R t=0.7, 40% win.
Verdict: DEAD (no reliable weekend premium or breakout). (bt/misc_ideas.py)

### 11. Gold hour-of-day drift (NY hours, 2012-2026) — DEAD after costs   [05:35 MYT]
  Hours with the same sign in >= 10 of 14 years: 00:00 (+11/-3), 09:00 (-10), 10:00 (+12/-2), 15:00 (-11), 18:00 (+11),
  19:00 (+12/-2), 20:00, 21:00. But the drift is 0.3-1.5 bp per hour and a round trip costs ~1.5 bp: every always-on rule
  is negative net (-0.6 to -1.4 bp/trade) except 18:00 NY (Asia open) at +0.04 bp, which is 2026 alone (+17.8 bp).
Verdict: DEAD. The 10:00 NY hour is up in 12 of 14 years (+0.74 bp) — consistent with the opening-candle edge, far below costs alone.

### 12. Volatility sizing for the live opening-candle strategy (TSLA + US100, 2022-26, Fed days skipped) — CANDIDATE improvement   [05:42 MYT]
Rule: scale = clamp(1-year median ATR% / today's ATR%, lo, hi), ATR known at the open; risk = 0.5% x scale.
  Finding: the edge is bigger on calm days — TSLA +0.122R (n=635) vs +0.082R on wild days (n=504); US100 +0.133 vs +0.065.
  fixed 0.5%:                   +0.101%/day, worst day -1.05%, maxDD -12.0%, pass (10%+5%) 78% in 4.7 months
  scale 0.5..1.5 (up and down): +0.107%/day, worst day -1.53%, maxDD -13.6%, pass 79-80%   -> not worth the tail
  scale DOWN only 0.5..1.0:     +0.092%/day, worst day -1.05%, maxDD -11.3%, pass 84% in 5.5 months
  scale down mild 0.7..1.0:     +0.094%/day, same DD, pass 84% in 5.4 months
  fixed 0.75%:                  +0.148%/day, maxDD -16.8%, pass 66% in 2.6 months
Verdict: CANDIDATE (an improvement, not an edge): cut size on high-volatility days, never add. +6 points of pass odds for
~0.7 month more. EA change: risk = 0.5% x min(1, median ATR(14, 250 days) / ATR(14)) with a floor of 0.5. (bt/vol_sizing.py)

### 13. Online scan — 2 sources read, 1 concrete rule found and tested (#14); the rest are cross-sectional stock effects
  (Xu 2017 first-2-hours momentum / last-2-hours reversal, long-short deciles of thousands of stocks) — not usable on 4 CFDs.
  Sources: alphaarchitect.com (Gao-Han-Li-Zhou intraday momentum), quantconnect.com strategy library, cxoadvisory.com (Xu 2017).

### 14. Intraday momentum: first 30 minutes predict the last 30 minutes (Gao, Han, Li, Zhou 2018 JFE) — DEAD here   [05:50 MYT]
Rule: signal = 10:00 price vs prior 16:00 close (also: the 9:30-10:00 candle alone); at 15:30 trade in that direction, exit 16:00.
  US100 (2021-26) net -1.1 bp/trade (gross -0.6), US500 -1.2 (gross -0.5), TSLA +0.7 bp t=0.4 (gross +2.3, cost 1.7), AAPL (2015-26) -3.1 bp t=-4.2.
  Candle-only signal: -1.5 / -1.4 / -1.7 / -1.7 bp. Nothing positive in both halves anywhere.
Verdict: DEAD. The published SPY effect (1993-2013) is absent in these CFDs 2015-2026, and the last 30 minutes are too small a move to pay the spread. (bt/intraday_mom.py)

### 15. Opening-candle calm-day filter (skip when ATR > k x 1-year median) — done, equivalent to #12   [2026-10-09 09:30 MYT]
  fixed 0.5% all days: 2276 trades, pass 78% in 4.7 mo | skip ATR > 1.5x median: 2027 trades, +0.095%/day, maxDD -12.0%, pass 84% in 5.5 mo
  skip > 1.25x: 1733 trades, pass 83% in 6.5 mo (too many good days lost) | skip >1.5x AND scale down 0.5..1.0: pass 85% in 5.9 mo.
Verdict: same pass odds as the scale-down-only rule (#12); keep the simpler rule — risk = 0.5% x min(1, median ATR / ATR), floor 0.5.

### 19. Tokyo-sweep exits (Shen, after the live gold trade of 8 Oct closed at London for -0.31R, then ran +1.6R) — DEAD   [2026-10-09 10:05 MYT]
Entry rebuilt as the SessionSetups_EA rule on gold M5 from M1 2012-2026: dip >= 1 x ATR(14, M5) below the 09:00 Tokyo open,
5-min close back above, buy; stop = min(dip low - 0.1 ATR, close - 0.5 ATR). 2,725 trades; median stop $2.2 = 0.12 daily ATR.
  live (hold to London):  -0.024R t=-0.7, 7/15 years | 1R -0.10 | 1.5R -0.08 | 2R -0.07 | 3R -0.06 (all with London time-out)
  hold to NY 08:00 +0.006 | hold to NY 16:00 +0.021 | hold 24h +0.085 (t 1.3, halves -0.03/+0.20, 2024-26 +0.63)
  3R else NY 16:00 -0.055 | 3R else 24h -0.055 | stop x1.5 -0.04 | stop x2 -0.04 | stop x2 + 2R -0.06
  stop = 1 daily ATR, 2R, 24h: +0.023 (t 1.7, 9/15 years, halves -0.03/+0.08) | stop 1 dATR hold to NY 16:00 -0.003
  trail 1R after +1R -0.07 | breakeven at +1R + 3R -0.06
  Baseline buy-every-day at 09:00 Tokyo, same exits: London -0.045, 3R -0.06, hold to NY 16:00 -0.024, hold 24h -0.004 (2024-26 +0.45).
Verdict: DEAD. No exit turns the entry into an edge; the long-hold variants only collect gold's 2024-26 rise (the no-sweep
baseline collects it too). The 8 Oct trade was one draw from a 32%-win, tiny-stop distribution. (bt/exits_tokyo.py)

### 20. Indicator crossovers x higher-timeframe filters x exits (fixed grid, 768 cells) — DEAD except one TSLA WATCH cell   [10:20 MYT]
Signals on 5m and 15m: EMA 9/21 cross, EMA 20/50 cross, MACD(12,26,9) signal cross, RSI(14) back through 30/70; long and short.
HTF filter: none / 1H EMA50 vs 200 / 4H EMA50 vs 200 (completed bars). Stop 2 x ATR(14, entry TF) or 0.5 daily ATR.
Exits 1R / 2R / 3R / opposite signal, 8h limit, no overnight holds. Costs + a coin-flip benchmark per cell.
  gold 2014-26: 0 of 192 cells positive (best -0.003R; 2xATR(5m) stop cells -0.14R = costs).
  US500 2025-26: best +0.020. US100 2025-26: best +0.059 (EMA20/50 5m, 1H filter, 3R; n=862, t 1.1).
  TSLA 2021-26: 64/192 positive; 1 cell passes the bar: EMA 20/50 on 5m, no filter, 2xATR stop, exit at the opposite cross
  same day: +0.077R, n=1725, t 2.2, halves +0.08/+0.07, 6/6 years, coin flip +0.02. Neighbours +0.04..+0.08 (t 1.2-1.9).
  Averages: HTF filter 1H/4H no better than none; RSI worst signal everywhere; 1R targets worst exit; MACD ~ EMA.
  Trap found and removed: with overnight holds allowed, TSLA "exit on opposite cross" cells showed +0.34R — but the coin flip
  showed +0.26R (a small stop + long hold harvests the drift asymmetrically, and gap fills are unrealistic). Same-day only.
Verdict: DEAD for gold/US100/US500; WATCH for TSLA EMA 20/50 (1 of 768 cells; likely the same intraday-trend effect the
opening candle already captures). What would change it: the TSLA cell holding +0.05R in 2027 data, and excess over coin flip > 0.05.
(bt/indicators.py, results/indicators_*.csv)

### 21. Forex Factory sweep: 14 systems read, 4 codeable as written, all 4 DEAD on gold 2012-2026   [2026-10-09 10:40 MYT]
Read via WebFetch (reddit blocked from the cloud): Trading Made Simple (152k replies), TMS(r), THV, HoLo, Pivot Trading,
Gold Levels, Scalping Gold 1-min, BiteFX, 5m 4R/R, M1 Countertrend (grid, no stop), Sniper Scalping, Day Trade Setup,
Wicks Get Filled, NY ORB gold (tiptoptrade). None of the 14 threads contains a trade log, myfxbook or forward test.
Codeable and tested (bt/ff_rules.py):
  A HoLo (highest/lowest H1 open of the broker day, fade the return, SL day extreme, BE+ at +0.07/+0.14 ATR, 08-12 NY):
    n=4048 -0.042R t=-1.9, 4/15 years; coin flip -0.02. Without the M15 confirmation -0.040. DEAD.
  B Trading Made Simple(r) 1:1 learner (HMA12 x EMA5(+2), HA, Stoch 8/14 vs 50, RSI14 vs 50, SL bar[2], TP 1:1):
    15m -0.117R (1/15 years), 1h -0.059 (4/15), 4h +0.022 t=0.7 (8/15, halves -0.02/+0.07). DEAD (breakeven at best on 4h).
  C NY open-range breakout gold, version B (5-candle 09:30 range, ATR(5)/body/volume filters, SL = breakout candle):
    1.5R -0.166R (2/15 years), 2.5R -0.127, author's scale-out -0.153; coin flip -0.08. DEAD (thread's own EA test agreed).
  D Wicks get filled (M15/M30, dip below the open then buy-stop at the prior close, TP = prior high, SL 1:1):
    as written -1.27R/-0.92R (wicks smaller than costs); wick >= 10x spread: -0.109 / -0.099R, 0-2/15 years; coin -0.07. DEAD.
Not codeable (discretionary or closed-source): THV, Pivot Trading, Gold Levels (needs options gamma data), BiteFX, Sniper,
DTS, Scalping Gold 1-min, 5m 4R/R (pattern undefined). M1 Countertrend is a no-stop grid: not for a prop account.

### 22. FTMO scenario engine: P(pass by 1/2/3/4 months), fail odds, income — by risk level and strategy mix   [2026-10-09 11:30 MYT]
Monte Carlo on the real trade lists (10-day block resampling, FTMO 10%+5%, 5% daily, 10% total, min 4 days), bt/scenario.py, results/scenarios.csv.
Live mix (OC TSLA + OC US100, 2022-26):
  risk 0.25%: pass 4m 2%, 12m 42%, fail 2%, median 8.3 mo | 0.50%: 2m 5%, 3m 15%, 4m 26%, 12m 71%, fail 19%, median 4.9 mo, maxDD 12%
  0.75%: 2m 18%, 3m 33%, 4m 44%, 12m 65%, fail 34%, median 3.0 mo | 1.0%: 1m 9%, 2m 30%, 3m 43%, 4m 50%, 12m 58%, fail 42%, median 2.0 mo
  1.5%: 1m 18%, 2m 38%, 12m 48%, fail 52% | 2.0%: 1m 24%, 2m 39%, 12m 42%, fail 58%, maxDD 37%.  Half edge at 0.5%: 47% pass / 39% fail.
Adding gold trend + pre-FOMC: +2 to +4 points at every risk level (0.5%: 75% pass, fail 18%). Gold trend alone at 0.5%: +0.21%/month, never passes.
Funded (12 months, 80% split, $10k): 0.5% -> keep 65%, ~$160-180/month; 0.75% -> keep 30%, ~$190-210; 1% -> keep 12-14%.
Reading: "fast pass" (1-2 months) needs 1-2% risk and is a coin flip with a 50-58% chance of losing the fee; the honest fast route is ~0.75%
(1 in 3 passes by 3 months, 1 in 3 fails). The high-probability route is 0.5% (71% within a year, 19% fail).

### 23. Opening-candle variations (TSLA, US100, US500 M30 2022-26; fixed list, every cell reported) — base rule stands   [11:45 MYT]
  60-min candle: TSLA +0.055 (worse), US100 +0.093, US500 +0.059. Exit 12:00 worse everywhere; exit 14:00 = 16:00.
  Candle range buckets: no monotonic pattern (tiny candles: TSLA n=25). Body/range >= 0.7: TSLA +0.13, US100 +0.16, US500 +0.01; dojis (<0.3) still >= 0.
  Candle against the overnight gap beats with-the-gap on all three (TSLA +0.12 vs +0.09; US100 +0.16 vs +0.04; US500 +0.19 vs -0.04) — report only.
  Weekday cells (TSLA Tue -0.14, Mon/Fri +0.24; US100 Mon -0.13): 15 cells, treated as noise. Cross-asset agreement filters: no effect.
  Daily R correlations: TSLA/US100 0.14, US100/US500 0.48.
  Stop-and-reverse after a stop-out: on 30-min bars looked like +0.17/+0.14/+0.18 but the 30-min bar hides the leg-2 stop; on 5-minute
  bars (proper check) TSLA +0.126 vs base +0.098 (reversal leg +0.066R, t 0.9), US100 2025-26 0.00, AAPL ~0. WATCH on TSLA only, not deployable.
Verdict: no variation beats the base rule with evidence; keep it as is. (bt/oc_var.py, bt/oc_sar_m5.py)

### 24. Online daily rules: RSI(2) and IBS mean reversion (Connors / Quantified Strategies; backtrex.com third-party test) — IBS on US100 WATCH   [2026-10-09 12:05 MYT]
Sources: backtrex.com RSI(2) NAS100 2016-26: CAGR +2.4%, 65 trades, 75% wins, maxDD -25% ("wins often, earns little");
quantifiedstrategies.substack.com IBS+RSI (rules paywalled; IBS rule used in its public form).
RSI(2) (<5 long above the 200-SMA, exit close > 5-SMA; mirror): US100 n=48 +0.27 ATR t=1.3; US500 n=52 +0.28 t=1.3; AAPL n=67 +0.23 t=1.6; TSLA +0.05. Too few trades.
IBS (<0.2 long above 200-SMA, exit on a close above the prior high or 5 days; mirror), with a 2-ATR stop, R per planned risk (bt/ibs.py):
  US100 2018-26: n=278 +0.083R t=2.3, 69% wins, halves +0.10/+0.07, last 60 +0.03, longs +0.13 (n=211) shorts -0.08; 6/9 years > 0.
  US500 +0.01; AAPL +0.04 (threshold 0.1: +0.195 t=4.1 — one cell, neighbours weak); TSLA -0.07. Stop 1 ATR kills it (44% stops).
Verdict: WATCH — US100 longs only, ~25 trades a year, about +1.5%/year at 0.5% risk; a diversifier, not a challenge strategy.

### 25. Queue items: expiry days DEAD, post-FOMC afternoon DEAD   [12:05 MYT]
  3rd-Friday day return: US100 -0.10 ATR, US500 -0.12, AAPL -0.12, TSLA -0.05 (all days +0.03/+0.04) -> slightly negative days, no rule.
  Monday after expiry: +0.02 / -0.01 / +0.13 / +0.10 — inconsistent. Post-FOMC 14:30-candle direction held to 16:00: US100 -3.3R/US500 -1.5R
  per unit of candle body (41 events, ~50% wins): the first 30 minutes after the statement reverse as often as they continue. DEAD.

### 26. Reddit sweep — blocked; tested the three most-shared rule sets from their original sources instead   [2026-10-09 11:40 MYT]
Reddit is unreachable from every route: WebSearch/WebFetch exclude it, and the Claude in Chrome extension (connected to
Shen's laptop) refuses reddit.com with "This site is not allowed due to safety restrictions" (a block on the site, not a
per-site permission). Not worked around (no mirrors). Substitute: rule sets those subs pass around most that the lab had
not tested, taken from the original sources. Shen can paste any Reddit post's rules into chat for a test.

#### 26a. "Beat the Market" noise-band intraday momentum (Zarattini, Aziz & Barbon 2024; SPY 2007-24 Sharpe 1.33) — CANDIDATE on US100 only
Rule as published: sigma(k) = mean over 14 prior sessions of |close at mark k / 9:30 open - 1|; UB = max(open, prior
close) x (1+sigma), LB = min(open, prior close) x (1-sigma); at 10:00, 10:30 ... 15:30 NY: long if price > max(UB, VWAP),
short if < min(LB, VWAP), else flat; flat at 16:00. VWAP from 30-min bars (typical price x tick volume). Costs: bar
spread half per side + commission. FTMO M30 2021-10..2026-10 (1,239 sessions). bt/noise_band.py, noise_band_check.py,
noise_band_later.py, combo_ftmo.py.
  US100: 1,082 trades (0.9/day), 42% win. At 1x notional (position = balance): +11.5%/yr, vol 8.9%, Sharpe 1.29, t 2.9,
    maxDD -7.4%, worst day -2.15%. Paper sizing: +17.9%/yr, Sharpe 1.31, maxDD -15.9%. Every year positive
    (paper sizing 22 +16.6%, 23 +29.6%, 24 +31.3%, 25 +5.9%, 26 +4.5%). Coin flip at the same times: -0.35 bp/day vs
    +4.55 real, beats 200/200 draws. Neighbours: opposite-band stop Sharpe 1.30, band x0.75 0.89, x1.25 1.17, x1.5 0.92;
    double spread 1.18. In the paper's sample (to Apr 2024) Sharpe 1.89; after it (out of sample) 0.83.
    M5-built vs M30-built on 339 common days (2025-05..2026-10): daily correlation 0.99, avg -0.85 vs -0.03 bp/day ->
    the M30 approximation is fine, and the last 17 months are FLAT.
    Overlap with the live rule: the 10:00 entries always take the opening candle's direction; daily corr 0.34. Entries
    from 10:30 only (diagnostic): Sharpe 1.34, t 2.9, years +17.5/+16.0/+7.5/+9.4/+1.8%, corr 0.31 -> a separate bet.
    Fed days +12.5 bp/day (n=38). Latest 60 sessions +3.3 bp/day vs +4.6 average (43% of stretches worse).
  US500 (the paper's own market): Sharpe 0.66, t 1.5; in-sample Sharpe 1.63, out of sample -0.27 (2025 -6.8%, 2026 -18.0%
    at paper sizing). Fails out of sample.
  TSLA: +26.7%/yr at 1x, Sharpe 1.23, t 2.8, maxDD -19.5%, worst day -4.6%; 2024 -5%; Fed days -19.8 bp/day; latest 60
    sessions -2.7 bp/day (20th percentile). WATCH (same stock-specific slump as the opening candle).
  FTMO (2022-26, both phases, 10-day blocks): opening candle 0.5% (live plan) 78% / 57% pass (full / half edge) in
    4.7 / 5.4 months. Band US100 alone 1x: 98% / 70% but 15 / 22 months; 2x: 88% / 60% in 6.8 / 8.5 months, worst day -4.3%
    (too close to the 5% daily limit). Opening candle + band US100 1x: 80% / 56% in 3.6 / 4.0 months, worst day -2.95%.
Verdict: CANDIDATE on US100 (passes the bar; beats coin flip; robust to settings and double spread) with two warnings:
flat for the last 17 months, and it already failed out of sample on US500. Adds speed (about a month), not pass odds.
Next: paper-trade it in the lab app next to the opening candle; add to the EA only if forward results track the model.

#### 26b. Supertrend (10, 3) and UT Bot (1, 10) stop-and-reverse, the most-copied TradingView scripts — DEAD
Rules: TradingView defaults; signal at the bar close, fill next open, reverse on the opposite signal; UT Bot also on
Heikin-Ashi closes. Always-in (swap 0.01%/night) and session-only modes. R = P&L / distance to the indicator line.
Grid: gold M5/M15/H1 2012-26, US100/US500 M30/H1 2021-26, TSLA/AAPL M5/M15/H1 2021-26 = 78 cells (bt/atr_trail.py,
results/atr_trail_cells.csv). 26 positive; 4 above the coin-flip 97.5% band; 1 passes the bar.
  gold: 1 of 18 positive (H1 Supertrend +0.017, t 0.5); M5/M15 all negative, UT Bot M5 -0.34R vs its coin flip -0.17R.
  US100 best +0.031R, US500 best +0.052R, none with t > 1.0. AAPL 1 of 18 positive.
  TSLA M5 Supertrend session-only: n=2,426, +0.055R, t 2.8, 6/6 years, halves +0.03/+0.08 — the same TSLA intraday-trend
  effect as #20's EMA cell and the opening candle; 1 of 78 cells.
Verdict: DEAD. What would change it: the TSLA cell holding up in 2027 with the opening candle switched off.

#### 26c. IBS mean reversion on the indices ("2.11 Sharpe" rule, Quantitativo, QQQ) — WATCH (Swing accounts only)
Rule as published: buy at the close when close < 10-day high - 2.5 x 25-day average range and IBS < 0.3; sell at the first
close above the previous day's high; no stop. Fixed variant: IBS < 0.2, same exit. Daily bars by FTMO trading day
Dec 2017..Oct 2026; spread US100 1.5 / US500 0.5 pts, swap 0.01%/night; R = P&L / ATR(14). Baseline: the same holding
periods from random days (index drift). bt/ibs.py.
  US100 published: n=85 (9/yr), +0.44R, t 3.5, 74% win, hold 3.9 days, 15% in market, excess over drift +0.32R (t 2.4),
    halves +0.27/+0.61, 8/9 years (2020 -0.27), worst trade -7.0% of price. +8.7%/yr at 1x notional.
  US100 IBS<0.2: n=244 (27/yr), +0.28R, t 3.8, excess over drift +0.16R (t 2.0), halves +0.29/+0.28, 2022 -0.03,
    2018 -0.16, 2026 -0.20; +15.8%/yr at 1x, 42% in market, worst trade -8.5%.
  US500: published n=78 +0.39R t 2.2 (excess t 1.7); IBS<0.2 n=228 +0.21R t 2.4 (excess t 1.4).
  Daily corr with the opening candle 0.02. Opening candle + IBS<0.2 US100 at 0.5x: 82% / 60% pass in 4.1 / 4.9 months;
  + band 1x as well: 82% / 59% in 3.2 / 3.8 months, worst day -4.4%.
Verdict: WATCH, agreeing with #24 (IBS<0.2 above the 200-SMA with a 2-ATR stop: US100 +0.083R t 2.3). Long-only in a rising market, excess over drift only t 2.0-2.4, no stop, needs overnight and weekend holds.
What would change it: a pre-2018 index test (needs older daily data) showing the excess over drift holds in flat markets.

### 27. Reddit post (r/Daytrading, pasted by Shen): ICT 1-minute model "MSS + FVG/iFVG/OB + OTE 0.705, SL 1.0, TP 0.0" — DEAD; the poster's numbers are backtest bugs   [2026-10-09 15:10 MYT]
Poster: NQ 1m Dec 2022-Dec 2025, AI-written script: 4,202 trades, 65.6% wins at 2.39R, +1.22R per trade, max DD 8R.
Rule as written (bt/ict_ote.py): MSS = body close through the last swing (n-bar fractal, known n bars later); fib on the MSS leg
(wicks); limit entry at 0.705 inside an FVG / iFVG / order block; SL 1.0, TP 0.0 (2.39R); invalid if 0.0 breaks before the fill.
Bid/ask fills; same-bar rule: fill + stop on one bar = loss, no TP on the fill bar, SL+TP on one bar = loss. Breakeven win rate 29.5%.
Honest, NO costs (n=3, with confluence, Asia+London+NY AM):
  US100 M1 (Jun-Oct 2026) n=303 -0.16R, 25% wins | US500 M1 n=283 -0.11R, 26% | US100 M5 (May 2025-Oct 2026) n=316 -0.19R, 24%
  gold M1 2024-26 n=3,055 -0.11R, 26% | gold M1 2012-23 n=13,721 -0.13R, 26% (t -10). n=5 pivots and "after a lower low" variants: -0.02 to -0.16R.
  By session: NY AM least bad (~0 before costs: US100 -0.14, US500 +0.04, gold -0.00/-0.04), Asia worst.
With real spreads: US100 -0.37R, US500 -0.69R, gold -0.51 / -0.79R. Median stop: US100 6 pts Asia, 16 pts NY AM; gold $0.2-1.4.
Bugs reproduced on the same data (no costs):
  optimistic same-bar ordering (TP first, TP allowed on the fill bar): +0.16 to +0.27R, 34-37% wins
  swing points marked without the n-bar delay (look-ahead): +0.11 to +0.55R, 33-46% wins
  both together: US100 M1 +1.86R 84% wins; gold 2012-23 +1.23R, 65.7% wins (poster: +1.22R, 65.6%)
Verdict: DEAD. The 65% win rate is look-ahead + same-candle optimism, not an edge. Same conclusion as the earlier SMC/ICT tests.
Note: every M1 export in data/raw is exactly 100,000 bars (MT5 "Max bars in chart" cap) -> 1-minute index tests cover only 3.5 months.
#### 27b. Thread follow-up: the poster forced SL-first when one candle hits both SL and TP; "it happened only once in 3 years, stats unchanged"
Consistent with our data: SL and TP on the same candle after entry = 0 of 401 trades (US100), 2 of 391 (US500), 59 of 18,471 (gold) —
the stop and target are a whole leg apart. The leak is the ENTRY candle (bt/ict_ote_leaks.py, no costs):
  the candle where the limit fills also runs through the stop in 16-19% of trades (US100 77/401, US500 61/391, gold 3,464/18,471);
  the entry candle also breaks 0.0 (should be no trade) in 47 / 23 / 1,767 cases.
  gold 2012-23: honest -0.118R 26.0% | stop ignored on entry candle -0.059 | TP counted on entry candle -0.033 | fill through a
  0.0 break -0.097 | TP-first on shared candles -0.108 | all four +0.241R 36.6% | look-ahead swings alone +0.083 | look-ahead + all
  four +1.118R 62.5%. US100: honest -0.197 -> look-ahead + all four +1.799R 82.6%.
Fix for the poster: check the stop on the entry candle itself, never count the target on the entry candle, drop setups whose
entry candle also breaks 0.0, confirm swings n candles late, and build the setup only from candles before the entry candle.

### 28. Reddit post (pasted): "Day trading stock indexes is dead — 72.4% of the Nasdaq's >1% moves in 2024 happened after hours; trade the night" — claims false on our data, overnight trades DEAD   [2026-10-09 15:10 MYT]
No rules in the post; checked its two claims and the obvious overnight trades on US100/US500 30-min bars 2021-09..2026-10 (FTMO).
  Claim 1: days with a >1% move overnight (16:00 -> 9:30) vs in regular hours (9:30 -> 16:00): US100 2024 29 vs 52 (overnight 36%), 2021-26 242 vs 400
    (38%); US500 2024 15 vs 22 (41%). Overnight share of variance 35-43% over 17.5 hours vs 57-65% in 6.5 regular hours.
  Claim 2: FTMO tick volume (CFD quote updates, not futures contracts) 49-50% in 9:30-16:00 -> per hour the session is ~2.7x busier.
  Trades (enter at the 16:00 close, exit at the 9:30 open, spread both ways + swap 0.01%/night): with the day's direction US100 -4.1 bp/night (t -1.7),
    US500 -2.9; against the day -0.7 / -3.0; always long +0.9 / -0.6 (t 0.4 / -0.3). Agrees with #6 (overnight premium ~+0.015 ATR, too small).
Verdict: DEAD. Overnight holds also put gap risk on FTMO's 5% daily limit.

### 29. Reddit post (pasted): "15 years trading indices: mark S/R on daily/hourly, trade only in the direction of the 1H 200 EMA, enter when RSI crosses 50" — DEAD (TSLA shows the known TSLA trend effect only)   [2026-10-09 15:20 MYT]
S/R marking is discretionary (and levels are dead in #0/#1); no stop/exit given -> fixed before running: stop 1.5 x ATR(14), targets 1R/2R/3R,
limit 24 bars (1H) / 32 bars (15m). Signal: RSI(14) crosses 50 in the 1H 200-EMA direction, on 1H and on 15m. Costs + coin flip (bt/ema200_rsi50.py).
  gold 2014-26: 1H -0.036/-0.011/+0.020R (1R/2R/3R), 15m -0.106/-0.091/-0.065R; coin flip about the same.
  US100 2021-26: 1H -0.04/-0.05/-0.02, 15m -0.06/-0.04/-0.01 (coin flip -0.01..+0.05). US500: -0.01 to -0.08 everywhere.
  TSLA with overnight holds looked like +0.15/+0.21R (1H 2R/3R) and +0.20/+0.30R (15m) — but the coin flip also scored +0.07 to +0.21R:
  stops "fill" at the stop price through overnight gaps. Same-day only: 1H +0.04/+0.05/+0.05R (t 1.3-1.5), 15m +0.02/+0.07/+0.06 (t 0.7-2.1),
  coin flip ~0 to +0.02 -> ~+0.05R excess, longs carry it: the same TSLA intraday trend as #20, #26b and the opening candle.
Verdict: DEAD on gold/US100/US500; nothing new on TSLA. The post's claim is survival ("kept my accounts alive"), not profit.

### 30. Reddit post (pasted): "How to become profitable: learn to trade liquidity" (4H swing = liquidity; after price takes it, 1H close back through the level, stop behind the sweep, target the next 4H swing, >= 1:2, breakeven) — DEAD on gold/US100/US500   [2026-10-09 15:35 MYT]
Poster trades GBPUSD/majors (~2 setups a week), gives no statistics; "breakdown" level and the 15-min early exit are discretionary.
Mechanical version fixed before running (bt/liq_4h1h.py): 4H n-bar fractal swings (n=3/5), usable once confirmed, each traded once;
sweep = 1H high above an unswept 4H swing high (mirror for lows); trigger = first 1H close back below the level within 12h; stop =
sweep extreme + 0.05 daily ATR; target = nearest unswept opposing 4H swing (only if >= 2R) or fixed 2R; breakeven at +1R or none; 5-day limit.
  gold 2012-26: swing target -0.02 to -0.05R (~20 trades/yr, 17-22% wins), 2R target -0.02 to -0.07R (130-200/yr); coin flip similar
    (swing-target coin flips +0.09..+0.18 = gold's uptrend on flipped longs).
  US100 2021-26: -0.02 to -0.30R. US500: -0.33 to +0.12R (the +0.12 cell t 0.9, its neighbours negative).
Verdict: DEAD on our instruments. Not tested on his market (no FX data in the repo) — would need GBPUSD/EURUSD H1 exports.

### 31. RedNote (小红书) video, "SMC交易员_M": "每天如何用 SMC 制定交易计划" (daily SMC plan on gold: daily OB -> 1H sweep + MSS -> 1H OB -> 5-min FVG respected -> target the IDM high) — DEAD   [2026-10-09 20:58 MYT]
Source: post + 2-min Mandarin video sent by Shen, transcribed with tools/video/video_notes.py. The poster shows one US-session long
(1:3, "+230 pips"). Rule as posted: daily bullish OB reached + liquidity swept; 1H MSS; the last down candle at the low = 1H OB; the
high left above (Asian-session high) = inducement (IDM) = target; US session: back into the 1H OB, 5-min sweep, 5-min bullish FVG,
a candle dips into the FVG and closes back above it -> buy; stop below the FVG; target IDM. Shorts mirrored.
Fixed before running (bt/smc_plan.py): daily OB = last down day among the 5 before a close above their highs, live until a daily
close below it (max 90 days); 1H 3-bar fractals usable 3 bars later; sweep = 1H low below the last swing low while overlapping a live
daily OB; MSS = 1H close above the last swing high within 24 h; 1H OB = last down 1H candle at/up to 3 bars before the low; IDM = high
from the MSS until price returns to the OB (setup cancelled if IDM is taken first or a 5-min close is 0.1 daily ATR below the OB);
5-min: new 12-bar low, FVG within 6 bars, respect within 12; entry at the respect close; stop min(FVG bottom, bar low) - 0.05 daily
ATR; only if target >= 2R; entries 08:00-16:00 NY; exits on 1-min bars (stop first), 24 h limit. Gold M1 2012-01..2026-10-07 (MT4,
UTC), FTMO spread by year + commission. Coin flip per trade.
  A as posted: 139 trades (9/yr), avg -0.42R, t -2.4, win 14%, 4/15 years > 0, last 30 -0.54R; coin flip +0.01.
    longs -0.10R (n 74), shorts -0.79R (n 65, 1/15 years > 0). 86% stopped, 11% reach the IDM (median 6.3R away); median stop 0.10%.
  B no daily-OB filter -0.24R (493). C rr >= 1 -0.42R. D any session -0.28R (214). E limit at the FVG top -0.35R (longs +0.00).
  F fixed 2R target -0.18R (208, 32% wins). G the 5-min trigger alone (no context, 2R, US session): -0.085R over 8,829, t -5.6.
Verdict: DEAD. Same family as #27/#30: a stop a few dollars under a 5-minute gap is taken by noise long before a far target.

#### 31b. Same rule at every timeframe nesting (Shen: "try 4H, 15-min swings, mix 1H and 5-min") — DEAD at every scale   [2026-10-09 21:20 MYT]
bt/smc_grid.py: zone TF (D1 / H4 / none) x structure TF (H4 / H1 / M15) x entry TF (M15 / M5 / M1), zone > structure > entry,
target IDM (>= 2R) or fixed 2R, US-session entries; every #31 definition counted in bars of its own timeframe; exits on 1-min,
3-day max; gold 2012-26, FTMO costs. 42 cells (results/smc_grid.csv): 9 positive, 33 negative, NONE passes the in-sample bar
(best in-sample t 1.07; bar is t >= 2.5). The cells with enough trades (M15/H1 structure, 30-190 trades a year) are -0.05 to -0.16R
(t -2 to -5). The positive cells are H4-structure cells with 4-14 trades a year (t 0.2-1.3); the best, D1/H4/M5/2R, +0.22R on 79
trades (in-sample +0.13, t 0.7); none/H4/M1/IDM +0.17R comes from 2024-26 longs in gold's uptrend (in-sample +0.05, t 0.2).
With 42 tries one lucky cell is expected; none reached even that. To rerun on indices/FX when the full export lands.

### 32. RedNote video "熊猫聊交易系统" (Coach Panda): "如何判断牛市来了" — a talk with no rules; its 3 claims tested   [2026-10-09 21:43 MYT]
Claims: (1) bull markets start when nobody is watching; (2) the signal is not rising but "can't fall" — dips get bought, bad news
can't push it down, price grinds up in a channel; (3) "会买的是徒弟，会卖才是师傅" — the exit decides what you make. Tests fixed before
running (bt/panda_bull.py, bt/panda_exit_baseline.py), daily bars, signal at the close, entry next open, costs + assumed swap
(5%/yr long CFDs, 1%/yr gold). Baselines: same direction + holding time from a random day; coin flip. Gold 2012-26, US100/US500
2018-26, TSLA 2019-26, AAPL 2015-26, BTC 2020-26.
  A "dip bought" day (>= 0.5 ATR below the open, closes in the top third) -> 5-day long: gold +0.05R vs random-day +0.06, US100
    +0.04 vs +0.06, US500 +0.03 vs +0.04, TSLA +0.16 vs +0.12 (2024+ negative), AAPL +0.10 vs +0.06, BTC +0.07 vs +0.10.
    Above-200-day only: same picture. DEAD as a timing signal (being long in a rising market is the whole effect).
  B shallow pullbacks in an uptrend (<= 1.5 ATR from the 20-day high, above the 200-day) -> 20-day long: beats random days on
    US100 (+0.23 vs +0.14, t 1.9, n 67) and AAPL (+0.20 vs +0.16); worse on gold, US500, TSLA, BTC. DEAD.
  C "bad news can't push it down" (Fed/CPI/jobs day, 9:30 candle -0.25 ATR, closes up): 6 events on US100, 4 on US500 (30-min data
    only from 2021-09) — untestable here. (All Fed/CPI/jobs days -> 5-day long: US100 +0.14 vs random +0.07, but -0.00 before 2024.)
  D exits on the same entries (close above the 20-day high, long, 2-ATR initial stop; R per 2 ATR):
    gold: 2-ATR trail +0.59, 3-ATR +0.71, 4-ATR +0.76, 10-day low +0.46, close < 50-day MA +0.90, hold 20d +0.34, hold 60d +0.80
    US100: +0.29 / +0.49 / +0.86 / +0.64 / +1.00 / +0.33 / +0.72;  US500: +0.06 / +0.19 / +0.09 / +0.16 / +0.24 / +0.21 / +0.30
    Entries vs random entry days with the same exit: better in 39 of 42 market x exit cells (edge mostly +0.1 to +0.7R; TSLA the
    exception). Slow exits (50-day MA, 4-ATR) best overall, the tight 2-ATR trail worst; but the best exit changes by period
    (gold before 2024: 3-ATR trail best; from 2024: 50-day MA, in gold's rally). 26-81 trades per market -> t about 2.
  Verdict: claims 1-2 DEAD as signals (A, B); claim 3 supported: exit choice moves results 2-10x and 20-day breakouts beat
  random entries — the same trend-following effect as #9 (gold, WATCH), now on 5 of 6 markets. Confirm on all ~110 markets with
  the full export (battery DON/MA rule books + an exit grid, backlog #39), with real swaps from the spec sheet.

### 33. RedNote video "Trading Dimsum": "5:1 Reward to Risk Ratio" (FVG retest after a break of structure, target the trendline liquidity) — 5:1 claim DEAD; 1-hour version with a near target = CANDIDATE on gold, pending other markets   [2026-10-09 21:48 MYT]
Rule as told (FX chart, short; longs mirrored): a strong drop leaves a bearish FVG and breaks structure (BOS); price pulls back up
along a rising trendline to the gap; sell when price touches the gap; stop at the high; target the liquidity under the trendline;
"a nice 5:1". Fixed before running (bt/fvg_retest.py): 3-bar fractals usable 3 bars later; BOS = close below the last swing low (each
used once); leg = highest high since the last swing high -> BOS bar; its first bearish FVG (up to 3 bars after the BOS) is the gap;
stop = leg high + 0.05 daily ATR; sell limit at the gap's lower edge for 48 bars, cancelled if price takes the leg high first.
Targets: T1 last confirmed pullback swing low (trendline's last touch), T2 fixed 5R, T3 low after the BOS; T1/T3 only if >= 2R.
Exits on 1-min bars, stop first, 5-day max; gold 2012-Oct 2026; FTMO spread + commission; coin flip per trade.
  15-min: T1 +0.050R (2,063 trades, t 1.2), T2 5R +0.031R (15,144, 19% wins), T3 +0.035R.
  1-hour: T1 +0.171R (657 trades, 44/yr, t 2.3, 32% wins, coin flip -0.235, 12/15 years > 0; longs +0.28, shorts +0.08;
    before 2024 +0.197 (n 540), from 2024 +0.049 (n 117)); T2 5R +0.016R (3,574); T3 +0.109R (792, t 1.6).
  Checks on 1-hour T1 (bt/fvg_retest_check.py): same side + same bracket from random minutes -0.048R (gold's drift doesn't explain
    it). Every neighbour positive: fractal n=2 +0.120 / n=5 +0.157; stop buffer 0 +0.204 (t 3.0) / 0.1 ATR +0.161; window 24 bars
    +0.112 / 96 bars +0.133; rr >= 1.5 +0.121 / >= 3 +0.415; entry at the gap middle +0.150. By year: 12 +.36 13 +.22 14 +.03
    15 +.50 16 +.36 17 +.14 18 +.18 19 -.16 20 +.16 21 -.23 22 +.25 23 +.56 24 -.08 25 +.03 26 +.26.
    Median hold 10 h (21% past 24 h): swap at ~5%/yr would cost ~0.03R -> ~+0.14R net.
Verdict: the 5:1 claim is DEAD (fixed 5R ~ 0). The 1-hour gap retest with the near pullback-low target meets the CANDIDATE bar
on gold (n >= 200, both halves > 0, t >= 2, +0.05R or better, no year below -0.3R), with two warnings: it was the best of 6 cells
tried, and 2024-26 is weak (+0.05R). The real test is markets it was never looked at on: the poster's FX pairs, indices and silver
from the full export (backlog #40). If those hold, paper-trade it next to the opening candle.

### 34. RedNote video "阿基米得": "趋势线破位后，FVG就是天然压力位" (after a trendline break, the FVG is resistance) — DEAD as shown   [2026-10-09 22:00 MYT]
Silent video, rules read from the frames: rising trendline; a close below it leaves a bearish FVG; sell the retest of the gap; stop
just above the gap (0.15% in the example); target ~2.5R (example 2.48R). Mirror for longs (example 4.52R).
Fixed before running (bt/tl_fvg.py): trendline through the last two confirmed 3-bar swing lows (second higher), held since the first
point; break = first close below it; gap = first bearish FVG from the leg high to 3 bars after the break; sell limit at the gap's
lower edge for 48 bars, cancelled if the leg high is taken first. Stop S1 = gap top + 0.05 ATR (the video's), S2 = leg high +
0.05 ATR. Targets 2R / 3R, or (S2) the last pullback low if >= 2R. Gold 2012-Oct 2026, exits on 1-min, FTMO costs, coin flip.
  As shown (stop above the gap): 15-min 2R -0.113R (9,420 trades, t -7.7, 2/15 years > 0), 3R -0.101R; 1-hour 2R -0.048R
    (2,081), 3R -0.077R. Median stop 0.10-0.14% — taken by noise.
  Stop above the leg high: 15-min -0.029 / -0.011R; 1-hour +0.036 / +0.050R (t 1.1-1.3, 11/15 years) — about zero.
  Stop above the leg high + last pullback low target (the #33 target): 15-min -0.007R (617); 1-hour +0.232R but 228 trades
    (15/yr), t 1.8, from 2024 -0.27R.
Verdict: DEAD as shown. The trendline adds nothing over #33's plain break of structure (fewer trades, weaker); what works in both is
the wide stop at the leg's high with a near target on the 1-hour chart, not the tight stop at the gap.

### 35. RedNote video "K线之下": "订单块交易策略" (order blocks: MTF engulfing, inducement trap, breaker block) — 1 and 2 DEAD; breaker block on 4-hour = CANDIDATE on gold, pending other markets   [2026-10-09 22:08 MYT]
10.5-minute lesson, transcribed. Valid OB = the key candle before a gap (full range), untested since, and the move breaks structure;
trade only the latest valid OB with the structure. S1: price returns to a higher-timeframe OB -> lower-timeframe engulfing -> enter,
stop just beyond the OB, 2R (D1->H1, H4->15m, H1->5m). S2: a minor support with several bounces above the OB ("inducement") ->
buy limit at the OB's middle, stop below, 2-3R. S3: breaker block — a valid OB broken with a change of character -> sell the
first retest, stop just above, 2R, one use. Fixed definitions in bt/ob_strategies.py docstring (3-bar fractals usable 3 bars
later; BOS within 20 bars with no touch before it; OB life 100 bars or until a newer valid OB; 0.05 daily ATR buffers).
Gold 2012-Oct 2026, exits on 1-min (stop first), 5-day max, FTMO costs, coin flip.
  S1 MTF engulfing: D1->H1 +0.052R (117, t 0.5); H4->15m -0.065R (693); H1->5m -0.103R (2,188, t -3.3). DEAD.
  S2 inducement, limit at OB middle: H4 35 trades (+0.12 / +0.06, too few); H1 -0.385 / -0.503R (144, t -3.6 / -4.2); 15m
    -0.127 / -0.141R (496). Without the inducement filter: H4 -0.067, H1 -0.074, 15m -0.159R (10,611, t -11.6). DEAD.
  S3 breaker retest, 2R: H4 +0.127R (813 trades, 55/yr, t 2.5, 40% wins, coin -0.247; longs +0.149, shorts +0.107; before 2024
    +0.103, from 2024 +0.222); H1 +0.047R (2,567, t 1.7); 15m +0.022R (10,535, t 1.6); all three 10/15 years > 0.
  Checks on H4 (bt/ob_breaker_check.py): random-timing same side -0.018R (not drift). By year 12 +.21 13 -.04 14 +.16 15 -.03
    16 +.26 17 +.27 18 -.15 19 +.05 20 -.08 21 +.01 22 +.55 23 -.11 24 +.25 25 +.31 26 .00. Every neighbour positive:
    fractal n=2 +0.130 / n=5 +0.128; buffer 0 +0.103 / 0.1 +0.121; life 50 +0.209 / 200 +0.117; target 1.5R +0.147 / 3R +0.073;
    entry at the block's middle +0.213 (t 3.7); no CHoCH requirement +0.127 (1,094).
Verdict: S1, S2 DEAD. S3 meets the CANDIDATE bar on gold (n >= 200, both halves > 0, t >= 2, >= +0.05R, worst year -0.15R),
robust to every setting, both sides, same sign on 3 timeframes. Warnings: best of 15 cells tried in this video; ~7R a year at
55 trades. With #33 it is the second "break, then retest with a structural stop" rule to work; check their overlap. Next: the same
rule unchanged on FX, indices, silver, oil from the full export (backlog #41), then paper-trade.

### 36. Three RedNote videos on pullback entries and trend strength — pullback methods DEAD; the momentum score helps a little, no edge   [2026-10-09 22:18 MYT]
Sources: 杰明GW "SMC，FVG和回撤进场，三法结合YYDS" (13.7 min: Fibonacci 0.618-0.886 / FVG / breakout-retest pullbacks, best when all
three coincide); 熊猫教练 "合格的短线选手，一定要看得懂动能" (7.6 min: a 10-point momentum score — trend candles, counter pullbacks,
unfilled FVGs +4, low overlap +3, inside a range -2; 8-10 = strong); 趋势周期形态 "如何判断趋势动能强劲" (4.5 min: same idea).
Fixed before running (bt/pullback_lab.py docstring): legs = confirmed swing high above the previous one, start = lowest swing low
between; limit entries for 48 bars after the high is confirmed, cancelled by a new high or a close below the start. FIB618 /
FIB786 (stop below the start), FVG (latest unfilled gap's top, stop below its first candle), BRK (the broken swing high), CONF
(gap inside the 0.618-0.886 zone with the broken high inside the gap). Targets: the leg high or 2R. Score computed per the table.
Gold 2012-Oct 2026, 15m / 1h / 4h, longs + shorts, exits on 1-min, FTMO costs, coin flip. 30 cells:
  15-min: all 10 negative, -0.04 to -0.09R (2,700-15,000 trades each; t to -7).
  1-hour: FIB618 -0.07 / -0.03, FIB786 -0.03 / -0.04, FVG +0.01 / +0.05 (1,548, t 1.5), BRK -0.09 / -0.04, CONF +0.01 / +0.04 (388).
  4-hour: -0.12 to +0.02.  "All three combined" (CONF) is no better than any single method.
  Momentum score (2R target, all cells pooled): legs scoring <= 4 (85% of legs) -0.063R (51,006 trades), 5-7 -0.008R (8,557),
    8-10 -0.017R (642). On 1-hour: <= 4 -0.037, 5-7 +0.084 (1,460), 8-10 +0.076 (103); 15-min and 4-hour no lift.
Verdict: the three pullback methods and their combination DEAD on gold. The momentum score removes some of the worst trades
(about +0.05R) but does not create an edge; the "8-10 strong trend" is rare (1% of legs). Worth one pre-registered test as a
filter on #33 and #35 (backlog #42), nothing more.

### 37. RedNote video "交易升级打怪": "FVG不是碰线就买，确认还在后面" (4-hour gap + 15-minute three-step confirmation) — DEAD   [2026-10-09 22:18 MYT]
Rule (41 s): a 4-hour bullish gap is only the location; on 15-minute: (1) the prior low is pierced and the candle closes back above;
(2) a close above the local bounce high leaves a new bullish gap; (3) price holds on the retest of that gap and strengthens -> buy;
abandon if the swept low breaks; example target = the prior high. Fixed before running (bt/fvg_htf_confirm.py docstring).
Gold 2012-Oct 2026, longs + shorts, exits on 1-min, FTMO costs:
  target prior 4-hour high: -0.129R (578 trades, t -2.7, 4/15 years > 0); with an extra confirmation candle +0.026R (249, t 0.4).
  target 2R: -0.106R (687); with the extra candle -0.031R (367).
Verdict: DEAD. Same family as #31 (higher-timeframe zone + lower-timeframe sweep/gap entry with a stop under the sweep).

### 38. RedNote video "源木派讲技术": "结构已经成立了，为什么还是不敢做?" (breakout-retest limit orders) + equal highs as "liquidity" (#40's video) — DEAD   [2026-10-09 22:54 MYT]
Source: 15.9-min live session (gold, NQ), transcribed + frames. Rules as told: (A) a trader's daily "farming" routine on ES/NQ,
"very high win rate": two wicks reach the same level, a big-bodied candle closes through it, on small timeframes one more candle
follows through; limit order back at the broken level, stop below, take profit at the prior high (elsewhere "a simple 1:2");
(B) "aggressive": a strong trend candle that truly breaks the swing high (body closes above), the leg's first pullback, bigger
timeframe trending the same way -> limit at 0.382 of the candle, the candle is the defence (stop below it), 1:2; move the order to
a newer breakout candle; (C, from #40's video) equal highs/lows are "potential liquidity" -> the run-and-close-back read.
Fixed before running (bt/breakout_retest.py docstring): big candle = range >= 1.5x the median of the previous 20 and body >= 60%
of the range; true breakout = first close above the last confirmed 3-bar swing high; equal-high level = last two confirmed swing
highs within 0.1 daily ATR, the older <= 40 bars back, unbroken, expires at 60 bars. A: limit at the level for 24 bars, stop =
breakout candle low - 0.05 ATR, target 2R or the highest high since the breakout (>= 1R). B: limit at high - 0.382 x range for
12 bars, stop = candle low - 0.05 ATR, 2R; HTF filter = higher-timeframe close > its 50-EMA (M5->H1, M15->H4, H1->D1). C: wick
above the level and close back below -> sell at the next minute, stop = bar high + 0.05 ATR, 2R. Gold 2012-Oct 2026, 5m / 15m /
1h, longs + shorts, exits on 1-min (stop first), FTMO costs, coin flip per trade. 21 cells, all negative:
  A two-wick break + retest: 5-min -0.17 to -0.25R (2,700-15,100 trades, 0-1/15 years > 0); 15-min -0.09 to -0.14R; 1-hour
    -0.11 / -0.13R, with follow-through -0.01R (325 trades, t -0.1) / -0.08R. Win rate 29-35% — not "high".
  B trend candle 0.382: 5-min -0.14R (25,357 trades; 13,097 with the HTF filter); 15-min -0.07 / -0.05R; 1-hour -0.06 / -0.01R
    (1,112 with the filter; before 2024 -0.05R, from 2024 +0.20R).
  C equal-high sweep -> reverse: 5-min -0.15R (22,910), 15-min -0.14R (7,588), 1-hour -0.09R (1,314); 0-5/15 years > 0. The
    continuation side (the coin flip) loses too (-0.04 to -0.14R): equal highs carry no direction either way after costs.
Verdict: DEAD on gold. The trader's own markets (ES/NQ = US500/US100) come with the full export: rule A unchanged there
(backlog #43).

### 39. RedNote video "格局Vision": "ICT课004｜先统一看图标准" (fix the feed, chart clock and touch rule before judging a rule) — checks on #33 and #35: #33 holds; #35 depends on where the 4-hour candles start -> WATCH   [2026-10-09 22:54 MYT]
The lesson (11 min, no trade rules): a sweep at 99.9 on one feed is 100.1 on another; Beijing vs New York chart time moves the
candles; touch / wick / cross / close are different events; flipping timeframes until one agrees is confirmation bias; after
changing a rule, re-test it (win rate, R:R, expectancy, drawdown, signal count). Applied to our two candidates, nothing re-tuned
(bt/data_standard_check.py, bt/h4_phase_check.py, bt/h1_phase_check.py):
  Feed: FTMO's own MT5 gold (15-min history from 2022-07) vs the MT4 feed both rules were found on; same window, every timeframe
    built from 15-min bars the same way, same spread model, exits on 15-min bars. Prices differ by a median $0.06 per bar.
    #33: MT4 181 trades +0.274R, FTMO 179 trades +0.254R; 82-85% the same trades, identical results on those (+0.229 / +0.227R,
    same win/loss on 100%). #35 (server clock): MT4 +0.171R (247), FTMO +0.166R (257); 89-92% the same trades. Both survive.
  Chart clock: #35 with the 4-hour grid started at UTC 00 / 01 / 02 / 03 (+4k): +0.127 (t 2.5) / +0.052 (t 1.1) / +0.125 (t 2.5)
    / +0.022R (t 0.4). On FTMO's server clock (17:00 New York = 21:00/22:00 UTC: the candles an EA would trade) +0.057R (820
    trades, t 1.1; before 2024 +0.014, from 2024 +0.237; longs -0.02, shorts +0.14). Pooled over the grids about +0.08R: the
    +0.13R in #35 was the lucky end of an arbitrary choice.
    #33 with the 1-hour grid at :00 / :15 / :30 / :45: +0.171 / +0.218 / +0.226 / +0.177R (t 2.3-3.1) — robust. But 2024+ is
    about zero on every grid (+0.05 / -0.10 / -0.08 / +0.08R; ~120 trades each, standard error ~0.13R), while FTMO's feed gives
    2024 / 2025 / 2026 +0.33 / +0.22 / +0.10R (15-min exits).
  Exit resolution: 15-min exits flatter both rules by +0.04-0.06R vs 1-min (inside the fill bar the order of touches is unknown):
    keep 1-minute exits for anything with a limit entry.
Verdict: #33 stays CANDIDATE (robust to feed and clock; the cross-market test, backlog #40, decides). #35 -> WATCH (+0.06R, t 1.1
on FTMO's own candles); its cross-market test (#41) now uses FTMO's server clock and reports all four hourly grid starts. New
standard (PROTOCOL): a 4-hour or daily candidate must hold on every hourly grid start and on the broker's clock.

### 40. RedNote video "交易修心社": "结构力场，一张图从哪里看起?" (how to read an SMC indicator) — no rules; its volume caveat holds; equal highs dead (#38 C)   [2026-10-09 22:54 MYT]
An 8-min walk through an SMC indicator (swing vs internal structure, BOS / CHoCH, strong / weak highs, order blocks with volume
numbers, breaker blocks, FVG mitigation by touch / wick / close / midpoint, equal highs/lows, multi-timeframe zones), with its own
caveats: labels are reading aids, not orders; the block's volume number "does not automatically mean stronger support or a higher
win rate"; overlapping zones from two timeframes are not two independent pieces of evidence. Checks:
  Block volume (bt/ob_volume.py): #35's blocks split into thirds by the OB candle's tick volume / the median of the 50 bars before.
    First return to the block (limit at its middle, stop below, 2R = #35 S2 without the inducement filter): the high-volume third
    beats the low third by +0.08R (4-hour UTC, t 0.7), +0.10R (1-hour, t 1.4), +0.08R (15-min, t 2.4), +0.03R (4-hour FTMO
    clock), but every third loses money (-0.01 to -0.23R). Breaker retest: the high-volume third is the worst on all four
    (-0.14R t -1.2, -0.10R t -1.4, -0.07R t -2.1, -0.28R t -2.4 vs the low third). The number doesn't make a block tradeable;
    a busy original block makes a worse breaker. Pre-registered for the cross-market #35 test (backlog #41): skip blocks with
    relative volume >= 1.2 — not adopted on gold (found by splitting the same trades).
  FVG mitigation by midpoint vs edge: already in #33 (+0.150 vs +0.171R) and #35 (+0.213 vs +0.127R) — same sign either way.
  Equal highs/lows as liquidity: #38 C, dead at every timeframe.
Verdict: no strategy; the video's own cautions agree with the data.

### 41. RedNote video "壹笑财经": "10分钟精读《系统交易方法》" (Bo Tao, 1998) — its principles are this protocol; the book's example rule shows no edge beyond holding the market   [2026-10-09 22:54 MYT]
An 8-min book summary: 3M (mind > money > market); a system must be complete (entry and exit) and objective ("if A then B", one
reading only); every loss taken by the rules is right and every win against them is wrong; formalise the idea, test it on lots
of data, "rather too strict than too lenient", don't optimise to the prettiest history; selling decides more than buying. These
are the rules this log already runs on. One claim the data doesn't share: that 10-30% losing signals is normal — our gold
candidates lose on 60-68% of trades and make money because winners are 2R+.
Its example rule (the formalisation demo): buy when the 5-day average crosses above the 20-day [and volume >= 1.5x the average of
the previous 5 days, "量比"]; out on the cross back below; 3-ATR catastrophic stop as the risk unit; long only; daily, next-open
entries, costs + assumed swap (quant/daily.py ma_cross). Gold 2012-26, US100/US500 2017-26, AAPL 2014-26, TSLA 2019-26, BTC 2020-26:
  plain cross: 425 trades, +0.31R each (t 4.3), but the same side and holding time from random days earns +0.21R: the cross adds
    +0.10R (t 1.3) — rising markets, not timing. Per market vs random timing: US500 +0.16, BTC +0.17, AAPL +0.11, gold +0.09,
    US100 +0.03, TSLA +0.03R.
  with the volume filter: 13 trades in total — CFD tick volume rarely jumps 1.5x on the cross day. Can't be judged.
Verdict: no edge so far. Both variants are in the cross-market battery (MA5_20_long, MA5_20_vol_long) for all 110 markets with
the export (real stock volume where FTMO has it).

### 42. RedNote video "杰明GW": "下方刚被扫，为何盯上前高？看首个FVG。" (30-min POI sweep -> change of character -> first gap, target the range high) — DEAD   [2026-10-09 23:08 MYT]
Rule (42 s, gold, 30-minute chart): a break of structure; its order block is the point of interest; the pullback sweeps a swing low
above the block (sell-side liquidity) into it; a lower-timeframe change of character and a strong reaction -> buy from the first
gap; stop under the sweep; target the buy-side liquidity (the range high). Fixed before running (bt/poi_sweep_fvg.py docstring):
BOS = first close above the last confirmed 30-min swing high; OB = last down candle at/before the leg low; POI = OB + 0.25 daily
ATR above; sweep = low below the latest post-BOS swing low above the POI, inside the POI, within 2 days; CHoCH = close above the last
internal swing high confirmed before the sweep (30-min, 2-bar fractals; or 5-min, 3-bar) within 6 hours; first bullish gap after the
sweep; limit at its top for 24 bars; stop = sweep low - 0.05 ATR; target the highest high since the leg low (>= 1R) or 2R.
Gold 2012-Oct 2026, longs + shorts, exits on 1-min, FTMO costs:
  30-min CHoCH + gap: range-high target -0.09R (47 trades, 3 a year), 2R -0.10R (127).
  5-min CHoCH + gap: range-high target -0.37R (212, t -3.4, 19% wins; coin flip +0.15R), 2R -0.33R (205, t -3.6).
Verdict: DEAD — the #31 family again (zone + sweep + lower-timeframe shift + gap entry with a stop under the sweep). The 5-minute
version points the wrong way more often than not.

### 43. RedNote repost (RossCameron777) of Jesse Rogers: NQ Asia-session trade with volume profiles (auction market theory; = Dalton's "80% rule") — DEAD on gold, about zero on US100/US500; one cell WATCH   [2026-10-09 23:08 MYT]
Rule (9.6 min, order-flow software): value areas (70% of each session's volume) moving higher = value-up market; a dip below the
prior value area is a discount and a likely fake-out; once price is accepted back inside, buy; stop under the last pivot; target
the value-area high; he moved the target up, then the stop to breakeven, and closed by hand at the POC when buying dried up (+$5.9k,
8 NQ contracts). The heatmap / order-flow confirmation can't be tested on bar data. Fixed before running (bt/value_area.py
docstring): profile from tick volume spread over each bar's range, bins 0.02 daily ATR, VA grown from the POC to 70%; value-up =
prior VAH and VAL both above the session before; V1 = value-up, a trade below the prior VAL, two consecutive 30-min closes back
inside -> buy next open, stop = excursion extreme - 0.05 ATR, target prior VAH, flat at the session end; V2 = Dalton's rule (opens
outside, two closes inside, no trend filter); V3 = V1 with the prior POC as target. ETH (broker day) and RTH (09:30-16:00 NY).
Gold 2012-Oct 2026 (1-min profile and exits); US100/US500 2021-Oct 2026 (30-min bars only).
  Gold ETH: V1 -0.088R (1,291 trades, t -2.7, 2/15 years > 0), V2 -0.051R (1,005), V3 -0.071R (1,068).
  US100 ETH: -0.004 / -0.031 / -0.026R (370-455).  US100 RTH: +0.009 / -0.011 / +0.096R (V3: 191 trades, t 2.3, 76% wins at
    0.26R reward, 6/6 years > 0, before 2024 +0.11, from 2024 +0.08, coin flip -0.12).
  US500 ETH: -0.000 / +0.015 / -0.011R.  US500 RTH: +0.016 / +0.039 / -0.024R.
  The "80%": price reached the far side of value 34% (gold), 36-48% (US100), 40-53% (US500) of the time.
Verdict: DEAD on gold; about zero on the indices; the 80% figure doesn't hold. One cell of 15 (US100 cash session, target the POC)
is +0.10R at t 2.3 — expected by luck about once in 15 cells, and the same rule on US500 is -0.02R. WATCH only: re-test unchanged on
the export's 5-minute index data from 2015 (backlog #44).

### 44. RedNote video "国金量化小雪": "量化软件QMT自动化下单全流程来啦" (2.7 min) — not a strategy; its order-flow checklist applied to OpeningCandle_EA: one real gap   [2026-10-09 23:08 MYT]
QMT is a Chinese A-share broker platform, but the five steps are the same for any EA: (1) live quotes subscribed; (2) the signal
de-duplicated so one moment can't send two orders; (3) the order sent with correct symbol, side, price, size; (4) order reports
watched (filled / partial / rejected; cancel and re-send stale limits); (5) positions updated and risk checked before every order
(funds, size, daily max loss); and run it on a simulated account first. OpeningCandle_EA.mq5 (read only, not changed):
  (1) quotes: checks for zero quotes and the server clock; no connection/stale-quote check — a dead feed just makes orders fail
      until the 5-minute window closes. Acceptable.
  (2) de-duplication: GAP. After a successful send it waits 0.5 s for the position; if the position isn't visible yet (or the
      request timed out but filled on the server), the next 1-second timer sends a second order the same day. The EA tracks only
      one ticket, so the second position gets no 15:59 exit and stays open on its stop alone, overnight. Fix: look for an open
      position with the EA's magic before every send, and don't re-send for ~10 s after a send while polling.
  (3) order: chart symbol, lot step/min/max, margin check, filling mode, SL normalised — good.
  (4) reports: polled every second; partial fills use the real position size; no pending orders — fine for this rule.
  (5) risk: 5% daily and 10% total limits on equity with close-on-breach, real-account guard, Prague-midnight day — good.
  Simulation first: running on the FTMO trial — good.
Verdict: no strategy to test; one EA fix queued (backlog #45), to ship together with the vol-sizing change when Shen says go.

### 45. RedNote video "大道无形我有型": "突破前高点买入策略详解" (silent 30 s: previous-day high swept, close back below -> sell to the previous-day low) — DEAD   [2026-10-10 00:05 MYT]
Rules from the frames: mark yesterday's high and low; price runs above yesterday's high ("流动性诱多"), the candle closes back below
-> sell; stop above the sweep high (0.17-0.19%); target yesterday's low (4.73R in the example); mirror at yesterday's low.
Fixed before running (bt/pdh_sweep.py): broker day 17:00-17:00 NY; the first bar above PDH starts the sweep, the first close back
below triggers; sell at the next open; stop = sweep high + 0.05 daily ATR; target PDL or 2R; flat at the day's end; one per side.
  Gold 2012-26: 5-min -0.016R (3,172 trades, 30% wins at 5.7R) / 2R -0.034R; 15-min +0.003R / -0.018R.
  EURUSD, GBPUSD, USDCHF 2018-26 (30-min): -0.098R (5,412) / -0.128R (0/9 years > 0).  US100 + US500 2022-26: -0.077 / -0.066R.
  The other direction (coin flip = the breakout continues) loses too.
Verdict: DEAD — a failed break of yesterday's high carries no direction.

### 46. RedNote repost (油管中文配音檔案館) of a Jesse Rogers NQ session: "gap down, everyone bearish -> wait for the open to prove it; it didn't -> squeeze long" — the testable core (trade against a big gap when the first candle goes against it) is the opening-candle rule's best days: WATCH   [2026-10-10 00:05 MYT]
22.7-min live session; order flow and heatmaps can't be tested on bars. Fixed before running (bt/gap_squeeze.py): session bars
09:30-16:00 NY, FTMO 30-min, Jan 2022 - Oct 2026; big gap = |09:30 open - previous close| >= 0.5 x ATR(14) of session ranges;
first candle against the gap -> trade its direction at 10:00, stop at its far end, target the previous close (gap fill) or none
(flat 16:00 = the opening-candle rule); for reference big-gap days where the first candle went with the gap.
  Against the gap, no target: +0.308R (522 trades, t 2.9, 43% wins): US100 +0.45, US500 +0.66, TSLA +0.05, AAPL -0.08R; by year
    22 +.17 23 +.66 24 +.36 25 +.39 26 -.08.  With the gap-fill target: +0.197R (510, t 2.5; the gap filled 34% of the time).
  With the gap: +0.010R (552): US100 -0.08, US500 +0.14, TSLA +0.01, AAPL -0.05.
Verdict: the same split #23 saw ("against the gap is better", report only) — now on 4 markets: on big-gap days the opening-candle
trades that go against the gap carry the edge, the ones with the gap are about zero. Post-hoc, so WATCH: pre-registered on the
export's 46 stocks and 14 indices (backlog #46) before it becomes a filter in the EA.

### 47. RedNote repost (油管中文配音檔案館) of JJ Simon: "$2M in prop payouts — the full roadmap" — his trade (fade the 8:30 news spike) DEAD; his prop-firm process = ours   [2026-10-10 00:05 MYT]
29-min talk. Process points: beat the prop firm, not the market (optimise risk:reward per firm's rule set; evals maximise pass
rate, funded accounts maximise expected value); track spend vs payouts (~3.5x when done right), risk of ruin < 0.5%, total
exposure across accounts, no martingale, backtest "out of 10 evals how many pass" not equity curves — what lab/ftmo_sim.py does.
His strategy ("fair pricing theory"): a big move on 8:30 red-folder news is priced in -> trade the reversion.
Fixed before running (bt/news_fade.py): NFP, CPI, PPI, Retail Sales, Durable Goods, GDP, Core PCE days at 08:30 NY (1,108 in the
calendar); move from the 08:30 open measured at 08:45 (gold, 1-min) or 09:00 (30-min bars); if >= 0.25 daily ATR, fade it; stop
beyond the spike + 0.05 ATR; target the pre-news price or half the move; flat 12:00; spread x 2 at entry.
  Gold 2012-26: -0.049R (227 trades) / half-move target -0.130R; following the move instead -0.22 / -0.17R.
  EURUSD, GBPUSD, USDCHF 2018-26: -0.240R (491, t -2.8) / -0.339R.
  US100 + US500 2022-26: +0.183R (153, t 1.0) but fading up-moves -0.28R and down-moves +0.73R: buying dips in a rising market.
Verdict: DEAD. Neither fading nor following the first 15-30 minutes after a release pays after costs.

### 48. Forex cross-market test of #33 and #35 (backlog #40/#41, first part: Shen's EURUSD, GBPUSD, USDCHF exports, 30-min bars 2018-26) — #35 breaker holds on forex: CANDIDATE; #33 mixed   [2026-10-10 00:05 MYT]
Rules untouched (bt/fx_cross_check.py, bt/fx_phase_check.py). 1-hour = two 30-min bars, 4-hour on FTMO's server clock (plus all
four UTC grid starts); exits on 30-min bars with a conservative fill rule (in the fill bar a stop touch counts, a target touch
doesn't; the coin flip skips the fill bar); spread x 1.2 + commission 0.0025%/side. The same pipeline on gold 2018-26 gives
#33 +0.108R / #35 +0.039R (FTMO clock) / +0.119R (UTC), in line with the 1-minute results, so the coarse exits don't flatter.
  #35 breaker, FTMO clock: EURUSD +0.098R (445 trades), GBPUSD +0.102R (474), USDCHF +0.148R (397); pooled +0.115R (1,316, t 2.9),
    before 2024 +0.115 / from 2024 +0.113, by year 18 +.06 19 +.12 20 +.12 21 +.18 22 +.20 23 -.05 24 +.16 25 +.10 26 +.07; longs
    +0.08, shorts +0.15; coin flip -0.30. Every 4-hour grid start positive on every pair: UTC +0h +0.178, +1h +0.058, +2h +0.073,
    +3h +0.082, FTMO clock +0.115 (pooled over grids about +0.10R).
  #33 gap retest: EURUSD +0.056R (329), GBPUSD +0.186R (354), USDCHF +0.209R (317); pooled +0.150R (1,000, t 2.4) but before 2024
    +0.034 / from 2024 +0.373, 2021 -0.32, 2026 +0.92 (101 trades).
Verdict: #35 passes the CANDIDATE bar on markets it was never looked at on (n >= 200, both halves +0.11, t 2.9, worst year
-0.05R), with gold on FTMO's clock weaker (+0.06R). Expect about +0.08-0.10R per trade, 50-60 trades a year per market. #33:
CANDIDATE on gold, mixed on forex. Next: all 28 pairs, metals and indices from the full export, then FTMO odds for the opening
candle + #35 on a forex basket (backlog #41).
