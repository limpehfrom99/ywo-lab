# Idea backlog (first queued = next to run)

1. [done] Period open/close levels (Shen, 2026-10-09). Red = every weekly open & close; white =
   monthly/quarterly/half-year/yearly open & close. Claim: LTF price pulls back to the level,
   respects the area, reverses. Test: bt/period_levels.py on gold M1 2012-2026 (1/5/15-min
   confirmation, 3R; coin-flip and fake-level benchmarks; reaction odds 0.2 ATR). Then the same on
   US100/US500/TSLA M5 2021-2026 (ftmo() in smc_data.py; nyd/nym present).
2. [done] Weekly-open bias (online: "trade with the weekly open"). Measurement: sign of
   (Monday 17:00 NY close - weekly open) vs rest-of-week return; and as a direction filter on the
   opening-candle trades (TSLA/US100 pickles). Gold, US500, US100.
3. [done] Weekly-open magnet (online claim: price revisits the weekly open ~70-80% of weeks).
   Measure: % of weeks price comes back within 0.05 ATR of the weekly open after first moving
   > 0.5 ATR away; same for the daily open (NY midnight / 9:30). Compare with the same statistic
   for a fake open (+0.37 ATR). If strong, a mean-reversion rule: fade moves > 1 ATR from the open.
4. [done] Turn-of-the-month (watch list): buy close of T-1 (last trading day minus one), sell
   close of T+3. US500, US100, gold M30 2017-2026. Costs + overnight swap (use 0.01%/night approx).
   Per-year table; Monte Carlo pass odds via lab/ftmo_sim.py if positive.
5. [done] Opening-gap fade US100/US500 (M5 2021-2026): gap = 9:30 NY open - prior 16:00 close;
   fade gaps of 0.3-1.0 ATR toward the prior close; stop = 1 gap; exit at fill or 11:00.
6. [done] Overnight return (academic: equities earn most of their return overnight): buy 15:55
   NY, sell 09:35 NY. US500/US100 M30 2017-2026; spread twice + swap. Also the inverse (intraday).
7. [done] Pre-FOMC drift (Lucca-Moench): long US500 from 16:00 NY day before FOMC to 14:00 on
   FOMC day. Fed days from lab/news.py fed_days. US500/US100 M30; costs.
8. [done] Short-term index reversal: US500/US100 daily (from M30): buy after 3 consecutive down
   closes, exit at first up close or 5 days; mirror for shorts. Costs.
9. [done] Multi-day trend following gold: 20-day Donchian breakout, exit on 10-day opposite
   channel, ATR(20)x2 stop. Daily bars from M1. Swap approx 0.01%/night. Per-year.
10. [done] Crypto weekend effect: BTC M30 2020-2026. Weekend (Fri 21:00 - Mon 00:00 UTC) return
    vs weekday; weekend range breakout on Monday open. FTMO crypto costs 0.0325%/side.
11. [done] Gold hour-of-day drift: average return by NY hour 2012-2026, by year; any hour with
    the same sign in >= 10 of 14 years. If one exists: always-on rule for that hour, costs.
