# Bernd Skorupinski's four TradingView indicators: web research

Date: 2026-10-10. Scope: COT, Valuation Tool, True Seasonality, UnFilled Order (UFO) supply & demand,
plus the Larry Williams and seasonal-research formulas they descend from.
Method: WebSearch + WebFetch only, plus a narrow cross-check against the local auto-caption
transcripts in `/home/claude/data/bernd_tx/` (marked **[TX]**; other drafts cover those in full).

**Confidence scale**

- **High**: stated by Bernd (his site, his TradingView pages, his own words on video) or by a primary
  source (Larry Williams' own site or plug-in docs, MRCI's own FAQ).
- **Medium**: a secondary source that cites a book page, or several independent clones that agree.
- **Low**: one unverified secondary source, a clone's marketing claim, or my inference.

**Access limits (affect what could be verified)**

- bernd-skorupinski.com and tradingview.com are readable only through WebFetch (curl gets a proxy 403),
  so the chart screenshots (which carry the status-line inputs) could not be read.
- Invite-only scripts publish no code. WebFetch does not render the code of open-source clones either.
- archive.org is blocked, Reddit was skipped, and YouTube's RSS is robots-disallowed.
- The shared WebSearch budget ran out near the end, so Jake Bernstein's method and MRCI's
  strategy-selection criteria were not verified.

---

## 0. Verdict on the current reconstruction

| Item | Current reconstruction | Verdict | Conf. |
|---|---|---|---|
| Valuation references | DXY, ZB1!, GC1! | **Confirmed.** These are the site's reference set and the defaults of every clone. His colours: purple = dollar, yellow = gold, blue = T-bonds [TX]. | High |
| Valuation thresholds | -0.75 / +0.75 | **Confirmed** on a ±1 scale: the site reads "undervalued under -0.75 level". Clones use ±75 on a ±100 scale. | High |
| Valuation core | s = EMA10(ln A − ln B), min-max to [-1,+1] over 480 days | **Structure probably wrong.** Every description (Bernd's "price deviation", Williams' "performance vs a benchmark", all clones) measures relative *change or deviation*, not the relative *level*. The meaning of 480 and 10 is unconfirmed; the site names the two numeric inputs "timeframe" and "smoothing value". | Medium |
| True Seasonality | 15, 30 | **Probably 15 = lookback in years, 30 = forecast bars.** He says "this is a 15 years ... forecast, looking at 15 years historical data" [TX], and the site lists "Adjustable forecast bars & lookback". He stresses that it aligns on **trading days, not calendar days** [TX]. | Medium |
| COT | 157-week index, 20/80 | **Confirmed, but only as his maximum lookback.** He reads **4 lookbacks (6 months, 1, 2 and 3 years)** of raw net positions, with 20/80 extremes; "three years ... that's the maximum that I look at" [TX]. | High |

---

## 1. Who publishes the indicators

| Finding | Source | Conf. |
|---|---|---|
| All four tools are TradingView invite-only scripts. After purchase they appear under the "Invite-Only" tab. Pricing: $49 one-month trial, or $249 "Lifetime Full Access" (6 modules, 28 materials). The course is delivered over Telegram. Both bundles include "4 COT indicators" plus Seasonality, Valuation and Unfilled Order. | https://bernd-skorupinski.com/ (FAQ and pricing) | High |
| The TradingView account is **TTMs_** (Premium, joined 21 May 2025). The "Valuation Tool", "True Seasonality" and "UnFilled Order Candle" script pages all send access requests to TTMs_, and their text copies the site word for word. No COT script by TTMs_ was found; it may be unlisted. | https://www.tradingview.com/u/TTMs_/ · https://it.tradingview.com/script/CC7qsxvi-Valuation-Tool/ · https://it.tradingview.com/script/J3706PII-True-Seasonality · https://it.tradingview.com/script/aWOAvqvY-UnFilled-Order-Candle/ | Medium-High |
| Bernd founded Online Trading Campus (OTC) in 2017. The 2023 versions were called "campus valuation tool", "smart money index with the COT index" and "seasonal/campus algo forecasting tool", and **ran on TradeStation**: "our indicators right they run on trade station". The TradingView versions date from 2025 (site images uploaded 2025/06–07). | https://onlinetradingcampus.com/ · [TX] `20230930_Why_I_Risked_6__on_ONE_Direction____200K_Challenge__Week_2_.txt`, `20230408_The__1_Hour_A_Day__Trading_Routine_That_Works.txt` | High |
| No user guide, PDF, blog post or FAQ on the indicators' maths exists on his site. The pages carry only marketing text and example screenshots. | the four indicator pages (section 2–5 URLs) | High |

