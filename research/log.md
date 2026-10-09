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
