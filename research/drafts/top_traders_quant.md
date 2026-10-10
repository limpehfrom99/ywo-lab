# Top traders and quant methods: documented rules, sources, testability (draft, 2026-10-10)

Input for the "top-trader" part of log #82-#89. Nothing here has been run yet. The rules in section 2 are written so they can be pasted
into a pre-registration block. Sessions, costs, swaps, baselines and pass bars follow research/PROTOCOL.md.

Status labels used below:
- **TESTED**: the lab has already run this rule or one with the same mechanism (log entry given). Do not re-run.
- **FAMILY**: no exact copy was run, but a close sibling was, and it died. Only worth running as part of a batch.
- **NEW T#**: not tested yet, testable on FTMO OHLC + tick volume + spread; ranked in section 2.
- **NO DATA**: needs fundamentals, futures curves, options, rate history or longer histories than the export has.
- **NO RULE**: there is no public mechanical rule, only principles or a closed system.

Caveats on sources:
- The shared WebSearch budget ran out partway through. Each rule is marked by how its source was checked: "read" means the page was
  fetched this session, and "ref" means a standard reference (book or paper) that was not re-read online.
- Most "famous trader" rules come from secondary sources. Where two sources disagree, both readings are given as pre-registered cells.
- No performance number below was reproduced. They are the sources' own claims: gross or net as stated, often in-sample.

---------------------------------------------------------------------------------------------------------------------------------

## 0. Bottom line

- About 45 named methods were reviewed. **About 20 are already TESTED or FAMILY.** That covers every Turtle/Donchian/MA/TSMOM rule,
  Dual Thrust, R-Breaker, Williams' breakout and Oops, the Raschke and Connors rules, IBS, NR7, Clenow, the Bollinger squeeze,
  ORB/opening candle, gap fade, the noise band, Supertrend (= Wilder's volatility stop) and Wyckoff springs (= sweep entries).
- **About 10 have NO RULE.** John W. Henry, Bill Dunn, Jerry Parker, Renaissance beyond what is already tested, Druckenmiller,
  傅海棠, 叶燕武 and the 期货日报 champions, and 幻方/九坤 (no rule-level CTA research found). CIS, Livermore and Gann give only
  principles or nebulous rules.
- **About 6 are NO DATA.** AQR carry (no historical rate or swap series), value (needs CPI/book values; commodity 5-year reversal
  has 1-6 usable commodities), the commodity skewness factor (the export's softs start 2023-24), CANSLIM fundamentals, and
  跨期/期现 spreads (no futures curves).
- **14 NEW testable rules are ranked in section 2.** Run these first: **T1 TD Sequential/Combo exhaustion** (the only one with
  peer-reviewed, permutation-tested evidence), **T2 the Korean volatility breakout** (noise-adaptive k + MA filter; extends the one
  intraday-momentum family that shows small edges here), **T3 Larry Williams' smash-day reversals** (third-party 2014-24 futures
  test, strongest on index longs).
- Side finding: data/x has M1 files for US100, US500, TSLA, NVDA and gold. Checked bars per day: **real 1-minute bars start
  2021-09-14 (US100/US500) and 2021-08-02 (TSLA/NVDA)**, gold from 2015. Before that, the index files hold one bar a day and
  TSLA/NVDA 6-7 bars a day, the same trap as PROTOCOL's M5 note. So Williams "Oops" on stocks/indices (#51, blocked on 1-minute
  data) is now testable for 2021-26 on those four symbols.

---------------------------------------------------------------------------------------------------------------------------------

## 1. Already tested in the lab: do not re-run