12. [done] Volatility sizing for the live opening-candle strategy: risk 0.5% x clamp(median ATR /
    today's ATR, 0.5, 1.5). Re-run challenge() Monte Carlo. Not an edge; an improvement check.
13. [done] Online scan: WebSearch "gold intraday strategy backtest edge", "nasdaq intraday
    seasonality anomaly", "weekly open strategy backtest", "index futures intraday anomalies study".
    Add any concrete mechanical rule found to this backlog with its source link. Max 15 minutes.
14. [done] Intraday momentum, first 30 min -> last 30 min (Gao-Han-Li-Zhou 2018; alphaarchitect.com, quantconnect.com). DEAD on US100/US500/TSLA/AAPL.
15. [done] Opening-candle calm-day filter: skip the trade entirely when today's ATR% > 1.5x (and > 1.25x) its 1-year
    median (edge is +0.12-0.13R on calm days vs +0.07-0.08R on wild days). Re-run challenge() pass odds vs fixed 0.5% and vs
    the scale-down-only rule from #12. Data: TSLA/US100 M30 exports, lab.opening_candle, Fed days skipped. (bt/vol_sizing.py as base)
16. [done -> log #25] Index expiry days: quad-witching (3rd Friday of Mar/Jun/Sep/Dec) and monthly opex (3rd Friday): return on the
    day, the day before and the Monday after, US100/US500 daily 2018-2026 (bt/daily_ideas.py daily_from_export). Baseline: all other days.
17. [done -> log #25] Post-FOMC afternoon (14:00 -> 16:00 NY on FOMC day): direction of the first 30 minutes after the statement
    (14:00-14:30 candle) held to 16:00, US100/US500 30-min 2021-26, costs; baseline coin flip. Note the Standard-account
    news rule forbids this; Swing accounts allow it.
18. [queued] Gold opening-candle family at other opens: the laptop lab already runs other market opens nightly; check its
    research_report.md when Shen sends it; do not duplicate here.
19. [done] Reddit sweep: blocked (extension refuses reddit.com). Substitutes tested as #26a-c (noise band, Supertrend/UT Bot, IBS).
20. [queued] Paper-trade the noise-band rule (#26a) on US100 in the lab app next to the opening candle; compare live vs model monthly.
21. [queued] Noise band with real 1-minute marks: when the laptop sends US100 M1 history, rebuild the bands and VWAP from M1
    (paper's resolution) and recheck 2025-26.

22. [queued] SMC timeframe grid (bt/smc_grid.py, #31b) on US100/US500/US30 (M5 from 2021-09) and the 28 FX pairs (M15 entries, H1/H4 structure) once the full export is unpacked.

## Added 2026-10-09 21:30 MYT — classic book / paper / code-base rules (exact rules fixed here; test as written, report every cell)
Data available in the repo now: gold M1 2012-2026 (data/gold_m1), TSLA/AAPL/US100/US500 M5 2021-08+ (data/ftmo), raw M30 exports
(US100/US500 daily-only bars before 2021-09, AAPL 2015+, TSLA 2019+, BTC 2020-08+). The full ~110-symbol export lands in data/x
(see quant/README.md) — items marked [needs export] wait for it. Costs, baselines and IS (<2024) / OOS (>=2024) split as in PROTOCOL.md.
23. [done -> log #49: pooled NR7 CANDIDATE, +0.164R, NR7 minus other days +0.157R t 3.5] Crabel NR7 + opening-range breakout (T. Crabel, "Day Trading with Short Term Price Patterns and ORB", 1990): on the day
    after an NR7 day (smallest daily range of the last 7) and, separately, after NR4: first break of the first-30-min range, stop at the
    other side, exit at the cash close. US100/US500/TSLA/AAPL (M5/M30), gold (London 08:00 and NY 08:20 opens). Baseline: same ORB on all days.
24. [done -> log #50: gold 24h day k=0.5 CANDIDATE +0.073R; indices/AAPL DEAD] Larry Williams volatility breakout ("Long-Term Secrets to Short-Term Trading"): buy stop at open + 0.5 x yesterday's range,
    sell stop at open - 0.5 x range (first touched only), stop = 0.5 x range from entry, exit at the close; variant exit next open.
    Gold (NY day), US100/US500/TSLA (cash session). k in {0.3, 0.5, 0.7}.
25. [done -> log #51: DEAD on gold; stocks/indices blocked on 1-minute data] Williams "Oops": the cash session opens below yesterday's low -> buy stop at yesterday's low; mirror above the high; stop
    at the day's extreme so far; exit at the close. US100/US500/TSLA/AAPL; gold at the NY open.
26. [queued] Raschke "Turtle Soup" (Connors & Raschke, "Street Smarts", 1995): today makes a new 20-day low, the previous 20-day low
    was >= 4 days ago -> buy stop at that previous low; stop 1 tick below today's low; exit after 1-3 days or trail; mirror for highs.
    Daily gold 2012+, indices daily 2017+, TSLA/AAPL daily.
27. [queued] Raschke "80-20s": yesterday opened in the top 20% of its range and closed in the bottom 20% -> today buy stop at
    yesterday's low after price trades >= 0.1 ATR below it; stop at today's low; exit at the close. Mirror. Gold, indices, stocks.
28. [queued] Raschke "Holy Grail": ADX(14) > 30 and rising; price pulls back to the 20-EMA -> buy stop above the pullback bar's high;
    stop at the pullback low; target the recent swing high; mirror. Daily and H4, gold + indices.
29. [queued] Connors "Double 7s" ("Short Term Trading Strategies That Work", 2008): close above the 200-day MA and at a 7-day low ->
    buy at the close; sell at the first close at a 7-day high. Indices daily, gold, TSLA/AAPL; also short mirror below the MA.
30. [queued] Dual Thrust (M. Chalek; the classic Chinese CTA rule): Range = max(HH-LC, HC-LL) over the last N days (N=4);
    buy stop at today's open + k1 x Range, sell stop at open - k2 x Range (k1=k2=0.5, also 0.3/0.7), stop-and-reverse,
    flat at the session close. Gold (NY day), US100/US500 (cash session), BTC (UTC day).
31. [queued] R-Breaker (R. Saidenberg; top-ranked in Chinese futures quant): six levels from yesterday's H/L/C (pivot, breakout
    buy/sell, reversal setup/enter levels, standard formulas); trend-follow on breakout, reverse on the setup->enter sequence; flat
    at the close. Gold, US100/US500.
32. [queued] Pre-holiday effect (Quantpedia; Ariel 1990): long the day before US market holidays, close-to-close. US500/US100 daily
    2017+ (holidays from the exchange calendar), costs + swap. Baseline: all other days.
33. [queued] Bollinger squeeze breakout (J. Bollinger): BB(20,2) width at its 125-bar low -> trade the first close outside the
    bands; stop at the middle band; exit when price closes back inside / at the opposite band. Gold daily + H4, indices daily.
34. [queued] MQL5 CodeBase EAs with published claims — read each page's source (WebFetch mql5.com/en/code/...), extract the exact
    rules, test on our longer history: "Stochastic Daily Breakout for Gold (+245% 2021-2026)", "Gold Breakout EA XAUUSD H4 (+90%
    2020-2026)", "ZoneUS30: reversion + positive swap", "The Nikkei EA that only buys when volume is quiet", "ORB Risk Managed".
    Gold/indices first; JP225/US30 [needs export].
35. [queued, needs export] Zarattini & Aziz (2023, SSRN "A Profitable Day Trading Strategy for the U.S. Equity Market"): 5-min ORB on
    "stocks in play" — each day take the stocks whose first-5-min tick volume / its 14-day average is highest (top 20% of the 46),
    trade the direction of the first 5-min candle with a stop at 10% of the 14-day ATR, exit at the close. FTMO stocks open 9:35, so the
    first bar is 9:35-9:40. Compare with the opening candle (#live) on the same stocks.
36. [queued, needs export] Gold/silver ratio mean reversion (E. Chan style): z-score of log(XAU/XAG) over 60 days; |z| > 2 -> long the
    cheap leg, short the rich leg (equal $ risk), exit at z = 0 or 20 days. Daily 2015+.
37. [queued, needs export] Clenow "Following the Trend" across every FTMO CFD: long when 50-EMA > 100-EMA and a 50-day high, 3-ATR
    trailing stop, mirror for shorts, ATR position sizing; portfolio of all markets vs each group. (Overlaps quant/ rule books.)
38. [queued] freqtrade-strategies (github.com/freqtrade/freqtrade-strategies): port the 5 most-starred long-only rules, test on BTC M30
    2020+ and ETH [needs export]; FTMO crypto costs 0.0325%/side. Low priority (1:1 leverage).
39. [queued, needs export] Trend-following exit grid across every market (#32D): entries = close above the 20/55-day high (long and short), exits = 2/3/4-ATR chandelier, 10-day low, 50-day MA, hold 20/60; random-entry baseline per cell; real swaps from symbol_specs.csv; pooled by group; walk-forward choice of exit (quant/walkforward.py).
40. [queued, needs export; first part done in #48: 3 pairs +0.150R pooled but +0.03 before 2024] #33 FVG retest (1-hour, BOS -> first FVG -> limit at the gap edge, stop at the leg high + 0.05 ATR, target the last pullback swing low, >= 2R) unchanged on every FX pair (the poster's market), US/EU indices, silver and oil; exits on the finest bars available; pooled by group; no re-tuning.
41. [queued, needs export; first part done in #48: EURUSD/GBPUSD/USDCHF +0.115R pooled on FTMO's clock] #35 breaker-block retest (4-hour and 1-hour, rules in bt/ob_strategies.py strat3) unchanged on every FX pair, US/EU indices, silver, oil; 4-hour candles on FTMO's server clock (bt/data_standard_check.h4_server) as the primary cell, all four hourly grid starts reported (#39: on gold it is +0.02 to +0.13R by start hour); pre-registered second cell: skip blocks whose candle tick volume >= 1.2 x the median of the 50 bars before (#40); pooled by group; overlap/correlation with #33 and the opening candle; then FTMO odds of OC + #33 (+ #35 only if it passes on the server clock).
42. [queued] Momentum-score filter (#36 table, bt/pullback_lab.py legs()) applied unchanged to the #33 and #35 trades: score >= 5 vs <= 4 on the leg before each setup; pre-registered: keep only if the filtered set beats the unfiltered by >= 0.05R in-sample (before 2024) AND out-of-sample.
43. [queued, needs export] #38 rule A ("two wicks, big-body break, retest the level"; bt/breakout_retest.py rule_a) unchanged on the
    trader's own markets US500 / US100 (ES / NQ), 5m / 15m / 1h, follow-through on and off, 2R and prior-high targets; gold was
    -0.01 to -0.25R in every cell. One pass, all cells reported; also rule B (trend candle 0.382) on the same markets.
44. [queued, needs export] #43 value-area rules (bt/value_area.py V1-V3, ETH + RTH) unchanged on the export's 5-minute US100 / US500
    (and US30, GER40, UK100) from 2015, profile from 5-min tick volume, exits on 5-min; pre-registered cell to confirm: US100 RTH V3
    (+0.096R, t 2.3 on 30-min bars 2021-26). Dead unless US100 RTH V3 holds before 2021 AND US500 RTH V3 turns positive.
45. [queued, needs "go"] OpeningCandle_EA duplicate-order guard (#44): before every send, FindPosition() by magic -> adopt + mark the
    day as traded; after a send that returns without a visible position, block re-sends for 10 s while polling; also adopt any
    extra position with the magic so the 15:59 exit closes all of them. Ship with the vol-sizing change.
46. [queued, needs export] #46 opening candle on big-gap days (|gap| >= 0.5 ATR): first candle against the gap vs with it, on all 46
    stocks + 14 indices from the export (bt/gap_squeeze.py logic). Pre-registered: becomes an EA filter (skip with-the-gap trades on
    big-gap days) only if against - with >= +0.10R pooled AND in both halves (2015-2023 / 2024-26) AND on >= 60% of symbols.
47. [waiting for Shen's upload] The 61-video RedNote profile batch: python3 -I tools/video/batch.py <zip or folder> <out>; skip exact
    and near duplicates of research/videos/index.csv; test every new mechanical rule as told (gold + forex + indices, coin flip
    and random-timing baselines), then a small pre-set neighbourhood with selection on 2015-2023 and a check on 2024-26 only;
    add every video to the index with its log entry and verdict.

48. [queued] NR7 filter on the live opening candle (from #49): OC trades (TSLA, US100; lab.opening_candle, M30 2022+) split by
    "yesterday was NR7" (cash-session range). Pre-registered: becomes a size-up rule (1.5x risk on NR7 days) only if NR7 - other days
    >= +0.05R on both TSLA and US100 AND FTMO pass odds (lab/ftmo_sim.py) improve. Report all cells.
49. [queued, needs export] #49 NR7 + ORB30 on all 46 stocks + 14 indices 2015+ (M5): NR7 minus other days >= +0.05R on >= 60% of
    symbols AND in 2024-26 -> CANDIDATE stands; also gold 2015+ FTMO feed for #50 (k=0.5, 24-hour day).
50. [blocked: needs 1-minute history] #51 Oops on stocks/indices: 45-76% of fills are ambiguous on 5/30-minute bars.
