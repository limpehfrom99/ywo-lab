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
