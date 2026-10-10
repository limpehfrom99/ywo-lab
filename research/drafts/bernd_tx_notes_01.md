# Bernd Skorupinski transcripts — notes, batch 01 (30 files, 2023-10-06 .. 2024-05-08)

Source list: research/drafts/bernd_tx_list_01. Files in /home/claude/data/bernd_tx/.
Auto-captions: no punctuation, mis-hearings. Quotes below are verbatim caption text (typos kept); my
corrections are in [brackets]. "INFER:" marks my inference, everything else is what he says.

## SYNTHESIS (batch 01: 30/30 files read in full, uploads 2023-10-06 .. 2024-05-08)

Method content is concentrated in 8 files: 20231025, 20231210, 20231225, 20240331, 20240427, 20240428,
20240504, 20240508. About 13 files are challenge diaries, lifestyle or mindset videos that carry only
results and risk numbers.

His frame, as he states it: a "two-step mechanical process". Step 1 is a bias from three "stars": the smart
money index (COT), valuation, and the seasonal "algo forecast". Step 2 is timing with S&D zones on unadjusted
continuous futures (monthly -> weekly -> daily), then execution on the CFD (20231025, 20240223, 20240217,
20240428).

### 1. Indicator evidence

| Setting | What he says (file) | vs our reconstruction |
|---|---|---|
| Valuation references | purple = dollar (DXY), yellow = gold ("@GC"), blue = treasury bonds ("@US" = 30y, i.e. ZB) (20231025, 20231210, 20240331) | **Confirms** DXY / ZB / GC |
| Which reference counts | Equity index: ZB "first and foremost ... the most important"; all three undervalued = "the best moves", rare (20231210, 20231225). Platinum: ZB ignored, "gold and dollar is important" (20231025). FX futures (CHF, MXN): DXY is required, "Ideally ... all three" (20240331, 20240428) | **Refines**: a primary reference per asset class |
| Valuation maths | "compare the price of equity indices ... on a ratio to interest rates" (20240217); the scale has a "floor" (20240331) and an "average" (20240504) | Consistent with scaled ln(asset/ref). **480, ±0.75 and EMA10 are never mentioned** |
| Valuation timeframe and data | daily (platinum, 20231025); weekly (peso, 20240331); unadjusted continuous futures in TradeStation ("@PL=...XN", "@GC=120XN+GJMQZ") (20231025, 20231210) | **Check**: we compute daily only and may use adjusted data. If he runs the same settings on weekly bars, 480 bars = 480 weeks |
| Valuation use | entry filter; exit early "once we're overvalued" (20231210); "not a timing tool" (20240428) | Adds an exit rule |
| COT groups | "smart money ... the users and producers" (blue); "fund managers"/"funds ... trend followers"; "retail"/"dumb money" (red); "actual positions ... not sentiment" (20231210, 20240428) | Report never named. INFER: legacy commercials / non-commercials / non-reportables |
| COT normalisation | "compared to their previous behavior", "in the past few years" (20231025, 20240331, 20240428) | Consistent with an index. **157 weeks never stated** |
| COT thresholds | "green horizontal line and ... red horizontal line ... the extremes"; output "bullish bearish or neutral" (20231210, 20240428) | Consistent with 20/80. **No numbers stated** |
| COT signal | Best: smart money at the bullish extreme AND retail at the bearish extreme, "at the opposite side" (20240428, 20231210). He also uses smart money alone (platinum) and retail alone (peso, monthly chart) | **Refine**: two lines (smart money, retail), opposite extremes |
| COT cadence and use | weekly, "updated every Saturday" (20240504); "make or break" for holding a trade (20231025); "not a timing tool"; expects "one or two ... green weekly candles" (20231210) | |
| Seasonality | "campus algo forecast" = "our seasonal forecasting tool with a twist", "not only real seasonality ... we can also forecast the future" (20240217, 20240428, 20240504, 20240508). No year count, averaging method, detrending or horizon stated | **"True Seasonality 15/30" is not mentioned.** Possible conflict: on 28 Apr 2024 it showed a low in "second week of May" and strength "until ... end of June", a horizon of about 2 months, longer than 30 trading days |
| Combination | Traded platinum on "two out of three stars" (Aug 2023, 20231025). Later: "all stars aligned" / A+ only (20240323, 20240428). Valuation and COT must confirm before any chart work (20240331) | ≥2/3 tradable, 3/3 preferred; zones time the entry |

**Readings stated with market and date.** He never gives a numeric indicator value in this batch.
- Platinum, ~4 Aug 2023: undervalued vs DXY, "almost" undervalued vs gold; COT smart money buying, then "even more bullish" by ~19 Aug; seasonal "tendency will come to an end", around 10 Aug (20231025, 20231118). ~24 Aug: "not close to overvalued" vs USD (20231210).
- Gold, late Aug 2023: smart money turning bullish while retail turns bearish (20231210).
- Dow, ~25-28 Aug 2023 and early Oct 2023: undervalued vs ZB, GC and DXY at the same time (20231210, 20231225, 20231010).
- MXN futures, pre-election months Jun 2006, 2012 and 2018: retail COT very bearish (and very bullish 3-4 months earlier); in 2012 and 2018 the peso was "extremely undervalued" vs DXY on the weekly chart (20240331).
- CHF futures, ~26-28 Apr 2024: smart money at the bullish extreme, retail at the bearish extreme, funds "most bearish since 2008"; valuation vs DXY "coming from undervalued", then "not even near the average" on ~4 May; forecast low in the 2nd week of May, strength until end of June, "big bottom" ~9 May (20240428, 20240504, 20240508).

### 2. Supply & demand rules as if-then (GAP = not stated in this batch)

**Zone definition**
- **R1. Anatomy.** A zone = leg-in + base + leg-out. DBR and RBD are named. RBR and DBD appear as parts of a "level on top of level" (20240427).
- **R2. Search.** Start from the current price and look left (down for demand, up for supply) for "the origin" of a strong move, "without cutting through" candles (20240427).
- **R3. Leg-out.** It must be large or "explosive", "ideally multiple candles"; one green candle followed by a pause is not a zone. GAP: numeric threshold.
- **R4. Lines.** Demand: proximal = "top of the bodies of the basing candles"; distal = lowest low, using wicks. Supply is the mirror image. GAPS: base-candle definition (body vs range, maximum count); whether leg candles set the distal.
- **R5. Data.** Judge a zone on unadjusted continuous futures: a zone broken on spot or adjusted data can still be valid there (20231210).

**Quality filters**
- **R6. Freshness.** A zone touched "the fourth or fifth time" has "absorbed all the unfulfilled orders", so expect a break. Zones already reacted from are "not fresh" = low quality (20231225, 20240504). GAP: whether a single touch already disqualifies.
- **R7. Big brother / small brother.** Take a lower-timeframe zone only if it sits inside a same-direction higher-timeframe zone ("daily covered by weekly"; "covered by monthly ... covered by weekly") (20231210, 20240428).
- **R8. Level on top of level.** DBR + RBR stacked = "protection" (20231210, 20240508).
- **R9. Trend.** Not required ("it's sideways Market", 20231025). GAP: action matrix, originality, flip zones.

**Timeframes**
- **R10.** Zones top-down M -> W -> D; enter on the daily ("execution time frame daily or weekly charts"). Use 240/180/60-min for refinement, add-ons and trailing. Day trading uses 60-min zones on index futures (20240223, 20240428, 20240504, 20240508, 20231025).

**Entry**
- **R11.** Set-and-forget limit at the proximal line. Pin bar or engulfing candles are noted but not required. GAP: the "3 entry models".
- **R12. Stacked zones.** Three options: enter the lower zone, the upper zone, or combine both with the stop "a little bit Above This distal level" (20240508).

**Stop and target**
- **R13. Stop.** "I use 33% of the zone as my stop loss" (20240428). INFER: stop = distal + 0.33 × zone height.
- **R14. Target.** The opposing higher-timeframe zone. Example: 3R, exactly "where the opposing weekly Zone Starts" (20240428). Usually 2-4R (20231123); minimum 1:2 (20231030). GAP: what to do when the opposing zone is less than 2R away.