---

## 2. Valuation Tool

### 2.1 Bernd's own description

Source: https://bernd-skorupinski.com/valuation-tool-indicator/ (the same text appears at https://tw.tradingview.com/script/CC7qsxvi-Valuation-Tool).

- **Purpose.** It judges relative value by measuring "price deviation" between chosen assets and is "used primarily to identify overbought and oversold conditions". **High**
- **Pairings.** "Equities and indices" are compared to the **Treasury Bond and the Dollar Index**. "Major FX pairs, precious metals and energies" are compared to the **Dollar Index**. **High**
- **Inputs.** The page lists three symbols, each of which can be shown or hidden, plus "threshold (lower and upper), timeframe, and smoothing value". The smoothing value is there "to reduce noise". **High**
  - Mapping these names onto the screenshot string `DXY, ZB1!, GC1!, 480, -0.75, 0.75, 10` by elimination gives timeframe = 480 and smoothing = 10. This is my inference. **Low-Medium**
- **Example.** On NASDAQ, both the Dollar Index line (blue) and the Treasury Bond line (orange) were "undervalued under -0.75 level". A Supply & Demand entry then ran "more than 1:3". **High**
- **Use.** "Best applied on weekly or daily charts". It is not a stand-alone signal; entries come from lower-timeframe tools such as supply and demand. **High**

### 2.2 How he reads it (his own words, [TX])

- **Indices vs T-bonds is the key test.** "for the equity indices the valuation tool is the most important tool ... every time we undervalued versus the treasury bonds this is a big big Buy Signal". Being undervalued "versus all three assets" (dollar, gold, bonds) marks "the bottoms". Source: `20230930_..._Week_2_.txt`. Also NASDAQ vs bonds on a daily chart in `20230309_The_NASDAQ_Trade_That_Made_Me__66_000.txt`, and NASDAQ "undervalued ... ZB1, 30-year Treasury bonds" in `20260731_I_Just_Bought_The_Nasdaq..._Here_s_My_EXACT_Trade..txt`. **High**
- **Gold vs the dollar, daily.** "close to the green horizontal line which means undervalued ... close to that red horizontal line we're overvalued versus dollar" (`20230930_...`). **High**
- **Platinum vs the dollar, as an exit.** He exits "once price gets overvalued versus the dollar" (`20230926_I_Documented_Every_Trade_of_My__200K_Challenge___Week_1.txt`). **High**
- **Silver vs gold.** "we are overvalued versus gold" (`20240602_Why_I_m_Shorting_Silver_Right_Now__Full_Breakdown_.txt`). **High**
- **Swiss franc vs gold.** "everything above that red horizontal line means strongly overvalued versus gold" (`20230529_How_I_Got_Funded__1_Million__Full_Breakdown_.txt`). **High**
- **How he uses it.** He uses valuation as a bias filter and as an exit or trailing trigger. Valuation, COT and seasonality agreeing makes an "All Stars aligned" (3/3) setup. **High**

### 2.3 Clones that claim to copy him, or that clearly copy the concept

