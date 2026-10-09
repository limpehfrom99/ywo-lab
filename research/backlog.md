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
16. [queued] Index expiry days: quad-witching (3rd Friday of Mar/Jun/Sep/Dec) and monthly opex (3rd Friday): return on the
    day, the day before and the Monday after, US100/US500 daily 2018-2026 (bt/daily_ideas.py daily_from_export). Baseline: all other days.
17. [queued] Post-FOMC afternoon (14:00 -> 16:00 NY on FOMC day): direction of the first 30 minutes after the statement
    (14:00-14:30 candle) held to 16:00, US100/US500 30-min 2021-26, costs; baseline coin flip. Note the Standard-account
    news rule forbids this; Swing accounts allow it.
18. [queued] Gold opening-candle family at other opens: the laptop lab already runs other market opens nightly; check its
    research_report.md when Shen sends it; do not duplicate here.
19. [done] Reddit sweep: blocked (extension refuses reddit.com). Substitutes tested as #26a-c (noise band, Supertrend/UT Bot, IBS).
20. [queued] Paper-trade the noise-band rule (#26a) on US100 in the lab app next to the opening candle; compare live vs model monthly.
21. [queued] Noise band with real 1-minute marks: when the laptop sends US100 M1 history, rebuild the bands and VWAP from M1
    (paper's resolution) and recheck 2025-26.