**Management**
- **R15.** At +1R, move the stop to break-even plus swap cover (20240504). In Aug 2023 this was still discretionary (20231025).
- **R16.** Then trail beyond each newly formed opposite zone on 240-min (or 60-min) bars (20240504); in 2023 he trailed below new daily RBRs (20231210). Near the target, tighten so a 2.5R excursion keeps at least 2R.
- **R17.** "never, ever take partial profits" (20240504).
- **R18. Early exits.** Exit when valuation turns overvalued before the target (20231210), when weekly COT stops supporting the trade (20231025), or when the "setup has changed"/the trade is "ranging for quite some time" (20231123).
- **R19. Add-ons.** Only if (1) the initial stop is at break-even, (2) fundamentals are unchanged, and (3) there is a new high-quality zone; same 2% risk (20240508). This conflicts with the Aug 2023 platinum add-on, which he placed while the first stop was not at break-even.

**Risk and news**
- **R20.** Challenges: 2% per trade, up to 6% on correlated same-direction positions. Funded: fixed 1% ($10k on $1M, $20k on $2M). Fixed-dollar R, no compounding; survive 10 straight losses (20240428, 20231217, 20240301, 20240126).
- **R21.** No news filter: he holds or enters through FOMC, CPI and Powell speeches (20231118, 20231210).

### 3. Other testable hypotheses