| Script | What it says it computes | Defaults | Source | Conf. |
|---|---|---|---|---|
| "OTC valuation indicator 2.0" (Nikhichuanhal655, 2 May 2025, invite-only, "inspired by Bernd Skorupinski's methodology") | Normalised index of the **percentage price deviation** between the asset and a reference. A moving average serves as the "fair value" baseline, with a volatility-adjusted smoothing filter. | Below **-75** = strong undervaluation. Length **13 on weekly** for reversals, **10 or 30** with the trend. GC1! vs DXY example. | https://www.tradingview.com/script/KMCxhuN7-OTC-valuation-indicator-2-0 | Medium |
| "RSV % Change — Legacy Edition" (Gumroad, claims "Built exactly on Bernd Skorupinski's original framework") | % change over Length for the asset and the benchmark; their spread is normalised over a rolling lookback to 0–100, then recentred to −100..+100. | ±75. Benchmark DXY by default; bonds, gold and BTC available. | https://rwb195.gumroad.com/l/souco | Low-Medium (marketing) |
| "Valuation" (dinisfranco2006, **open source**) | "Relative Difference = Symbol % Change − Benchmark % Change", rescaled over a longer rolling window to −100..+100. | **Lookback 10**, **rescale window 100**, DXY / GC1! / ZB1!, ±75. | https://es.tradingview.com/script/3XoNi1Ap-Valuation | Medium |
| "Valuation Tool" (leoguia777, closed source) | % change over a Period Length for the asset and 3 comparisons; asset minus benchmark; "Rescale Function" to −100..+100. | Rescale Length **100**, DXY / Gold / 30Y bonds, ±75. | https://www.tradingview.com/script/fbTEOCZC/ | Medium |
| "COT Index + COT Report + Valuation Tool + Seasonality" (leoguia777) | A four-in-one copy of the OTC toolset. | Valuation defaults DXY, Gold, Bonds. | https://www.tradingview.com/script/h3Rqq38f/ | Low |
| "Asset Valuation Tool" (DOSALGO, invite-only) | Asset ÷ benchmark ratio, then a "modified RSI" of that ratio, rescaled to −100..+100. | **Lookback 10**, lines at ±75, bonds / gold / DXY. | https://www.tradingview.com/script/fuZmc54y-Asset-Valuation-Tool/ | Medium |
| "Swing Elite Valuation Tool" | A ratio normalised as a % move from a baseline, on a 0–100 scale. | 88+ overvalued, <10 undervalued; ZB1 / DXY / GC1. | https://ru.tradingview.com/script/3r7KMf7x-Swing-Elite-Valuation-Tool | Low |

**Consensus of the clones.** They measure relative performance over a short window (about 10 bars) and min-max rescale it over a longer window to ±100, with ±75 extremes. None uses the relative price level.

### 2.4 Larry Williams' Valuation index ("WillVal", 1990)

- **Origin.** Larry dates WillVal to 1990 and describes it as "Another revolutionary indicator to tell when a commodity is over/under valued". No formula is given. https://futures.ireallytrade.com/innovation/ **High**
- **Official Larry Williams plug-in for StockCharts (stocks).**
  - It compares "performance to a benchmark over time". Benchmark = **TLT, GLD or UUP** (bonds, gold, dollar).
  - **Lookback 65 periods** by default. "By default, the upper (overvalued) line is set at 75 and the lower (undervalued) line is set at 15."
  - Buy when the value crosses back above the lower line. Daily or weekly charts.
  - Source: https://help.stockcharts.com/charts-and-tools/stockchartsacp-plug-ins/larry-williams-stock-trading-starter-pack-plug-in **High** for the defaults; the formula is not given.
- **The most specific published recipe**, quoted as internet text in a 2017 ProRealCode thread. It matches Williams' style but is unattributed. Source: https://www.prorealcode.com/topic/wiil-val-indicator (also https://www.prorealcode.com/reply/51351/). **Medium**
  - "Divide the price of any commodity by the price of Gold ... multiply this by 100 to normalize."
  - "a 2 week or 2 period exponential average" and "a 22-week average or 22-period exponential", with the remark "It does not make much difference which mathematical formula you use."
  - Pal = EMA2 − EMA22 (the text says "subtract the 2 period averages from the 22 period averages", but the code uses EMA2 − EMA22).
  - WillVal = 100 × (Pal − lowest Pal of last 3 years) / (highest − lowest of last 3 years), on a **weekly** chart.
  - The ProRealCode version plots reference lines at **75 / 15**.