| Requested method | Lab test (log / backlog) | Verdict |
|---|---|---|
| Turtles System 1/2 (20/55-day breakout, 10/20-day exit, 2N stop) | DON20, DON55, DON20_long (#68 battery); gold Donchian (#9); trend exit grid incl. 20/55 entries + chandelier/10-day/50-MA exits (#39 in #75) | DEAD after costs + swaps on every group; gold WATCH (slow, long-biased); crypto N55 chandelier WATCH (edge is 2011-17) |
| Donchian 4-week rule; Donchian 5/20 MA | DON20 (#68); MA5_20_long, MA5_20_vol_long (#68); EMA/MACD grid (#20) | DEAD |
| TSMOM (Moskowitz-Ooi-Pedersen 2012; AQR, Man AHL trend) | TSMOM12, TSMOM3 (#68) | DEAD |
| Seykota-style EMA trend; PTJ 200-day as a stand-alone timing rule | MA50_200 (#68); EMA 9/21, 20/50 + 1H/4H EMA50/200 filters (#20) | DEAD (T5 below tests the 200-day only as a filter on the live edges) |
| Thorp MUD stat-arb; RenTech "reversion after stocks get out of whack" | XSREV weekly reversal on US stocks (#68); pairs z > 2 (results.md) | DEAD |
| RenTech "morning patterns predict the afternoon" | IMOM_ovn / IMOM_30 / IMOM_day (#14, #68) | DEAD |
| Dual Thrust | #75 (q75_intraday.md) | CANDIDATE only on US100 cash k = 0.5 (marginal); DEAD elsewhere |
| R-Breaker | #75 | DEAD |
| Larry Williams volatility breakout | #50, #71 | gold 24h k = 0.5 WATCH (p_alone 0.001, bootstrap low < 0); indices/AAPL DEAD |
| Williams "Oops" | #51 | DEAD on gold; stocks/indices were blocked on 1-minute data. data/x now has real M1 for US100/US500 (from 2021-09-14) and TSLA/NVDA (from 2021-08-02) |
| Raschke Turtle Soup, 80-20s, Holy Grail; Connors Double 7s | #52, #53, #54 + #71, #55 | DEAD |
| Connors RSI(2); IBS | #24, #26c, #68 | WATCH: US-index longs (IBS US100 +0.08R; RSI2 US indices OOS +0.11) |
| Crabel NR7/NR4 + ORB | #49, #69 | DEAD as a general filter |
| Clenow "Following the Trend" | #75 | DEAD |
| Bollinger squeeze | #75 | DEAD |
| ORB / opening candle / 开盘区间突破 / 日内动量 | live OC30; ORB15/30/60 (#68, #70); IMOM (#14) | OC live; US-index ORB30 WATCH |
| Gap fade (opening gap >= 1 ATR) | #70, #72 | CANDIDATE (EU + US indices) |
| Noise band (Zarattini-Aziz-Barbon) | #26a, #60, #74 | CANDIDATE (US100) |
| Supertrend / UT Bot (= Wilder's Volatility System, ATR stop-and-reverse; India's most-used indicator) | #26b | DEAD |
| Wyckoff spring / upthrust (break of range support, close back inside) | Turtle Soup (#52), liquidity sweeps (#30, #45), SMC (#31) | FAMILY, DEAD |
| 52-week-high breakout (Darvas / O'Neil / Minervini entry trigger) | HIGH52 (#68) | DEAD (T14 Darvas adds the box condition) |
| Turn of the month / Williams-type calendar days | #4, TOM (#68), pre-holiday (#75), seasonal windows (#64) | DEAD; 80%-hit seasonal windows WATCH as a filter |
| 跨品种 ratio trades (gold/silver; US500/US100) | #36 in #75; pairs (results.md) | DEAD |
| Stocks in play (relative volume ORB) | #35 in #75 | DEAD |

---------------------------------------------------------------------------------------------------------------------------------

## 2. Ranked NEW testable rules (T1-T14), exact definitions

### Ranking criteria (in this order)
1. Documented evidence: peer-reviewed > third-party backtest with costs > the author's own claims > nothing.
2. Mechanism not already dead in this lab (section 1).
3. Agreement with what is alive here: intraday momentum (OC, noise band, Williams VB/Dual Thrust on gold/US100), index
   mean reversion after declines (IBS/RSI2 longs WATCH), and big-gap fades.
4. Trade count for FTMO (enough signals inside 1-3 months, pooled over symbols) and data fit (history length, costs, swaps,
   1:1 leverage on stocks/crypto/energy/softs on Swing).

### Common conventions (all T-rules)
- Data: data/x export via quant/universe.load (fixes applied). Daily rules use the battery's daily frame (quant/daily.py, server
  day). Intraday rules use quant/sessions.py session matrices (cash session for indices/stocks, nymex for energy, london24 and
  us_cash for metals, london24 and ny_fx for FX, us_cash and london24 for crypto). Multi-timeframe bar rules go in a
  bt/xrules_*.py module and run with bt/xrun.py --export (M5-D1). H4/D1 results are rerun with --h4-offset 1/2/3.
- Fills: stop entries fill at max(level, bar open) (gap-through). Limit entries follow PROTOCOL's same-bar rules: fill first;
  only the open can cancel; when exits are coarser than M1, the stop counts inside the fill bar.
- R = P/L / initial stop distance, after spread (bar SPREAD), commission (universe.COMMISSION) and swaps for overnight holds
  (symbol_specs.csv swap_long/swap_short; only current values exist, so apply them as constants and say so).
- Splits: in-sample before 2024-01-01, out-of-sample from 2024. Pass bar = PROTOCOL rule 4 (n >= 200, t >= 2, mean >= +0.05R,
  both halves > 0, no year < -0.3R) on the pre-registered primary cell AND beats its baseline; then p_best <= 0.10 over all cells
  of the idea (selection-aware permutation) and BCa 95% lower bound > 0.
- Baselines: daily/swing = same direction and holding from random days of the same symbol and year; intraday = coin flip at the
  same moment with the same distances.
- Report pooled by group with and without crypto (PROTOCOL: 2018-21 coins give single +100R trades).

---------------------------------------------------------------------------------------------------------------------------------

### T1. TD Sequential / TD Combo exhaustion reversal (Tom DeMark). Rank 1
**Sources:** Lissandrin, Daly & Sornette, "Statistical testing of DeMark technical indicators on commodity futures", SFI RP 15-56
(2015), J. Investment Strategies 6(3):53-91 (2017) (read: https://ideas.repec.org/p/chf/rpseri/rp1556.html,
https://www.risk.net/journal-of-investment-strategies/5293521/statistical-testing-of-demark-technical-indicators-on-commodity-futures);
definitions: https://www.mql5.com/en/blogs/post/746570 (read), https://oxfordstrat.com/indicators/td-sequential-2/ (read);
DeMark, "The New Science of Technical Analysis" (1994) (ref; TD risk level).

**Definitions** (buy side; the sell side mirrors it with highs and lows swapped and the inequalities reversed):
1. Bearish price flip at bar t: `C[t-1] > C[t-5]` and `C[t] < C[t-4]`. The flip bar is setup count 1.
2. Buy setup: each following bar with `C[i] < C[i-4]` adds 1. Any bar with `C[i] >= C[i-4]` before count 9 cancels the setup
   (wait for a new flip). Count 9 at bar s9 completes the setup.
3. Perfection: `min(L[s8], L[s9]) <= min(L[s6], L[s7])`.
4. TDST (setup trend) of a buy setup = highest high of the 9 setup bars.
5. Buy countdown (Sequential): starts at s9 (s9 itself may count). A bar counts when `C[i] <= L[i-2]`; counts need not be
   consecutive. Bar 13 also needs `L[i] <= C[cd8]` (close of countdown bar 8); otherwise 13 is deferred to the first bar that meets
   both. The countdown is cancelled if (a) a sell setup completes, (b) any close is above the active TDST, or (c) a new buy setup
   completes, which restarts the countdown from the new s9 (simplified recycle).
6. Buy countdown (Combo, variant cell): starts at setup bar 1. A bar counts when `C[i] <= L[i-2]`, `L[i] <= L[i-1]`,
   `C[i] < C[i-1]`, and `C[i] <` the close of the previous counted bar. 13 completes it.

**Trades:**
- Signals: S9 = any completed buy setup; S9P = perfected at s9; C13 = completed Sequential countdown; K13 = completed Combo
  countdown. Enter long at the next bar's open.
- Stop = TD risk level. Take the bar b* with the lowest low among the setup bars (S9/S9P) or among s9..cd13 (C13/K13); the stop is
  `L[b*] - TrueRange[b*]`. Skip the signal if the stop is more than 4 x ATR(14) away (log the skips).
- Exit: at the close of the H-th bar after entry, H in {1, 3, 5, 10}; primary H = 5. The paper finds predictive power only over a
  limited range of holding days.
- Both directions; report longs and shorts separately.

**Primary cell (pre-register):** D1, the paper's market type (metals XAU/XAG/XPT/XPD, energy UKOIL/USOIL, plus NATGAS and softs from
2023-24), signals C13 + S9P, H = 5. Then every symbol x {M30, H1, H4 x 4 offsets, D1} x {S9, S9P, C13, K13} x H.
**Baselines:** random entry days with the same side and holding; S9 vs S9P as a control for perfection; the opposite side.
**Evidence:** 21 commodity futures, daily 2004-2014, entries compared against randomized entries with the same count and holding.
The paper reports "statistically significant predictive power on a wide range of commodity futures", over a narrow window of
holding days; signals are sparse (1-5 per year per market). Oxford Strat ran 42 futures 1980-2013 with time exits and gives charts
only (no numbers in the text).
**Why rank 1:** it is the only candidate with peer-reviewed, permutation-tested evidence. Its mechanism (9-13 bars of exhaustion) is
not one of the lab's dead 1-3-day reversal patterns. 94 symbols x 4 timeframes give thousands of signals.
**Risks:** vendor definitions differ, so pre-register exactly the above. The effect is small and short-lived; on M30/H1, costs may
eat it.
**Cost to test:** M (one xrules module; counting logic about 120 lines).

---------------------------------------------------------------------------------------------------------------------------------

### T2. Korean volatility breakout (변동성 돌파): Larry Williams VB with noise-adaptive k, MA-score filter, vol targeting. Rank 2
**Sources:** WikiDocs "파이썬을 이용한 비트코인 자동매매" (target = today's open + (yesterday's high - low) x 0.5, refreshed at the
09:00 KST daily open; read: https://wikidocs.net/129988, https://wikidocs.net/book/1665); TVExtBot Korean VB scripts with
"평균 노이즈비율(K)" (read: https://it.tradingview.com/script/Csjrwdit, https://cn.tradingview.com/script/8gF0O6eF); VB explainer
(K = 0.6 "noise ratio", exit next open; read: https://kr.tradingview.com/chart/TSLA/vlvAMwqN-Volatility-Breakout-Trading-Explained).
The noise-ratio and MA-score definitions are the standard Korean retail-quant formulation (systrader79 / 강환국 books). They were not
retrievable this session (ref), so pre-register them as written here. GSV sub-cell: Oxford Strat (read: https://oxfordstrat.com/?p=6908).

**Rule:**
- Day: server day for crypto, metals and FX (primary), with the 00:00 UTC day (= Upbit's 09:00 KST candle) as a cell. Indices:
  cash session (primary) and the server day.
- `Range = H[d-1] - L[d-1]`. `Noise[d] = 1 - |O[d] - C[d]| / (H[d] - L[d])` (skip H = L days).
- k: cell A `k = mean(Noise[d-20..d-1])`; cell B `k = 0.5` (equal to lab #50, so the filters are isolated).
- Entry: buy stop at `O[d] + k x Range`. Long-only is primary (the Korean spot-crypto practice); the mirrored short is its own cell.
- MA-score filter: `score = #{n in 3,5,10,20 : C[d-1] > SMA_n(C)[d-1]} / 4`. Trade only if score > 0 (cell on/off). Size = score x
  the base risk; this affects the FTMO simulation only. Report R and score-weighted R.
- Vol targeting (sizing only): `weight = min(1, 0.02 / (Range / C[d-1]))`.
- Exit: next day's open (primary); same day's close as a cell.
- Stop for R: today's open `O[d]`, i.e. the breakout has failed if price returns to the open (primary). Cell: no stop, R per 1 x
  ATR(20), which matches the original.
- GSV sub-cell (Williams, Oxford Strat reading): per bar, `noise = O-L if C>O; H-O if C<O; min(O-L, H-O) if C=O`. `GSV = 2 x
  SMA10(noise)`. Buy stop at `O[d] + GSV` if `C[d-1] > C[d-1-n]`; sell stop at `O[d] - GSV` if `C[d-1] < C[d-1-n]`, n in {10, 20}.
  Exit at the close of day 1 (and day 5 as a cell). Stop = 6 x ATR(20).

**Primary cell:** BTCUSD and ETHUSD, long-only, cell A k, MA filter on, exit next open, fills on M5. Then XRP, LTC, ADA, DOGE, SOL,
XAUUSD (24h), US100/US500 (cash and server day), all FX.
**Baselines:** a long from open to next open on random days of the same year (crypto drift!); lab #50's fixed-k VB on the same days.
**Evidence:** lab #50/#71: gold 24h k = 0.5 +0.03 to +0.07R, p_alone 0.001 but bootstrap low < 0 (WATCH). #75: Dual Thrust (same
family) CANDIDATE on US100 cash k = 0.5. Korean sources show no audited performance.
**Why rank 2:** it extends the only family with real (if small) intraday momentum in this lab. The noise-adaptive k fixes the obvious
weakness of a fixed k. VB was never run on crypto here.
**Risks:** FTMO crypto costs (0.0325%/side + spread) on 1-day holds; 1:1 crypto leverage on Swing caps size; weekends.
**Cost to test:** S (extend quant/mcpt_wvb.py).

---------------------------------------------------------------------------------------------------------------------------------

### T3. Larry Williams smash-day reversals (naked-close and hidden smash). Rank 3
**Sources:** Williams, "Long-Term Secrets to Short-Term Trading" (1999) (ref). Third-party test: Rogue Quant, "I Backtested Larry
Williams' Trading Strategy Across 15 Markets" (read: https://roguequant.substack.com/p/i-backtested-larry-williams-trading). Pattern
variants: https://prorealcode.com/prorealtime-indicators/larry-williams-smash-days (read).

**Rule (buy side; mirror for sells):**
- Naked-close smash bar t: `C[t] < L[t-1]` and `C[t] = min(C[t-N+1..t])`, N = 8 (primary; cell N = 3). Rogue Quant words the
  look-back as "prior close lowest of 3-8 days"; the reading above is pre-registered.
- Hidden smash bar t (cell): `C[t] > C[t-1]`, `C[t] < O[t]`, and `C[t] - L[t] <= 0.25 x (H[t] - L[t])`.
- Entry: buy stop at `H[t] + 1 tick`, valid on bar t+1 only.
- Stop: `L[t]` (the smash bar's low).
- Exit: (a, primary) Williams' bail-out: out at the first open after entry that is above the entry price, or at the close of bar 5.
  (b, cell) Rogue Quant's always-in rule: reverse on the opposite signal.

**Primary cell:** US + EU indices, longs, D1. Then every symbol, D1 + H4 (4 offsets) + H1, both sides.
**Baselines:** random days with the same holding; "buy stop above yesterday's high" on every day (the unconditional trigger).
**Evidence (Rogue Quant, 2014-2024, futures, $2.50 commission + $12.50 slippage per contract):** S&P 500 longs: 80% winners, profit
factor 6.94 (small sample). Nikkei, Dow and Russell longs strong, shorts weak. Euro profitable on both sides. AUD/CAD/JPY good on
shorts. Adding a stop made results worse almost everywhere.
**Why rank 3:** there is third-party evidence with costs, and its best side (index longs after a down-smash) matches the lab's IBS/RSI2
index-long WATCH. It differs from 80-20s/Oops (#53/#51), which buy back at yesterday's low; a smash needs a close through the low
and then a break of the smash bar's high.
**Risks:** overlap with IBS (report the trade overlap); index-long drift (hence the random-day baseline).
**Cost to test:** S.

---------------------------------------------------------------------------------------------------------------------------------

### T4. BNF deviation (乖離率) reversion: Takashi Kotegawa. Rank 4
**Sources:** PickMyTrade write-up: kairi = (close - MA25)/MA25; the -20% to -35% thresholds are tied to the 2001-02 Japanese market;
exit when kairi returns to 0 (read: https://blog.pickmytrade.trade/bnf-takashi-kotegawa-strategy-pickmytrade/).
https://behindtheinvestment.substack.com/p/bnf-and-his-trading-journey ("at least 20% below the 25-day MA, adjusted by market and
sector"; read). Japanese deviation statistics: AllAbout 2011 (Nishimura, 統計で勝つトレード; read: https://allabout.co.jp/gm/gc/383697/).
Counter-evidence: Alajbeg, Bubaš & Vasić (read: https://www.bib.irb.hr/913079).

**Rule:**
- `kairi[t] = C[t] / SMA25(C)[t] - 1`.
- Long at the next open when `kairi[t] <= -theta`.
  - Raw thresholds: stocks theta in {15%, 20%, 25%} (primary 20%); indices theta in {5%, 7%, 10%} (primary 7%).
  - Scaled version (every symbol, so FX/metals/crypto get signals): kairi at or below its 2.5th percentile of the previous 500
    bars (cell: 1st percentile).
- Exit: next open after the first close with `kairi >= 0` (back to the MA, BNF's exit); time stop 10 bars; protective stop
  entry - 3 x ATR(14), which also defines R.
- One position per symbol; re-arm only after kairi > -theta/2. A short mirror (kairi >= +theta) is a separate cell; BNF bought dips.

**Primary cell:** the 30 US stock CFDs + 4 US indices, D1, raw thresholds, long-only. Then the scaled version on every symbol, D1 and H4.
**Baselines:** random days with the same holding; trade overlap with IBS/RSI2.
**Evidence:** BNF's record is real but anecdotal: about ¥1.6M grew to roughly ¥18.5B (secondary, inconsistent figures). AllAbout's
Japanese-stock test of deep deviations (-30%): 11,849 trades, 75.3% winners, mean +9.16% per trade, ~11.5-day holds (2011; the
article's deviation base is ambiguous). **Against:** in US stocks, buying far below nearly all moving averages gave the LOWEST later
returns (Alajbeg et al.). Reversal was strongest only 0-5% below the 20/50-day MA over 1-2 weeks.
**Why rank 4:** simple, documented exit, and it fits the index mean-reversion WATCH. Ranked below T1-T3 because the US
counter-evidence is direct.
**Risks:** **survivorship bias.** The 30 FTMO stocks are 2026 survivors, so dip-buying them flatters results; weight the index and
scaled results. Signals are rare for indices (2018-Q4, 2020-03, 2022, 2025-04).
**Cost to test:** S (quant/daily.py signal function).

---------------------------------------------------------------------------------------------------------------------------------

### T5. Paul Tudor Jones' 200-day rule as a filter on the live edges. Rank 5
**Source:** PTJ via Tren Griffin (25iq, 2015): "My metric for everything I look at is the 200-day moving average of closing prices"
and "get out of anything that falls below the 200-day moving average" (read:
https://thereformedbroker.com/2015/07/27/ptj-on-being-on-the-right-side-of-the-trend/).

**Rule:** a trade is allowed only in the direction of the prior day's close vs the 200-day SMA of daily closes: long only if
`C[d-1] > SMA200[d-1]`, short only if `C[d-1] < SMA200[d-1]`. Apply it unchanged to (1) the live OC30 (TSLA, US100; live settings,
Fed days skipped), (2) the index gap fade (>= 1 ATR, 9 indices) and (3) the US100 noise band.
**Keep rule (pre-register):** filtered minus unfiltered >= +0.05R in both halves on that strategy, AND FTMO pass odds at half edge
improve (quant/ftmo_opt.py); otherwise drop it.
**Evidence:** an anecdotal quote. Stand-alone 200-day timing is already DEAD here (MA50_200, TSMOM). The filter on intraday edges is
untested; similar regime filters (calm-day, NR7) did not help.
**Why rank 5:** it costs almost nothing and can be deployed in the EA immediately if it passes.
**Cost to test:** XS.

---------------------------------------------------------------------------------------------------------------------------------

### T6. Thermostat (恒温器): Pruitt & Hill, choppy/trend regime switch. Rank 6
**Sources:** Pruitt & Hill, "Building Winning Trading Systems with TradeStation" (2002/2012), Thermostat p.138 (ref). MT5 port and
description (read: https://www.mql5.com/zh/market/product/32558). Book-code discussion (read: https://nexusfi.com/showthread.php?p=792671).

**Rule (daily bars):**
- `CMI[t] = 100 x |C[t] - C[t-29]| / (max(H[t-29..t]) - min(L[t-29..t]))`, Pruitt's ChoppyMarketIndex(30).
- **Swing mode** (CMI < 20), orders for bar t+1, with `key = (H[t]+L[t]+C[t])/3` and ATR10:
  - Cell A (book code as reconstructed): if `C[t] > key` ("sell-easier day"), buyPt = `O[t+1] + 0.75 ATR`, sellPt =
    `O[t+1] - 0.50 ATR`. Otherwise ("buy-easier day") buyPt = `O[t+1] + 0.50 ATR`, sellPt = `O[t+1] - 0.75 ATR`.
  - Cell B (the MT5 port's reading): the easier side is the side of the close vs key.
  - Then `buyPt = max(buyPt, SMA3(L)[t])`, `sellPt = min(sellPt, SMA3(H)[t])`. Stop-and-reverse at these stop orders.
- **Trend mode** (CMI >= 20): buy stop at BB(50, +2 sigma), sell stop at BB(50, -2 sigma); exit trend trades at a stop on SMA(50).
  Swing trades still open when the mode flips get a protective stop at entry -/+ 3 ATR10.
- R per trade = P/L / (3 x ATR10 at entry) for swing trades, or / distance to SMA(50) at entry for trend trades.

**Primary cell:** D1, every symbol, cell A. Then cell B and H4 (4 offsets).
**Baselines:** random entries with the same exits; lab #50 VB on the same symbols.
**Evidence:** none independent (book; the MT5 product page reports no performance).
**Why rank 6:** it is the Chinese classic "恒温器". Splitting VB-type swing entries by CMI is informative on its own: report swing
entries by CMI bucket.
**Cost to test:** M.

---------------------------------------------------------------------------------------------------------------------------------

### T7. Classic CTA trend book: Aberration, King Keltner (金肯特纳), Bollinger Bandit (布林强盗), Dynamic Breakout II (动态突破). Rank 7
**Sources:**
- Aberration: Keith Fitschen, built 1986, released 1993, named a Futures Truth "top 10" system (read:
  https://www.traders.com/Documentation/FEEDbk_docs/2007/08/Interview/interview.html, https://www.thechartist.com.au/?p=18460). TqSdk code
  BOLL(26, 2), enter above/below the band, exit at the midline (read: https://doc.shinnytech.com/tqsdk/1.6.0/demo/example/aberration.html).
  Chinese texts use N = 35 (ref).
- King Keltner and Bollinger Bandit: book code reproduced at https://nexusfi.com/showthread.php?p=792671 (read).
- DBO II: https://www.quantconnect.com/tutorials/dynamic-breakout-ii-strategy/ (read).

**Rules (D1; mirror for shorts):**
- **Aberration:** mid = SMA(N), bands = mid +/- 2 x StDev(C, N), N in {26, 35} (primary 35). Long at the next open after a close above
  the upper band. Exit at the next open after a close below mid. Stop-for-R = the distance to mid at entry.
- **King Keltner:** `mid = SMA40((H+L+C)/3)`, band = mid +/- ATR(40). Buy stop at the upper band while mid is rising (`mid[t] >
  mid[t-1]`); sell stop at the lower band while mid is falling. Exit with a stop at mid.
- **Bollinger Bandit:** BB(50, +/-1.25 sigma); filter `ROC = C - C[29]` (rocCalcLength 30; > 0 longs, < 0 shorts); stop entries at
  the bands. Exit at
  SMA(liq) of C, where liq starts at 50 and drops by 1 each bar in the trade (floor 10). The exit applies only while SMA(liq) is
  below the upper band (longs) or above the lower band (shorts).
- **DBO II:** `sigma = StDev(C, 30)`. `n[t] = round(n[t-1] x (1 + (sigma[t] - sigma[t-1]) / sigma[t]))`, clamped to [20, 60] (start
  20). Long if `C[t-1] > BB_upper(n, 2)` and price > `max(H, n)` (stop order). Exit when price < SMA(n). Shorts mirrored. The bands
  use an SMA midline (Pruitt's BollingerBand); QuantConnect's port uses an EMA, so pre-register SMA.

**Primary cell:** each system on every symbol D1, with swaps; pooled by group. Then H4 with 4 offsets.
**Baseline:** random entries with the same exit, as in #39.
**Evidence:** Aberration's Futures Truth ranking (1990s, gross of today's costs). DBO II (QuantConnect): EURUSD 2010-16 +2.3%/yr,
Sharpe 0.31, max DD about 14%; GBPUSD negative. King Keltner and Bollinger Bandit: book only.
**Why rank 7:** this completes the Chinese CTA canon the backlog asked for, and it checks whether "exit at the moving average" (the
best exit in #32) rescues trend entries. Prior: low, since DON/MA/TSMOM/Clenow are all DEAD after costs + swaps here.
**Cost to test:** M (four signal functions in quant/daily.py style).

---------------------------------------------------------------------------------------------------------------------------------

### T8. 空中花园 (Sky Garden): big gap + first-bar break in the gap direction. Rank 8
**Source:** WonderTrader CTA intraday docs (read: https://wtdocs.readthedocs.io/zh/latest/docs/strategies/ctadaytradestra.html). Long if
price > the first bar's high and open > yesterday's close x 1.01; short if price < the first bar's low and below yesterday's close
x 0.99; one trade a day; flat at 14:55; 5-minute bars; CSI index futures 2014-09 to 2019-09.

**Rule:**
- `gap = O[d] / C[d-1] - 1`, from the cash session open and the previous cash close.
- If gap >= +1%: buy stop at the high of the first M-minute bar (M = 5 primary; 15, 30), valid until the close. If gap <= -1%: sell
  stop at the first bar's low.
- Original: no stop, exit at the session close (cell with R per 0.5 daily ATR). FTMO cell (primary): stop at the first bar's other
  end, exit at the close.
- ATR-scaled cell: |gap| >= 0.5 or 1.0 daily ATR.
- Pre-registered mirror (not in the source): a big gap and the first-bar break goes AGAINST the gap -> trade against the gap, stop
  at the first bar's other end. This connects to #46's US-index WATCH and #70's gap fade.
- At most one trade per day.

**Primary cell:** US + EU indices, M5 (US100/US500 also on real M1 from 2021-09-14). Then stocks, JP225/HK50/AUS200, energy at the
NYMEX open.
**Baseline:** coin flip at the same moments; the lab's GAPgo cells.
**Evidence:** WonderTrader reports "good backtest results", weak 2016 to early 2018 (charts only). Lab: GAPgo DEAD; on big-gap days
OC with the gap -0.05R vs against +0.26R on US indices (#69). So expect the with-gap leg to lose and the mirror to win.
**Why rank 8:** it is cheap and directly tells the live gap fade whether waiting for a failed first bar adds anything.
**Cost to test:** S (quant/intraday.gap pattern).

---------------------------------------------------------------------------------------------------------------------------------

### T9. Andrea Unger: prior-session breakout with the "Daily Factor" (body/range) filter. Rank 9
**Sources:** Unger Academy video transcript: Daily Factor = |close - open| / (high - low) of the prior session; a trend-direction
breakout of the previous day's high/low; flat at the end of the day; crude oil on 15-min bars, 2010+ (read:
https://ungeracademy.com/?p=6853). Same style in their DAX/Nasdaq contest strategies (read:
https://blog2.ungeracademy.com/top-trading-strategies-from-unger-academys-june-contest/). Unger won the World Cup Trading
Championship four times (ref).

**Rule:**
- `DF = |C - O| / (H - L)` of the prior session.
- Buy stop at the prior session high; sell stop at the prior session low. Active from 30 minutes after the open to 1 hour before the
  close. First touch only; skip if the open is already beyond the level.
- Trend filter (Unger: "in the direction of the trend", which he does not define): longs only if `C[d-1] > SMA20(C)`, shorts only if
  below (cell on/off).
- Pattern filter: cell A `DF > 0.5` (as in his example), cell B `DF < 0.5`.
- Stop: 0.5 x daily ATR(14) from entry. Exit at the session close.

**Primary cell:** USOIL M15 (nymex session), then GER40 M15 and US100 M5, then everything.
**Baseline:** the same breakout without the DF filter (= #81's plain prior-day breakout, with this stop).
**Evidence:** Unger's video: about 3,000 unfiltered trades averaging about $4-5; with the filter about 1,800 trades averaging about
$50 (weak since 2023). Lab #81: plain prior-day breakouts -0.14R ex-crypto (with a different stop).
**Cost to test:** S (reuse quant/lance_levels.py).

---------------------------------------------------------------------------------------------------------------------------------

### T10. 菲阿里四价 (Fiali four-price). Rank 10
**Sources:** WonderTrader (read: link in T8): long when price > yesterday's high AND > today's open; short when price < yesterday's low
AND < today's open; exit if price crosses back through today's open; one entry a day; flat at the close. TqSdk code (read:
https://doc.shinnytech.com/tqsdk/1.6.0/demo/example/fairy_four_price.html): the same rails, exit when price returns to the open, flat at
14:50. BigQuant (read: https://bigquant.com/wiki/doc/i0szuqOJgA): at most 2 entries.

**Rule:**
- Long: first time in the session that price > max(H[d-1], O[d]); buy stop at that level. Short: price < min(L[d-1], O[d]).
- Stop: O[d]. Skip the day if O[d] is already beyond H[d-1] or L[d-1] (the stop distance would be <= 0).
- One entry a day (primary); cell: up to two. Exit at the session close.
- Sessions: cash (indices/stocks), nymex (energy), london24 + us_cash (metals), london24 + ny_fx (FX), UTC day (crypto). M5.

**Evidence:** WonderTrader: "overall return modest" (CSI futures 2014-19). The demos give no numbers. Lab #81 (prior-day breakouts)
was DEAD.
**Why rank 10:** a Chinese classic and cheap to run. The stop at the open is the only real difference from #81.
**Cost to test:** XS.

---------------------------------------------------------------------------------------------------------------------------------

### T11. O'Neil market direction + Minervini Trend Template, as filters for long trades. Rank 11
**Sources:** O'Neil "How to Make Money in Stocks" (ref). Follow-through and distribution-day state machine as ported (read:
https://de.tradingview.com/script/ianwnyEH-O-Neil-Market-Timing). Minervini's Trend Template (read:
https://sharpely.in/blogs/minervini-trend-template-for-stage2-stocks/; "Trade Like a Stock Market Wizard", 2013, ref). Minervini won the
US Investing Championship (1997, 2021) (ref).

**Rules:**
- Distribution day (index): `C/C[-1] - 1 <= -0.2%` and `tickvol > tickvol[-1]`. States (port defaults):
  - pressure: >= 5 distribution days in 25 sessions;
  - correction: >= 7 distribution days and >= 6% below the 25-session high;
  - rally attempt: begins after 3 days with no new low;
  - follow-through day: day >= 4 of the attempt with a close >= +1.6% (cell +1.25%) on higher tick volume -> confirmed uptrend.
- Trend Template (per stock), all 8 must hold:
  1. C > SMA150 and C > SMA200;
  2. SMA150 > SMA200;
  3. SMA200 rising over 21 sessions (cell: 105);
  4. SMA50 > SMA150 and SMA50 > SMA200;
  5. C > SMA50;
  6. C >= 1.30 x the 52-week low (book; some sources 1.25);
  7. C >= 0.75 x the 52-week high;
  8. RS rank >= 70, the percentile of the 12-month return within the 30 FTMO stocks.
- Use: OC/gap-fade/IBS longs on indices only in "confirmed uptrend"; TSLA OC longs only when TSLA passes the template. Keep rule as
  in T5.

**Caveat:** FTMO tick volume is not exchange volume.
**Cost to test:** S.

---------------------------------------------------------------------------------------------------------------------------------

### T12. Camarilla H3 fade / H4 breakout (Nick Stott 1989; Indian intraday staple). Rank 12
**Sources:** Camarilla rules "H3/L3 against the trend, stop around H4/L4; H4/L4 breakout" (read:
https://cn.tradingview.com/script/MXkclJVM-Camarilla-Pivot-Points-V2-Backtest). The level formula is the standard one (ref; the page did
not print it).

**Rule:** from the prior session's H, L, C with R = H - L:
- `H3 = C + 1.1R/4`, `H4 = C + 1.1R/2`, `L3 = C - 1.1R/4`, `L4 = C - 1.1R/2`.
- Fade: from 15 minutes after the open, sell limit at H3 (first touch), stop H4, target C, otherwise out at the close. Buy limit at
  L3, stop L4, target C.
- Breakout cell: buy stop at H4, stop H3, target 2R or the close; mirror at L4.
- PROTOCOL fill-first rules apply. M5 primary; indices, FX, metals.

**Evidence:** none found (educational scripts). Its siblings R-Breaker (#75) and period levels (#1) are DEAD. Low prior.
**Cost to test:** XS (bt/sr_diag.py levels engine).

---------------------------------------------------------------------------------------------------------------------------------

### T13. ATR channel, intraday (ATR通道; WonderTrader "ATR策略"). Rank 13
**Source:** WonderTrader (read: link in T8). k1 = k2 = 0.5; ATR and the MA both over 10 bars; mid = mean of the previous 10 closes
(the current bar excluded); flat at 14:55-15:15; 5-minute bars; CSI index futures 2014-19, profitable mostly before 2016.

**Rule:**
- On M5 (primary; M15, M30): `mid = mean(C[t-10..t-1])`, `ATR = mean(TR[t-10..t-1])`, `upper = mid + 0.5 ATR`,
  `lower = mid - 0.5 ATR`.
- Long on a break above upper (stop order); short on a break below lower. Exit long when price < mid, exit short when price > mid.
- No entries in the last 20 minutes; flat 5 minutes before the session close. R = P/L / |entry - mid| at entry.

**Evidence:** WonderTrader as above. Expect costs to dominate on M5 (the lab's 5/15-minute crossover grid #20 was DEAD).
**Cost to test:** XS.

---------------------------------------------------------------------------------------------------------------------------------

### T14. Darvas box breakout (stocks + indices, D1). Rank 14
**Sources:** Darvas, "How I Made $2,000,000 in the Stock Market" (1960) (ref). Box construction (read:
https://www.sharescope.co.uk/sharescope_tutorial33.jsp).

**Rule:**
- Box top: a new 252-bar high followed by 3 bars whose highs stay below it. Box bottom: the lowest low since the top, confirmed once 3
  bars fail to undercut it.
- Entry: buy stop at the top + 1 tick (cell: close above the top). Volume cell: breakout bar tick volume >= 1.5 x its 20-bar mean.
- Stop: the box bottom - 1 tick. Trail: when a new box forms higher, move the stop to its bottom. Time cap 120 bars.

**Evidence:** the book's claim (about $25k to about $2M, 1957-59). The lab's HIGH52 (52-week-high entry) is DEAD. Low prior; it only
adds the consolidation condition and box trailing.
**Cost to test:** S.

---------------------------------------------------------------------------------------------------------------------------------

## 3. Profiles: who, documented method, sources, evidence, testability, status

### 3.1 Systematic / quant traders and funds

| Who | Documented method (exact where public) | Evidence | Sources | Testable? / status |
|---|---|---|---|---|
| **Turtles (Dennis/Eckhardt)** | N = 20-day Wilder ATR; unit = 1% equity / (N x $/pt); S1: 20-day breakout, skip if the last S1 breakout was a winner, 10-day exit; S2: 55-day breakout, 20-day exit; stop 2N; add a unit every N/2, max 4 | Turtles' 1980s records; MQL5 port expects 30-40% win rate (no numbers) | read: https://www.mql5.com/en/articles/23448 ; ref: C. Faith, "Way of the Turtle" (2007) | TESTED (DON20/DON55, #9, #39). Only the S1 skip filter and pyramiding are untested variants of a dead family; not ranked |
| **Richard Donchian** | 4-week rule (20-day channel, always in); 5/20-day MA crossover | Historical | ref | TESTED (DON20, MA5_20) |
| **Ed Seykota** | EMA trend following: fast about 20 / slow about 200 days, ADX > 20 filter, ATR(20) x 3-5 stop, 1% risk, portfolio heat cap 20% (MQL5 reconstruction from Market Wizards) | Market Wizards anecdote (1989) | read: https://www.mql5.com/en/articles/24279 ; ref: Schwager 1989 | FAMILY (MA50_200, EMA grid #20). Not ranked |
| **John W. Henry** | Long-term multi-timeframe trend following across financial/metals futures; no public rules | Track record 1980s-2000s; closed 2012 | ref | NO RULE |
| **Bill Dunn (DUNN WMA)** | "100% systematic, medium to long-term trend following"; 26 -> 52 futures (2006); 3 -> 100+ models per future; risk was a fixed 20% VaR target, then the "Adaptive Risk Profile" (2013): 99% VaR 8-22%, average 15% | Program since 1984 | read: https://www.rcmalternatives.com/?p=4647 | NO RULE (the sizing idea, vol targeting, is already tested as #12) |
| **Jerry Parker (Chesapeake)** | Turtle-trained long-term trend following; "trend following with rules works"; no rules published | Chesapeake since 1988 | read: https://www.turtletrader.com/jerryparker/ | NO RULE (FAMILY: long breakouts DEAD) |
| **Renaissance / Jim Simons** | Public facts only: mean-reversion and trend signals; holding 1.5 days to 1.5 weeks; "patterns in morning trading that predicted afternoon trades"; pair patterns; signals kept at p < 0.01; "right 50.75% of the time"; a weekly-rally momentum strategy was switched off after the dot-com bust | Medallion record (Zuckerman 2019) | read: https://novelinvestor.com/notes/the-man-who-solved-the-market-by-gregory-zuckerman/ | TESTED in spirit: IMOM morning -> afternoon DEAD (#14), XSREV DEAD, pairs DEAD. No rule to copy |
| **Ed Thorp** | MUD ("most up, most down") stat-arb: rank stocks by the last ~2 weeks' return (adjusted for splits/dividends); buy the most-down decile, short the most-up decile (Thorp's "best"/"worst" deciles by expected return); hold a few weeks; simulated about 20%/yr, market-neutral but noisy (shelved) | Thorp's Wilmott "Statistical Arbitrage" series | read: https://c.mql5.com/forextsd/forum/70/statistical_arbitrage_-_part_ii.pdf | TESTED (XSREV weekly, #68). A 10-day/decile variant on the 30 stocks is a near-duplicate |
| **Perry Kaufman** | KAMA: ER = \|C - C[n]\| / sum\|dC\| (n = 10); sc = (ER x (2/3 - 2/31) + 2/31)^2; trade when KAMA turns by more than a filter (a fraction of the 20-day stdev of KAMA changes) | Book tests (1995+) | ref: "Smarter Trading" (1995), "Trading Systems and Methods" | FAMILY (MA trend DEAD). ER as a regime filter is a possible future filter test; not ranked |
| **John Ehlers** | MAMA/FAMA (fast 0.5, slow 0.05) crossovers, Instantaneous Trendline, Fisher transform, roofing filter | Author's articles; no independent tests found | ref: S&C Sept 2001; "Rocket Science for Traders" | FAMILY (smoothed MA crossovers DEAD, #20). Not ranked |
| **Tom DeMark** | TD Sequential / Combo / Setup Trend (full definitions in T1) | **Peer-reviewed:** Lissandrin, Daly & Sornette 2017 | read: see T1 | **NEW T1** |
| **Welles Wilder** | Volatility System (ATR(7) x 3.0 SAR off the significant close); Parabolic SAR (AF 0.02, step 0.02, max 0.20); DMI/ADX; RSI(14) 70/30 | Book (1978) | read: https://download.esignal.com/products/workstation/help/charts/studies/wilders_volatility.htm | Volatility System = Supertrend family, DEAD (#26b); ADX in Holy Grail DEAD (#54); RSI 30/70 DEAD (#20); PSAR FAMILY. Not ranked |
| **Larry Williams (other systems)** | Smash day (T3); hidden smash day; GSV (T2 sub-cell); specialist trap (failed 5-10-day box breakout, which is Turtle-soup-like); Oops (tested); VB (tested); TDOM/day-of-week seasonals; 1987 Robbins Cup | Rogue Quant 2014-24 smash-day test; Oxford Strat GSV (charts only) | read: T2/T3 links | **NEW T3, T2 (GSV)**; specialist trap FAMILY (#52 DEAD); TDOM FAMILY (TOM DEAD) |
| **Kevin Davey** | Publishes a process, not a system: build on in-sample data, walk-forward, Monte Carlo, incubate before going live. Top-3 in the World Cup Championship of Futures Trading 2005-07 (bio) | Contest results | ref: "Building Winning Algorithmic Trading Systems" (Wiley 2014) | NO RULE (the lab's PROTOCOL already follows the process) |
| **Andrea Unger** | Intraday breakouts of the prior session H/L with pattern filters ("Daily Factor" = body/range), time windows, end-of-day exits; e.g. gold hourly: long window bars 18-22, short bars 9-12 of the 17:00-NY-based session, exits at 01:00 / 09:00 | Video claims (T9); 4x World Cup champion | read: T9 links + https://ungeracademy.com/blog/breakout-strategy-on-hourly-bars-how-does-it-work-example-on-gold | **NEW T9**. The gold hourly time-window rule is a tuned single-market example; skip it |

### 3.2 Published factor strategies (AQR, Man AHL)

| Factor | Exact definition (paper) | Evidence | Testable with our data? / status |
|---|---|---|---|
| Time-series momentum (Moskowitz, Ooi & Pedersen 2012, JFE; Hurst, Ooi & Pedersen 2017) | Sign of the past 12-month (also 1-, 3-month) excess return; position scaled to 40% / ex-ante vol (EWMA vol); monthly | 58 futures 1965-2009 (ref) | TESTED (TSMOM12, TSMOM3, #68): DEAD after FTMO costs/swaps |
| Carry (Koijen, Moskowitz, Pedersen & Vrugt 2018, JFE) | FX: interest-rate differential (forward discount); indices: dividend yield minus rate; commodities: roll yield | Strong across asset classes (ref) | NO DATA: FTMO gives only today's swaps (symbol_specs.csv swap_long/short), and the export has no curve or rate history. Unlock: monthly policy rates (FRED) for 8 currencies, then an FX carry ranking with swaps |
| Value (Asness, Moskowitz & Pedersen 2013, JF) | Commodities: log(average spot 4.5-5.5 years ago / spot today); FX: 5-year real-exchange-rate change (needs CPI); index: BE/ME | Everywhere value premium (ref: https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf) | Mostly NO DATA. Only a 5-year-reversal proxy on FX (D1 from 2000), giving tests from 2005; weak. Not ranked |
| Defensive / Betting Against Beta (Frazzini & Pedersen 2014, JFE) | Long low-beta, short high-beta, each levered to beta 1; monthly | Strong in US stocks and across countries (ref) | Testable only on the 30 stock CFDs with D1 from 2019-20 (about 70 months; 1:1 leverage, swaps). Low power; not ranked |
| Quality minus junk (AQR) | Profitability/growth/safety | ref | NO DATA (fundamentals) |
| Commodity skewness (Fernandez-Perez, Frijns, Fuertes & Miffre 2018, JBF) | 12 months of daily returns -> skewness; long the lowest quintile, short the highest; monthly | 27 futures 1987-2014: about 8%/yr gross, Sharpe 0.78 | read: https://research.ou.nl/en/publications/the-skewness-of-commodity-futures-returns/ , https://www.cxoadvisory.com/?p=27787 . NO DATA in practice: softs start 2023-24; only about 6 commodities have >= 5 years |
| Man AHL volatility targeting (Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert 2018) | Scale exposure to a constant target vol; helps risk assets (equities, credit) via the leverage effect, little for bonds/FX/commodities | Long histories (ref: https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf) | TESTED as sizing for the live OC (#12, #15) |
| Man AHL / Carver EWMAC trend | EWMA crossovers 2/8 ... 64/256, scaled forecasts, vol-targeted portfolio | ref: R. Carver, "Systematic Trading" (2015) | FAMILY (MA/TSMOM DEAD). Not ranked |

### 3.3 Authors behind the Chinese CTA canon (Fitschen, Pruitt & Hill)
The "classic" strategies on Chinese platforms (TqSdk, WonderTrader, BigQuant, TB/文华) are mostly translations of US 1990s systems.
TqSdk's demo list (read: https://tqsdk-python.readthedocs.io/en/latest/_sources/demo/strategy.rst.txt) includes Aberration, double MA,
价格动量, 自动扶梯, 菲阿里四价, R-Breaker, Dual Thrust, grid, Turtle, VWAP, plus TRIX/CMO/Vortex/Hull/Keltner/Aroon/VPT trend demos
and arbitrage demos.
- Aberration (Fitschen), King Keltner, Bollinger Bandit, Dynamic Breakout II, Thermostat (Pruitt & Hill): **NEW T6, T7**.
- 自动扶梯 (escalator; TqSdk code, read: https://doc.shinnytech.com/tqsdk/1.6.0/demo/example/escalator.html), D1:
  - long when C[-2] > max(MA8, MA40), the bar before closed in the bottom 25% of its range ((C-L)/(H-L) <= 0.25), and the last bar
    closed in the top 25% (>= 0.75);
  - short mirrored;
  - exit when a close goes 1 tick beyond the min (max) of the two prior bars' lows (highs).
  - A trend-pullback reversal. FAMILY (pullback methods #36 DEAD; IBS overlap). Not ranked; a cheap add-on to T3's batch if wanted.
- 价格动量, TRIX, CMO, Vortex, Hull, Aroon: indicator trend-crossover demos; FAMILY (#20 DEAD).

### 3.4 Investing / trading legends

| Who | Documented rule | Evidence | Sources | Status |
|---|---|---|---|---|
| **Jesse Livermore** | Market Key (1940): prices kept in 6 columns (secondary rally, natural rally, upward trend, downward trend, natural reaction, secondary reaction); column moves on fixed point swings (about 6 points; pivotal points confirmed about 3 points beyond); enter only when price penetrates a pivotal point, add only at continuation pivots, exit when a penetration fails | No tests. "10 pages of rules ... 18 columns", "None of the rules are tested" | read: https://www.luxalgo.com/library/concept/livermore-pivotal-point.md , https://dailyspeculations.com/wordpress/?p=153 ; ref: "How to Trade in Stocks" (1940) | Mechanically it is a percent-swing trend system: FAMILY (Donchian/Darvas). Not ranked |
| **Nicolas Darvas** | Box rules (T14) | Book claim | see T14 | **NEW T14** |
| **William O'Neil** | Cup-with-handle (from the book, ref): cup 7-65 weeks, 12-33% deep, handle >= 1-2 weeks in the upper half and <= 10-15% deep, buy at the handle high + $0.10 on volume >= 40-50% above average; cut losses at 7-8%; take 20-25%. Follow-through / distribution days (T11) | IBD's own studies | read: T11 link; ref: "How to Make Money in Stocks" | Price pattern: low-power test on the 30 stocks (FAMILY: HIGH52/Darvas). Market-direction rules: **NEW T11** (filter). CANSLIM fundamentals: NO DATA |
| **Mark Minervini** | Trend Template (8 criteria, T11); VCP: successive pullbacks contracting (e.g. 25% -> 15% -> 8% -> 3%) with volume drying up; buy the pivot break; stop <= 7-8% | US Investing Championship 1997, 2021 (ref) | read: T11 link | Trend Template: **NEW T11** (filter). VCP: pattern too loose to pre-register without tuning; not ranked |
| **Stan Weinstein** | Stage analysis (1988): 30-week MA; stage 2 = price above a rising MA after a base; buy the weekly breakout above resistance on volume >= 2x average, with Mansfield RS > 0; exit below the MA. The MQL5 automation uses a 150-day SMA, a slope over 10 bars, stage 1->2 transitions, tick volume > 1.8x the 20-bar mean, RSI >= 50, a 2-ATR stop, a 3R target | Book; the MQL5 article gives no numbers | read: https://www.mql5.com/en/articles/22746 | FAMILY (MA trend + 52-week breakouts DEAD). Not ranked |
| **Paul Tudor Jones** | 200-day MA as the metric; out below it | Quote | read: T5 link | Stand-alone TESTED (MA family); filter **NEW T5** |
| **Wyckoff** | Spring: undercut of range support with little follow-through, quick re-entry; buy after a quiet test holding above the spring low; stop just below the spring low | Texts, not tests | read: https://www.luxalgo.com/library/concept/spring/ | FAMILY (Turtle Soup #52, sweeps #30/#45: DEAD) |
| **W. D. Gann** | Swing charts (Krausz/Hartle): the swing turns up after 2 consecutive higher highs; the trend turns up when the last swing peak is exceeded ("use two-day charts"); angles/Square of 9 are not mechanical | None | read: https://www.traders.com/Documentation/FEEDbk_docs/1999/10/Abstracts_new/Hartle/Hartle9910.html | FAMILY (swing breakout = Donchian-like). Not ranked |
| **Stanley Druckenmiller** | Liquidity/central-bank-driven discretionary macro; no published mechanical rule | | | NO RULE |

### 3.5 Chinese methods

| Method | Rule | Evidence | Sources | Status |
|---|---|---|---|---|
| **菲阿里四价** | T10 | "Modest" (WonderTrader) | WonderTrader, TqSdk, BigQuant (T10 links) | **NEW T10** |
| **空中花园** | T8 | "Good", weak 2016-18 | WonderTrader (T8 link) | **NEW T8** |
| **Aberration** | T7 | Futures Truth top 10 (1990s) | T7 links | **NEW T7** |
| **海龟** | Turtle rules (3.1) | | 3.1 | TESTED |
| **ATR通道** | T13 | Profit mostly before 2016 | WonderTrader (T8 link) | **NEW T13** |
| **Keltner / 金肯特纳** | T7 King Keltner (Pruitt & Hill) | Book | NexusFi (T7 link) | **NEW T7** |
| **开盘区间突破 variants** | ORB15/30/60, Dual Thrust, R-Breaker; 恒温器 is T6 | | quant/intraday.py; q75_intraday.md | TESTED (T6 NEW) |
| **日内动量** | First 30 min -> last 30 min (Gao et al.) | | log #14 | TESTED (#14) |
| **跨期 / 期现** | Calendar and basis spreads | | TqSdk arbitrage demos (strategy list) | NO DATA (no futures curves or spot/futures pairs) |
| **跨品种** | Gold/silver, US500/US100 ratios (DEAD); Brent-WTI (UKOIL D1 2016+, USOIL 2020+) is testable but belongs to the dead pairs family | | TqSdk arbitrage demos | FAMILY. Not ranked |
| **期货日报 champions** | No mechanical rules published. Example: 丁伟锋 (9th contest, lightweight group): trend-only, "看大做小" (higher timeframe sets direction, intraday pattern times entry), volume-range bias, small stops, about 65% win rate, R:R up to 1:10-1:20, "no feeling, no trade". Huatai Futures studied the top-100 accounts of the 10-year special award: index futures (CSI 1000/500/300) gave 35.7% of net profits; commodities uneven (gold, shipping index, lithium as broad trend pools); single-product "burst" accounts (29) vs diversified; the dominant theme rotated over time | Contest P&L | read: https://finance.sina.cn/futuremarket/qszx/2020-11-22/detail-iiznezxs3062835.d.html , https://www.fxbaogao.com/detail/5459868 , https://bbs.tbquant.net/thread/forum10919 | NO RULE. The Huatai finding (index-futures trend capture dominates) is consistent with the lab's index intraday-momentum edges |
| **傅海棠** | Fundamental supply/demand ("天时地利人和"), heavy concentration; no price rule | | | NO RULE / NO DATA |
| **叶燕武** | No documented mechanical rule found | | | NO RULE |
| **幻方 / 九坤 CTA factors** | No rule-level public CTA research found. 九坤 started as proprietary CTA and moved to AI-driven trading after 2018 (cs.com.cn) | | read: https://www.cs.com.cn/tzjj/jjks/202207/t20220725_6286624.html | NO RULE. Public CTA factor research (momentum, term structure, basis, skewness) is covered in 3.2 |

### 3.6 Japanese methods

| Who | Rule | Evidence | Sources | Status |
|---|---|---|---|---|
| **Takashi Kotegawa (BNF)** | Buy at -20% to -35% kairi from the 25-day MA (thresholds set by market and sector; tied to 2001-02); exit on the rebound to the MA; later intraday dip rebounds | Record (secondary); Japanese deviation statistics; US counter-evidence | T4 links; also https://www.ebc.com/forex/takashi-kotegawa-strategy-how-to-win-big-in-the-stock-market (read: an intraday reading with 5-10% drops, 1-3% targets, no sources) | **NEW T4**. The intraday variant is FAMILY (first-hour reversal FHR0.5/0.8 in #68, no survivor) |
| **cis** | Principles: buy what is rising, hold while it rises, sell once it starts to fall, never average down, don't take profits early in an advance | Record (anecdotal) | read: https://diamond.jp/articles/-/197252 | NO RULE. Maps to the tested momentum families (OC, ORB, Donchian) |
| **Ichimoku (Hosoda); envelope/kairi conventions** | Tenkan/Kijun crosses, price vs cloud; 25-day MA envelope +/-10-20% for stocks, 20-day +/-5-10% for the Nikkei | None given | read: https://kabu.com/investment/guide/technical/15.html , https://media.rakuten-sec.net/articles/-/49429 | Ichimoku = FAMILY (MA cross DEAD); envelopes fold into T4 |

### 3.7 Korean methods
- **변동성 돌파 (Larry Williams VB) with noise ratio, MA score and vol targeting**: the dominant Korean retail systematic method,
  especially in Upbit crypto bots. **NEW T2.**
- Dual momentum / static asset allocation (강환국-style books): monthly ETF rotation; not a prop-firm fit. Absolute momentum = TESTED
  (TSMOM).

### 3.8 Indian methods
- Supertrend (10, 3): TESTED (#26b, DEAD). Opening-range breakouts on Nifty/BankNifty: TESTED (ORB). 9:20 straddles: NO DATA (options).
- CPR (Frank Ochoa, "Secrets of a Pivot Boss"): `P = (H+L+C)/3`, `BC = (H+L)/2`, `TC = 2P - BC`. A narrow CPR (width % in the low
  percentile of its own history) is said to precede trend days; the script's author calls this "folklore until measured" (read:
  https://vn.tradingview.com/script/294UHHew-Options-Decision-Dashboard-CPR-Expected-Move-Day-Type/). A narrow-range-day filter is
  FAMILY with NR7 (#49/#69 DEAD).
- Camarilla: **NEW T12.**

---------------------------------------------------------------------------------------------------------------------------------

## 4. What extra data would unlock the NO DATA items
| Item | Data needed | Where |
|---|---|---|
| FX carry (AQR) | Monthly policy or 3-month rates for USD, EUR, JPY, GBP, AUD, NZD, CAD, CHF (2000-2026) | FRED CSVs (Shen can download, as with DGS10) |
| Commodity skewness / value / momentum cross-section | Long daily histories for softs, grains and energy | Older MT4 or TradingView exports of the futures |
| CANSLIM / quality / BAB with fundamentals | EPS growth, ROE, book values | Not in MT5; skip |
| 跨期 / 期现, term-structure factors | Futures curves | Not available on FTMO CFDs |

---------------------------------------------------------------------------------------------------------------------------------

## 5. Suggested run order (one pre-registration block each; no tuning after the first run)
1. T1 TD Sequential/Combo: bt/xrules_td.py, every symbol and timeframe, primary D1 commodities C13+S9P H5.
2. T2 Korean VB: extend quant/mcpt_wvb.py; primary BTC/ETH long-only, noise-k, MA filter, exit next open.
3. T3 Smash day: quant/daily.py signal plus the bail-out exit; primary US/EU indices longs D1.
4. T5 PTJ filter: on the existing OC/gap-fade/noise-band trade lists (minutes of compute).
5. T4 BNF kairi: quant/daily.py; primary US stocks + US indices; report the survivorship caveat in the verdict line.
6. T8 + T10 (空中花园, 菲阿里四价) as one Chinese-intraday batch on the session matrices; T13 and T12 alongside if time allows.
7. T6 + T7 (Thermostat + trend book) as one daily batch with swaps and random-entry baselines.
8. T9, T11, T14 last.