- **H1. US presidential cycle, Dow 1973-2023** (20240119).
  - Mean year % change: election year +7.84% (excluding 2008's -32.72%), pre-election +16.31%, post-election +8.8%, midterm +1.54%.
  - Election-year path: top late Feb to early Mar; low around the 3rd week of March; up from April to early May; weak May; up from end-May to mid/late August (buy dates 27 Jun and 25 Jul); top 14 Aug to 2 Sep; weakest 14 Sep to 29 Oct (-4% to -10%); October low to 31 Dec +5% to +15%.
- **H2. Decennial cycle, S&P 500, 14 decades** (20240414).
  - Year 5: up 13 of 14 times, summed about +300%.
  - Year 1: 9 up, 4 down.
  - Years 7 and 0: net negative (sums -40% / -20%).
  - Years 2-3: contain the bottoms.
- **H3. Mexican election cycle, MXN futures monthly** (20240331). Elections Jul 2000/2006/2012/2018 in sample, Jun 2024 out of sample. Claims: down in the 3-4 months before; low in the month before the election; election-month candle green; rally for several months afterwards; retail COT high before and low at the bottom. External check, not from the transcripts: I believe June 2024 was a sharp peso sell-off, so the "election month green" claim failed out of sample. Verify with data.
- **H4. Mini gap** (20240508, early form in 20231118).
  - Definition: on 60-180-min futures bars, Open[t] < Low[t-1] (gap down) or Open[t] > High[t-1] (gap up).
  - Claims: rare; occurs in very high or very low volatility; "usually getting filled very quickly"; acts as a magnet toward nearby zones.
  - "Very quickly" is not quantified (test N bars).
- **H5. Zone exhaustion.** Probability of a break rises with the number of touches; 4-5 touches -> break expected.
- **H6. Valuation confluence.** Undervalued vs all three references (rare) beats a single-reference signal.
- **H7. COT opposite extremes.** Smart money at the upper line and retail at the lower line -> positive returns over the next 1-8 weeks.
- **Note.** The "correlation trade" (20231217) is just 3 × 2% same-direction precious-metal longs, not a spread trade.

### 4. Five most useful quotes for coding

1. 20240217: "I want to compare the price of equity indices like NASDAQ down S&P 500 on a ratio to interest rates" -> valuation is a log ratio.
2. 20231210: "first and foremost this is the most important valuation measurement the treasury bonds ... when we are undervalued versus all of the three assets treasury bonds at us gold at CC and dollar dxy the US dollar then we are getting the best moves" -> reference weighting.
3. 20231025: "purple is dollar yellow is gold blue we can reject it's treasury bonds there's no relation to uh Platinum here but gold and dollar is important" -> a subset of references per market.
4. 20240428: "we look at cut data always based on how do they behave how do their position look like based on the previous data" + "I want to see the retailers down here in that extreme and on the opposite side I want to see the smart money here" -> COT index logic.
5. 20240428: "I use 33% of the zone as my stop loss" (with the 20240427 line placement) -> stop buffer.

### D. Results for realism checks

- **VST $1M A-book.**
  - Payouts: $40k (29 Aug 2023), $30k (22 Sep), $20k (26 Oct).
  - Six months: 32 trades, average hold 22 days, maximum drawdown 2.77%, +12.66% at 1% risk.
  - Swaps: $15k out of $137k gross.
  - Claimed "100% win rate" counts break-evens as non-losses; an earlier video counted them as losses and gave 70%.
- **Stated KPI targets.** 40-50% win rate, 2R per month, 20-24R per year; "12 to 24% return per year"; some months only "four or five trades".
- **Challenges.** 3 trades in 11 days; 4 trades in 16 days (worst drawdown about 4%).
- **Holding times.** "a couple of days ... one or two weeks"; the platinum trade lasted about 3.5 weeks.

---

## Per-file notes (in upload order)

### 1. 20231006_I_Recorded_Every_Day_Of_My__400K_Prop_Firm_Challenge.txt (2023-10-06)
Content: intro to "season 2" of his live challenge documentary: 2 x $200K True Forex Funds challenges ($400K).
- A (indicators): none.
- B (S&D): none. Only labels his approach "set and forget": "teaching my profitable set forg [set-and-forget] approach to trading".
- C: none.
- D (results/risk/self-description):
  - "I manage whopping $2.4 million of Pop [prop] trading Capital"; "CEO of a licensed training consultancy based in fabulous Dubai".
  - Challenge rules he accepts: phase 1 target 8%, phase 2 5%, "5% maximum daily loss 10% maximum overall loss", no time limit, weekend holding allowed. He likes no time limit: "we can only focus on high quality trade setups we don't have to feel rushed".

### 2. 20231010_Passing_a__200K_Prop_Firm_Challenge_With_Pure_Swing_Trading.txt (2023-10-10)
Content: end of his FundedNext $200K challenge documentary (passed in 11 calendar days, 3 trades: platinum, gold, Dow Jones).
- A (indicators):
  - Valuation, Dow Jones (early Oct 2023, long): reference set = gold + dollar + treasury bonds: "here on the Dow Jones also the fundamentals were perfect right under valued versus gold dollar and uh the treasury bonds like a picture perfect fundamental trade based on our proprietary indicator". Supports the DXY/ZB/GC reference set for an index. Reading: Dow undervalued vs all three (no number given).
  - Platinum and gold longs justified by "fundamentals"/COT (inference: "smart money" = commercials): "Platinum why did we take that Platinum trade the fundamentals were super strong"; "gold super strong fundamentals we traded with the smart money".
- B (S&D): no rules. Watches the target on 5-min only for the camera: "usually I would not go down to a 5 minute chart".
  - Vague price-level remark while waiting for the Dow target: "the 80 is obvious vious L also the uh 480s also an obstacle 80s and 30s are obstacles" (round-number-ish obstacles; vague, not a rule).
- C: none.
- D: "completing the challenge with a 100% win rate"; "three trades only"; "no stupid sculping no day trading normal swing trading"; drawdown early: "I almost lost 3% of my total 10% total draw down limit in the first couple of days". Fills minimum trading days with "two micr lots ... on euro dollar".

### 3. 20231015_How_Do_Prop_Firms_Work___Watch_Before_Buying_A_Challenge_.txt (2023-10-15)
Content: generic prop-firm buyer's guide (this transcript has punctuation; reads like a scripted/dubbed text). No method content.
- A: none. B: none. C: none.
- D:
  - "full-time trader managing $2.4 million in prop trading capital at major firms such as FTMO, Search Trader [Surge Trader], and VST Global".
  - Readiness rule of thumb: "You will know when you are ready, when you have more than 20 consistently profitable trades. ... You can win 50% or 30% of them." (win-rate expectation 30-50%).
  - Prefers swing accounts (weekend holding): "a swing account option that allows you to hold positions over the weekend. This is one of my favorite options."
  - "my biggest investor, the CEO of VST Global, explains how he abandoned the daily drawdown rule for my $1 million account".
  - Rejects no-stop-loss / double-leverage add-ons: "the lack of a stop loss and double leverage, which I honestly consider counterarguments".

### 4. 20231025_The_Worst_Start_I_ve_Had_On_A_Prop_Challenge.txt (2023-10-25; trades recorded 4-12 Aug 2023)
Content: week 1 of the True Forex Funds 2 x $200K challenge. One trade: platinum long (entered Fri 4 Aug 2023, plus add-on). RICH FILE.
- A (indicators):
  - **3 "stars", took it with 2 of 3** (combination rule): "I entered this trade based on my twostep mechanical process we are undervalued versus the dollar and almost undervalued versus gold and we are our smart money index is showing that the that the smart money is buying which is great as well it's not necessarily a seasonal sweet SP sweet spot so it's not not all stars aligned so it's two out of three stars". INFER: "two-step" = (1) fundamentals/bias stars, (2) market timing with zones.
  - **Valuation display (3 lines, colour-coded)**: "the line that is important here is is it purple purple and yellow line because purple is dollar yellow is gold blue we can reject it's treasury bonds there's no relation to uh Platinum here but gold and dollar is important". -> per market he picks which references count; for platinum only DXY + gold, ZB ignored. Timeframe: "let me do the daily full screen now we are undervalued".
  - Valuation back-check he shows: "when we had undervaluation gold and gold and dollar at the same time ... every time we got a significant Rally from there" (both refs undervalued together = stronger signal; INFER).
  - Data: he reads valuation on an UNADJUSTED continuous futures chart in TradeStation: "we have unadjusted and adjusted charts ... let me quickly go to the unadjusted Chart first at PL equal 120 xn" (INFER: TradeStation symbol like @PL=1x0XN; "XN" = non-adjusted). Relevant for our ln-difference computation (back-adjusted vs unadjusted).
  - **COT ("smart money index", blue line), read weekly, used as the make-or-break for holding**: "the smart money index will be for me to make or break ... if the Blue Line next week continues to rise on Monday ... if the smart money continues to buy I will stay in that trade" (else exit "roughly at break even").
  - COT normalisation is relative to their own history: "every time in the past few years the smart money is that bullish in relation to the past how they behaved in the past here we got a rally ... every time they were on a similar bullish level the smart money we printed the low" (lookback "past few years" = vague; consistent with an index over ~3y).
  - Seasonality, platinum ~10 Aug 2023: "the seasonal tendency will come to an end and we expect price to go down that's negative".
  - Readings (platinum): ~4 Aug 2023 undervalued vs DXY, "almost undervalued" vs gold, COT smart money buying, seasonality not supportive; ~11-12 Aug 2023 COT "continues to be very very bullish".
  - Calls his tools "AI indicators" (caption garbled): "my tools are the gr delr of the AI indicators out there so I will never change any of them".
- B (S&D):
  - Nested zones: "on the weekly chart it's a weekly demand Zone and ... you have a daily demand Zone The Daily is covered by the weekly which is also high high quality" (INFER: daily zone inside a weekly zone = quality plus).
  - Trend context noted but not required: "it's not a trend rate per se it's sideways Market".
  - Reversal candle at zone noted: "it's forming a pinb bar almost a hammer candle"; weekly: "we closed like a pin bar a hammer candle not the best per se because it has kind of a red body but from a structural point of view it's potentially a reversal candle".
  - Formation named: "we might go a little bit lower into now this drop base R [rally]".
  - Everything pre-planned (set and forget): "the entry is pre-planned the stop- loss is pre-planned the target is pre-planned the risk is pre pre-planned".
  - Stop below the weekly zone: "the weekly Zone where the stop loss is below you see it's holding".
  - Break-even rule: discretionary; he declined to move the first position to BE after a shallow touch: "we just had a shallow Touch of this demand Zone it can it's a swing trade it can potentially go a little bit deeper and then go higher so that's why I don't want to move these stop losses to break even yet".
  - Extra bullish confirmation (discretionary): "if we close above yesterday's high that would be also rather bullish".
  - Day-trading: equity-index short limits at 60-min supply zones, unfilled by "two points": "clobex trades ... my day trading strategy which is called the clobex rap [INFER: 'Globex trap']" ; "the supply zones on a 60-minute chart and here on the NASDAQ on a 60-minute chart".
- D (risk/results):
  - Risk: "2% of Risk by the way aggressive and the second even more aggressive another 2% which I call addon" -> 4% on one idea.
  - Hold time: "it's a swing trade though this can take a couple of days and even this can take uh one or two weeks to play out".
  - Drawdown: "we are down now almost 3 and a half% on that Platinum trade"; "it's my biggest draw down in a challenge so far".

### 5. 20231030_How_I_Manage_My_Trading_Accounts_Like_A_Business.txt (2023-10-30)
Content: "trade like a business" pep talk; written trading plan; no indicator content.
- A: none.
- B: only generic: minimum reward:risk "aim for risk to reward ratio of at least 1 to two"; S&D "by identifying those sweet supply and demand imbalances you can decide if the market is playing in your favor or not".
- C: none.
- D: win-rate expectation "they've only need to win around 30 to 40% of their trades"; "I manage $2.4 million with poom [prop] capital".

### 6. 20231107_10_Trading_Hacks_I_Use_After_10_Years.txt (2023-11-07)
Content: 10 "hacks" (only 9 given).
- A (indicators):
  - Max three indicators: "I have never used more than three indicators at the same time".
  - In-house tools: "our indicators and forecasting tools that we developed inhouse I think those are the best"; he calls them AI-type "new age indicators". Priority: "supply and demand is still King ... if you fully Master supply and demand you will be the master of entry and exit the indicators will be the last thing you have to worry about".
  - Still uses RSI divergence occasionally: "good old Divergence and spotting that perfect reversal on the SSI [RSI] which is totally fine I still do that sometimes too" (vague).
- B (S&D):
  - Workflow: analysis on TradingView/TradeStation, then copy levels to the prop platform: "always do your analysis on trading view or trade station and then copy your set or stop entry Target to your progress [prop] trading environment".
  - "supply and demand is smart money concept just a fancier name" (caption "the blind demand").
  - Routine: "within 60 minutes I'm at my desk and [analyzing] charts ... I'm a swing Trader".
- C (cycles): presidential cycle -> 2023 pre-election year = bullish US equities: "right now in 2023 we're in the pre-election cycle and I called it we're in for a bull market for the US equities".
- D: none numeric.

### 7. 20231118_I_Held_a_Losing_Trade_for_2_Weeks__Here_s_Why_.txt (2023-11-18; recorded 14-19 Aug 2023)
Content: week 2 of the True Forex Funds challenge; still only the platinum long (2 positions).
- A (indicators):
  - COT on the WEEKLY chart in TradeStation, "Blue Line smart money": "open up the weekly chart ... fundamentally Blue Line smart money you see they're getting even more bullish ... I'm still like exceptionally bullish here on Platinum" (reading: platinum COT smart money rising further, ~19 Aug 2023).
  - Holds because "price is not following fundamentals yet"; plans re-entry after a stop-out while fundamentals hold: "if we go lower I planning to re-enter because at some point of time price has to follow the fundamentals".
- B (S&D):
  - Timeframes: "I trade only on higher time frames like daily and weekly"; but looks at 4H for lower zones: "heavy retracement back into 4our [4-hour] demand Zone down here ... we held the losss [lows]".
  - News: no news filter stated; he holds through FOMC/CPI and expects news spikes to go against him because "I trade against retail money and who trades the news yes of course retail Traders".
  - Patience / no manual closing: "my entries stop- loss and Target are all set automatically strictly following my rules ... once I'm in a trade I stick to my plan".
  - Hopes for confirmation candles (discretionary): "bullish daily engulfing"; weekly "pin bar ... hammer candle ... for the next two weeks I expect the uh bullish candle".
- C (gaps = early form of "mini gap"): gaps on the 15-min and daily chart get filled:
  - "I go to 15minute chart you see a few gaps here and these gaps usually are getting filled ... the Gap that I'm kind of happy about is all the way up here so I consider this a fake move and tomorrow hopefully this Gap up here is going to get filled".
  - "we have a few mini gaps here one we have still the big one up here I still believe they're going to get filled"; daily: "here is a mini Gap so we should go higher here and then we should break this Supply". Outcome (17 Aug): "we filled that Gap here ... but then we hit Supply".
  - Definition of a mini gap is NOT given here (vague); see file 30.
- D (costs/holding): swap on platinum CFD after ~2 weeks/3 weekends: "the swap alone ... is already quite high so it's 05% [0.5%] of the position". Holding time already "two weeks". Drawdown at worst ~4%, back to ~-1% by 19 Aug.

### 8. 20231123_How_I_Documented__90_705_In_Prop_Payouts__Full_Audit_.txt (2023-11-23)
Content: myfxbook audit of his VST Global $1M A-book account, Aug-Oct 2023. Results only.
- A: none.
- B (management, stated):
  - Break-even/manual exits exist: "a break even trade that's when you manually close the trade because the setup has changed or because it has been ranging for quite some time or simply move the stop- loss to break even" ; "I don't usually recommend doing this for beginners".
  - Targets: initial R:R "usually between two and four RS"; sometimes extends target: "in some of these trades I moved the target to capitalize on the gains".
  - Same trades copied manually to every account: "a good trade is a good trade regardless of account size so I will definitely trade it on each one of my accounts".
- D (results; useful realism check):
  - 17 trades, 5 "losses" (2 micro test trades + 3 break-evens), "12 divided by 17 * 100 and my win rate appears to to be 70%"; "11 out of 16 Longs and one short" (caption garbled) ; "you will always find in my track record more Longs than shorts".
  - "my average win Is 1,39 pips which equals $757 for [garbled; avg win ~ $7.57k?] and my average loss is only 30 Pips of $15"; "my best trade was almost $20,000 and my worst trade cost me ... $46".
  - Risk: "since I only took 05 R [0.5%? garbled] in each one of these trades my risk to reward ratio ended up being 1 to n[ine]" ; "the one to9 is my achieved risk reward".
  - Payouts: $40,000 on 29 Aug 2023 (26 days after funding on 3 Aug 2023), $30,000 on 22 Sep 2023, $20,000 on 26 Oct 2023 -> ~$90.7k on $1M in ~3 months (~9%/quarter).
  - Concentration: "gold platinum and silver amounted to right about 80% of my winnings this quarter".
  - Costs: "I pay commissions conversion rates and swaps more than ... what I lose trading".

### 9. 20231202_I_Fact-Checked_Reddit_s_Prop_Trading_Advice__10_Years_In_.txt (2023-12-02)
Content: Reddit prop-trading Q&A from Koh Samui. No method content.
- A: none. B: none. C: none.
- D: accounts: "a 400k account with f[TMO]" and "funded another 2 million with search Trader [Surge Trader]"; swaps matter ("some prop firms ... artificially increase the swaps to force you to close your positions earlier"); wants larger drawdown limits "so we as Traders have more buffer in a losing streak and can also take a little bit more percentage risk".

### 10. 20231210_How_I_m_Up__11_000_on_a__400K_Prop_Challenge__Week_3_.txt (2023-12-10; recorded 21-27 Aug 2023)
Content: week 3 of True Forex Funds challenge: platinum (2 pos) + new gold long (21 Aug) + Dow/US30 long (25 Aug). RICHEST FILE OF THE BATCH.
- A (indicators):
  - **Data = unadjusted continuous futures**: "always the analysis happens on an unadjusted continuous Futures chart the underlying asset is really important ... then not only the continuous chart but the unadjusted continuous chart then do your supply and demand analysis and you can also add some conventional technical analysis". Gold symbol: "look at this gold chart at GC equal 120x and plus g j m q set" (INFER: TradeStation custom symbol "@GC=120XN+GJMQZ" = unadjusted, rolled only through Feb/Apr/Jun/Aug/Dec; meaning of "=120" not explained -> "something that we teach in our uh Futures course"). Intro: "you'll have to spend some time analyzing the underlying assets over the continuous unadjusted charts".
  - **COT display**: "step one using our proprietary indicators in order to get bullish bearish or neutral smart money Index ... you see the green horizontal line and you see the red horizontal line so these are the extremes green means bullish red means bearish and the blue line represents the smart money and the red line represents the retail traders". -> an index with two extreme thresholds; output = bullish / bearish / neutral. Groups: smart money (commercials, INFER) and "retail" (INFER: small speculators/non-reportables). Thresholds not stated numerically (consistent with 20/80 but unconfirmed).
  - **COT combination of groups**: best = smart money bullish AND retail bearish: "the blue line is getting bullish the smart money and that's why ... my alert bels went on ... the icing on the cake is basically that the retailers are slowly getting bearish". Back-check: "the retailers were bearish and the smart money was bullish and this was the low"; "retailers super bearish you get this bottom of all bottoms here and this monster R[ally] from 1600 to well more than 2,000"; symmetric: "retailers get then eventually bullish and then smart money is getting bearish and then you get this uh nice drop". Smart money alone can suffice: "here again only smart money ... smart money super bullish well retail money close bullish but neutral but then you get this very very nice move up".
  - COT timing expectation is modest: "we don't need a lot by the way right we just need um one or two ... green weekly candles and this would give us a very nice risk to reward ratio".
  - **Valuation, Dow Jones (equity index)**: "we use here on our valuation tool tool the treasury bonds and of course gold and the dollar so the Blue Line indicates the treasury bond so ideally we are undervalued versus the the treasury bonds so first and foremost this is the most important valuation measurement the treasury bonds ... however when we are undervalued versus all of the three assets treasury bonds at us [@US = 30y T-bond, i.e. ZB] gold at CC [@GC] and dollar dxy the US dollar then we are getting the best moves ... it doesn't happen very often". -> CONFIRMS reference set DXY/ZB/GC and adds a hierarchy for equity indices: ZB is primary, all-three is best.
  - **Valuation as an exit**: platinum vs USD (purple): "we are not close to overvalued so either we're going to get out up here [supply target] or we're going to get out once we're overvalued because once we overvalued this is where price usually ... turns ... we can observe this on a daily base".
  - Readings: gold COT late Aug 2023: smart money crossing to bullish, retail turning bearish ("big no-brainer"); Dow ~25-27 Aug 2023: undervalued vs ZB, GC and DXY simultaneously; platinum ~24 Aug 2023: "not close to overvalued" vs USD.
- B (S&D):
  - **Big brother / small brother**: "drop base ready [rally] coming from that Weekly demand so it's daily covered by weekly Big Brother small brother principle Perfect".
  - Unadjusted futures decide zone validity: spot XAUUSD and adjusted futures had broken the daily demand, "let's look at our custom Futures charts what are called unadjusted charts ... we are still in the middle of that demand zone"; "the only chart that was in demand in that high quality demand Zone was the unadjusted continuous gold chart".
  - **"Level on top of level" (protection)**: "we have a created a drop base rally followed by a rally base rally which is called a level on top of level so price is not able just to fall through".
  - **Leg-out quality**: needs "institutional", "decisive", "explosive" candle after the zone; otherwise risk of bear flag: "we definitely need here a decisive move explosive move here otherwise this could also ... end up to be just like a bare [bear] flag".
  - **Trailing stop**: "we created another R base really [rally-base-rally] another nice protection here so my stop losses ... will now go below that rally base rally on Monday" (stop moved below each new demand zone that forms in the trade direction).
  - Stop placement: "stop loss below that daily drop base rally" (Dow). Targets: "I expect here price to go higher back into this daily weekly Supply".
  - Analysis on completed candles: "I do it early morning of the next day so I can also analyze the completed previous Day candle".
  - Channel breakouts noted: "we broke through this parallel Channel which is now also of course super bullish" (discretionary).
  - News: entered US30 limit into Powell/Jackson Hole: "I expect volatility ... because Fed chair Powell is speaking now but so I expect to get filled" (no news filter).
- D (risk/results):
  - "I started trading Futures in 2013 and cfds in 2019"; "I took five prop film challenges since and I passed each and every one of them".
  - "putting 2% on the line with each trade if I have two positions open on my Platinum trade that's already 4% ... three open positions ... a 6% risk". Correlation awareness: 4% platinum + 2% gold all precious metals vs 5% daily limit; plan B = manual exit "so I don't lose more than 5% in one day".
  - Progress: +$8k (4%) by 24 Aug, +$11k (5.5%) by 27 Aug on $200k.

### 11. 20231217_The_Correlation_Trade_That_Passed_My_Challenge_n_in_1_Day.txt (2023-12-17; recorded 14-15 Sep 2023)
Content: FundedNext $200K verification passed in <24h with three precious-metal longs (gold, silver, platinum; caption also says "XPDUSD").
- A: none (no indicator detail; "I absolutely believe in my tools").
- B: none mechanical. Watches 1-hour chart near target only.
- C ("correlation trade" = stacking same-direction positions in correlated markets, NOT a spread/pair trade):
  - "correlation is extremely risky and you need to be absolutely sure of your positions because if things go south, your losses are also amplified".
  - "I went with 2% risk per trade times three open positions at the same time. This equals 6% risk, exceeding my daily draw down limit of 5%."
  - Entered "yesterday at 6 p.m. 644" (14 Sep 2023, 18:44), all three hit targets "in less than 24 hours".
- D: "Three trades, 24 hours, $10,000" (5% target on $200k); "proven to be effective five out of five challenges so far"; earlier fastest: FTMO verification "I passed in 5 days".

### 12. 20231225_How_I_Manually_Closed_My_US30___XAUUSD_Swing_Trades_At_Supply_Zones.txt (2023-12-25; recorded ~28 Aug 2023)
Content: week 4, closing all True Forex Funds positions manually to pass (8% = $16k per $200k account).
- A (indicators):
  - Valuation, Dow (~28 Aug 2023): undervalued vs all three refs, ZB primary: "Dow seems strong again because we are undervalued ... not ... only versus the treasury bonds which is usually the primary asset that I'm going to measure the Dow with ... but we are under valued versus dollar we are undervalued versus gold ... once we are undervalued versus all of them ... we don't get this very often but this is when we get a really really strong move".
- B (S&D):
  - **Freshness / zone consumption (explicit)**: "the past few times this area was rejected but it's the fourth or fifth time so I would expect all um unfield [unfilled] orders being filled in this particular area I would expect price to go through here".
  - Gold: "there's no strong Supply in this area ... this reacted from this Supply this reacted from this Supply ... so you see all the supplies are not fresh anymore which means that ... this is also not strong Supply so since it's not fresh it's not ... high quality I would expect price to go through these particular areas". -> rule: a zone already reacted from = not fresh = low quality = expect break-through.
  - Manual exit at opposing lower-TF supply when the move is stretched (challenge context): "Platinum is in a 4our [4-hour] supply Zone and we stretched that move already quite a lot ... that's why I'm closing now manually both Platinum trades".
  - Target adjustment to recent 4H highs to finish the challenge (discretionary).
- D: "it took us 16 days ... four trades 100% win rate on both accounts" ($400k True Forex Funds passed). Self: "I love trading indices and precious medals".

### 13. 20240104_What_10_Years_of_Trading_Actually_Bought_Me.txt (2024-01-04)
Content: family boat-trip vlog, Koh Samui. No method content.
- A/B/C: none.
- D: "I quit my corporate job 10 years ago and I'm a fulltime Trader ever since"; "last month I actually made $34,000 which I would consider on the lower side of things".

### 14. 20240115_The_Equation_Behind_Consistent_Trading.txt (2024-01-15)
Content: scripted mindset piece ("Protocols + Effective Routines + Feedback Loop + Habituation = skill development"). No method content.
- A/B/C/D: none (generic: keep a trading plan and journal; "protocols include strategies, configurations, rules, and procedures for preparing, analyzing, processing, and executing a trade").

### 15. 20240119_The_50-Year_Dow_Jones_Pattern_Most_Traders_Never_Use.txt (2024-01-19)
Content: free "campus stocks and indices yearly roadmap" PDF for 2024, based on the US presidential (4-year) cycle on the Dow. Many testable numbers.
- A (tools): presidential-cycle seasonality on US30. Data base: "this data goes back 50 plus years in time and during these 50 years we have experienced 12 election cycles"; "my overall research is based on over 100 Years of price information". He does not update for news: "am I going to update these forecasts based on news ... frankly I won't".
- C (testable claims, Dow Jones, "from 1973 to 2023"):
  - Average yearly change by cycle year: "in presidential election years it Rose by 7.84% it's excluding minus 32.7 2% drop during the 2008 financial crisis in pre-election years ... an increase of 16.31% post elction year saw a rise of 8.8% ... midterm election years the increase was just 1.54%".
  - "out of the nine times a president ran for reelection ... the incumbent won six times"; "it hardly matters for the stock market whether Republican or Democrat is elected in both cases higher prices have been observed at the year end"; "during these reelection years we've seen a more significant selloff in February March".
  - 2024 (election year) path he projects: top "late February to the beginning of March and the bottoming mid to late March" (short #1); "Dow to bottom around the third week of March ... rally throughout the entire month of April towards the beginning of may" (long #2); "the week [weak] month of May will give us shorting opportunities"; "a nice rally starting at the end of May until mid to end of August"; "two sweet spots for buying ... June 27th and July 25th"; "I expect the top to be between August 14th and September 2nd"; "between September 14th and October 29th is the weakest period in election Years ... a significant drop between 4% and 10% any try to take new highs in October is virtually impossible"; "a confident rally between 5% and 15% starting from the lowest point of October all the way till the end of December".
  - Longer view: "We'll have to wait until 2026 for that bearish sentiment" (i.e. midterm year 2026 bearish).
  - Earlier calls: Dec 2022 Instagram: "I predicted the 20 23 to be a bull year".
- Exact cycle construction (which years averaged, closes vs. path, detrended?) NOT given -> vague.
- D: none.

### 16. 20240126_Why_The_1__Rule_Is_Quietly_Costing_You.txt (2024-01-26)
Content: position sizing - argues for fixed dollar risk (R) over a fixed 1% rule. No indicator content.
- B (risk rules, stated):
  - Fixed-$ risk per trade, kept constant until the account grows a lot: "the fixed dollar risk approach is your best bet"; "find the dollar amount that you're comfortable with ... stick to that amount until your account doubles or even triples".
  - Size so you can survive a streak: "make sure you can handle at least 10 consecutive losses without ... going financially broke".
  - Set and forget: "choose an amount that allows you to forget about your trade for at least a day".
  - Measure in R: "rewards are measured as multiples of the risk taken for example to R means the reward should be double the risk".
- D: argues pros withdraw profits every few months so % sizing doesn't compound (backtests should probably use fixed-$ R, not compounding %).

### 17. 20240202_How_Smart_Money_Actually_Moves_Price__Leaked_Video_.txt (2024-02-02)
Content: commentary on the Jim Cramer "leaked" video; S&D logic in story form (punctuated, dubbed-style transcript).
- A: none.
- B (S&D basics, stated):
  - Supply zone = rally, base, drop (RBD) seen as "Price spikes, consolidation, and sharp price declines. Surge, bottom, decline. Exactly right. So we just identified the supply zone."
  - Drawing: "draw two lines around that level, a proximal and a distal line, highlight the area with a yellow box, and bring that level forward ... we wait for the price to return to that area, then we take action."
  - Rationale (unfilled orders): "the banks and institutions that sell here cannot sell everything they want to sell, otherwise the price would never have dropped so drastically".
  - News: ignore it as a decision input: "we don't know why media outlets release certain information ... That is why we can never make decisions based on that information."
  - Explosive candles = institutions: "those big, exploding candlestick charts? You know this is caused by banks and institutions."
- C: claim "when the market starts to go down, it goes down much faster than when it goes up" (fear > greed) - generic.
- D: none.

### 18. 20240217_The_4-Stage_Method_I_Use_to_Predict_Any_Market.txt (2024-02-17)
Content: his "umbrella strategy" = 4 sub-strategies: (1) fundamentals, (2) technicals (S&D), (3) futures / all asset classes, (4) CFD execution. Tool list as of Feb 2024.
- A (indicators) - the tool set he names here is **smart money index + "campus algo forecast" + "campus valuation"** (no "True Seasonality" by name in this file):
  - COT: "smart money Index this very tool will allow you to follow the institutional powerhouses ... we want to buy when they are buying and we want to sell [when they are] selling".
  - Forecast: "campus algo forecast using this tool we can consistently project the most upto-date projections of the next major Rally or decline in the future it is a powerful tool because it gives you a glimpse of future" (INFER: the projection tool; could be the seasonality/forecast line; details not given).
  - **Valuation = ratio to a reference**: "I believe that interest rates have an extreme influence on the price of stocks therefore I want to compare the price of equity indices like NASDAQ down S&P 500 on a ratio to interest rates and this would give us indication of whether the US Stock Market is priced relatively low compared to interest rates undervalued or if the stock market is priced relatively High compared to interest rates overvalued". -> supports ln(asset) - ln(reference) (= log of the ratio); reference for equity indices = rates (bond futures).
  - "hybrid AI": "a powerful server look at thousands and hundred thousands of relevant financial data points then filter those data points through sophisticated calculations back tests and logic ... it's hybrid because I fly it myself" (marketing; no parameters).
  - Roles: "fundamentals lack Market timing but they are much more predictive of when Major Market moves may take place"; "fundamentals always come before technicals".
- B (S&D): "technical analysis should be mainly used for finding good entry points stop levels and Target prices"; "the most accurate one is supply and demand period"; rejects lagging indicators (RSI, Bollinger, MAs): "price has to move first for the indicators to move as well".
  - Analyse on futures, execute CFD: "I apply all my fundamental and technical analysis on the underlying asset which is the Futures"; "I sometimes see big discrepancies between the price of the underlying asset of Futures and the cfd".
- C: universe (liquid futures): "equity indices like S&P 500 NASDAQ Dow Jones German Dux [DAX] or the niik [Nikkei] interest rates like treasury notes and bonds ... energies and metals like crude oil natural gas gold silver or copper currencies like the Euro British pound or the US dollar Index also agricultureal like corn coffee or sugar".
- D: "I only started my ft more [FTMO] journey in June 2022"; "number one Trader on ftim Mo's Global leaderboard for three consecutive months"; "listed on the ftmo leaderboard 120 times"; "over $1 million in payouts $4 million in funding".

### 19. 20240223_How_Compound_Interest_Actually_Grows_a_Trading_Account.txt (2024-02-23)
Content: compound-interest / wealth talk. One method line.
- A/B: **two-step process with execution timeframe**: "I focus on my twep [two-step] mechanical process step one getting biased in the market with my fundamental forecasting tools step two timing the market with technicals like supply and demand execution time frame daily or weekly charts".
- C: none (generic compounding maths).
- D: return expectation: "by following these simple steps and taking advantage of my 20 24 yearly Market forecast you can realistically make a solid 12 to 24% return per year" (and examples using 1%/month).

### 20. 20240301_I_m_The_First_Trader_Funded__2_000_000_Without_A_Challenge.txt (2024-03-01)
Content: VST Global adds a 2nd $1M (now $2M, no challenge); 6-month KPIs; "offense/defense" talk. Results + risk rules only.
- A: none.
- B (risk, stated):
  - **Funded-account risk = fixed 1%**: "I risk 10k per trade. That's my standard. That's 1% of my $1 million account. And now it's 20K since my account grew to $2 million."; "if I'm trading a $100,000 account, my exposure would be $1,000 per trade. That's one R." (vs 2% per trade in the 2023 challenges, files 4/10/11).
  - Annual target in R: "I made 120K in 6 months. So, I earned 12R. And I forecast I will end the year making between 18 to 24 ... RS which means I earn roughly 20% yearly".
- D (VST account, ~Aug 2023-Feb 2024):
  - "32 trades taken. Average trade length, 22 days. Best trade, roughly $20,000 or $3,541 pips [garbled]. Worst trade roughly $47 or minus.1 pips. Highest draw down $2.77% [2.77%] 12.66% gain by taking 1% risk per trade only and 100% win rate."; "I still haven't experienced any meaningful losses, only a few break even trades."
  - "more than $120,000 in payouts ... roughly 12% of profits in 6 months only. Actually, it was exactly $137,000, but I had to pay 15K in swaps alone." (swap drag ~11% of gross).
  - Date slip: says first million received "on the 3rd of August 2022" (file 8 says 2023).
  - REALISM NOTE: 32 trades / 6 months with avg hold 22 days -> ~5 concurrent positions on average (INFER); "100% win rate" counts break-evens as non-losses.

### 21. 20240309_The_Million_Housewives_Who_Moved_The_Currency_Market.txt (2024-03-09)
Content: history story on "Mrs Watanabe" yen carry trade (1990s-Abenomics). No method content.
- A/B/D: none.
- C: only historical narrative (carry trade unwinds into yen spikes in Aug 1998 and 2008). No rule with numbers.

### 22. 20240316_5_Reasons_Why_I_m_NOT_Scalping_Forex__As__1_FTMO_Trader_.txt (2024-03-16)
Content: anti-scalping; swing-trading lifestyle. Useful frequency/KPI numbers.
- A: none.
- B:
  - Timeframes: "I started analyzing the monthly weekly and daily charts"; "swing trading with a focus on the daily time frame charts allows you to avoid all the intraday noise".
  - R:R: "with a daily chart signal your risk reward ratio can be one to two one to three or even better".
  - Time spent: "set aside 15 to 20 minutes in the morning and another 15 to 20 minutes in the evening"; "spend just 20 to 40 minutes each day monitoring higher time frame charts".
  - Risk: "managing a hefty 3 million of prop ... Capital taking just 1% risk per trade means you're putting a whopping $30,000 at stake".
- D (targets/realism): **KPIs: "40 to 50% win rate and more importantly two RS per month on average and between 20 to 24 [R] per year"**; frequency: "some months I might only make four or five trades instead of 30 to 50"; "120 [leader]board appearances in less than one and a half years".

### 23. 20240323_The_Overtrading_Fix_That_Took_Me_to__1_on_FTMO.txt (2024-03-23)
Content: overtrading causes and fixes (scripted/dubbed transcript). A few rules.
- A: only the "stars aligned" idea as the A+ filter: "Make sure you choose only the highest quality trading setups. I call them 'the stars have aligned' settings. You can call them A+ level setups. Make it your rule to only take A+ level setups." (cf. file 4 where he traded a 2-of-3-stars setup; INFER: 3/3 = A+, 2/3 is tradable but lower grade).
- B:
  - Limit entries, never chase: "Professionals never chase price. They let the price come to them."
  - Re-entry after a stop (stated here): "If the trade breaks this level and closes at the stop, this is no longer the setup we believed in." (vs file 7 where he planned to re-enter platinum lower on fundamentals - mild contradiction).
  - Day-trading time window (for day traders): "if you are trading in the American session, only place trades in the first 2 hours of the session".
  - Optional caps: "Consider setting a maximum number of trades per day, week, month, or a maximum loss limit"; ignore outside research: "avoiding reading research reports and outside signals".
  - Risk: fixed money risk model (refers to file 16).
- D: "32 trades on my $ 1 million funded account ... My best trades brought in almost $ 20,000, while my worst was only $48. So ... I haven't had a single losing trade."

### 24. 20240331_How_I_Predicted_the_Peso_Crash_2_Years_Early___Full_Setup.txt (2024-03-31)
Content: full top-down setup on Mexican peso futures ("MP1", monthly -> weekly) around the June 2024 Mexican presidential election. RICH: shows how COT + valuation + zones are combined.
- A (indicators):
  - **COT on the monthly chart, RETAIL line used as contrarian**: "This is the smart money index. The red line that you see here is the retailers or in other words, the dumb money. We want to buy when they are selling and sell when they are buying. When the indicator is pointing all the way up, it means the retailers are buying aggressively. And when it's pointing all the way down ... they are selling." Normalised to own history: "the retailers were always at the low right before the elections compared to their previous behavior. So June 2006, low relative to where they were before. June 2012 ... June 2018, same exact thing." and "three to four months before the elections. They were very bullish compared to their previous behavior ... It dropped all the way to one month before the elections."
  - **Valuation on the WEEKLY chart, bounded scale**: "Let's go to the weekly chart now and load up the valuation tool ... The Mexican peso was undervalued versus the dollar plotted as the purple line. That's why it's almost touching the floor here, extremely undervalued. It also appears to be relatively low to the bonds plotted as the blue line and gold as well, which is the yellow line." (same 3 refs/colours; "touching the floor" fits a min-max scaled oscillator).
  - **Order of operations (explicit)**: "price follows the fundamentals. That's why I only apply technical analysis after the confirmation from the valuation tool and the smart money index."
  - **Entry checklist for the May 2024 long-peso trade**: "First, I'm waiting for the price to drop, maybe into this weekly demand here. This will be followed by a signal from the smart money index that retailers are very bearish relative to their previous behavior. Next, I want to see this purple line drop all the way to the bottom. This means the Mexican peso is undervalued versus the dollar. Ideally, I want to see all three, gold, bonds, and dollar undervalued in May." (DXY is the must-have ref for an FX future; all three = ideal.)
  - Mirror for the short: "if it does [rally], we'll have to be overvalued versus the dollar, and we'll see the retailers on the smart money index extremely bullish".
  - Readings: MXN futures retail COT very low in June 2006, June 2012, June 2018 and high 3-4 months before each election; 2012 and 2018 pre-election bottoms: peso "extremely undervalued" vs DXY and "relatively low" vs bonds and gold. 2024 expectation: retail "very bullish" before the election = "my first go signal" for a short peso (long USDMXN) "late March or in April"; main trade = long peso (short USDMXN) from the May 2024 bottom.
- B (S&D):
  - Top-down: "let's start where every trader should start, the monthly chart"; bottoms formed at monthly demand: "it bottomed where there was monthly demand"; entry zone = "high quality weekly and monthly demand zones".
  - Futures analysis, CFD execution with inversion: "this chart is the peso futures while on the forex pair it's going to be the USD Mexican peso so it's inverted".
  - Holding: "hold it through the election month in June ... and maybe even hold on to that all the way into mid or the end of the year".
- C (testable hypothesis, Mexican election cycle on MXN futures, monthly): "Prior to each election, the market drops. However, the election month itself is always a green candle. And this is always followed by a pretty long rally."; "the bottom or the start of the rally is always in a month prior to the elections month"; "it has been doing so for the past 24 years with exactly the same results each time". Elections: Jul 2000, Jul 2006, Jul 2012, Jul 2018, Jun 2024. n = 4 cycles ("we have 24 years and four previous election cycles").
  - EXTERNAL CHECK (my knowledge, not from transcript; verify with data): the June 2024 election month was a sharp peso SELL-OFF (USDMXN ~17 -> ~18.3+), i.e. the "election month always green" rule failed out of sample in 2024.
- D: none.

### 25. 20240409_Why_I_Walked_Away_From_My_Own_Prop_Firm.txt (2024-04-09)
Content: story of the aborted "My Campus Fund" prop firm (Eightcap + PropTradeTech, B-book-only offer refused). No method content.
- A/B/C: none.
- D: he shares trades with students: "I share all my trades with our campus students and obviously most of these trades are successful"; started FTMO prop trading ~2022 ("I had only two three month of prop trading under my belt with ftmo" at end of 2022); paid ~"$220,000 [or $20,000; caption unclear] to launch this prop firm".

### 26. 20240414_The_Stock_Market_Follows_a_10-Year_Pattern__Almost_Nobody_Uses_It_.txt (2024-04-14)
Content: decennial cycle (Edgar Lawrence Smith 1938, Yale Hirsch) on the S&P 500, his updated table. Testable.
- A (tool): decennial table on S&P 500 monthly; used as "road map", explicitly NOT a timing tool: "I never claimed Cycles are perfect or that we should use them to time our positions ... they give us perspective or a road map for each year in the decades to come"; timing still by S&D. "apply the desal [decennial] pattern on the S&P 500 monthly chart that's it".
- C (testable claims; S&P 500, "140 years of relevant data points ... 14 decades"):
  - Tops in years ending 7 and 0: "decades ending with sevens and zeros like 2000 or 2007 or 2020 that is when we should expect tops".
  - Bottoms in years ending 2 and 3: "years ending in two or 3 like 2003 2012 2023 or even 1992 these are the years where the stock market usually bottoms"; "we see some small recovery by the end of those years".
  - Year 1: "in all the years ending with one we have seen four negative years and nine positive years".
  - Year 5: "almost 300% change in percentage" summed over decades; "of all 14 decades we have seen the market [rise] 13 times and the one year that appears as negative was only negative by 1%".
  - Years 8 and 9: "also amazing" (no numbers).
  - Years 7 and 0: "we have more negative years than positive ones and the overall performance in those years alone is even negative by minus 40% and minus 20%" (which digit gets which number is unclear; INFER: performance row = sum of annual % changes per year digit).
  - 2020 call: "I was among those who predicted a crash in 2020"; brother Yan (campus mentor) in 2021: buy in 2022.
- B: long-term trades can be held "anywhere between one year to 20 years" (index CFDs with swaps).
- D: none.

### 27. 20240427_Supply___Demand_Zones__The_Rule-Based_Method__Full_Walkthrough_.txt (2024-04-27)
Content: "supply and demand prop trader series", lesson 3: zone anatomy, line placement, 3-step zone search. KEY S&D FILE. (Terminology is Online-Trading-Academy style: proximal/distal, leg-in/base/leg-out, "zone qualifiers".)
- B (S&D, stated rules):
  - Anatomy: "a zone or level always consists of three parts leg in base and leg out".
  - DBR: "first a drop in price that is our leg in then some basing that is our base and suddenly you get a strong move out to the upside from that area which is our leg out now the base in this area represents your imbalance ... where we can find unfilled buy orders ... drop base rally visually it looks like a u shape"; RBD = "inverted u- shape".
  - **Demand line placement**: "the proximal line will be drawn across the top of the bodies of the basing candles the dist[al] line is going to be drawn below the low or in this case I use the wigs [wicks] because they happen to be low but if there were no wigs I would just use the bottom of the bodies of the candles so whatever the low low is that's what I'm going to be drawing for my dist line".
  - **Supply line placement**: "across the top of the wig or the high for the basing candles [= distal] the lower line is going to be the proximal line and that will be drawn across the bodies of the basing candles".
    - GAP: whether proximal = highest body top among base candles (INFER yes), and whether the distal uses only base candles or also leg-in/leg-out extremes - not stated here.
  - **Zone search (3 steps)**: "we start off always at the hard right Edge ... current price ... look left and down until we find the origin of a strong r[ally] in price ... you have to go along the candles without cutting through them"; supply = "look left and up for the origin of a move".
  - **Leg-out qualifier**: "the size of the leg out is one of the institutional footprints that we call Zone qualifiers we have many of those Zone qualifiers"; reject: "we have only one green candle that's starting off the bullish move and we already pause that's not what I want to see for a demand zone"; want: "we want to leave the levels with large green candles the larger the candles the bigger the imbalance"; supply: "the leg out has to be explosive strong ideally multiple candles"; zone must be at "the origin of an overall move".
  - **Entry/stop**: "place your set entry at the proximal Line stop loss below the dist line"; targets: "we haven't discussed the rules for Target yet ... something for the entire blueprint course" (GAP).
  - Example timeframes: "oil Futures 240 minute chart weekly income"; "Uber ... 72 minute chart ... weekly income strategies" (INFER: "weekly income" = a shorter-TF style in his course).
  - Base-candle definition (body vs range, max count): NOT given (GAP).
- A/C/D: none.

### 28. 20240428_My_Full_Process_for_a__2.1M_Prop_Challenge__USD_CHF_Setup_.txt (2024-04-28)
Content: first trade of his live $2.1M (6 firms) challenge: short USDCHF (= long CHF futures). FULL WALK-THROUGH OF ALL THREE TOOLS + ZONES + STOP RULE. KEY FILE.
- A (indicators):
  - **Raw COT, weekly, 3 groups, on the unadjusted CHF futures chart (TradeStation)**: "we start with the cut [COT] report and you see here up here the the red lines this is the retail data and Below these are fund managers very important these are actual positions in the market this is not sentiment ... this is the Swiss frank Futures un adjusted chart on trade station the weekly chart".
    - Groups he names: retail (red), "fund managers" ("the funds are Trend followers"), and "the Smart money the users and producers". INFER: legacy-style split = commercials (smart money; he uses the disaggregated words "producers/users"), non-commercials/large specs ("funds"), non-reportables ("retail"). Which CFTC report is NOT stated.
    - Normalisation = relative to own history: "we look at cut data always based on how do they behave how do their position look like based on the previous data ... compared to their previous Behavior".
    - Retail contrarian: "when they are very bearish ... price starts to Rally ... retailers are always wrong in the market" (he counts ~11 past instances on the weekly chart).
    - Funds at multi-year extreme = contrarian too: "they're now right now very very bearish and they're as bearish as basically there were in the past well since 2008 ... and there were one more time 2018 and this is basically also when price started to Rally".
    - Smart money: "they're really bullish compared to their previous behavior ... whenever they're extremely bullish compared to their previous Behavior ... price is [rallying]".
  - **Smart money index rule (both extremes, opposite sides)**: "our smart compos [= "campus"; file 29 says "our compass smart money index"] smart money index that basically translates that c[ot] data into an index ... we have two horizontal lines on our index the green and the red ... I want to see the smart money and the retailers at the opposite side ... I want to see the retailers down here in that extreme and on the opposite side I want to see the smart money here ... we are in an total extreme here the smart money is extremely bullish and the retail money is extremely bearish". Not timing: "it doesn't mean it happens tomorrow right it's not a timing tool it's a weekly chart".
  - **Valuation (FX future -> vs dollar)**: "I'm looking at valuation here versus the dollar obviously here we're talking Swiss frank USD ... since it's the Futures chart I need to be undervalued versus the dollar and now ... I was already undervalued I'm coming from undervalued"; symmetric: "whenever we are under valued we can ... look for a long and if we are overvalued ... we would look to go short"; not timing: "it's not a timing tool also it can take some time". Admits a failure: "here you see undervalued but it didn't really work here".
  - **Seasonal forecast = "seasonality with a twist"**: "we look at the forecast which is based on a ... seasonality tool with a Twist let me call it with a Twist because it's not only real seasonality because here we can also forecast the future here and what we see here basically is ... the tool is forecasting a low around well second week of May until ... end of June so almost for two month"; precision: "it's not always accurate by the day the forecasting tool it gives us also an indication ... when we see a bottom and when we see a top".
  - **Combination**: "we want to have all stars aligned ... we don't want to only have one tool speaking one language we want all the tools speaking the same language"; here COT + valuation + forecast all bullish CHF -> "super biased".
  - Readings (CHF futures, ~26-28 Apr 2024): retail "very bearish" (from very bullish); funds most bearish since 2008 (also 2018); smart money extremely bullish -> index at both extremes; valuation vs DXY "coming from undervalued"; forecast low ~2nd week of May 2024, up until ~end of June 2024.
- B (S&D):
  - **Big brother / small brother top-down M -> W -> D**: "I start with a monthly chart so I want to use what I call Big Brother small brother principle ... we are in a monthly demand zone ... in a drop base R[ally] we are here in a weekly level on top of level ... drop base really overlapping level followed by an rally base rally ... we are covered by monthly we are covered by weekly and now if we look at the daily chart here because I want to time it based on the daily chart".
  - Execution on the CFD (inverted): entry zone on USDCHF daily: "we are here in that rally base drop preferred version so that proximal line here this is going to be my entry" (INFER: RBD/DBR reversal formations "preferred"; not defined here).
  - **STOP RULE (explicit)**: "the red line is this is a simple rule I use 33% of the zone as my stop loss" (INFER: stop = distal line + 33% of zone height beyond the distal).
  - **Targets**: draws 1:1, 1:2, 1:3; "I put a one two three Target for now because this is where the opposing weekly Zone Starts" -> target = 3R, coinciding with the opposing weekly zone. Price numbers garbled ("entry ... 9727 stop loss 92679 ... target ... 88 87 0").
  - Risk: "I take 2% risk per trade entry to stop loss ... Target here is a 6% basically".
- D: "$2.1 million in challenge value across six different prop firms"; trade called before fill ("call every single trade I take before it happens").

### 29. 20240504_How_I_Trail_My_Stop_Loss_Using_Supply___Demand_Zones.txt (2024-05-04)
Content: management of the USDCHF short from file 28 (it worked). Transcript looks machine-translated ("deal" = trade, "offer zone"/"bid zone" = supply zone). KEY MANAGEMENT FILE.
- A (indicators):
  - COT update cadence: "every Saturday, our c[ampus] smart money index is updated, and I want to see if anything has changed in the behavior of retail traders". Reading: CHF retail "a little more bullish, although still in that extreme zone" one week, then "becoming even more pessimistic compared to last week" -> "this movement is definitely not over yet".
  - Valuation has a midline/average: "we're moving from undervalued to higher, but we're not even near the average ... we're not even close to an overvalued state where we would expect a correction". Reading: CHF vs DXY early May 2024: rising out of undervalued, still below average. (Supports a centred scale, e.g. [-1,+1] with 0 = average.)
  - **Name equivalence**: "our algorithmic forecast, which is our seasonal forecasting tool with a twist" -> the "campus algo forecast" of file 18 IS the seasonal forecast. Reading: CHF "the optimism will last until almost the end of June" 2024.
  - "our smart money index, which is based on COT data".
  - Fundamentals used to decide how aggressively to manage: "we need to know how aggressively we want to manage this position. That's why we first need to see fundamentally what to expect next".
- B (S&D / management, stated rules):
  - **No partials, single target**: "single target works best, which is, roughly speaking, 'hit or miss.' Yes, I manage trades, but I never, ever take partial profits."
  - **Break-even at 1R, swap-adjusted**: "since the price has already reached a one-to- one ratio, for me this means moving the stop loss exactly to the breakeven point"; "you don't want to bet it exactly at breakeven. You need to take swaps into account ... place it at a level that covers the swaps".
  - **Trailing behind new zones on lower TF**: "switch to a smaller timeframe ... the 240- minute chart ... you pull your stop up based on supply and demand ... always move your stop loss above the next supply zone that is created ... on a 240- minute chart. And if you want to follow the deal more closely, you switch to the 60- minute chart". Summary: "at 1:1 the rules are clear: we move our stop loss to breakeven, taking into account swaps, and then you can start following the deal based on the offer [supply] zones. That is, always place your stop loss above the newly created supply zone."
  - Near target, protect >= 2R: "when the price gets close to our target ... we're going to trade on a shorter timeframe because ... we don't want the price to get to a risk- reward ratio of 2.5 to 1 ... [and] go back to 1, so we want to lock in at least two 'Rs'" (target here ~3R per file 28).
  - **Adding (pyramiding) after BE**: "if the price actually goes back into that supply zone ... 'fall-base-fall' [DBD], we would potentially open a short again. And that's how you can add to a position, by the way, when your initial stop loss is at breakeven."
  - **Freshness / exhaustion**: "This is the initial level of demand. He touched it once, twice, three, four times. So he absorbed all the unfulfilled orders. So the next time the price drops, it will break through this zone, and there is literally nothing below this zone. It's all air."
  - Reversal candle: "We have a bullish engulfing on the weekly timeframe. This is the mother of all price reversal candles"; "coming from weekly and monthly demand, plus from this level we have a reversal candle".
  - "The trend is your friend until the very end of the range."
- D: many viewers copied the trade ("You guys even passed the challenges just because of this one deal").

### 30. 20240508_The_Futures__Mini_Gap__That_Predicts_Reversals__Forex_Can_t_Show_You_This_.txt (2024-05-08)
Content: $2.1M challenge ep. 3: mini-gap definition, "level on top of level" entry options, explicit ADD-ON RULES. KEY FILE.
- A (indicators):
  - Seasonal forecast used for timing context on the DAILY futures chart: "using our campus algo forecast our seasonal forecast with a Twist ... that dip here was forecasted quite nicely by our tool and now the bottom the bottom of all bottoms big bottom at least is supposed to happen tomorrow so it makes sense it aligns It lines up with our entry". Reading: CHF futures forecast big bottom ~9 May 2024.
- C (**mini gap definition**):
  - "here on the 180 minute chart ... this is what I call ... a mini Gap ... mini gaps are only visible on Lower time frame charts and they usually happen during High volatility periods or very very low volatility periods ... from this candle low to this candle the next candle open we have this Gap here and these mini gaps based on my observ[ation] usually act like a magnet".
  - "you don't see them very often but if you see them then they're usually getting filled very quickly"; "you only see them on the Futures charts on Lower time frame charts you could even go down to 60 minutes".
  - Use: gap sits inside/near the demand zone -> expect price to fill it and then turn: "this Gap is just right right into this demand Zone ... if price drops into that Supply Zone filling this mini Gap ... I would expect if we come lower this is where price will go and will stop and then from here from this Zone price is going to Rally".
  - INFER (definition for code): on futures bars of 60-180 min, gap-down if Open[t] < Low[t-1] (gap-up if Open[t] > High[t-1]); hypothesis: unfilled gap is filled (price trades back to Low[t-1]/High[t-1]) within N bars. N not given ("very quickly").
- B (S&D):
  - Entry refinement on futures + CFD at 180-min: "both charts on 180 minutes 3 hour charts and this is where we're going to Define our entries".
  - **Level on top of level (supply)**: "a supply zone drop base drop followed by another drop based drop and this is what I call a level on top of level the lower level is the proximal level the upper level is the distal level". Three placements: proximal-only (stop above lower zone; best R:R but can be stopped before the upper zone), distal-only ("less likelihood to get filled" but "very high risk to reward"), or combined: "I combine it to one I sacrifice on risk to reward" with "my stop loss just a little bit Above This distal level" (stop = beyond the upper zone's distal + small buffer).
  - **ADD-ON RULES (explicit)**: "rule number one put your initial stop loss to break even ... rule number two is fundamentally still same scenario right nothing has changed fundamentally that's why we are allowed to add on and rule number three technically or we can just say supply and demand high quality level"; "it's basically just a new position with like the same rule set being applied". Risk on the add-on: "again 2% risk on that combined level".
  - Uses a 4-hour supply zone as an (already triggered) add-on zone: "the 4-Hour Supply Zone on the USD Swiss frank triggered already".
  - Classical pattern as confluence (discretionary): "a picture perfect Head and Shoulders setting up on the Swiss frank ... technical Head and Shoulder targets ... makes also sense because here we have another very very high quality ... demand which is also Daily and weekly demand".
- D: challenge goal stated: "pass this challenge ideally with higher time frame trades".