- **Same structure in other platforms.**
  - MQL5 "WILL_VAL": `WV = 100*(Value-Min)/(Max-Min)`, `Value = EMA(Price,p1) − EMA(Price,p2)`, `Price = Close(current)/Close(Instrument)`. https://www.mql5.com/en/code/22099 **Medium**
  - NinjaTrader forum WillVal: Spread = (A−B)/(A+B)×100, Pal = SMA1 − SMA2, then Williams %R of Pal. https://forum.ninjatrader.com/forum/ninjatrader-7/indicator-development-aa/67756-willval?p=622639 **Low**
- **tradeviZion "Larry Williams Valuation Index" (open source).** Ratio×100, short EMA − long EMA, min-max to 0–100. **85 / 15** manual levels. Default symbols TVC:DXY, COMEX:GC1!, CBOT:ZB1!.
  - Lookback was 156 bars ("weekly, ~3 years"). The V2 notes cut it to **26 bars**: Larry "in his current seminars ... uses 26 bars, about six months on weekly charts".
  - Source: https://ru.tradingview.com/script/dKwos20x-Larry-Williams-Valuation-Index-tradeviZion **Medium** (secondary claim about the seminars)
  - Another open-source variant (QiwEE23w) adds a sector ETF for stocks and uses a 156 lookback with 85/15: https://www.tradingview.com/script/QiwEE23w/ **Low**
- **Related: Williams' "Will-Spread".**
  - *Long-Term Secrets to Short-Term Trading*: EMA5 − EMA20 of 100×A/B, via https://www.tradingview.com/script/Rak6df4K/. **Medium**
  - *Trade Stocks & Commodities with the Insiders*, p.155: "subtracting 21 and 3 ma", via https://www.tradingview.com/script/jHwRQXBE-Normalized-Willspread-Indicator/. **Medium**
