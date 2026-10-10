# Top traders of prop firms and trading competitions: what they actually do, as testable rules

Draft, 10 Oct 2026. Desk research only: **no backtest was run**, so every rule below can be pre-registered exactly as written
(PROTOCOL rule 1). Novelty was checked against research/log.md (#1-#82), research/backlog.md (#1-#69) and drafts/q75_*.md.

## 0. Summary

- **Verified records are rare, and disclosed methods are rarer.** Contest organisers verify returns (Robbins World Cup: audited
  real money; US Investing Championship (USIC): brokerage statements). Prop firms publish only selected case studies and payout
  totals. MetaQuotes ATC winners and Chinese/Korean contest winners almost never disclosed rules.
- **Who wins, by venue:**
  - Robbins futures: systematic portfolio traders (Unger 2008-10, Davey 2006, his student Serafini 2017, Scherman 2023, Unger's
    students in 2024).
  - USIC: momentum-leader stock traders (Minervini 1997/2021 and his students in 2023-25; Kell 2020; Luk 2025).
  - FTMO's published winners: intraday traders in gold, US indices and FX, clustered at institutional flow times. These are the
    NY open, the London 4 pm fix, the Tokyo morning/fix and the 18:00 NY reopen.
- **The two consistent, mechanical families not yet tested in the lab:**
  1. **Scheduled-flow (fixing) trades in FX**: the London 4 pm WMR fix, the month-end hedge rebalancing at that fix, and the Tokyo
     9:55 fix / gotobi days. Each is backed by FTMO account evidence, academic papers and practitioner use.
  2. **Champions' rule families that never ran here**: Unger's time-of-day/day-of-week "bias" systems, and the momentum-leader
     stock swing setups (Kullamägi/Luk breakouts, pullback "undercut & reclaim", episodic pivots, Minervini's trend template).
- **Section 4 holds 15 new rules, ranked.** Ten more mechanizable methods were already tested in the lab (section 5).

## 1. Method and limits

- **Sources read:**
  - WebSearch (about 60 queries in English, Chinese, Japanese, Korean, Spanish and Russian); this hit the session's search
    limit.
  - WebFetch of about 75 pages: FTMO blog case studies, organiser halls of fame, Unger Academy rule write-ups, MetaQuotes
    interviews, Qullamaggie, TraderLion, NBER, Bloomberg Línea, Zai FX, Chinese/Korean/Polish press.
- **Reddit:** skipped, as instructed.
- **YouTube:** videos not watched. TopstepTV stories and FTMO video interviews were covered only through text pages.
- **Thin areas** (the search budget ran out before they were covered further; send a follow-up to continue):
  - The5ers, FundingPips, Alpha Capital, FXIFY and Apex: no public behaviour statistics or rule disclosures were found.
  - Darwinex: no DARWIN provider describing an exact method was found.
  - Korean contests: rules undisclosed.
  - ATC 2011 winner: name not retrieved.
- **Clock convention:** times are local exchange times, with New York (NY) times added. The FTMO server = NY + 7 h all year. FX in
  the export is M15 only (2015+). Index intraday starts Oct 2021 / 2022. Stocks D1 start 2019-20 (AAPL/MSFT 2007), intraday 2020-22.

## 2. Evidence by venue

### 2.1 FTMO

FTMO does **not** publish aggregate statistics on pass rate, instruments, holding time or risk per trade (CoinLaw's audit of FTMO's
pages, 2026). Instead it publishes about 40 "Successful Traders Stories" plus an older "FTMO Traders Analysis" series. These are
account-level analyses of selected profitable accounts (simulated accounts, chosen by FTMO, so survivorship applies).

What 15 analysed accounts show:

| Account (FTMO article) | Market | Trades | Win % | RRR | Hold | Where the profit came from (platform time, as FTMO states it) | Bias |
|---|---|---|---|---|---|---|---|
| Scalper, several accounts ("what consistent trading looks like") | FX majors + crosses | 21 / many | >90 | 0.65-0.73 | minutes | **All trades opened 17:58-18:00 platform time (= 15:58-16:00 London = the WMR 4 pm fix)** | long only |
| EURUSD-only ("losses are part of profitable trading") | EURUSD | 46 | 74 | 1.16 | intraday | **Best entries 01:00-02:00 CET (= 09:00-10:00 Tokyo, around the 9:55 fix)** | both |
| CAD-pairs trader (same article) | FX crosses, EURCAD best | 51 | 55 | 2.11 | minutes | not stated | mostly short |
| Yen-pairs scaler (same article) | 5 instruments, yen best | 24 | 42 | 3.52 | intraday | not stated | long-tilted |
| Gold scalper $50,333 | XAUUSD | 572 | 50 | 1.60 | scalps | ~15:00 platform (GMT+3) = 08:00 NY | balanced |
| "Machine-like" gold scalper | XAUUSD | 249 | 37 | 2.80 | seconds to hours | 16:00-20:00 (CET) = US open / EU close overlap | mostly short |
| 5.59-RRR gold trader | XAUUSD | n/a | 28 | 5.59 | losers minutes, winners 3-4 h | **~01:00 platform (GMT+3) = 18:00 NY reopen** | mostly short |
| US500 trader $27,734 | US500 (+GER40) | 662 | 39 | 2.06 | minutes to hours | **~01:00 platform (GMT+3) = 18:00 NY reopen** | almost all short |
| US100 "sniper" | US100 | 24 | 71 | 2.04 | minutes | 14:00-16:00 platform, around the US open | balanced |
| Index scalper 77% | GER40, US100, US30, US500 | n/a | 77 | ~0.66 | seconds to minutes | ~14:00 and ~17:00 platform (US open, EU close) | mostly short |
| EURUSD "<2 trades a day" | EURUSD | 45 | 53 | 2.40 | hours | 06:00-08:00 and ~15:00 platform | n/a |
| High-RRR $93,168 | XAUUSD, HK50, EURUSD, AUDUSD | 72 | 31 | 4.78 | up to 4 days | ~06:00, 11:00, 13:00 platform (EU open/overlap) | longs better |
| Precious metals 20% / 9 days | XAUUSD, XAGUSD | 52 | 44 | 3.67 | ~4 h | 23:00-06:00 platform (Asian session) | both |
| Swing FX, 20 pairs ("different paths") | 20 FX pairs | 37 | 46 | 2.79 | half held overnight | yen and CHF pairs **earned positive swap** | both |
| Swing FX, 11 trades ("less is more") | AUDCAD, USDJPY, AUDJPY | 11 | 64 | 5.17 | days | n/a | mostly short |

Patterns worth testing:
- **Profits cluster at scheduled institutional flows**, not at random hours: the NY open (already the lab's main theme), the
  London 4 pm fix, the Tokyo morning/fix, and the first hour after the 17:00-18:00 NY daily break.
- **Two working profiles:** high win rate with RRR < 1 (scalpers), or 28-50% wins with RRR 2-5.6 (intraday/swing).
- **Sizing by stop distance;** the largest single loss stayed under about 1% of the account where FTMO reports it.

### 2.2 Other prop firms: base rates (no behaviour data on methods was found)

- **Topstep, 2025:**
  - 16.8% of Trading Combines were completed.
  - 51.8% of participants reached a funded account at least once.
  - 33.3% of funded traders received a payout.
  - 0.71% of Express Funded traders were called up to a Live account.
  - Source: Topstep figures as quoted by Fortunly and AlphaExCapital.
- **FPFX Tech** (back office for 10 firms, about 300,000 accounts of 100,000 traders): 14% passed, about 7% of all traders were ever
  paid, and the average payout was about 4% of the account.
- **FundedNext, Feb 2026:**
  - $15.19 m was paid to 8,340 traders; the mean per transaction was $1,119 and the median $567.
  - The paid CFD accounts' median win rate was 50%, and 41% of them won less than half their trades.
- **Pass rates elsewhere:** E8 17.7%; Fintokei 2-5% (2-step); The Funded Trader about 1% ever paid.
- **Why accounts fail:** OneFunded failures were 78.7% daily-loss breaches and 15% max-drawdown breaches.
- **Lesson for rule design:** the daily loss limit kills most accounts. Negative-skew rules (scalps, night mean reversion) need a
  hard daily risk cap.

### 2.3 Robbins World Cup Championship (organiser-audited real money)

| Year | Champion | Return | What is known about the method |
|---|---|---|---|
| 1987 | Larry Williams | 11,376% | COT, seasonals, %R, volatility breakouts. "Markets are always right, you won't be, so run stops." |
| 1997 | Michelle Williams | 1,001% | her father's methods (no detail) |
| 2005 / 06 / 07 | Kevin Davey | 148% (2nd) / 106.7% (1st) / 111.6% (2nd) | Systematic trend following, "an x day breakout with oscillator confirmation"; walk-forward and Monte Carlo testing; target about 100% a year |
| 2007, 2014 (+ 2011 stocks) | Michael Cook | 249.7%, 366% | Hybrid, "more trader than system purist"; market-based stops; no public rules |
| 2008-2010 | Andrea Unger | 671.9%, 115.4%, 239.6% | Fully systematic portfolio: "bias" (time-of-day / day-of-week), breakout, reversal systems, plus a library of price "patterns" as filters. Several systems published with rules (R4, R10, R13). |
| 2017 | Stefano Serafini | 217.2% | Unger Academy student |
| 2023 | Ivan Scherman | 491.4% | 100% algorithmic fund: trades "only when a behaviour pattern programmed into one of our algorithms appears"; no rules |
| 2024 (leader mid-year) | "Michael", Unger student | +136% by June, 5.4% max DD | "I trade like six, seven strategies ... only the best from hundreds" |
| 2015 FX (per Zai FX) / Japan FX2017 | バカラ村 (Bakaramura) | +51.73% (Japan FX2017) | Discretionary FX: H4/H1 flag patterns and fundamentals; small first position, adds on confirmation; tight-stop day trades "allow larger size" |
| 2022 FX | K. Takegawa | 333.7% | no method found |

The organiser's table lists "STORM LLC" as the 2015 forex champion. Whether that is Bakaramura's entity is unverified.

### 2.4 US Investing Championship (brokerage statements reviewed; not an audited composite)

| Trader | Result | Method (own words / closest source) |
|---|---|---|
| Mark Minervini | 1997 +155% ($250k own money); 2021 +334.8% ($1m+ division) | SEPA: 8-point Trend Template plus volatility-contraction (VCP) pivot breakouts; max 7-8% loss |
| David Ryan | 1985 +161%; 1987 two-year +578% | CAN SLIM base breakouts (O'Neil) |
| Oliver Kell | 2020 +941.1% | "Cycle of price action": wedge pop ("the price reclaims both the 10-day and 20-day EMAs after a sharp drop") and EMA crossback (first pullback to the rising 10/20 EMA) |
| Martin Luk | 2025 +969.8% (Stock record); 2024 +283.1% | "Buy weakness in strength, not weakness in weakness"; momentum stocks up 30%+ over 1/3/6 months; pullbacks to the 9/21 EMA and AVWAP; enter on an undercut-and-reclaim; stops "often between 1% and 4%"; trail with the 9 EMA; low win rate, 10-30R winners |
| Law Wai-Sum, Judy Lai, Goverdhan Gajjala, Bob Weissman | 2023-25 division wins (+115% to +805%) | Minervini students or clients (SEPA) |
| Kristjan Kullamägi (not a contestant; public broker statements) | (Luk's lineage) | Three setups: breakout, episodic pivot, parabolic short. "Stop is always lows of the day"; risks 0.25-1% per trade |

### 2.5 MetaQuotes Automated Trading Championship 2006-2012 (fully automated; little logic ever published)

| Year | Winner / notable | What was disclosed |
|---|---|---|
| 2006 | Roman Zamozhniy "Rich", +250% | Would win "if the market went flat"; watches Bollinger Band widening (a flat-market mean-reversion EA) |
| 2007 | Olexandr Topchylo "Better" | Neural network (C++ to MQL4). His 2011 EA trades EURUSD, GBPUSD and USDCHF with limit orders: "It doesn't use any indicators." His report says EAs average −0.55 pips/trade and tend "to fix small profits and allow losses to grow". |
| 2007 (2nd, 3rd) | William Boatright "wackena"; Vasiliy Lavrinenko "PegasMaster" | Hard-coded multi-timeframe logic; nothing else |
| 2008 | Kiril Kartunov | nothing |
| 2010 | Boris Odintsov "bobsley", $77,000 | One indicator plus SL/TP; settings kept "secret" |
| 2012 (2nd) | Juan Pablo Alonso | EURUSD algorithm from "statistical analysis of historical EUR\USD data" |
| 2012 (3rd) | Alexey Materov | GBPJPY stop-and-reverse on a slow and a fast moving average (built partly from other symbols), very large TP, no stop loss |

ATC rules are mostly undisclosed. What was disclosed (MA crosses, Bollinger mean reversion, ATR stops) maps to families the lab
already tested, apart from flat-market reversion (R7).

### 2.6 Darwinex / Myfxbook long-run accounts

- **No Darwinex DARWIN** with a documented exact method was found.
- **Long-lived Myfxbook EAs with a described method** are "night scalpers": Night Hunter Pro (Myfxbook since Oct 2020; vendor
  figures inconsistent), Evening Scalper Pro, Starlight and Viper. They fade deviations from a moving average or band on quiet FX
  crosses in the hours after the NY close (M5/M15, TP 5-20 pips, fixed SL, news/spread filters). They are "extremely
  broker-dependent" because of rollover spreads (R7).

### 2.7 China: 期货日报 全国期货实盘交易大赛 (Futures Daily national live trading competition)

- **Huatai Futures study of the top 100 accounts of the 10-year special award:**
  - Stock-index futures are the largest profit source: CSI 1000/500/300 together give 35.7% of net profit.
  - Gold, the container-freight index and lithium carbonate are "broad trend pools".
  - Two winning account types: concentrated single-product bursts (29 of 100) and diversified accounts.
  - Winners rotate to the current market theme.
- **Current (2026) national competition, per Gelonghui:** the **quant group (1,558 accounts) was the only group with positive
  aggregate profit**. The press credits "risk discipline and reduced human interference, not a high win rate". Many quant
  strategies still failed. 10jqka puts the group's share of profitable accounts at 41.82% (late Aug 2026).
- **Champion methods published are discretionary:**
  - 林波 (heavy-weight group): long-term valuation plus medium-term sentiment, contrarian at extremes, using 1/5-1/4 of capital.
  - 丁伟锋 (9th, light-weight): intraday patterns in the direction set by a larger-timeframe volume range, about 65% wins: "设好止损，要么止损出，要么等下一个形态出来平仓".
- **Classic Chinese CTA rules** (Dual Thrust, R-Breaker, Hans123 / prior-day breakouts) are already tested (section 5).

### 2.8 Japan and Korea

- **Japan:**
  - Robbins Japan FX2017 winner (Bakaramura): discretionary (2.3).
  - The most systematic, widely traded Japanese retail edge is the **仲値 (Tokyo 9:55 fix) / 五十日 (gotobi) USDJPY trade**. Ito &
    Yamada (NBER w22820) document predictable customer buying of foreign currency at the Tokyo fix and calendar effects (R3).
  - BNF's 25-day-MA deviation contrarian buys are the same family as RSI2/IBS/Double 7s (tested).
- **Korea:**
  - Kiwoom 영웅전 (about 270k domestic + 150k overseas entrants since 2023; top players' trades shown at 3-minute delay) and
    Hankyung Star Wars publish rankings, not rules.
  - Known winner styles are intraday momentum chasing (급등주 따라잡기) and the "closing bet" (종가베팅) (R15; low credibility).

## 3. Trader profiles: credibility, markets, timeframe, method, link to a rule

| Trader | Record and verification | Markets | Timeframe | Method in their words | Rule |
|---|---|---|---|---|---|
| FTMO fix scalper | FTMO account data (simulated, selected; 21+ trades) | FX majors and crosses | minutes | "only entered long positions", opened "just before 6pm of the platform time" | R1, R2 |
| FTMO EURUSD trader | as above (46 trades) | EURUSD | intraday | best entries 01:00-02:00 CET | R3 (weak) |
| FTMO 18:00-reopen shorts (US500, gold) | as above | US500, XAUUSD | minutes to hours | profits around 01:00 platform, mostly shorts | R14 |
| Larry Williams | Robbins 1987, audited | futures | days | COT / seasonals / %R / breakouts | tested (#50, #51, #64, #82) |
| Kevin Davey | Robbins 2005-07, organiser standings | futures | days | "x day breakout with oscillator confirmation"; seminar entries | R8 (+ Donchian tested) |
| Andrea Unger (+ Serafini, students) | Robbins 2008-10, audited; his own 2025 account "not even 10%", 14.16% DD | ES, NQ, FDAX, GC, CL, HG | 5-60 min, intraday and multiday | bias, breakout, reversal, patterns | R4, R10, R13 |
| Michael Cook | Robbins 2007/2014 | futures | swing | discretionary overlay on systems | none (no rules) |
| Ivan Scherman | Robbins 2023 | futures | n/a | algorithmic, undisclosed | none |
| Mark Minervini (+ students) | USIC 1997/2021 (+2023-25) | US stocks | days to weeks | Trend Template + VCP | R11 |
| Martin Luk / Oliver Kell | USIC 2025 / 2020 | US stocks | days to weeks | pullback undercut-and-reclaim; EMA crossback; 9/10/20 EMA trails | R5, R6 |
| Kristjan Kullamägi | broker statements, not audited | US stocks | days to weeks | breakout, episodic pivot, parabolic short | R5, R9, R12 |
| ATC winners (Rich, Better, bobsley, Materov) | MetaQuotes contest (real-time accounts) | FX | M15-H4 | flat-market BB reversion; neural net; MA trend | R7 (Rich) |
| Night-scalper EAs | Myfxbook (vendor numbers inconsistent) | FX crosses | M5-M15 | fade deviations after the NY close | R7 |
| Bakaramura | Robbins FX (organiser lists STORM LLC for 2015), Japan FX2017 | USD pairs | H4/H1, day | flags plus fundamentals, discretionary | none |
| 林波, 丁伟锋, CN quant group | Futures Daily competition (exchange-account based) | CN futures | intraday to long | valuation/sentiment; intraday patterns | none (no data or rules) |
| Korean contest winners | broker contests | KRX stocks | intraday / overnight | momentum chasing; closing bets | R15 |

## 4. Ranked NEW testable rules (exact definitions)

### 4.1 How the rules are written and rated

**Shared conventions** (PROTOCOL rules 2-4; quant/universe.py costs):
- **Costs:** 1.2 × bar spread at entry and exit, plus FTMO commission per side; swaps for every 17:00 NY rollover held.
- **Volatility unit:** ATR(20) on server-day D1 bars as of the previous day.
- **Fills:** entries at the next bar's open after a signal on a closed bar. A bar touching stop and target counts as a stop.
  Stops that gap fill at the open.
- **Pass bar:** PROTOCOL rule 4 on the primary cell **and** beating the named baselines by ≥ +0.05R. Then a selection-aware
  permutation test over all cells of the idea (p_best ≤ 0.10).
- **Grids:** every cell named below is fixed now and must be reported.

**Ratings:**
- **Credibility**, meaning evidence of real performance:
  - H: verified real money and the trader's own rule, or a long-documented peer-reviewed effect.
  - M: verified trader but a partly reconstructed rule, or a published backtest with out-of-sample/live claims.
  - L: anecdotal or commercial.
- **Testability** with FTMO OHLC + tick volume + spread:
  - H: all inputs available and 400+ trades expected.
  - M: proxies needed or small n.
  - L: key input missing.
- **Novelty** against log/backlog:
  - H: no tested analogue.
  - M: a related idea was tested, but this rule's distinguishing element was not.
  - L: near-duplicate.

### 4.2 Ranking

| Rank | Rule | From | Markets / TF | Cred. | Test. | Nov. | Why here |
|---|---|---|---|---|---|---|---|
| 1 | London 4 pm fix: after-fix USD reversal (+ into-fix, session flip, gold PM-auction cells) | FTMO fix scalper; Krohn-Mueller-Whelan; Breedon-Ranaldo; Ito-Yamada | 7 USD majors M15, gold M1 | M-H | H | H | Daily, many pairs, a new family; costs are the main risk |
| 2 | Month-end fix hedge-rebalancing trade | Melvin-Prins; FX desks; FTMO fix scalper | EUR/GBP/JPY/AUD vs USD, M15 + index D1 | M-H | H | H | Large predictable flow, fully mechanical, low correlation with anything live |
| 3 | Tokyo 9:55 fix / gotobi USDJPY | Japanese retail practice; Ito-Yamada; FTMO EURUSD trader | USDJPY (+ yen crosses) M15 | M | H | H | Clear clock, about 850 gotobi trades since 2015 |
| 4 | Unger DAX early-week afternoon breakout + evening-to-morning bias | Andrea Unger (Robbins 2008-10) | GER40 (EU50, FRA40, US idx checks) M15 | M | H | H | A champion's own rules, ported 1:1. "Strategy of the month" means selection bias. |
| 5 | Momentum-leader breakout (ORH entry, LOD stop, 10-SMA trail) | Kullamägi; Luk (USIC 2025) | 30 US stock CFDs D1 + M5 | M-H | M | H | Best-verified style in USIC, untested here; small universe |
| 6 | Momentum pullback "undercut and reclaim" | Luk; Kell (USIC 2020) | stocks D1 | M-H | M | M-H | D1-only, so the longest stock history |
| 7 | Night FX-cross mean reversion | Myfxbook night scalpers; ATC 2006 "Rich" | 12 FX pairs M15 | L-M | H | H | High n, new; negative skew, spread-sensitive |
| 8 | Davey range-expansion momentum | Kevin Davey | every symbol D1 / H4 / H1 | L-M | H | H | Cheap all-market test |
| 9 | Episodic pivot, multi-day hold | Kullamägi; PEAD literature | stocks M5 + D1 | M-H | M-L | M-H | Strong anomaly, few events in 30 mega-caps |
| 10 | Crude-oil false breakout with low-volume filter | Andrea Unger (published backtest) | USOIL / UKOIL M30 | M-L | H | M | The volume filter is the new element versus #45 |
| 11 | Minervini Trend Template + VCP breakout | Minervini (USIC 1997/2021) | stocks D1 | M | M | M | Overlaps HIGH52 / xsmom; the proxy is uncertain |
| 12 | Parabolic short (and long) | Kullamägi | stocks + crypto D1 + M5 | M | M-L | H | Rare events; crypto adds n |
| 13 | Gold flat-day prior-session breakout | Andrea Unger (claimed live since 2016) | XAUUSD M5 / M1 | M | H | L-M | Cheap; close to Williams VB (#50) |
| 14 | 18:00 NY reopen gap fade | FTMO case studies (US500, gold) | US500, US100, US30, XAUUSD M5 | L | H | M-H | Cheap falsification of an FTMO pattern |
| 15 | "Closing bet" 종가베팅 | Korean contest lore | stocks M5 | L | H | M | Clean test; the academic "tug of war" finding suggests it may fail |

---

### R1. London 4 pm WMR fix: USD into the fix and reversal after it (rank 1)

**Sources and evidence:**
- The FTMO scalper's trades all opened 17:58-18:00 platform time (= 15:58-16:00 London), long only, >90% wins, RRR 0.73.
- Krohn, Mueller & Whelan, "Foreign Exchange Fixings and Returns Around the Clock" (Journal of Finance, 2024; cited from memory,
  not fetched): the USD appreciates into fixes and depreciates after.
- Ito & Yamada (NBER w23327): London-fix price anomalies persist after the 2015 reform.
- Breedon & Ranaldo (SSRN 2099321): currencies depreciate in local business hours. QuantRocket's replication (EURUSD short
  03:00-11:00 NY, long 11:00-16:00 NY) shows a Sharpe of 0.70 net of IB costs.

**Markets and data:**
- Pairs: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD. The USD sign is s = +1 when USD is the base currency, −1
  otherwise.
- FTMO M15 bars, 2015-01 to 2026-10, converted server → UTC → Europe/London. 16:00 London is 11:00 NY except about 4 weeks a year
  (12:00 NY).
- Days: Mon-Fri, excluding 24 Dec-2 Jan.
- Prices: P1 = open of the 15:00 London bar, P2 = open of the 16:00 bar, P3 = open of the 17:00 bar.

**1A primary (after-fix reversal):**
- Trigger: |P2 − P1| ≥ 0.10 × ATR.
- Entry: at P2, against the USD move into the fix. If USD rose 15:00→16:00, sell USD.
- Target: half retrace, at P2 − 0.5 × (P2 − P1).
- Stop: P2 + sign(P2 − P1) × max(|P2 − P1|, 0.15 × ATR).
- Time exit: at P3.

**Other cells (all reported):**
- 1A thresholds 0.05 / 0.10 / 0.20 × ATR; 1A time exit at the 16:30 bar instead of P3.
- **1B (into-fix USD bid):** buy USD at P1 every day, exit at P2; stop 0.15 × ATR.
- **1C (session flip, EURUSD / GBPUSD / USDCHF):** buy USD at the 08:00 London bar open and exit at P2. Then sell USD at P2 and
  exit at the 21:00 London bar open (= 16:00 NY). Stops 0.5 × ATR.
- **1D (gold, LBMA PM auction 15:00 London = 10:00 NY):** run 1A and 1B on XAUUSD M1, with P1 = 14:00, P2 = 15:00, P3 = 16:00
  London. This is partly covered by the gold hour-of-day test (#11).

**Baselines:**
- (a) a coin flip at the same times;
- (b) a "fake fix": the identical rule at 14:00 and at 18:00 London.
- 1A must beat both by ≥ +0.05R.

**Statistics:**
- Day-clustered t-stats, because the 7 pairs share the USD leg.
- Expected n: 1A about 10,000 pair-trades over about 2,900 days.

**Ratings:** Credibility M-H, Testability H, Novelty H.

**Risk:** the FTMO FX commission (0.0025%/side ≈ 0.5 pip round trip on EURUSD) may eat a few-pip edge. 1C is likely about
+0.03R/trade at FTMO costs, so treat it as context.

### R2. Month-end hedge rebalancing at the 4 pm fix (rank 2)

**Sources:**
- Melvin & Prins, "Equity hedging and exchange rates at the London 4 p.m. fix" (Journal of Financial Markets, 2015; cited from
  memory, not fetched). Foreign holders of US equities re-hedge at month end, so when US stocks outperformed, USD is sold at the
  month-end fix.
- Ito & Yamada (w22820): calendar effects around fixes.

**Pairs and index legs:** EURUSD vs EU50.cash; GBPUSD vs UK100.cash; USDJPY vs JP225.cash; AUDUSD vs AUS200.cash. The US leg is
US500.cash. Use FTMO D1 closes (2018+; AUS200 2019+).

**Signal:**
- T = the last London business day of the month. M0 = the last server day of the previous month.
- rel = ln(US500[T−1] / US500[M0]) − ln(Idx[T−1] / Idx[M0]).
- rel ≥ +2%: sell USD against that currency.
- rel ≤ −2%: buy USD.
- Otherwise: no trade.

**Trade:**
- Entry: open of the 15:00 London M15 bar on day T.
- Exit: open of the 16:15 London bar.
- Stop: 0.3 × ATR.

**Cells:**
- Thresholds 0 / 1 / 3%.
- Entry at 14:00 London.
- Exit at 16:00 or 17:00 London.
- December reported separately.

**Baselines:** (a) the same direction at the same time on T−5..T−1; (b) a coin flip on T.

**Expected n:** about 420 at a 0% threshold (105 months × 4 pairs); perhaps half that at 2%.

**Ratings:** Credibility M-H, Testability H, Novelty H. A low-frequency diversifier, about 3-4 trades a month.

### R3. Tokyo 9:55 fix (仲値) and gotobi (五十日) USDJPY (rank 3)

**Sources:**
- Japanese retail practice: the 仲値トレード ("nakane trade": buy USDJPY into the Tokyo fix, especially on gotobi days).
- Ito & Yamada, NBER w22820: customer orders predictably buy foreign currency at the Tokyo fix, and there are calendar effects.
- FTMO's EURUSD trader's best hour is the Tokyo morning.

**Clock and calendar:**
- JST (UTC+9, no DST). FTMO M15, 2015+. 09:00 JST = 00:00 UTC = 02:00 or 03:00 server time.
- Business days: Mon-Fri, excluding Japanese holidays (python `holidays`, JP) and 31 Dec-3 Jan.
- Gotobi: the 5th, 10th, 15th, 20th, 25th and last day of the month. If that day is a holiday or weekend, use the business day
  before it.

**3A primary:**
- Days: gotobi days only.
- Entry: buy USDJPY at the open of the 09:00 JST bar.
- Exit: open of the 09:45 JST bar.
- Stop: 0.25 × ATR.

**Other cells:**
- **3B:** the same trade on every business day.
- **3C (after-fix reversal):** sell USDJPY at the 10:00 JST bar open, exit at the 11:00 bar open; run on gotobi days and on all
  days.
- Report also: EURJPY, GBPJPY and AUDJPY bought, and EURUSD/GBPUSD sold (USD bid), at the same times.

**Baselines:**
- 3A minus non-gotobi days;
- a coin flip;
- a fake window at 11:00-11:45 JST.

**Expected n:** 3A about 850; 3B about 2,900.

**Ratings:** Credibility M, Testability H, Novelty H.

**Risk:** the effect may have shrunk since the 2010s, and Tokyo-morning spread plus commission is about 1.2 pips. Report results
by year.

### R4. Unger DAX bias systems (rank 4)

**Sources:**
- Unger Academy "Strategy of the Month, June 2025" (FDAX): long only Mon-Wed; "Orders are triggered at the highest high of the
  last 16 bars"; window about 16:00-22:00; "closes all open positions by the end of Wednesday"; average trade about €600, backtest
  from 2010.
- "Trading DAX futures: €122,000 in 2 years" (Intraday Bias): buy at 17:15, exit at 09:00 the next day. Since Apr 2021: 173 trades,
  56% winners, more than €38,000 on one FDAX contract.
- Both are published *winners* among many systems, so selection bias applies.

**4A (early-week afternoon breakout):**
- Data: GER40.cash; M15 built from M5 on the Europe/Berlin clock (intraday since 2022).
- Entry days: Monday, Tuesday, Wednesday.
- Order window: bars opening 16:00-21:30 Berlin (≈ 10:00-15:30 NY).
- Order: when flat, place a buy stop at HH16, the highest high of the previous 16 M15 bars (a continuous series, so Monday's
  first bars look back into Friday). Fill at HH16, or at the bar's open if it opens above. At most 1 entry per day; positions
  never stack.
- Exit: market at 21:59 Berlin on Wednesday, or at the stop.
- Stop: 1.0 × ATR below the entry (cell: 0.5 × ATR). Swaps are charged.
- Cells: EU50.cash and FRA40.cash on the same clock; US500/US100 with the window set to the last 4 cash hours (12:00-15:45 NY)
  and the exit at 15:55 NY on Wednesday.
- Baselines: the same rule entering Thu-Fri (exit Friday 21:59); random entry times Mon-Wed with the same exit; always long from
  Monday 16:00 to Wednesday 21:59.
- Expected n: about 200-250.

**4B (evening-to-morning bias):**
- Entry: buy GER40 at the open of the 17:15 Berlin bar, Mon-Thu.
- Exit: open of the 09:00 Berlin bar the next day.
- Stop: 1.0 × ATR.
- Baselines: the same holding length from 09:15 and from 22:00; a coin flip.
- Expected n: about 1,000.
- Note: this is the first DAX test of the overnight idea (#6 was US-only and DEAD).

**Ratings:** Credibility M, Testability H, Novelty H.

### R5. Momentum-leader breakout (rank 5)

**Sources:** Kullamägi's "3 timeless setups" (breakout); Luk's lineage (USIC 2025, verified statements).

**Universe and data:** the 30 FTMO US stock CFDs. D1 (2019-20+; AAPL/MSFT 2007) for the setup; M5 (2020-22+) for the entry.

**Filters as of yesterday's close (t−1):**
- **F1 (prior move):** the largest of the 21-, 63- and 126-day returns is ≥ +30%.
- **F2 (trend):** C > SMA10 > SMA20, and SMA20 > SMA20 five days earlier.
- **F3 (orderly consolidation, the last 10 sessions):** high-low range ≤ 2.5 × ATR14; min Low(t−5..t−1) ≥ min Low(t−10..t−6);
  C(t−1) ≥ 0.90 × max High(t−10..t−1).
- **Pivot** = max High(t−10..t−1).

**Entry on day t:**
- ORH5 = high of the first M5 bar of the session (09:35-09:40 NY since FTMO's 2024 change).
- Buy at the first move above max(Pivot, ORH5), between the end of the first bar and 15:00 NY.

**Stop:** the low of the day up to entry (LOD). Skip the trade if entry − LOD > 1.0 × ATR14.

**Exits:**
- At the close of day 3: sell 1/3 if above entry, then move the stop to entry.
- The rest exits at the first close below SMA10 (cell: SMA20).
- Maximum hold 60 sessions.

**D1-only cell (for the longer history):** buy stop at the Pivot; stop 1 × ATR14; same exits.

**Baselines:** (a) random entry days with F1+F2 true and the same exits; (b) a plain 10-day-high break without F3.

**Ratings:** Credibility M-H, Testability M (expected n about 100-300), Novelty H.

**Notes:**
- Kullamägi risks 0.25-1%/trade.
- FTMO Swing leverage is 1:1 on stocks, so a 3% LOD stop at 0.5% risk is about 17% of the balance per position. Cap at 4 open
  positions.

### R6. Momentum pullback, "undercut and reclaim" (rank 6)

**Sources:** Luk ("buy weakness in strength"; flush below support, then a reclaim; stops 1-4%; 9-EMA trail) and Kell (EMA
crossback: the first pullback to the rising 10/20 EMA).

**Universe:** the same 30 stocks, D1.

**Filters at t−1:**
- 63-day return ≥ +30%, or 126-day return ≥ +50%.
- EMA9 > EMA21 > SMA50.
- EMA21 rising (above its value 5 days earlier).

**Setup on day t:** Low(t) < min(Low(t−1), EMA21(t−1)), AND Close(t) > max(Low(t−1), EMA21(t−1)), AND Close(t) ≥ Open(t).

**Entry:** at day t's close (the 15:55 NY M5 bar, or the D1 close).

**Stop:** Low(t). Skip if the stop is more than 4% below the entry.

**Exit:** the first close below EMA9 (cell: EMA21), or the stop. Maximum hold 40 sessions.

**Baselines:** (a) the same filters, entering at the close on random days; (b) a plain touch of EMA21 without the undercut.

**Ratings:** Credibility M-H, Testability M-H, Novelty M-H. The lab's pullback tests (#36, Holy Grail #54/#71) ran on gold and
indices, never on momentum-selected stocks.

### R7. Night FX-cross mean reversion (rank 7)

**Sources:** the Myfxbook night-scalper EAs (Night Hunter Pro, Evening Scalper Pro, Starlight, Viper), and the ATC 2006 winner
Rich's flat-market logic with Bollinger-width monitoring.

**Pairs:** EURGBP, EURCHF, AUDCAD, AUDNZD, NZDCAD, EURCAD, GBPCAD, GBPCHF, EURAUD, USDCHF, EURUSD, GBPUSD. M15, 2015+, NY clock.

**Signal window:**
- Cell A (primary): bars opening 17:30-19:45 NY (00:30-02:45 server), after the rollover spread spike and before Tokyo.
- Cell B: 17:30-23:45 NY.
- Cell C: 15:30-16:45 NY.

**Long entry:** Close < lower Bollinger Band (20, 2.0) AND RSI(14) < 30 → enter at the next open. Shorts are the mirror image.

**Filters:**
- BB width ≤ 1.5 × its median over the prior 500 bars (flat market only).
- The bar's spread ≤ 2 × the pair's median spread for that hour.
- No entries Friday after 15:00 NY or on the day before a US holiday.
- One position per pair; no re-entry in a pair after a stop that night.

**Exits:**
- Target: the BB middle (SMA20) at entry, as a fixed price.
- Stop: 2.5 × ATR(14, M15).
- Time exit: 02:00 NY (09:00 server).

**Baselines:** (a) random direction at the same times; (b) the identical rule during 08:00-11:45 NY (to show it is specific to
the night).

**Risk cap:** total night risk ≤ 1% across all pairs, because the pairs are correlated and the payoff has negative skew.

**Ratings:** Credibility L-M, Testability H, Novelty H. The lab tested Asian breakouts only, never night reversion.

### R8. Davey range-expansion momentum (rank 8)

**Source:** Kevin Davey's seminar entry "Momentum and Big Range: Go with momentum after big range" (ProRealCode transcript). His
contest system was "an x day breakout with oscillator confirmation".

**Data:** every export symbol. D1 on server days is the primary cell; H4 on the server clock and H1 are cells.

**Signal at bar t:** Range(t) = H − L. Range(t) > SMA20(Range)(t−1) + 2 × SD20(Range)(t−1), AND Close(t) > Close(t−10) → buy at
the next open. Shorts are the mirror image (Close(t) < Close(t−10)).

**Exits:**
- Stop: 1.0 × ATR20.
- Time exit: the close of the 5th bar (cells: 3 and 10 bars).
- No target.

**Baselines:** (a) a coin flip at the same entries; (b) the same exits after random bars.

**Ratings:** Credibility L-M, Testability H, Novelty H.

**Note:** gold's "busy market" filter (results.md) made breakouts worse, so expect a split by asset group.

### R9. Episodic pivot, multi-day (rank 9)

**Sources:**
- Kullamägi's EP: a 10%+ gap on news, heavy volume ("traded their average daily volume in the first 15-30 minutes"), entry at the
  opening-range high (ORH), stop at the low of the day, trailing on the 10/20-day MA.
- PEAD literature: Bernard & Thomas 1989 (cited from memory, not fetched).

**Universe:** the 30 stocks, M5 + D1.

**Signal on day t:**
- Gap(t) = Open(t)/Close(t−1) − 1 ≥ +max(8%, 2.5 × ATR14/Close(t−1)).
- The tick volume of the first 30 minutes ≥ 3 × its 20-day median for the same window.
- Not already extended: Close(t−1)/Close(t−63) − 1 ≤ +20%.

**Entry:** a buy stop at ORH5, live until 11:00 NY.

**Stop:** LOD at entry. Skip if the risk is more than 1.5 × ATR14.

**Exits:** 1/3 at the close of day 3 if in profit (stop then moved to entry); the rest at the first close below SMA10 (cell:
SMA20); maximum hold 60 sessions.

**Other cells:**
- Intraday only, out at 15:55 NY. This links to the stocks-in-play result #75, which was DEAD at −0.25R.
- Negative EP: short at ORL5 after a gap down of at least the mirrored threshold; stop at HOD.

**Baselines:** (a) all gaps above the threshold without the volume filter; (b) random days with the same exits.

**Ratings:** Credibility M-H, Testability M-L (expected n about 80-150), Novelty M-H.

### R10. Unger crude-oil false breakout with a low-volume filter (rank 10)

**Source:** Andrea Unger, Benzinga, May 2025.
- Optimised 2010-24 backtest: the base rule had 2,989 trades at $33 average.
- With volume filter length 15: 1,319 trades at $64.
- With the stop/target and "Pattern −8": $98 average and $12,750 maximum drawdown per CL contract.

**Data:** USOIL.cash M30 built from M5 (2021+); UKOIL.cash 2022+. The day is the server day (17:00-17:00 NY).

**Short setup:**
- The breakout bar i has High(i) > PDH (the prior server-day high).
- Its tick volume is below the mean of bars i−15..i−1.
- The next bar closes below PDH → sell at the following open.

**Pattern filter (an approximation of Unger's "Pattern −8"):** (day Open − day Low so far) ≤ 1.0 × (Open − Low) of the prior day.

**Long setup:** the mirror image at PDL, with the filter (High − Open) ≤ the prior day's (High − Open).

**Exits:**
- Stop: 0.5 × ATR. Target: 0.65 × ATR. These are Unger's $1,400 / $1,800 per CL contract at an ATR of about $2.8.
- Exit at 16:55 NY if neither is hit.
- At most one trade per side per day.

**Cross-checks, unchanged:** XAUUSD, XAGUSD, US500, GER40 on M30.

**Baselines:** (a) the same entries without the volume filter (= #45's sweep rule); (b) a coin flip.

**Ratings:** Credibility M-L (heavily optimised), Testability H, Novelty M.

### R11. Minervini Trend Template + VCP breakout (rank 11)

**Source:** Minervini, *Trade Like a Stock Market Wizard* (2013): the Trend Template, VCP, and the 7-8% maximum loss. USIC 1997
and 2021.

**Universe:** the 30 stocks, D1.

**Template at t−1 (all eight must hold):**
1. C > SMA150 and C > SMA200.
2. SMA150 > SMA200.
3. SMA200 > SMA200 of 21 sessions earlier.
4. SMA50 > SMA150 and SMA50 > SMA200.
5. C > SMA50.
6. C ≥ 1.30 × the 252-day low.
7. C ≥ 0.75 × the 252-day high.
8. The 126-day return minus US500's 126-day return is at or above the 70th percentile of the 30-stock universe (the RS ≥ 70
   proxy).

**VCP proxy (last 60 sessions):**
- Swings are 5-bar fractals.
- There are at least 2 successive pullbacks, each with depth ≤ 0.7 × the previous one, and the last depth is ≤ 10%.
- Mean tick volume of the last 10 sessions ≤ 0.8 × the mean of the prior 50.
- Pivot = the swing high before the last pullback.

**Entry:**
- A buy stop at pivot × 1.001.
- If the breakout day's tick volume is below 1.4 × SMA50(volume), exit at that day's close.

**Stop:** max(the last pullback's low, entry × 0.92).

**Exits:**
- Sell half at +20% and move the stop to breakeven.
- The rest exits at the first close below SMA50.
- Time stop: out at day 20 if the gain is below +5%.

**Baselines:** (a) the template alone, entering on random qualifying days; (b) HIGH52 from the battery.

**Ratings:** Credibility M (the trader's record is H, the proxy is uncertain), Testability M, Novelty M.

### R12. Parabolic short, and long (rank 12)

**Source:** Kullamägi's parabolic short: large caps up 50-100%+ in days or weeks; 3-5+ up days; short at the opening-range low
(ORL); stop at the high of the day; target the 10/20-day MA.

**Universe:** the 30 stocks plus the 7 crypto CFDs. D1 + M5.

**Setup at t−1:**
- At least 3 consecutive higher closes.
- Close − SMA10 ≥ 4 × ATR14.
- 5-day return ≥ max(+25%, 5 × ATR14/price).

**Short entry on day t:** at the ORL5 break (crypto: the 09:30 NY M5 bar), live until 12:00 NY.

**Stop:** HOD at entry.

**Exits:** target = SMA10 at entry; time exit at the close of day 5.

**Long cell:** at least 3 lower closes and SMA10 − Close ≥ 4 × ATR14 → buy at ORH5; stop at LOD; target SMA10.

**Baselines:** a coin flip; the opposite side.

**Ratings:** Credibility M, Testability M-L (rare events), Novelty H.

### R13. Unger gold "flat-day" prior-session breakout (rank 13)

**Source:** Unger Academy, "Intraday trading on gold". Since 2008: about 1,200 trades and about $202k net on 1 GC contract
(average $162). Claimed live since 2016. The exits were "monetary" and their values were not given.

**Data:** XAUUSD; M5 for signals and M1 for fills; 2015+; server day.

**Filter:** |C(d−1) − C(d−2)| ≤ 0.2 × ATR (cell: 0.3).

**Entry on day d:**
- A buy stop at H(d−1) and a sell stop at L(d−1). The first touch only; no reversal.
- Entries 18:00 NY to 16:00 NY.

**Exits:** stop 0.5 × ATR; exit at 16:55 NY.

**Baselines:** (a) the same rule on non-flat days; (b) correlation with the Williams volatility breakout (#50 WATCH).

**Ratings:** Credibility M, Testability H, Novelty L-M.

### R14. 18:00 NY reopen gap fade (rank 14)

**Source:** FTMO case studies. The US500 trader (662 trades, profits around 01:00 platform, almost all short) and the 5.59-RRR
gold trader (profits around 01:00 platform, mostly short). 01:00 server = 18:00 NY, the first bar after the daily
17:00-18:00 NY break.

**Markets:** US500, US100, US30 (M5) and XAUUSD (M1).

**Signal:** G = Open(18:00 NY) − Close(last bar before 17:00 NY). Trade if |G| ≥ 0.10 × ATR.

**Trade:**
- Entry: the next bar's open (18:05), toward the 16:55 close.
- Target: that close.
- Stop: |G| beyond the 18:00 open.
- Time exit: 20:00 NY.

**Report-only cell:** the sign of the 18:00-19:00 return, followed and faded, with no gap condition.

**Ratings:** Credibility L (two accounts; the platform-time clustering may just be the traders' own time zones), Testability H,
Novelty M-H (#11 covered gold's hour-of-day drift, not the reopen gap).

### R15. Korean "closing bet" 종가베팅 (rank 15)

**Sources:** Korean contest lore (no audited winner disclosure). The test is a falsification check. Lou, Polk & Skouras (2019,
"A tug of war"; cited from memory, not fetched) find that intraday and overnight returns pull in opposite directions across US
stocks, so a strong close need not carry overnight.

**Universe:** the 30 stocks, M5.

**Signal at 15:50 NY on day t (all three):**
- The return since yesterday's close ≥ +3% (cells: 2% and 5%).
- (P − Low(t)) ≥ 0.9 × (High(t) − Low(t)).
- Tick volume from the open to 15:50 ≥ 1.5 × its 20-day median.

**Trade:**
- Entry: buy at the 15:55 bar's open.
- Exit: the 10:00 NY bar's open next session (cell: the first bar).
- Stop: 1 × ATR14, live from the next open. One swap is charged.

**Baselines:** (a) the same-time close of random stocks; (b) the weak-close mirror.

**Ratings:** Credibility L, Testability H, Novelty M (#6 tested overnight holds unconditionally).

## 5. Mechanical, but already tested in the lab (not repeated above)

| Method (trader) | Lab entry | Status |
|---|---|---|
| Volatility breakout; Oops (Williams 1987) | #50 / #71, #51 | gold WATCH; Oops DEAD / blocked |
| COT, seasonality (Williams; Bernd) | #82 (running), #64 | seasonality WATCH as a filter |
| Turn of month / TDOM (Williams) | #4 | DEAD |
| Donchian / x-day breakout trend following (Davey's contest style; CN quant-group CTAs) | #9, #68, #75 (#37 Clenow, #39 exit grid) | DEAD after costs and swaps (one crypto WATCH) |
| Unger DAX first-hour range breakout, with a skip after big trend days | ≈ ORB60 in the battery (#68) | DEAD per symbol; the trend-day filter itself was never tested (could be a cell of ORB) |
| Unger S&P intraday reversal at the prior-day low; live-cattle false breakout | ≈ Oops (#51), Turtle Soup (#52), PDH sweep (#45) | DEAD |
| Unger S&P "day drop" (bearish close in the bottom 20% → buy) | ≈ IBS (#24, #26c) | WATCH |
| Unger gold Supertrend; DAX Bollinger multiday | #26b; #33 / #75 squeeze | DEAD |
| Unger gold/DAX time-of-day bias | #11 (gold hour-of-day) | DEAD for gold; the DAX version is new (R4) |
| Dual Thrust; R-Breaker (CN CTA classics) | #75 | US100 marginal CANDIDATE; R-Breaker DEAD |
| Hans123, 菲阿里四价 (four-price), 空中花园 (gap + first-bar break) | ≈ ORB / prior-day breakouts / GAPgo (#68, #81) | DEAD |
| BNF 25-day-MA deviation | ≈ RSI2 / IBS / Double 7s (#24, #55) | WATCH / DEAD |
| Stocks in play, 5-minute opening range (≈ EP intraday) | #75 | DEAD (−0.25R) |
| Kell EMA crossback on indices / gold | ≈ Holy Grail (#54, #71) | DEAD; the stock version is R6 |

## 6. Not mechanizable, or not testable with OHLC + tick volume + spread

- Michael Cook's TICK-based tools (needs NYSE TICK).
- Order-flow scalping (needs an order book).
- Bakaramura's and 林波's fundamental/sentiment calls.
- Minervini/CAN SLIM earnings criteria (no fundamentals; R11 is the price-only proxy).
- Option strategies of Unger Academy, Chuck Hughes and others.
- ATC 2007/2010 EA internals (undisclosed).
- FX carry plus trend, as in FTMO's positive-swap swing trader. This needs a history of swap or policy rates; the export carries
  only today's swaps (log #64).

## 7. Sources

**FTMO**
- [Successful Traders Stories (index)](https://ftmo.com/en/blog/category/successful-traders-stories/)
- [What consistent trading looks like](https://ftmo.com/en/blog/ftmo-traders-analysis-what-consistent-trading-looks-like/)
- [Losses are part of profitable trading](https://ftmo.com/en/blog/ftmo-traders-analysis-losses-are-part-of-profitable-trading/)
- [Different paths to great results](https://ftmo.com/en/blog/ftmo-traders-analysis-different-paths-to-great-results/)
- [Less is sometimes more](https://ftmo.com/en/blog/ftmo-traders-analysis-less-is-sometimes-more/)
- [Gold scalper $50,333](https://ftmo.com/en/blog/how-a-gold-scalper-secured-50333-in-2-weeks/)
- [Machine-like scalper](https://ftmo.com/en/blog/the-machine-like-scalper-a-24-5-return-in-12-days-on-gold/)
- [US100 sniper](https://ftmo.com/en/blog/nearly-40000-in-two-weeks-how-a-sniper-scalper-mastered-us100/)
- [Index scalping 77%](https://ftmo.com/en/blog/massive-77-08-win-rate-prime-trader-earns-27175-through-precise-index-scalping/)
- [EURUSD 32%](https://ftmo.com/en/blog/under-two-trades-a-day-delivered-a-32-return-on-eurusd/)
- [High RRR $93,168](https://ftmo.com/en/blog/high-rrr-in-action-how-patience-delivered-a-93168-profit/)
- [Precious metals](https://ftmo.com/en/blog/precious-metals-masterclass-a-20-gain-in-just-9-trading-days/)
- [Swing trader $56k](https://ftmo.com/en/blog/a-swing-trader-overcame-a-month-long-drawdown-to-secure-over-56000/)
- [US500 trader](https://ftmo.com/en/blog/how-a-us500-trader-secured-27734-despite-heavy-drawdowns/)
- [5.59 RRR](https://ftmo.com/en/blog/the-power-of-a-5-59-rrr-a-31253-profit-built-on-a-28-win-rate/)
- [CoinLaw FTMO statistics](https://coinlaw.io/ftmo-statistics/)
- [FTMO (OANDA) trader page](https://ftmo.oanda.com/?p=2629)

**Prop-firm base rates**
- [Fortunly pass rates](https://fortunly.com/statistics/prop-firm-challenge-pass-rate-statistics/)
- [AlphaExCapital Topstep review](https://www.alphaexcapital.com/prop-trading/topstep-review)
- [Finance Magnates: FPFX 300k accounts](https://www.financemagnates.com/forex/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts/)
- [Finance Magnates: FundedNext Feb 2026](https://www.financemagnates.com/forex/analysis/prop-firm-fundednext-says-it-paid-1519m-to-8340-traders-in-february/)
- [CoinGape 93% report](https://coingape.com/blog/93-of-funded-prop-traders-never-see-a-payout-a-new-report-explains-why/)

**Robbins World Cup**
- [ireallytrade hall of fame](https://ireallytrade.com/halloffame)
- [CTE World Cup table](https://completetradersedge.com/world-cup-trading-championships/)
- [CTE Larry Williams](https://completetradersedge.com/larry-williams-11376-percent-trading-record/)
- [CTE Kevin Davey](https://completetradersedge.com/?p=235275)
- [Van Tharp: Davey, part 1](https://vantharp.com/Weekly_update/Weekly_258_Feb_15_2006.htm)
- [Van Tharp: Davey, part 2](https://vantharp.com/Weekly_update/Weekly_259_Feb_22_2006.htm)
- [ProRealCode: 5 Davey entries](https://www.prorealcode.com/topic/5-entries-from-kevin-davey/)
- [Michael Cook podcast](https://sites.libsyn.com/66295/039-interview-with-michael-cook)
- [Substack: World Cup / Robbins](https://quantamentaltrader.substack.com/p/world-cup-trading-championship-and)
- [Bloomberg Línea: Scherman (results)](https://www.bloomberglinea.com/2024/01/17/el-campeon-mundial-en-trading-de-futuros/)
- [Bloomberg Línea: Scherman (interview)](https://www.bloomberglinea.com/latinoamerica/argentina/el-campeon-mundial-en-trading-de-futuros-es-argentino-y-estos-son-sus-secretos/)
- [MQL5: Teregulov](https://www.mql5.com/en/forum/412370/37077251)

**Andrea Unger**
- [Unger on Benzinga: crude-oil false breakout](https://www.benzinga.com/trading-ideas/technicals/25/05/45202553/is-the-false-breakout-strategy-worth-using-on-crude-oil-futures)
- [DAX bias + trend (June 2025)](https://ungeracademy.com/?p=8068)
- [DAX €122,000](https://ungeracademy.com/blog/trading-dax-futures-eur122-000-in-2-years-with-these-strategies-explanation-rules)
- [Gold intraday](https://ungeracademy.com/blog/intraday-trading-on-gold-usd37-000-of-gain-in-2-years-with-these-strategies-rules-details)
- [Gold Supertrend / high-low](https://ungeracademy.com/blog/gold-futures-trading-strategies-supertrend-and-high-low-breakout-techniques-usd80-000-gained-in-2023-and-2024)
- [S&P reversal](https://ungeracademy.com/blog/s-and-p-500-strategies-intraday-reversal-multiday-pattern-with-performance)
- [Gold reversal (Aug 2025)](https://ungeracademy.com/?p=8581)
- [6 student strategies](https://ungeracademy.com/?p=6734)
- [Michael +258%](https://ungeracademy.com/?p=6951)
- [2025 performance](https://ungeracademy.com/blog/2025-trading-performance-real-returns-lessons)
- [Overnight vs intraday](https://ungeracademy.com/blog/overnight-or-intraday-trading)
- [DAX first hour](https://ungeracademy.com/blog/dax-first-hour-strategy-last-year-performance)

**US Investing Championship**
- [CTE research sheet (PDF)](https://completetradersedge.com/wp-content/uploads/2026/09/CTE-Research-Sheet-US-Investing-Championship-2.pdf)
- [CTE real-money records](https://completetradersedge.com/?p=234478)
- [Qullamaggie's 3 setups](https://qullamaggie.com/my-3-timeless-setups-that-have-made-me-tens-of-millions/)
- [TraderLion: Kell EMA crossback](https://traderlion.com/technical-analysis/trading-the-ema-crossback/)
- [FinancialWisdomTV: Luk](https://www.financialwisdomtv.com/post/martin-luk-s-pullback-trading-strategy-how-the-2025-u-s-investing-champion-finds-low-risk-high-re)

**MetaQuotes ATC**
- [MetaQuotes 2007 results](https://www.metaquotes.net/en/company/news/3504)
- [MQL5 article 1552](https://www.mql5.com/en/articles/1552)
- [MQL5 article 1550](https://www.mql5.com/en/articles/1550)
- [Better interview](https://www.mql5.com/en/articles/545)
- [Better's analytical report](https://www.mql5.com/en/forum/105866)
- [Odintsov](https://www.mql5.com/en/forum/5390)
- [ATC 2008](https://www.metatrader4.com/es/company/74)
- [ATC 2006](https://www.metatrader5.com/pt/news/1349)
- [Baruch: Alonso](https://mfe.baruch.cuny.edu/baruch-mfe-student-jp-alonso-second-place-in-the-metaquotes-automated-trading-championship-2012/)
- [Comparic: Materov](https://comparic.pl/wywiad-z-alexeyem-materovem-zdobywca-3-miejsca-w-mistrzostwach-automatycznego-tradingu-2012/)

**FX fixes**
- [NBER w21518](https://www.nber.org/papers/w21518)
- [NBER w22820](https://www.nber.org/papers/w22820)
- [NBER w23327](https://www.nber.org/papers/w23327)
- [QuantRocket: Breedon-Ranaldo replication](https://quantrocket.com/blog/business-day-fx-patterns/)
- Krohn-Mueller-Whelan (Journal of Finance 2024), Melvin-Prins (Journal of Financial Markets 2015), Bernard-Thomas (1989) and
  Lou-Polk-Skouras (2019): cited from memory, not fetched.

**Night scalpers**
- [NYC Servers: Night Hunter Pro review](https://newyorkcityservers.com/blog/night-hunter-pro-review)
- [NYC Servers: mean-reversion EAs](https://newyorkcityservers.com/blog/best-forex-mean-reversion-eas-robots)

**China**
- [Huatai report (fxbaogao)](https://www.fxbaogao.com/detail/5459868)
- [同花顺 (10jqka): 林波](https://news.10jqka.com.cn/20260901/c679482552.shtml)
- [格隆汇 (Gelonghui): quant group](https://m.gelonghui.com/p/6812780)
- [Sina: 丁伟锋](https://finance.sina.cn/futuremarket/qszx/2020-11-22/detail-iiznezxs3062835.d.html)

**Japan and Korea**
- [Zai FX: Bakaramura result](https://zai.diamond.jp/articles/-/284826)
- [Zai FX: Bakaramura trades](https://zai.diamond.jp/articles/-/288443)
- [Gaitame: Bakaramura](https://www.gaitame.com/media/entry/2023/12/01/113000)
- [Hankyung: Kiwoom contest](https://www.hankyung.com/article/2025021171266)
- [Hankyung: Star Wars winner](https://www.hankyung.com/amp/2026070565251)
- [Etoday: Halstatt](https://www.etoday.co.kr/news/view/292521)