- **Which comparison market for which asset (Williams).**
  - Commodities vs **gold** (ProRealCode recipe).
  - Stocks vs **T-bonds, gold, dollar** (StockCharts plug-in).
  - Bonds read against gold: "I want the relationship between bonds and, let's say, gold, to be giving me the signal" (S&C interview, July 1997, https://traders.com/Documentation/FEEDbk_docs/1997/07/0797Williams.html).
  - **Medium**

**Takeaway.** Williams' WillVal is a *momentum of the ratio* (short EMA minus long EMA of A/B), stochastic-normalised over a long window. Bernd's tool and its clones are the same idea in ±1 / ±100 form. None of the sources uses the level of ln(A/B).

---

## 3. COT ("4 COT indicators")

### 3.1 Bernd's own description

Source: https://bernd-skorupinski.com/cot-commitment-of-traders-indicator/

- **Components.** "COT Index, COT Commercial Net Position, COT Non-Commercial Net Position, COT Non-Reportable Net Position". These are the **Legacy-report** groups; futures-only vs futures-and-options is not stated. **High**
- **Groups.** Commercials are hedgers. Non-commercials are funds that "will most of the time trade with the trend". Non-reportables are "small or retail traders". **High**
- **Settings.** "Customisable historical period and threshold". "Best applied on weekly future chart". **High**
- **Example, GC1! weekly.** "Blue graph indicate the Commercial Index, showing on the extreme low under 20 level" is read as a "potential change in market direction the upside". "Orange graph indicate the Non-Commercial Index, showing an extreme high level above 80" is read as trend continuation up. **High** that this is what the page says (but see 3.5).

### 3.2 How he reads it (his own words, [TX])

- **Net positions with Fibonacci 0.2 / 0.8.** He draws a Fibonacci retracement from the highest to the lowest net position over the lookback. "if my retailers are below the 20% reading then we are in an extreme bearish reading. If we above the 80% reading then we are in a very bullish reading. If you're anywhere in between we are neutral."
  - Lookbacks: "this six month, one year, two year or three year look back". He starts at "the smallest look back which is six month".
  - Source: `20251226_This_Data_Shows_WHERE_the_Market_Turns__COT_MASTERCLASS__-_Ep._1.txt`. **High**
- **Three years is the maximum.** "three year that's the maximum that I look at ... if we were in a three-year extreme then this would mean a very very big move". Retail traders "extremely bullish three-year extreme" plus smart money "three-year extreme bearish" means "I expect this Market to drop". Source: `20240602_..._Shorting_Silver_...txt`. **High**
- **Six-month extreme.** Being beyond the red line is "a six month extreme". "it's not a timing tool because timing we do with the technicals". Source: `20240609_Mexican_Peso__My_Full_Bottom-Catch_Trade__Part_2_.txt`. **High**
- **Rule set.** Trade with the commercials ("smart money") and against the non-reportables ("retailers") (COT masterclass). **High**
- **2026 "terminal" version.** COT data since 1986 across 31 markets. Extremes are tested on a 1-year and a 3-year lookback with a **3-month forward horizon**: "Look back a year to notice the extreme. Measure three months ahead". Source: `20260714_I_m_Buying_Silver__NOT_Gold._Here_s_Why..txt`. **High** (as a description of the method)

### 3.3 Clone

"OTC COT / smart money Index 2.0" (Nikhichuanhal655, May 2025, "Inspired by Bernd Skorupinski's institutional approach") says:

- "Look back 6 months to 3 years for extremes": 6 months to follow the trend, 3 years to spot market shifts.
- "Above 80 = bullish extreme (commercials heavily long)", "Below 20 = bearish extreme".
- Source: https://www.tradingview.com/script/BgxhZ2my-OTC-COT-smart-money-Index-2-0 **Medium**

### 3.4 Larry Williams' COT index

- **Formula.** *Trade Stocks and Commodities with the Insiders: Secrets of the COT Report* (2005), p.34: "Current week's value − Lowest value of last three years" / "Highest high of last three years − Lowest low of last three years" × 100%.
  - The script author says Williams "uses 3 years Commercial index" by default and reads above 80 as bullish, below 20 as bearish, weekly only, as a bias tool and not a timing tool.
  - Source: https://www.tradingview.com/script/FDi7l1v6-COT-Index (Dixon_Chai). **Medium-High** (cites the page)
- **Later default: 26 weeks.** A book passage quoted on ForexFactory (2008): "In the old days, as I have discussed, we used a three-year look-back." and "I have defaulted to the 26-week or one-half year window". Formula name: "Stochastic Custom (COT Commercials/Open Interest, vara)".
  - In other words: a stochastic of (commercial net / total open interest) over 26 weeks. This is the "Commercials Versus Total Open Interest" indicator, later sold as **WillCo**.
  - Sources: https://www.forexfactory.com/thread/85724-charting-the-cot-report and https://quantnet.com/threads/open-interest-cot-report-stochastic.1428/post-16522. Book chapter list: https://oreilly.com/library/view/trade-stocks-and/9780471741251 (Ch.4 "The COT Index", Ch.10 "A New Indicator: Commercials Versus Total Open Interest").
  - **Medium-High.** That the passage comes from the 2005 book is my inference; the thread does not name the book.
- **Williams' vendor suites list separate indices.** Commercials, Large Spec and Small Spec indices, plus WillCo and "WillValFC" (Symbolik). No parameters are published. https://symbolik.com/addons/larry-williams-futures-indicators **High** (existence only)
- **Common practice (MetaCOT, MQL5).** Index = ((curr−min)/(max−min))×100. Recommended lookbacks 26/52/156 weeks. "0–20 and 80–100" are extremes. Briese Movement Index: 6-week change, ±40. https://mql5.com/fr/code/16767 and https://it.tradingview.com/script/wrhu1aHK-Briese-CoT-Movement-Index/ (COT Bible ch.7 p.75). **Medium**

### 3.5 Contradiction to note

The site's gold example reads **commercials < 20** as a potential upside turn. That is opposite to Williams, and opposite to Bernd's own spoken rule (smart money extremely bearish → expect a drop). Treat the site copy as unreliable on this point; Bernd's spoken rule matches Williams. **Medium**

---

## 4. True Seasonality

### 4.1 Bernd's own description

Sources: https://bernd-skorupinski.com/true-seasonality-indicator/ and the copy at https://it.tradingview.com/script/J3706PII-True-Seasonality

- "designed to forecast price based on historical data, best use on daily chart". **High**
- A blue graph shows "the few projected days in the future". **High**
- Inputs: "Adjustable forecast bars & lookback". **High**
- Example: gold on 8 Apr 2025 showed an uptrend until mid-April, then sideways. **High**

### 4.2 His own words [TX]

- **Trading-day alignment.** "our own proprietary OTC true seasonality indicator ... very dynamic, it changes its forecast because it's not calculated based on calendar days. It's calculated based on trading days". He back-tests it by showing what the tool "would have forecasted" each year from 2014 (a 10-year pattern on a 10-year gold daily chart). Source: `20251119_XAUUSD_December__January_Pattern__The_Seasonal_Edge_Most_Traders_Ignore.txt`. **High**
- **Lookback and horizon.** "this is a 15 years ... 15 years forecast so looking at 15 years historical data and then we are projecting", a drop "for the next ... almost four weeks". Source: `20240602_..._Silver_...txt`. **High**
- **Hit rates.** He mentions "the last 10 to 15 years" and "dropped ... 12 out of 15 times" (same XAUUSD file). **High**
- **2026 version: seasonal windows.** Example: "going back 15 years, day by day ... Crude oil tends to rise. It closed higher 87% of the time. 13 of the last 15 years". Another example: "same 80%, same 15 years". It "only counts the days when the market actually worked". Sources: `20260811_Why_I_m_Buying_AND_Selling_OIL_This_Week.txt` and `20260814_The_AUDUSD_Short_Is_Almost_Here....txt`. **High**

### 4.3 Clone

"OTC Seasonal forecasting tool 2.0" ("Inspired by Bernd Skorupinski's institutional strategy"):

- Average seasonal performance over **5, 10 and 15 years** (green, red and blue curves), with "custom smoothing".
- Use when at least two curves agree, as a "contextual filter rather than a trade trigger".
- Source: https://www.tradingview.com/script/zmqcjXFi-OTC-Seasonal-forecasting-tool-2-0 **Medium**

### 4.4 Larry Williams' True Seasonal (1973)

- It "uses only data up to the date being calculated", so it has no look-ahead.
- "The default lookback period for the Williams True Seasonal is one year", and Larry recommends increasing it.
- It works on daily and weekly charts.
- Source: https://help.stockcharts.com/charts-and-tools/stockchartsacp-plug-ins/larry-williams-stock-trading-starter-pack-plug-in **High**
- StockCharts also says it "measures the difference between a security's price and its average price over a specific period", which implies detrending against an average. The averaging length is not given. https://articles.stockcharts.com/article/articles-chartwatchers-2023-09-optimizing-your-stock-selectio-527/ **Medium**

### 4.5 Moore Research (MRCI) seasonal pattern: exact method

- **Per-year normalisation.** Each day's price is converted to its position within *that year's* range (low = 0, high = 100). Example from the FAQ: "a price of 16 in a year with a low of 10 and high of 40 is assigned 20".
- **Averaging.** For each day, the values are averaged across years ("we do not average prices").
- **Final scale.** The averaged curve is renormalised so its lowest value = 0 and highest = 100.
- **Windows.** Patterns are published for 5, 15 and up to 30 years; the standard pattern uses 15 years.
- **Use.** "the seasonal pattern can be used only for TIMING and DIRECTION".
- Sources:
  - https://www.mrci.com/web/help-pages/frequently-asked-questions/84-charts/415-seasonal-pattern-chart-explanation.html
  - https://mrci.com/web/help-pages/frequently-asked-questions/78-meats-research/3203-whats-the-difference-between-average-a-non-average-charts-from-editor-jerry-toepke.html
  - https://www.mrci.com/web/help-pages/frequently-asked-questions/66-spread-questions/392-y-scale-on-mrci-graphs.html
- **High**

Bernd's 2026 "80% over 15 years" windows match the MRCI style of seasonal strategies. That MRCI uses an 80% / 15-year cut-off is my background knowledge, **not verified** in this session. Jake Bernstein's method (weekly up-percentages, key-date seasonals) was also **not verified** (search budget). **Low**

---

## 5. UnFilled Order (UFO) supply & demand

### 5.1 Bernd's own description

Sources: https://bernd-skorupinski.com/unfilled-order-supply-and-demand-indicator/ and https://it.tradingview.com/script/aWOAvqvY-UnFilled-Order-Candle/

- A UFO is "a trace of institutional position in the price action". **High**
- It forms in Rally-Base-Rally, Rally-Base-Drop, Drop-Base-Drop and Drop-Base-Rally structures. **High**
- "Base has small body candle compared to its near candles". **High**
- The only input is "Adjustable body candle ratio"; its default is not stated. **High**
- Colours: light green = bullish base, orange = bearish base. **High**
- Entry: "Place buy limit on the proximal (upper) level". **High**
- Base selection uses "location, originality, freshness". **High**

### 5.2 His lesson rules [TX]

- **Candle classes.**
  - Indecisive (base): "body is smaller or equal to 50% of the range".
  - Decisive: body > 50%.
  - Explosive: "body is bigger than 70% of the range", *and* the candle must be "abnormally bigger than the previous few candles".
  - Source: `20240802_The_4_Supply___Demand_Formations__RBR__DBR__RBD__DBD_Explained_.txt` and `20240823_The_Candle_That_Tricks_Most_Traders__Supply___Demand_.txt`. **High**
- **Zone shape.** "the leg out has to be an explosive candle". The base needs "between one and six indecisive candles" (`20250731_The_Base_Candle_Rule_That_Filters_Out_Bad_Supply___Demand_Zones.txt`). **High**
- **Lines.** For demand, the proximal line runs "across the top of the bodies of the basing candles" and the distal line below the lowest wick. Supply is the mirror image (`20240427_Supply___Demand_Zones__The_Rule-Based_Method__Full_Walkthrough_.txt`). **High**
- **Freshness.** Freshness is counted on the "preferred" (narrow) zone versus the "wider" version (`20250822_..._Freshness_Explained_.txt`). **High**

---

## 6. Best reconstruction: formulas to code

All series use data available at bar close only. COT data are dated Tuesday and released Friday, so lag them at least to the Friday close.

### 6.1 Valuation (primary V1, with variants to A/B test)

```
inputs: refs = [DXY, ZB1!, GC1!]; n = 10; W = 480 (daily bars); lo_th = -0.75; hi_th = +0.75
for each ref B (forward-filled onto the asset's sessions):
    D  = pct_change(A, n) - pct_change(B, n)           # relative performance (clone formula)
    V  = 2*(D - rolling_min(D, W)) / (rolling_max(D, W) - rolling_min(D, W)) - 1   # in [-1, +1]
undervalued_vs_B = V <= lo_th ;  overvalued_vs_B = V >= hi_th
```

- **V1s.** Same as V1 with EMA(n) smoothing applied to D *or* to V. The site calls 10 a "smoothing value".
- **V2 (deviation from fair value, matching the OTC 2.0 clone).** R = A/B; D = R/SMA(R, n) − 1; then the same rescale.
- **V3 (current lab version, kept as control).** D = EMA10(ln A − ln B); rescale over 480.
- **V4 (Williams WillVal, weekly).** R = 100·A/B; Pal = EMA(R,2) − EMA(R,22); WV = 100·(Pal − min_L)/(max_L − min_L).
  - L = 156 weeks (original) or 26 (claimed current).
  - Levels 75/15 (StockCharts) or 85/15 (tradeviZion).
  - Buy when WV crosses back above the lower level.
- **Rescale window.** Also test W = 100, the clones' default.

**Reading rules (Bernd).**

- Stock indices: long bias when V ≤ −0.75 vs ZB1!. The strongest signal is undervalued vs all three references.
- FX, metals and energies: use DXY. Silver and CHF: use GC1!.
- Exit or trail a long when V ≥ +0.75 vs the relevant reference.

### 6.2 COT

```
weekly Legacy COT; groups g in {comm, noncomm, nonrep}; N_g = long_g - short_g
for L in (26, 52, 104, 156):            # 6m, 1y, 2y, 3y  (use 157 if the window counts the current week)
    I[g, L] = 100 * (N_g - min_L(N_g)) / (max_L(N_g) - min_L(N_g))
bull_L = I[comm, L] >= 80  or  I[nonrep, L] <= 20       # with smart money / against retail
bear_L = I[comm, L] <= 20  or  I[nonrep, L] >= 80
strength = longest L that is in extreme (3y = strongest); bias only, no timing
```

Optional variant, Williams WillCo: run the same stochastic on N_comm / OpenInterest with L = 26.

### 6.3 True Seasonality

```
daily bars; d = trading-day index within the year of bar t (sessions since 1 Jan)
for y in the last Y = 15 completed years (no look-ahead):
    p0 = close at trading-day d of year y
    path_y[k] = ln(close at trading-day d+k of year y / p0),  k = 1..F (F = 30)
proj[k] = mean_y path_y[k];  hit = share of years with path_y[F] > 0
seasonal_bull = proj[F] > 0 (strong if hit >= 0.8, i.e. >= 12/15);  bear mirror
```

- Alternative (MRCI pattern): per-year (close − yearLow)/(yearHigh − yearLow)·100, averaged by trading-day index across Y years, then renormalised to 0–100. Read the slope over the next F days.
- Also test Y = 5 and Y = 10, the clone's 5/10/15 curves.

### 6.4 UFO zones

```
range = high - low; body = |close - open|
indecisive: body <= 0.5*range ; decisive: body > 0.5*range
explosive : body > 0.7*range and range > k*mean(range of previous m bars)   # k, m unknown: try k=1.5..2, m=5..10
zone = leg-in (decisive/explosive) + 1..6 indecisive base candles + explosive leg-out
demand: proximal = max(open, close) over base; distal = min(low) over base   (supply: mirror)
fresh = proximal not touched since formation; entry = limit at proximal; stop beyond distal
```

### 6.5 Combining the tools

- Bias = agreement of COT, valuation and seasonality ("All Stars aligned" = 3/3).
- Entry = a fresh higher-timeframe zone in the bias direction.
- Targets per the notes in bernd_tx_notes_00: 3–4R normally, 2R for beginners.

---

## 7. Open questions

1. **Valuation inputs.** What are 480 and 10 exactly: rescale window or a security() timeframe? ROC length or post-smoothing? Is the core relative % change (clones), deviation from a moving average (OTC 2.0 clone), or ratio level (current lab)? Is the rescale a rolling window or all-history? Reading the screenshot's y-axis and how often the line crosses ±0.75 would discriminate between V1 and V3.
2. **Valuation timeframe.** Is valuation computed on the chart timeframe? He shows daily mostly; the site says "weekly or daily".
3. **COT report type.** Futures-only or futures + options? Raw net positions or % of open interest? Does the indicator run 4 lookbacks at once, or one adjustable lookback (he switches between 6m/1y/2y/3y by hand with a Fibonacci tool)?
4. **COT reading conflict.** The site's gold example (commercials < 20 read as bullish) contradicts his spoken rule; which matches the shipped indicator's colouring and alerts?
5. **True Seasonality inputs.** Is "15, 30" lookback-years/forecast-bars or the reverse? Is the output an average forward path (as in 6.3) or an MRCI-style %-of-range pattern? Is there detrending (Williams) or smoothing (clone)? Is the current year excluded?
6. **UFO defaults.** Is the "body candle ratio" default 0.5? What is the "abnormally bigger" rule for explosive leg-outs? Does the indicator enforce the 1–6 base-candle limit?
7. **2026 terminal.** It looks like a new, separate product (COT since 1986, seasonal-window scanning, 3-month forward-return validation). Are its thresholds the same as the TradingView indicators?
8. **Not verified this session.** Jake Bernstein's seasonal method, MRCI's strategy-selection criteria, and the exact text of Williams' WillVal in his books (the search budget ran out; no book text was available).
