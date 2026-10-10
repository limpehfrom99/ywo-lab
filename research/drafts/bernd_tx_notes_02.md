# Bernd Skorupinski transcripts, batch 02 (30 files, 2024-05-11 to 2025-01-17)

# SYNTHESIS

Coverage: all 30 files read in full. Method content is concentrated in 02, 04, 09, 11, 13, 15, 16, 17, 19, 21, 27 and 30, with partial content in 06, 07, 14, 24, 26, 28 and 29. The rest (01, 05, 08, 10, 12, 18, 20, 22, 23, 25) are vlogs or business videos.
File numbers [NN] refer to the per-file sections below. "INF" = my inference, "GAP" = he does not say.

## 1. Indicator evidence

| Setting | What he says [file, date] | Verdict vs our reconstruction |
|---|---|---|
| COT report type | Never named. The raw chart shows "retailers" (red), "fund managers" (yellow/orange) and "commercials ... the producers" (blue) [02, 2024-06-02]. He uses the same view for silver, MXN, CHF, EC and DX futures. | GAP. The labels fit the legacy report (commercials / non-commercials / non-reportables) with his own names. "Fund managers" and "producers" hint at the disaggregated report, but he uses the same view on financial futures. |
| COT groups in the index | The index panel has two lines: retail (red) and commercials (blue) [02]. MXN is read on retail only [04]. EC and DX are read on retail only [27]. | Refines: compute an index for retail and one for commercials. Retail is his main contrarian input. Large specs are not used in the index. |
| COT lookback | A "weeks look back" input. He uses 26 ("six month"), 52, 104 and three years: "three year that's the maximum that I look at" [02, 04]. Signals are graded as 6-month, 1-year, 2-year or 3-year extremes; a 3-year extreme means a "monster move". | Partly confirms 157 weeks (it is about his 3-year maximum, 156). Refutes a single window: he steps through 26/52/104/156 and treats the longest window still at an extreme as the strength. He also cites full-history extremes ("most bearish ever ... back to 2011", DX [27]; commercials "highest ... in the last four years", CHF [09]). |
| COT thresholds | Green (upper) and red (lower) horizontal lines, with no numbers. He treats "above the green line" as the same thing as "the most bullish in the past two years" [02]. | 20/80 is NOT confirmed. INF: his wording fits thresholds near 0/100 better than 20/80. Check this on his screenshots. |
| COT combination | Best case: retail at one extreme and commercials at the opposite extreme ("we hardly have that") [02]. Single-group extremes are also shown before moves [02, 04]. "We always want to trade against the retailers" [02, 04, 27]. In [09] the raw COT and the "smart money index" count as two separate green lights. | Add an "opposite extremes" flag as the top grade. |
| Valuation references | A toggleable set that includes the dollar, treasury bonds and gold [02]; "interest rates gold dollar Index bonds" [26]. Chosen per market: silver uses gold ONLY ("remove ... the treasury bonds ... don't necessarily care about the dollar") [02]. MXN, CHF and EC use the US dollar [04, 09, 27]. DX uses the EURO [27]. | Confirms DXY/ZB/GC as the reference set, but they are not always all used. Choose the references per market. "DX vs Euro" is not in our triple. |
| Valuation length | "my length how many candles I can go back ... switch between short-term valuation long-term valuation" [04]. He uses "long-term valuation" for silver and MXN [02, 04]. No numbers are given. | 480 and 10 are NOT confirmed. One length input switches between short-term and long-term (INF: either the smoothing/ROC period or the normalisation window). |
| Valuation thresholds and scale | Horizontal lines: "close to the red horizontal line which means we're getting overvalued"; for DX, "a little bit around the mean" [27]. Shown on a daily chart [27]. Being close to a line counts as support [04, 27]. | ±0.75 is not stated. A centred oscillator is consistent with a [-1, +1] scale. Red = the overvalued line. The daily timeframe is confirmed. |
| Valuation data | "I can run all of my tools like valuation and algo forecast on the C[ME] charts" (TradeStation) [27]. | Feed it futures data (he prefers unadjusted continuous contracts). |
| Seasonality years | "15 years forecast so looking at 15 years historical data and then we are projecting" [02]; "looking back at 15 years of data" [09]. | CONFIRMS 15. |
| Seasonality projection | His readings span about 4 weeks (silver [02]), about 6 weeks (YM, late May to July [14]) and about 9-10 weeks (MXN, 10 June to "mid of August" [04]). | 30 days is NOT confirmed: his readings run past 30 days. |
| Seasonality method | Not described; averaging and detrending are a GAP. The tool is named "campus algo seasonal forecast" [27]. He reads turning points: "paints a similar picture only shifted a few weeks into the future" [09]; "you cannot go exactly by the date" [04]. | Agreement = the direction of the projected path over the next weeks, with a timing tolerance of a few weeks. |
| Tool combination | "two out of three rules met ... all three rules met It's All Stars aligned trade" [02]; "three out of three ... my fundamental rules are met" [04]; "I don't need to have every single one of them giving me the green light I do want to see as many of them agreeing" [09]. Beginner rule: "only enter trade if all stars are aligned" [06]. No override order is stated. | Score = the number of agreeing tools; 3/3 = "All Stars aligned". He never explicitly says whether 2/3 is tradeable. COT is the lead input in every example. |

Concrete readings
- Silver, 2024-06-02: retail COT at a 3-year bullish extreme and commercials at a 3-year bearish extreme. Seasonality flat for a few days, then down for about 4 weeks. Overvalued vs gold. Trade: short around 31.2-31.3 [02, 09].
- MXN futures, 2024-06-09: retail COT at a 6-month bearish extreme, entering a 1-year extreme, in a 2-year extreme, not yet at a 3-year extreme. Seasonal bottom around 14 June and high around mid-August. Long-term undervalued vs USD. Trade: long MXN, i.e. short USD/MXN [04]. 3-year retail extremes also marked the Covid 2020 bottom and the October 2023 bottom [04].
- CHF futures, about 2024-04-28: retail extremely bearish; commercials at their highest in 4 years; the smart money index rising sharply. Undervalued vs the dollar. The algo forecast showed a revisit of the bottom. Trade: long CHF, i.e. short USD/CHF [09]. On 2024-06-02 retail was even more bearish [02].
- EC (Euro FX futures), 2024-09-18: retail quite bullish vs its prior behaviour (it was bearish weeks and months earlier). Close to overvalued vs USD. Seasonal top, then a sharp decline [27].
- DX, 2024-09-18: retail "most bearish ever" (data back to 2011; "not seen in 15 years"). Valuation vs the Euro around the mean, nearing undervalued. Seasonal bottom, then a sharp rally. Trade: short EUR/USD, held 4 days, +$24k [27].
- YM, late May 2024: seasonal low at the end of May, a one-week rally, then the real rally from the end of June into July [14]. NQ, September 2024: "dropping ... as expected September drop" [15].

Other tools found
- CME gaps on unadjusted continuous futures (overnight gaps, rollover gaps and a "mini gap"). He expects them to fill and uses them as targets [04, 27, 29]. For FX trades, the adjusted and the unadjusted futures chart must both reach a level [27]. TradeStation symbols: @EC=103XN and @DX=103XN [27].
- A 3% ZigZag for pivots [19] and a 33%/66% split for location [16].
- Not in this batch: the Bitcoin tool, open interest, the "3 entry models", flip zones, and decennial detail beyond a teaser.

## 2. S&D rules as if-then (with gaps)
1. Candle class [11, 13]. Body = |C-O|, range = H-L. Indecisive if body <= 50% of range. Decisive if body > 50%. Explosive if body > 70% AND the candle is "abnormally bigger than the previous few candles" (GAP: number of candles and the size multiple). A candle with a small range "in context" counts as indecisive whatever its body ratio.
2. Zone [11, 13, 16]:
   - Leg-in: a decisive or explosive candle.
   - Base: one or more indecisive candles (GAP: maximum count; his examples use 1-4).
   - Leg-out: an explosive candle, OR "abnormally bigger candles that are decisive if they're followed by another decisive candle".
   - HTF location zones only need a decisive or explosive leg-out. Fallback: "everything that looks like a level is a level".
   - Identify the leg-out first, then the leg-in, then the base. DBR/RBR = demand, RBD/DBD = supply.
3. Lines [15]:
   - Demand proximal: the highest high of the base (wider version) or the highest body of the base (preferred version).
   - Demand distal: the lowest low of leg-in + base + leg-out for DBR, or of base + leg-out for RBR.
   - Supply is the mirror image.
   - Wider = more fills; preferred = better R:R; "no right and wrong".
4. Freshness [13, 16, 26]:
   - LTF zone: invalid once price has come back and touched it.
   - HTF location zone: measured on the preferred version. About 25% penetration is allowed; 50% or more = invalid.
   - Originality/authenticity is named but not defined (GAP).
5. Location [16, 17]:
   - Take the nearest fresh HTF supply above price and the nearest fresh HTF demand below it.
   - Split the range between their distal lines at 33% and 66%.
   - Labels run from very cheap (inside the demand zone) through equilibrium to very expensive (inside the supply zone). How the zones and thirds overlap is my inference.
6. Direction [19]:
   - On the same HTF, use 3% ZigZag pivots: the last 3 highs and 3 lows, excluding the current unconfirmed swing.
   - Uptrend = two higher lows. Downtrend = two lower highs. Otherwise sideways.
   - GAP: the exact comparison is not defined.
7. Action matrix [30]:
   - Demand: allowed at low/very low (grade A in an uptrend, B sideways, C in a downtrend), or at equilibrium in an uptrend (B).
   - Supply: allowed at high/very high (A in a downtrend, B sideways, C in an uptrend), or at equilibrium in a downtrend (B).
   - Never demand at a high location; never supply at a low location. Equilibrium + sideways = no trade.
   - This supersedes [16], which called equilibrium a "no touch area".
8. Big brother / small brother [17, 02, 09]:
   - The LTF zone must lie inside an HTF zone on the same side ("covered"), ideally daily inside weekly inside monthly.
   - Enter at the LTF zone, not at the HTF zone's proximal line.
9. Timeframes [16, 02]:
   - Swing: HTF weekly and monthly; LTF from 600-minute to daily (he uses daily, 960, 720 and 240-minute).
   - Day trading: HTF daily; LTF 2-8 hours.
10. Entry [03, 15, 02, 04, 27]:
    - A resting limit order at the LTF proximal line, set and forget. Overlapping zones may be merged. He may front-run slightly to improve the fill.
    - No confirmation needed [03]. Shooting stars and engulfing candles are only "add-ons".
    - For FX, the futures charts must also be at a zone.
    - GAP: the "3 entry models" and the "sniper" rules for lower-timeframe entries.
11. Stop [15, 02, 29]:
    - "Below the distal ... not on the distal" (GAP: buffer size), or beyond the swing pivot [02].
    - A deep stop when the COT reading is extreme [29].
12. Target [17, 02, 04, 06, 14, 27]:
    - The next opposing HTF zone; ignore opposing LTF zones.
    - He draws 1:1, 2:1 and 3:1 lines. In challenges he holds until the account passes. No target when he expects new highs [14]. A gap fill is the first take-profit.
    - Starter rule [06]: move to break-even at 1R, take profit at 2R.
    - GAP: no minimum R:R.
13. Risk [02, 15, 24, 26, 28]:
    - A fixed dollar risk per trade, whatever the zone size.
    - 2% per trade in the 2024 challenges; 1-1.5% ($10k-$20k) on his $1-2M private account; "1 to 2%" in general.
    - GAP: maximum positions per idea (the USD/CHF initial trade and add-on were each 2%).
    - News: discretionary; he sometimes goes flat before big news [26].

## 3. Other testable hypotheses
- H1 Presidential cycle (S&P 500 since 1900) [21]:
  - Post-election year: average +5%, up in 13 of 27 years.
  - Midterm year: the only negative year.
  - Pre-election year: average +13%, up in 21 of 26 years.
  - Election year: average +9%, up in 18 of 26 years.
- H2 Election-year path [21]: a high in April, a seasonal low in May, a peak around September, a low around the early-November election, then a year-end rally. Trade: long US index from the election to the end of December (claimed +9% in both 2016 and 2020).
- H3 Decennial [21] (caption figures garbled): year 4 up 8 of 13 times, "+88%" (likely 8.8%) from the seasonal low; year 5 ("phenomenal five") up 13 of 14 times, "300%" (likely 30%).
- H4 Dow 2024 roadmap [28, 14]: bullish April; "sell in May"; bullish summer to August; short early September; long from end of October through the Christmas rally.
- H5 Futures gaps [04, 27]:
  - Daily gaps on unadjusted CME futures (not visible on spot FX) fill "rather quickly".
  - Rollover gaps act as targets.
  - Test: fill probability within N days.
- H6 COT windows [02, 04]: forward returns after retail and/or commercial index extremes at 26, 52, 104 and 156 weeks; larger moves for longer windows.
- H7 Valuation [09, 04]: "every single time silver was overvalued versus gold the price crashed"; MXN long-term undervalued vs USD = bottoms.
- H8 MXN around Mexican elections (2006/2012/2018 used as a back-test for 2024) [29].

## 4. Five quotes for coding his tools
1. "weeks look back ... I'm looking back 104 weeks ... trading year has 52 weeks ... if I go here to even further three year that's the maximum that I look at" [02], with "I entered 26 which means basically I'm looking six month back" [04].
2. "we want to see basically ... both of them in an extreme where the retailers are in a bullish extreme and the smart money is in a bearish extreme we hardly have that" [02].
3. "this is a 15 years you see 15 years forecast so looking at 15 years historical data and then we are projecting" [02].
4. "we want to see basically only valuation versus gold ... I remove here quickly the treasury bonds and I don't necessarily care about the dollar and this is long-term valuation" [02], with "my length how many candles I can go back ... switch between short-term valuation long-term valuation" [04].
5. "I don't need to have every single one of them giving me the green light I do want to see as many of them agreeing with each other" [09].

## D. Stated results, risk and holding times (realism)
- Private A-book $1M account from 3 Aug 2023, $2M from Feb 2024 [24]:
  - 58 trades to 3 Oct 2024, "almost one trade per week".
  - "over 30 Rs" (INF: about +0.5R per trade).
  - Average risk about $18k (1-1.5%).
  - Best trade +$66k, worst -$83.
  - Biggest payout $384k.
- Prop contract: 7% maximum drawdown, no daily limit, +$1M every 6 months if profitable [14].
- Prop challenges: "100% win rate" on 8 prop challenges [09].
- Holding times: fills take days [09]; holds last days to weeks, up to about 2 months [16]; the EUR/USD trade lasted 4 days after a 3-week wait [27].
- Workload: 15 minutes in the morning plus 15 minutes at the US cash open, and 30-60 minutes of weekend analysis [07]; "1 hour a day 3 to 5 days a week" [24].
- Income claims: more than $1M per year [22, 25]; $500k on his main account in 2024 [28].

How his story changes over time:
- Risk per trade: 2% in the June 2024 challenges vs 1-1.5% on the private account.
- Equilibrium location: a blanket ban (Sept 2024) vs tradeable with the trend (Jan 2025).
- Tool names: "seasonal forecasting tool" (Jun 2024), then "campus algo forecast" (Jul 2024), then "campus algo seasonal forecast" (Dec 2024); "campus smart money index" (Jun 2024) vs "COT index" (Dec 2024).

---

# Per-file notes

Conventions: "Q:" = verbatim quote from the auto-caption (mis-hearings kept as-is, my reading in [brackets]).
"INF:" = my inference, not stated by him. "vague" = he does not give a rule.

## 01. 20240511_The_6-Step_Blueprint_I_Used_To_Escape_The_Rat_Race.txt
Lifestyle / motivation video. No indicator or S&D rules.
- D (profile): Q: "as a full-time multi-asset swing Trader I oversee millions in capital for proprietary firms recently achieving recognition as the alltime record holder by fmo [FTMO]"
- D (business): Q: "licensed investment consultancy with a global team of over 20 employees our headquarters are situated in Dubai"
- D (style/holding): Q: "it's always the same amount of time if you swing trade like me"
- D (income target, not a trading rule): Q: "aim for earning 30% more than what's required to maintain your current lifestyle"
- Nothing on COT / Valuation / Seasonality / S&D.

## 02. 20240602_Why_I_m_Shorting_Silver_Right_Now__Full_Breakdown_.txt
"$2.1M challenge across six prop firms", episode 4. Silver short setup + USD/CHF update. HIGH VALUE (all 3 tools shown on one market).
Process: Q: "my two-step mechanical process fundamentals technicals" (fundamentals = COT, seasonality, valuation; technicals = S&D zones for timing).

A. COT (silver, as of 2024-06-02)
- Report groups on the raw chart: Q: "the red are the retailers the yellow the fund managers orange yellow and the blue one the smart money the commercials here ... the producers". INF: three groups = commercials, large specs ("fund managers"), small specs/non-reportables ("retailers"). He does not say legacy vs disaggregated; "fund managers" + "producers" wording could hint at disaggregated, but vague.
- Index panel shows only 2 lines: Q: "the red line here represents the retailers the Blue Line represents the smart money the commercial". Large specs not used in the index here.
- Thresholds are horizontal lines, numbers not stated: Q: "they're above the green horizontal line which means they're an extreme and the blue line the smart money is below the red horizontal line which means they're also an extreme".
- LOOKBACK (key): Q: "weeks look back ... I'm looking back 104 weeks ... trading year has 52 weeks so if I put here 52 I would look hey how bearish are they in relation to one year ... if I go here to even further three year that's the maximum that I look at". => he grades extremes as 1-year (52w), 2-year (104w), 3-year (156w) extremes; 3 years is his maximum. Supports ~156-157w as the top setting but he actively switches 52/104/156.
- Index semantics: Q: "the retailers are the most bullish in the past two years and the smart money is the most bearish in the most past two years" => consistent with a min-max (stochastic-style) index of net positions over the lookback.
- Combination of groups: Q: "we want to see ... both of them in an extreme where the retailers are in a bullish extreme and the smart money is in a bearish extreme we hardly have that". Single-group extreme also shown preceding moves: Q: "the retailers getting into an extreme and the ... smart money was not even fully in extreme and we got this big red move". => Ideal = commercials and retail at opposite extremes; one group at extreme = weaker signal (INF).
- Direction rule: Q: "we know we have to trade against the retailers".
- Not timing: Q: "that's why it's not a timing tool that's why we need technicals to time the market but it gives us a clear bias".
- Size of move vs lookback: Q: "if we were in a threeyear extreme then this would mean a very very big move".
- READING: silver 2024-06-02: Q: "the retailers haven't been that bullish in the past three years ... the smart money hasn't been that bearish in the past three years" => retail 3y bullish extreme, commercials 3y bearish extreme -> short bias.
- Historical claim (2020): Q: "2020 ... this is when the retailers were in extreme ... there is no such such thing as a Black Swan event because we can anticipate these crashes".
- Chart for COT: uses unadjusted continuous futures, not back-adjusted: Q: "this is not just at SI which would be the adjusted chart ... we are talking about an unadjusted continuous chart 120 xn plus hkn set [garbled symbol]". Q: "this is a Futures unadjusted continuous childart which is really relevant for you to understand if you analyze futures of on higher time frames".
- USD/CHF update (2024-06-02): Q: "retailers are getting again more bearish perfect ... we would expect a move higher price is rising". Position = "USD Swiss frank short and the Ed on [add-on]", i.e. SHORT USD/CHF = long CHF futures (confirmed in file 09: analysis on the inverted CHF futures chart). So the COT read is on CHF futures: retail more bearish CHF -> expect CHF futures higher.

A. True Seasonality (silver)
- Q: "our seasonal forecasting tool ... this is a 15 years you see 15 years forecast so looking at 15 years historical data and then we are projecting". CONFIRMS 15 years.
- Projection length: reading covers "almost four weeks" (consistent with a ~30-day projection, not stated as a parameter).
- READING: silver 2024-06-02: Q: "it's the next few days it's a little bit flat but then we drop basically into the whole month ... a drop here on Silver for the next well almost four weeks".

A. Valuation (silver)
- Reference markets are toggled per asset: Q: "we want to see basically only valuation versus gold so gold silver relationship is really important ... now I remove here quickly the treasury bonds and I don't necessarily care about the dollar and this is long-term valuation". => tool has (at least) dollar, treasury bonds, gold as references; for silver he keeps ONLY gold. "long-term valuation" implies a long-term vs short-term setting exists (vague; INF: could be the 480 lookback or the ROC period).
- Rule: Q: "once we are overvalued versus gold then we need to short silver".
- READING: silver 2024-06-02 "overvalued versus gold" (no number given).

A. Combination
- Q: "so we have two out of we have two out of three rules met ... the third rule is basically valuation".
- Q: "all three rules met It's All Stars aligned trade cut retailers super bullish actually in a three years extreme um we have the smart money bearish also in a three years extreme we have seasonality in our favor for the next uh four weeks and we are overvalued versus gold". => "All Stars aligned" = 3/3. Does not say whether 2/3 is tradeable here.
- Claim: Q: "fundamentals can never be wrong fundamentals are going to play out eventually ... Market timing can always be be wrong".

B. S&D (silver)
- Monthly: Q: "drop based drop followed by a drop based drop again level on top of level ... overlapping level on top of level scenario we hit the dist [distal] level". So price had already traded to the monthly supply distal line.
- Big brother/small brother: Q: "a daily is cover by the weekly and weekly is covered by the monthly this is what I call ... a big brothers small brother principle".
- Weekly supply "drop based drop" + Q: "a shooting St[ar] another add-on right technically we have like a reversal candle here on the weekly" (pattern = add-on, not required).
- No chasing: Q: "could we just short below that Weekly shooting star yes we could but I don't want to chase price here ... wait for a little retracement higher".
- Entry timeframes: Q: "I like two time frames besides the daily or actually three I like 960 720 and 240" (960-min, 720-min, 240-min).
- Zone drawing (vague): Q: "starting the level on that Wick over wick on that daily ... this is basically the 960 level a little bit refined".
- Entry placement = compromise / front-run: Q: "it's always like this tradeoff ... probability of getting filled versus risk to reward proposition"; Q: "I'm planning to go short a little bit lower already ... I would not expect price to go really deep into that daily level ... it's a compromise between actually 960 entry and 2 40 entry". (silver entry ~31.20-31.30)
- Stop: Q: "we put our stop loss above the pivot to be perfectly protected" / "stop loss obviously above the pivot". (Stop referenced to swing pivot, no buffer stated.)
- Targets: Q: "one to one 2: one 3: one ... we don't need a 4 to one here ... we're doing a challenge ... we are not here for risk to reward we are here for passing the challenge"; Q: "we take it basically until we pass the challenge".
- Risk: Q: "like always 2% risk per trade not more and also not less".
- Management: set-and-forget, no updates; Q: "if you want to take profits take profits".
D. Q: "I'm 5% in profit" on a 200k (copied) challenge with the USD/CHF initial+add-on; firm targets differ (6%, 10%); swap vs swap-free accounts handled individually.

## 03. 20240607_Why_Price_Turns_Exactly_Where_It_Does__Supply___Demand_.txt
"Supply and demand pro trader series ... Lesson Four". Conceptual lesson, no indicators. Wording closely mirrors classic OTA/Seiden "core strategy" teaching (Walmart analogy, novice mistakes). He calls it Q: "my OTC content" (INF: his Online Trading Campus course).

B. S&D rules stated
- Zone exists only after price leaves: Q: "we let price move away ... that's when we conclude that Supply exceeds demand at the origin of that drob [drop]".
- Drawing: Q: "wrap two lines around that level proximately [proximal] this line highlight the area with a yellow box and carry that level forward". Demand: Q: "that's when we draw our proximal distal lines in we wrap two lines around this level and carry this level forward".
- ENTRY = limit at proximal, stop below zone: Q: "we want to be biased right here at the proximal line and put the protective stop just below the area buying right here at the proximal line according to our rules is the lowest risk highest reward and highest probability time to buy". (No buffer size given.)
- Anti-confirmation: Q: "if we wait for confirmation here and then buy what what's now happened to our risk is it gone up ... reward ... gone down". Q: "adding anything to your analysis that lacks [lags] price ... adds risk and decreases profit margin". (Indicators/MAs/chart-pattern breakouts rejected for entries.)
- Who to trade against: novice = Q: "buying after railing [rallying] price ... buying right into a price level where Supply exceeds demand"; mirror for sellers after a drop into demand.
- HTF context required: Q: "I don't want you to go out and buy and sell on every 5 minute demand and Supply level you find you have to know where those are in relation to larger time frame supply and demand".
- Zone qualifiers mentioned but not defined: Q: "when we get into the institutional Footprints what we call S qualifiers" (vague; INF: = odds enhancers).
- Nothing on COT / Valuation / Seasonality.

## 04. 20240609_Mexican_Peso__My_Full_Bottom-Catch_Trade__Part_2_.txt
MXN long (futures) = USD/MXN short (forex). Part 2 of an election-cycle idea (part 1 two months earlier). HIGH VALUE.
Process: Q: "my two-step mechanical process ... we start with the fundamentals because we have to be ... fundamentally biased to get into any trade".
Analyse futures, trade forex inverse: Q: "we have to analy[ze] the underlying asset which is the Mexican pay[so] Futures ... the inverse pair of the currency pair".

A. COT (MXN futures, as of 2024-06-09) - only RETAIL group used here
- Q: "we going to look at the retail cut [COT] data first and this is the raw data ... compared to their previous Behavior they're already getting very very bearish ... this is not sentiment ... these are [real] positions".
- Index name: Q: "my campus smart money index".
- LOOKBACK 26 weeks also used: Q: "I entered 26 which means basically I'm looking six month back and want to see if they're in a six Monon [month] extreme ... they're below the red line and if they're below the red horizontal line it means they're are in a six month extreme".
- Then 52 / 104 / 156: Q: "what about one year ... we are also now entering a one year extreme ... now I'm going to look at two years and wow we are getting even in a 2-year extreme ... now I look at three years because that's the maximum ... we not yet in a three-year extreme".
- Monster-move claim: Q: "if you're also in a three-year Extreme ... then you can expect a monster move at some point of time".
- History cited: Q: "Corona 3E [3-year] extreme this is when we get the bottom of all bottoms ... we got a three-year extreme ... in October 2023 and this is when we got that bottom".
- READING MXN retail 2024-06-09: 6-month extreme short, entering 1-year extreme, in 2-year extreme, close to (not in) 3-year extreme. Q: "this tells me the retailers will be absolutely wrong".
- Q: "once they're in a six months extreme we might get a nice rally although again it's not a timing tool".

A. Seasonality ("forecasting model"), MXN
- READING (said on Sunday 2024-06-09): Q: "tomorrow is Monday the 10th ... we might so go a little bit up then maybe a little bit lower and the bottom of all bottoms is around the 14th ... then we see the ultimate High around mid of mid of August ... basically two months of not necessarily a rally because we're going to see some tops and some bottoms".
- NOTE vs reconstruction: he reads the projection ~9-10 weeks ahead (to mid-August), longer than a 30-day projection. Either the projection setting is longer than 30 days here, or he is reading beyond the "30" (vague). Flag for check.
- Q: "obviously you cannot go exactly by the date".

A. Valuation, MXN
- Reference chosen by pair: Q: "our valuation model versus ... the US dollar because here we are pairing Mexican peso versus US dollar so obviously the valuation versus the US dollar is really important".
- Rule: Q: "we have to be obviously undervalued to go along [long] the Mexican peso".
- LENGTH setting: Q: "we're looking here at long-term valuation I can also ... show you here my length how many candles I can go back here I can I can switch between short-term valuation long-term valuation". => a "length" input in candles switches short-term vs long-term valuation; numbers not shown in the audio. INF: maps to either the ROC period (10) or the 480 normalisation window; which one is "length" is vague.
- Q: "obviously if we are long-term undervalued we might be short-term undervalued as well".
- Back-test claim (eyeballed): Q: "every time we are long-term undervalued we are getting these here close to long-term under valuation and we're getting these nice moves". Note "close to" also counted.
- READING MXN 2024-06-09: long-term undervalued vs USD (no number).

A. Combination: Q: "three out of three extremely biased so that's why my fundamental rules are met so that's why I can go into my step two which is basically the market timing with Technical".
C. Also election-based: Q: "this trade idea is also based on Mexican president elections".

B. S&D
- Charts: Q: "The unadjusted Continuous chart at mp1 equal 103 xn [garbled symbol]" vs Q: "the adjusted continuous chart at mp1". Timing done on the adjusted chart: Q: "looks a little bit nicer for timing purpose is here at mp1 the adjusted chart because ... the level is a little bit smaller it's a little bit tighter".
- ZONE LINES (key): Q: "snap mode ... the line snaps basically to the the bottom of that wig [wick] and to the basically top of the body of the basing candles that's my preferred version here on the Mexican peso weekly Zone". => demand: distal = lowest wick, proximal = highest BODY of the base candle(s).
- Merging overlapping zones: Q: "we have that drop base rally followed by a rally based rally so it's an overlapping level on top of level what I'm just doing basically here is combining both levels ... get a little bit deeper entry".
- Falling knife leeway: Q: "we you don't try to be like ex exact precise sniper mode entry we give price a little bit of leeway wiggle room".
- Big brother/small brother: Q: "the daily is clearly covered by the weekly super important again Big Brother small brother technically is m[et]".
- Targets: Q: "we are very mechanical so one to one 2 to one 3 to one we can all add these lines".
- Futures must confirm forex: Q: "a level by itself doesn't mean anything if it's not backed by fundamental tools and not backed by ... the Futures chart". Entry condition: Q: "ideal scenario is we wait for the Futures to get into that preferred weekly demand and then the Forex ... will be at the same time in that daily level on top of level Supply and then we can short this pair".
- Carry: Q: "this trade is also what I would consider a carry trade because you have positive very big positive swap so we can stay in this trade a little bit longer".

C. Futures gap (testable)
- Q: "this over night Gap will get filled very very likely". Q: "whenever you see these unsustainable gaps in the Futures they're very very likely to get filled right rather quickly". Gap not visible on the spot FX daily.
- Gap fill used as first target: Q: "you can place a one to two target here ... once we fill that Gap this is your first profit that you can definitely take".
- Risk: vague (Q: "do proper risk management do proper money management").

## 05. 20240614_I_Built_This_With_Prop_Trading_Profit.txt
Lifestyle vlog (Koh Samui villa build, Thai land law, buying a bull statue). No trading method content.
- D: Q: "I bought this villa with cash from trading profits ... since I bought this villa purely from profits".
- Nothing on COT / Valuation / Seasonality / S&D / risk.

## 06. 20240628_10_Trading_Lessons_I_Wish_I_Knew_Earlier.txt
Generic lessons list. Few numbers but some testable management rules.
- B (timeframes): Q: "to me the monthly weekly and daily charts are where I do my analysis"; Q: "wait for those no-brainer trades on the daily chart"; Q: "a sad [set] and forget and get a life trading approach and focusing on daily chart time frames".
- B (exit rule, stated as a starter rule, TESTABLE): Q: "have mechanical rules in the beginning such as I will move my stop loss to break even at 1:1 risk to reward ratio and take profits at 1 to2 [1:2] ... once you established a proper sample size you can tweak on that rule based on your own collected data".
- B (entry filter): Q: "only enter trade if all stars are aligned or in other words if all criteria is met if not you stay out". Confluence definition: Q: "a clear fundamental bias that also hits a higher time frame Supply or demand level".
- B (post-win rule): Q: "like taking a 24 to 48 hour break from the market after big win".
- B (risk sizing): vague "sleep test": Q: "keep scaling it back until you can shut down your charts and not stress over your trades". No % given.
- B (frequency): Q: "really good trades ... don't come around all that often but ... you don't need to trade a lot to make good money" (low frequency).
- D: Q: "more than 12 years of hustling"; Q: "alltime record holder from fmo [FTMO]".
- Nothing on COT / Valuation / Seasonality parameters.

## 07. 20240705_I_Spent__20_000_Building_My_Trading_Desk___Here_s_Where_I_Find_My_Setups.txt
Desk tour + routine. Confirms business name: Q: "our online trading campus our office is actually based in the Opus by Omnia" (so "OTC"/"campus" = Online Trading Campus).
- A (platform, important for reproducing tools): Q: "on trade station where I run all my proprietary tools my indicators my forecasting tools". Watchlist/alerts on TradingView: Q: "these are trading view charts where I can just place an alert line and I get alerted if the setup that I'm planning to take is coming into fruition".
- C/universe: Q: "I go through all the markets basically all Futures markets right all that I trade Equity indices stocks precious metals treasuries energies agricultural Market and FX Majors".
- Routine: weekend analysis Q: "my weekly routine starts on a Saturday ... maybe 30 minutes to do my whole analysis". Daily: Q: "I get here with a cup of coffee at 700 a.m. ... I check my fundamental tools ... to see if something significantly changed or not I check my setups and it takes me literally 15 minutes"; evening check at the US cash open: Q: "the US Stock Market opens between 5:30 and 6:30 [Dubai time] ... this is where I expect the highest volatility". Q: "maximum 30 minutes a day".
- A/B: fundamental tools are re-checked daily (INF: daily-updated inputs, e.g. valuation/seasonality; COT is weekly).
- Reading (webinar clip, recording date unknown): Q: "today we cover the equity indices ... I believe if we continue to go higher than next week we will get our March shorting opportunity" (INF: a seasonal/timing expectation for a March short in indices; year not stated).
- No COT/valuation/seasonality parameters.

## 08. 20240712_What__Set___Forget__Trading_Actually_Buys_You.txt
Family vlog (Koh Samui elephant sanctuary, Ang Thong boat trip). No trading content at all (only joke: Q: "everything that goes up has to come down").
- Nothing on A/B/C/D.

## 09. 20240719_I_Called_6_Prop_Challenges_Live___Before_a_Single_Trade_Filled.txt
Recap of the six live-called prop challenges (USD/CHF short from 2024-04-28, silver short from ~2024-06-02). HIGH VALUE: here he lists FOUR "green lights".

A. Combination rule (key quote)
- Q: "I have to follow my strict set of rules these rules are my DNA I don't need to have every single one of them giving me the green light I do want to see as many of them agreeing with each other that's the only way to filter out the less probability trades". => NOT a strict all-must-agree rule; more agreement = higher quality. "All Star aligned" = all agree.
- Q: "This is what I call an Allstar line [All-Star aligned] trade we have got the cut [COT] the smart money index the valuation tool and the algo forecast all agreeing on the same thing". => here the raw COT read and the "smart money index" count as two separate lights (4 lights: COT raw, Smart Money Index, Valuation, Algo Forecast).

A. COT, CHF futures (idea posted 2024-04-28)
- Futures chart, inverted vs the FX pair: Q: "I do my analysis on the inverted Futures chart"; Q: "my analysis is all made on the Futures Frank USD chart and my actual trades are placed in the Forex Market the USD Frank pair".
- Raw COT: Q: "this large movement indicates that retailers behavior is extremely bearish compared to their previous Behavior then I compared the retailer coot data versus The Producers data this is the smart money that we want to follow and check this out they couldn't be more bullish actually the highest they have been in the last four years".
- READING CHF futures ~2024-04-28: retail extremely bearish; commercials ("producers") highest net long in 4 years. (Note: "4 years" > his usual 3-year max lookback; here he's reading raw positions, not the index.)
- Index: Q: "the smart money index it's showing an even bigger indic ation with a significant upward movement from the smart money contrasting with the bearish behavior of retail Traders".

A. Valuation, CHF: Q: "the Frank was undervalued versus the dollar so the valuation tool agreed".

A. "Campus Algo Forecast" (= the seasonal forecasting tool, INF from silver line below)
- Q: "the campus Alo [Algo] forecast indicator and interestingly it paints a similar picture only shifted a few weeks into the future ... the forecaster does what it does best it predicts the future but I don't use it to time the market we use supply and demand for that ... the algo forecast did predict the bottom revisit with a great accuracy".
- Silver: Q: "The Alo forecast predicts exactly the same thing when looking back at 15 years of data". => the "algo forecast" uses 15 years of data, same as the seasonal "forecasting tool" in file 02.

A. Silver recap (~2024-06-02): Q: "the retail Traders on the cut and the smart money index are super bullish producers could be [couldn't be] more bearish valuation versus gold is overvalued every single time silver was overvalued versus gold the price crashed".

B. S&D (CHF)
- Q: "level on top of level we return to the demand Zone big brother in the demand Zone small brother in the same demand Zone". (Big/small brother = HTF zone contains the LTF zone.)
- Add-on price-action: Q: "we also got the weekly engulfing the mother of all price action reversal candles".
- Second (add-on) trade: Q: "we generated a second trade out of thin air on the same pair since our fundamentals didn't change and we are in a high quality Supply level unlike lightning we can strike the same place twice".
- Lower-TF entries: Q: "discussing when to take add on trades and ... secrets about sniper entries and how to make sure you get filled on Lower time frames" (details not given here; vague).
- Q: "we then Define our stop andry [and entry] Target using our supply and demand".
D. Results / execution
- Q: "I haven't yet lost a single trade on any of the eight challenges that I took with these eight different prop firms I passed every single one of them with a 100% win rate". (6 live + 2 earlier.)
- Q: "I leverage Myself by entering as many challenges as I possibly can enter at the same time and then manually copy the same trades across each each one of these accounts".
- Holding/fill: Q: "each one of these trades was a swing trade it took days for them to get filled".
- Q: "I barely had an hour each day to manage these trades".

## 10. 20240729_The_Number_1_FTMO_Trader_Goes_Off-Grid_in_Kenya.txt
Travel vlog (Nairobi, FXPesa keynote, safari), recorded around May 2024 (he mentions going to Bali "June 10th or 11th"). Almost no trading content.
- Reading, market NOT named (teaser clip, context missing): Q: "We will see a decline at the end of May , followed by a nice rebound in the summer". Vague: cannot attribute to a market or a tool.
- Q: "It's like betting their house on a trade, which is never a good idea."
- Nothing else on A/B/C/D.

## 11. 20240802_The_4_Supply___Demand_Formations__RBR__DBR__RBD__DBD_Explained_.txt
S&D pro trader series lesson (formations + candle classes). HIGH VALUE for coding the base/leg rules.
B. Formations
- Demand: Q: "number one a drop base rally ... from being balanced price R[allies] sharply to the upside ... the demand area is in the base where the market was balanced ... the origin of the imbalance"; Q: "the second demand formation is the rally based rally ... the demand Zone would be the base".
- Supply: Q: "rally Bas drop ... from the balance State you get a steep chop [drop] in price"; Q: "drop base drop ... with a base being the place where the price was balanced".
- Action: Q: "demand formations drop base rally and R base rally we are going to buy when price comes back into the base and the supply formation really based drop and drop based drop we are going to sell when price comes back again into the base".
- Carry forward / no chasing: Q: "we carry it Forward because we don't want to chase price and sell the first drop".
B. CANDLE CLASSIFICATION (exact numbers)
- Indecisive (base): Q: "the body is smaller or equal to 50% of the range". (range = wick to wick, body = open to close: Q: "the entire range from bottom wig to top wig compared to the body from open to close")
- Decisive: Q: "the body must be bigger than 50% of the entire range".
- Explosive: Q: "if the body is bigger than 70% of the range it could be an explosive candle for this candle there's going to be another rule it also must be abnormally bigger than the previous candles". ("abnormally bigger" not quantified = gap.)
- Roles: Q: "the base for example should be Bal[anced] therefore we are going to look for indecisive candles in the base the move out of the base should be explosive". (Leg-in requirement not stated here; number of base candles not stated here.)
D. Q: "the same supply and demand strategy I used to pass over 10 prop challenges with a success rate of 100%".
- Nothing on COT / Valuation / Seasonality.

## 12. 20240809_The_Trader_s_Edge__My_Daily_Routine_for_Peak_Performance.txt
Fitness/lifestyle vlog (Muay Thai, ice bath, Koh Samui). No trading method content.
- Profile only: Q: "I'm now 40 years old"; no alcohol for 13-15 years.
- Nothing on A/B/C/D.

## 13. 20240823_The_Candle_That_Tricks_Most_Traders__Supply___Demand_.txt
S&D pro trader series "lesson six": quick-reference zone rules + live NQ 4h example (chart dated "August the 13th roughly 2 p.m.", 2024). HIGH VALUE.
B. Core principle: Q: "don't buy unless we in a discount and don't sell unless it's a premium".
B. Zone rules ("cards")
- LEG-IN: Q: "leg in is the price action prior to the base it is made of a decisive or an explosive candle and it can be a r[ally] or drop depending on the formation".
- BASE: Q: "the base is made of one or multiple indecisive candles and this is the origin of imbalance". (No max count stated; example below uses 4 base candles; another uses 1.)
- LEG-OUT: Q: "the leg out has to be an explosive candle the rule for an explosive candle is number one the body has to be bigger than 70% of the entire range and more importantly number two the candle has to be abnormally bigger than the previous few candles because the sheer size of the candle is more important than the body to range relationship".
- ALTERNATIVE LEG-OUT: Q: "the leg out can consist of abnormally bigger candles that are decisive if they're followed by another decisive candle".
- Context override: Q: "the body is 100% And there are no wigs however in reality this is more like a indecisive candle because the range of the candle is extremely small in context". Q: "everything that can be caused by retailers I put I can put in the base". => small-range candles count as indecisive regardless of body/range. ("abnormally bigger" / "small in context" not quantified = GAP; INF: compare range to an average of the previous N candles.)
- ORDER OF IDENTIFICATION: Q: "the first step is always to identify the leg out step two is to identify the leg in followed by the last step of identifying the base".
- Scanning procedure: Q: "we will start at current price ... we will go up and left and obviously we cannot cross candles"; Q: "go down and left never cut candles go to the bottom of that pivot draw a horizontal line". INF: only zones not crossed by later price are considered (consistent with freshness).
- Drawing: Q: "I draw The Wider version proximal distal line I use my yellow box". ("Wider version" vs the body-based "preferred version" of file 04; INF: wider = wick-to-wick of the base.)
- FRESHNESS (invalidation): Q: "that zone already worked out price moved away came back hit the zone and then price crashed from here so that zone is already used ... it's not fresh anymore so it's not a valid Supply Zone here anymore and this is one of our Zone qualifiers". Q: "it has been touched ... it's not fresh". => a zone is invalid after its first return/touch.
- Timeframe switch when structure unclear: Q: "I change the time frame now from from a 4H hour I move to an 8 Hour chart so now you see the entire chart the picture changed".
- Example base: four candles (indecisive, indecisive, small green "looks explosive" but Q: "not normally [abnormally] bigger ... I can use it in my base", indecisive) with a decisive leg-in; another demand zone with Q: "clear base with one indecisive candle".
- Q: "we are fully rule-based fully mechanical black and white".
- Which zone to trade: deferred (Q: "which of them to trade ... we we will also cover later in the course").
- Nothing on COT / Valuation / Seasonality.

## 14. 20240830_WHAT_REAL_TRADERS_TAUGHT_ME_IN_MIAMI.txt
Miami podcast-tour vlog (recorded ~late May 2024: the YM idea expects "a low here now end of May"). One live trade idea + prop-contract details.
A. Seasonality ("forecasting tool"), YM / Dow futures, READING (~late May 2024):
- Q: "what I'm looking here is seasonality here on the Dow Jones on the ym ... we said sell in May and go away and now June and July the summer is going to be particularly strong on the equity indices".
- Q: "we are going to have a low here now end of May and then for like one week we're going to see another nice nice rally according to our forecasting tool and the real rally is going to start end of June but maybe we can position ourself already now in the next upcoming days and then stay long until July". (Reading extends ~6+ weeks ahead.)
- Refers to an earlier "entire yearly road map on the us30" video (INF: the decennial/annual roadmap video, other batch).
B. S&D (YM 4h)
- Q: "on a 4our [4-hour] charts there are three demand levels I call that level on top of levels ... I combined both of these 4H hour levels".
- Q: "my stop loss below I don't need a Target because I expect new highs set forget and get alive [a life]". => when bias expects new highs: no TP, stop below combined zone.
- Routine: Q: "I do my analysis during the weekend place my trades on Monday and then I just followups throughout the week".
C. Agricultural futures seasonality (claim): Q: "my early career I traded like all agricultural markets like orange juice like lean H[ogs] soybeans soybean oil ... they're very seasonal as well because obviously ... you plant them you harvest them ... you can predict the ... end of the band [trend] facing quite nicely".
D. Private prop contract: Q: "I'm managing 2 million dollar in real funds ... I have a 7% draw down limit but I don't have a daily drawn [drawdown] limit"; Q: "every 6 months they If I Stay profitable right and within the risk parameters they increase by another million"; profit split Q: "100% ... I get all the money ... they copy the trades". Path: 100k challenge -> 100k real -> 200k real -> (1M challenge waived) -> 1M -> 2M.
D. Prop stats claim: Q: "less than 1% get to the first payout they might get funded right maybe 10% gets funded".
- Business: Q: "since 2019 in Dubai we run a licensed investment consultancy ... regulated by the UAE government ... more than 20 employees ... seven Mentor training desk".
- (Speaker unclear, possibly the guest Kyle): Q: "trying to make two or three good decisions a week I'm trying to make one".

## 15. 20240906_How_to_Draw_Supply___Demand_Zones_Accurately.txt
S&D lesson: exact line-placement rules (slides + live NQ 240-min on TradeStation). HIGH VALUE (codeable).
B. Line definitions
- Q: "the distal line is the line furthest away from current price ... the proximal line is the line that is closest to current price".
- TWO VERSIONS: Q: "there's a wider version and there's a preferred version".
  - Wider (demand): Q: "the proximal is drawn at the highest Wick and the distal at the lowest wig [wick] of the entire formation" (proximal = highest wick OF THE BASE).
  - Preferred (demand): Q: "the proximal line is here drawn at the highest body and the distal at the lowest wig of the entire formation"; Q: "the proximal line is drawn at the highest candle body in the base".
  - Supply mirrors: wider proximal = lowest wick of the base; preferred Q: "the proximal is at the lowest body and to dis[tal] let the highest we[wick] of the entire formation"; Q: "the proximal line is drawn at the lowest candle body in the base".
- DISTAL by formation type (key, codeable):
  - Reversal (DBR / RBD): Q: "the line placement when it comes to the distal line never never never changes it's always at the bottom of all bottoms at the at the lowest wi[ck] of the entire formation" (leg-in + base + leg-out).
  - Continuation (RBR / DBD): Q: "it's not at the lowest point of the entire formation only when you have that u-shape formation the trop base rally then it's the entire formation but if you have a rally base rally then it's basically at the lowest point of the base and the leg out and you can disregard the leg in". DBD: Q: "we cannot consider the leg in for the distal line we have to consider only the base and D leg out".
  - Proximal never uses leg candles: Q: "the proximal line never changes ... it's only the dist line that changes".
B. STOP: Q: "the stop L[oss] has to go below the distal regardless not on the distal below the distal right because the distal line is still the is still part of the imbalance". Buffer size NOT given (Q: "we're going to talk about this in another lesson").
B. Which version: Q: "there's no right and wrong". Tradeoff: Q: "the advantage [of wider] the likelihood of getting filled is higher and the disadvantage is the profit margin is lower ... [preferred] the profit margin is higher and the disadvantage is the likelihood of getting fil[led] is a little bit lower". Earlier (file 04) he called body-proximal "my preferred version".
B/D. RISK: Q: "you know me I'm preaching the fixed dollar risk approach so regardless of seone [zone] size". Illustration only: Q: "$100,000 prop firm account 1% risk is $1,000". Example R:R 3:1 (wider) vs 4:1 (preferred), illustrative.
B. Live example (NQ 4h): Q: "explosive followed by explosive so this is a clear institutional activity ... clear leg in explosive leg in leg in base base base leg out" => DBR with 3-candle base.
A/C. READING (NQ, ~early Sept 2024): Q: "we're dropping right now by the way as expected September drop" (INF: seasonal expectation; tool not named).
- Q: "we haven't even covered I would say 5% of supply and demand".

## 16. 20240913_The_3-Step_Process_That_Tells_You_Exactly_Which_Zone_to_Trade__Supply___Demand_lesson_.txt
S&D lesson: the "three-step mechanical process" and step 1 LOCATION; live on CHF futures weekly. HIGH VALUE (codeable).
B. Three-step process
- Q: "the first step ... it's called location ... to determine whether price is cheap or whether price is expensive or whether price is in what we call equilibrium"; Q: "the second step of the three-step process is Direction ... just simple trend on the chart also in HTF"; Q: "the last step ... is called zoning process and this is used to place your set stop entry Target and this is done in TF [LTF] in lower time frame".
B. TIMEFRAMES ("income streams")
- Day trading ("daily income", trades last hours/days): Q: "for your higher time frame basically for your location and Direction use the daily time frame and for then the zoning process ... from 2 hour to 4 hour to 8 Hour charts".
- Swing ("weekly and monthly income", days to months): Q: "for the higher time frame the weekly and the monthly chart ... for the lower time frames to place our set we go then down basically starting from a 600 minute to a daily".
- His own: Q: "I like to basically cover my location on a weekly and monthly chart and then I go down to the lower time frame usually it's daily chart on 960 minute chart".
- Q: "the bigger the time frame the bigger the imbalance the more unfilled orders the higher the probability of a successful trade".
- D (holding): Q: "I had a trade even that last for like close to two months".
B. LOCATION algorithm (HTF)
- Q: "step one ... you identify the first fresh Supply zone ... step two is basically identify First fresh demand Zone on the higher time frame". (Nearest zones above/below current price: Q: "you find your first the nearest Supply Zone that has to be fresh".)
- Q: "you divide the range from distal the highest distal to lowest distal into three equal parts so you get basically five parts very high high equilibrium low very low or in other words very cheap cheap equilibrium expensive ... very expensive". Q: "with my trade station I basically just do 33% and 66%". Q: "this is basically very cheap down here in in demand". INF: very cheap = inside demand zone, cheap = lower third, equilibrium = middle third, expensive = upper third, very expensive = inside supply zone (exact handling of zone/third overlap not stated = gap).
- Permission, not trigger: Q: "if price is in this area expensive and very expensive ... this is where you can look too short but it doesn't necessarily mean you're going to short"; Q: "if price is in equilibrium ... this is the no touch area".
B. HTF zone rules for location
- Q: "your leg in has to be made of decisive or explosive candle ... your base you draw based on a preferred version and it has to be fresh 25% preferred rule ... the leg out is made of a decisive or explosive candle" (HTF leg-out may be merely decisive; LTF leg-out must be explosive per file 13).
- FRESHNESS (HTF): Q: "freshness test based on preferred and a violation of approximately 25% is still be uh allowed". Q: "wider version it can be violated we don't care but we measure freshness based on preferred version". Reason: Q: "a high quality weekly or high quality mon[thly] Zone usually is been tested a couple of times ... sometimes even three or four times". Examples: Q: "almost like 80% or close to ... 90% so it's a violation"; Q: "tested by roughly 50% then we would need to go higher"; Q: "Maybe by 10% ... we eyeball that".
- Touch definition: Q: "if price just came very close to that but never touched that zone ... it's not a violation".
- ALTERNATIVE RULE: Q: "if there's no Zone visible according to our rules on higher time frame ... then you can apply the rule everything that looks like a level is a level".
- Zone qualifiers listed but deferred: Q: "we cover freshness and something like um authenticity of the Zone later on when we cover Zone qualifiers and Zone qualifiers is important for step three the lower time frame zoning process".
- Meta: Q: "rules are made to be adjusted".
READING CHF futures weekly (~2024-09-13): Q: "price is in equilibrium meaning no touch area ... we're closer to expensive yes but we are still in equilibrium".

## 17. 20240920_The_Supply___Demand_Rule_I_d_Never_Trade_Without__Big_Brother___Small_Brother_.txt
S&D lesson: Big Brother / Small Brother (BB/SB) = "the most important rule". Live: CHF futures weekly -> daily. HIGH VALUE.
B. Definition and rule
- Q: "if you find a Zone a lower time frame Zone that is covered by the higher time frame zone ... this is what we or what I call Big Brother small brother principle and this big brother small brother principle is the most important rule there is meaning in other words trading covered by the higher time frame".
- Q: "it's my first rule I always have to be covered by the higher time frame ... if I do Market timing I have to be covered there's no way around".
- Entry location = LTF zone INSIDE the HTF zone, not the HTF proximal: Q: "if price comes all the way into the Zone here starting here I'm not going to short here because I wait for price to go into my ... lower time frame high quality ... Supply ... the green area is my small brother the whole yellow area is my big brother".
- Pairs: swing = weekly (BB) -> daily (SB); day trading: Q: "you could use the daily chart and then you could say my lower time frame is the 4our chart so your 4our chart has to be covered by the daily chart".
B. Equilibrium filter (location): Q: "even if this Supply zone is high quality you would not want to engage in this trade because it's in equilibrium".
B. TARGET logic: Q: "you would now have a profit margin or ... risk to reward proposition all the way to the next higher time frame Zone"; Q: "if you go to lower time frame and you see some opposing zones ... you could conceptually speaking disregard these lower time frame opposing zones because you are trading with the strength of the higher time frame zone".
B. Failure reasons: Q: "both zones big and small brother must be of high quality to support each other"; Q: "if we go against the trend there's also higher um possibility to get stopped out".
B. Advanced drawing for HTF: Q: "for me in my rules more advanced rules I just highlight The Wider version". Alternative rule applied to a supply with no basing candle: Q: "there's a long wig and a also big body so I would basically say Okay apply here my rules everything that looks like a level is a level".
- Q: "once you are more advanced ... you not need to split this the the whole area into multiple parts" (thirds are a beginner visual aid).
READING CHF futures weekly (~2024-09-20): Q: "price is moving already from that very expensive area"; nearest DBD supply Q: "already tested way more than 25%" -> skipped for a higher supply. Daily small-brother supply found inside weekly supply (RBD); demand side: daily "level on top of level" inside weekly demand.
- Nothing on COT / Valuation / Seasonality.

## 18. 20240924_This_Prop_Firm_Stole__27_000___So_I_Investigated_Them.txt
Prop-firm dispute (Indigo Trader Funding). No method content.
- D: Q: "My account had $ 27,000 in profit on August 14, and on August 18, it was already $33,000" (Indigo account from the live documentary challenge, 2024).
- D (risk consistency claim): Q: "My risk management is the same for all my accounts".
- D: firm's refusal email cited "the risk inherent in your strategy" (firm's claim, not his).
- D: Q: "I have already reached the maximum limit in all these established firms"; private A-book firm Q: "the only prop firm I have never had a problem with".
- Nothing on A/B/C.

## 19. 20240928_How_to_Read_Trend_Direction_with_Supply___Demand__Mechanical_Rules_.txt
S&D lesson: step 2 DIRECTION (trend). Live: CHF futures weekly with ZigZag. HIGH VALUE (codeable).
B. Trend rules (exact)
- Uptrend: Q: "what is required for an uptrend so we Define higher lows and higher highs from current price so two lows that's the rule ... we need two higher lows then you have ... an uptrend".
- Downtrend: Q: "once we have two lower highs ... then we have an downtrend by definition".
- Sideways: Q: "if no clear trend is recognizable then Define it as a sideways Trend".
- Pivot set: Q: "we identify six recent pivots three lows and three highs to establish current Trend ... the six most recent pivots that's actually important not six random pivots". Current bar excluded: Q: "we start at current price this is not yet a pivot because if price continues to Rally then this is not yet a pivot".
- Pivot tool: Q: "it's called sixc [ZigZag] percentage you have also on trading view ... I'm just changing here ... the retrace percentage ... I do it to three uh% so I get more six saxs [zigzags]". => ZigZag 3% reversal on the weekly chart (CHF futures). Q: "whether you do eight or if you want to do 10 it's just a rule but for me the rule is six pivots".
- Same TF as location: Q: "on the higher time frame where you do your location it's important to do it on the same time frame".
- Ambiguity left open (GAP): with 3 lows/3 highs, "two higher lows" could mean L3>L2>L1 (two consecutive higher lows) or two lows each higher than prior; example: HL + LH mix => sideways.
B. Concepts
- Trend definition: Q: "trend is simply price traveling ... from higher time frame Supply to higher time frame demand and vice versa higher time frame we would talk basically monthly".
- Trade impulse, enter on correction: Q: "the correction move is the pullback from the primary direction is the opportunity to enter the trend ... we wait for price to come to us ... into a de[mand] or Supply Zone into the impulse Zone".
- Uptrend zone pattern: RBRs form inside impulses, DBRs form at end of corrections (mirror in downtrends).
- Early-trend preference: Q: "we don't want to buy the uptrend at the end of the bend [trend]". Advanced "anticipatory Trend analysis" = predicting the end of the trend (not defined here).
READING CHF futures weekly (~2024-09-28): Q: "clear definition here of a weekly sideways Trend"; price rallying into the "high very high area Supply area where we are allowed to short".
- Nothing on COT / Valuation / Seasonality.

## 20. 20241004_A_Real_Family_Day_on_Our_Island.txt
Family vlog (Koh Samui temples, boat trip, Four Seasons). No trading content.
- Nothing on A/B/C/D.

## 21. 20241013_The_Presidential_Election_Cycle__Explained_.txt
Presidential election cycle (Yale Hirsch) + decennial teaser. TESTABLE numbers (all S&P 500 per his narration; he says Dow/NQ "they all correlated").
C. Definitions: Q: "one term equals one cycle and one cycle equals 4 years ... year one is the post elction year year two midterm year three pre-election year year four election year with elections always taking place in November". Data: Q: "seasonality data going all the way back to 1900".
C. Stated stats (to verify):
- Post-election: Q: "only a 5% average increase out of the 27 post election years only 13 were bullish".
- Midterm: Q: "it's the only bearish year out of the four ... the market chops around ... whenever we are in one of those years I avoid trading based on the presidential election cycle".
- Pre-election: Q: "averaging at 13% performance in 21 out of 26 pre-election years we've seen a bullish Market"; Q: "2023 ... bullish with a 25% gain from the lowest point"; Q: "2019 ... we see a 32% increase".
- Election year: Q: "the average gains are around 9% ... out of 26 election years 18 were bullish"; Q: "2020 ... a 70% rise from the seasonal low and a 15% year end gain"; Q: "2016 ... a 25% chump [jump] from the seasonal low and a 9% year ending increase"; Q: "seven out of 10 times the election year will be bullish".
- Election-year path: Q: "a new higher high in April followed by a seasonal low in May and then a massive surge upward this move typically Peaks around September"; 2020: Q: "seasonal law [low] in April and the seasonal top in September followed by a predictable LW [low] in early November right around the election date and from there the end of year rally".
- END-OF-YEAR RULE (testable): Q: "The last two cycles saw 9% increase from November to December that's 9% in 2020 and another 9% in 2016"; Q: "if you're a stock investor by November sell in December if you're swing Trader take a TW Monon [two-month] long position". => H: in election years, long US index from early Nov (election) to end Dec.
- Execution: Q: "no sculping no intraday no day trading just open up your chart on The Daily and weekly time frames get your old supply and demand notes".
READING 2024 (as of ~2024-10-13): Q: "in 2024 it was so strong that it topped out by mchine dead [garbled, likely mid-July] as a result the next low came in August instead of November ... after the elections I'm expecting another search [surge] upward and a breakout".
C. Decennial (teaser): Q: "the fourth year of each decade which is 2024 for us has been positive eight out of 13 times with an average increase of 88% [likely 8.8%; caption] from the seasonal low"; Q: "2025 is going to be an absurd postelection year ... what we call a phenomenal five ... 13 out of 14 times it turned out to be a bullish year with 300% [likely 30%; caption] of gains". (Numbers garbled; verify against Hirsch decennial data.)
- Nothing on COT / Valuation / True Seasonality parameters.

## 22. 20241115_How_To_ACTUALLY_Build_Wealth_With_Trading__Step_By_Step.txt
Wealth/compounding talk. Only risk-scaling numbers and income claims.
- D (risk, example from his older case-study clip): Q: "your risk percentage stays at 1% but your risk per trade jumps from $500 to $4,000 and your reward grows with it to a mouth watering $88,000 [$8,000] per trade that's a conservative example where we are targeting only a one to2 risk to reward ratio". (1% of 50k -> 400k; 1:2 R:R illustrative.)
- B: Q: "the way how you place your set the entire process never changes regardless of your risk the only variable in this entire equation that changes is the risk you're going to take per trade".
- D (income): Q: "when we add that amount to my payouts from all other accounts that I manag[e] the total would be north of a million dollar"; Q: "my first year in shading [trading] I made less than 10K more than 10 years later and that 10K grew to $1 million".
- Background: corporate job in Dubai (automotive) 16 years ago; started trading 3 years into it.
- Nothing on A/B indicator or zone rules.

## 23. 20241123_I_m_Giving_Away_5_Trading_Desk_Setups_to_Celebrate_100K.txt
100k-subscriber giveaway. No method content.
- D: channel started March 2023; Q: "Your credibility to me is not your license, but your verified track record."
- Nothing on A/B/C.

## 24. 20241129_Why_My_Worst_Trade_in_a_Year_Cost_Just__83.txt
Track-record video for his private ("VST") $2M A-book prop account. HIGH VALUE for realism checks (D).
D. Account and stats (as stated; captions garble some dollar figures)
- Q: "the account was funded with $1 million on August 3rd 2023 and then topped up with another million in February 2024 my last trade closed on October 3rd 2024 and the next day I with[drew] $384,000 making it the biggest payout in my 11 years of trade".
- Q: "my payouts from this account alone over the past year totaled $55,000 [caption; context 'record revenue of half million dollar' => likely ~$550,000] in exactly one year 2 months and one day".
- RISK: Q: "from day one of getting this account my risk has always been between 1 to 1.5%"; Q: "I was risking 1% per trade so about $10,000 per trade which then went up to $20,000 per trade".
- TRADE COUNT / EXPECTANCY: Q: "I placed exactly 58 trades almost one trade per week and I've collected over 30 Rs in that period with my average risk per trade being around 18K". => ~0.5R per trade over ~14 months (INF: 30R x ~1-1.5% = ~30-45% return on the account).
- Q: "my best trade closed with $66,000 in profit and my worst trade cost me just $83".
- Early stats: Q: "my first payout of $440,000 [caption; likely $44,000] on a 29th of August so exactly 26 days after I received the account"; Q: "$137,000 but I had to pay 15 gain swaps [~15k in swaps] alone we left things at $120,000 in gains" (as of the earlier update).
- Time: Q: "1 hour a day 3 to 5 days a week".
- Verification: third-party performance verification (GIPS-style) + public FXBook link (per him).
- Q: "I only enter trades when the market gives me permission"; Q: "quality over quantity and less is more".
- C/reading: Q: "I was also giving out free signals and published my entire trading plan for September" (2024; content not in this file).
- Nothing on A/B parameters.

## 25. 20241206_How_To_Avoid_Trading_Scammers_In_2026.txt
Anti-guru video. Little method content.
- A (how he describes his tools): Q: "the effort that went into developing some of the best Trading indic[ators] out there that aren't price driven or in other words indicators that predict the market rather than following it". (Note: the valuation tool as we reconstruct it IS price-derived; his claim is marketing-level, vague.)
- Background: Q: "I was mentored by Traders who worked in the pit of the Chicago mercile [Mercantile] Exchange".
- D: Q: "I generate $1 million per year"; FXBook records every trade (Q: "even if it was a test trade that lasted only 6 seconds").
- OTC platform: mentors, daily/weekly analysis, "all of my proprietary courses" (no specifics).
- Nothing on parameters / zone rules.

## 26. 20241213_Trading_Is_NOT_80__Psychology__Here_s_What_Actually_Matters_.txt
"Skill over psychology" video. A few useful statements on tool inputs, risk and news.
- A/B framework: Q: "I just focus on two factors it's my fundamentals and my technicals fundamentals Drive price but with fundamentals I cannot time the market and that's why I use Technic[als]".
- A (what the fundamental tools cover; supports DXY/ZB/GC as valuation references): Q: "fundamentals make all the necessary connections between interest rates gold dollar Index bonds seasonal trends overvaluation of assets and hidden Market orders having tools designed specifically to figure all of this out". (INF: "hidden market orders" = COT/unfilled orders.)
- B (freshness, firm stance): Q: "thinking a demand Zone that was visited three times before will hold for the fourth time ... I call that a non-fresh Zone I disregard it completely and I carried the next Zone instead". (Contrast: HTF location zones allow ~25% test, file 16.)
- B (pre-planned orders): Q: "the trade is already locked entry stop loss take profit all pre-planned".
- B/D (RISK): Q: "the need to risk only 1 to 2% per trade the need to diversify your portfolio".
- B (NEWS handling, vague/discretionary): Q: "I understand the logic of those traders who close the open positions before big news events to avoid having to gamble which way the animal spirits might go heck sometimes I'm one of them".
- C (election follow-up, Nov 2024): Q: "on the very same day that Trump won the elections we saw massive upward movement ... this is Animal Spirits in action" (consistent with his election-year breakout call in file 21).
- Anti-indicator: Q: "don't waste your time with price-based indicators like RSI or moving averages".

## 27. 20241220_Your_Forex_Chart_Is_Lying_To_You__Here_s_the_One_Banks_Actually_Use_.txt
EUR/USD short (Sept 2024) explained with futures charts, CME gaps and all three tools on EC and DX. HIGH VALUE.
A. Tools named: Q: "our three proprietary fundamental forecasting tools the cut [COT] index here the retail Traders here on the second chart it's a daily chart here the campus valuation tool versus the US dollar and here the campus algo seasonal forecast". => "Campus Algo Seasonal Forecast" = the seasonal tool; valuation shown on a DAILY chart.
- Platform/data: Q: "I prefer trade station because I can run all of my tools like valuation and algo forecast on the c[ME] charts"; Q: "most of the times we do our analysis on the Futures unadjusted charts". Symbols: Q: "the E[C] unadjusted chart which we find on trade station under the symbol at ecal 103 XM [@EC=103XN]"; DX: Q: "at DX equals 103 xn [@DX=103XN]". (Same "=103XN" suffix as the garbled MXN/silver symbols in files 02/04. INF: TradeStation custom continuous contract, "N" = not back-adjusted.)
A. COT readings (back-test view "pretending today is the 18th of September" 2024)
- EC (Euro FX futures), retail: Q: "the retailers were extremely bullish compared to their previous Behavior ... previously a couple of ... weeks and months back they were actually quite bearish now they're getting quite bullish". Rule: Q: "we always want to do the opposite ... of what the retailers are doing ... It's always important to look at their previous behavior".
- DX (dollar index futures), retail: Q: "a massive drop in retail Behavior the likes of which I hadn't been seen in 15 years"; Q: "we go all the way back to 2011 the retailers ... were the most bearish ever ... you see that here on the cut index the retailers were the most bearish ever on the US dollar index". => here he judges the extreme against the FULL history since 2011, not a 26-156w window (or the chart simply shows it).
- Cross-market use: Q: "that made me so bearish not on the US dollar but so bearish on the Euro US dollar". => COT of the dollar index used to trade EUR/USD.
A. Valuation readings (18 Sept 2024)
- EC vs USD: Q: "in terms of valuation versus the US dollar we are close to the red horizontal line which means we're getting overvalued so we are close to overvaluation". => RED line = overvalued threshold; "close to" counted as supportive.
- DX vs EURO: Q: "When it comes to valuation versus the Euro we are a little bit around the mean we are not yet fully undervalued but we are getting there". => for DX the reference market is the EURO (not DXY); "around the mean" language implies a centred oscillator.
A. Seasonality ("forecasting tool") readings (18 Sept 2024)
- EC: Q: "look what our forecasting tool is forecasting that from here we are making the top and we getting a sharp decline".
- DX: Q: "it's forecasting also that we making a low here a bottom here and ... the following weeks a sharp sharp rally".
A. Combination: Q: "it was such a high probability um all stars align trade" (COT EC + COT DX + valuation EC/DX + seasonality EC/DX all pointing to EUR/USD down; valuation only "close to").
B. S&D / execution
- Multi-chart rule: Q: "what you want to accomplish is ... that the unadjusted and the adjusted chart both hits a level ... they might not hit the same level because ... of ... the rollover Gap but you want them to hit the level". Workflow: Q: "you go to Euro USD chart Forex you highlight the levels that you like then you look at the Futures you take an adjusted and ideally unadjusted chart you look hey are they both hitting a l[evel] as well and ... then you're good to go". Contract-specific (ECZ24) = optional extra layer.
- Zone choice: Q: "level on top of level on the daily chart ... I choose also again a bigger imbalance so bigger level for me to trade so to give price more room to breathe". Zone = daily RBD supply.
- Q: "you cannot be 100% accurate with timing ... price can go deep inside the Zone price can hit your stop loss".
C. CME GAPS (testable)
- Q: "gaps on unadjusted charts are extremely important ... but only when we look at gaps on the CME Futures unadjusted sharts"; Q: "the only gaps that matter are those gaps seen by institutional Traders they trade them fill them and push the market either toward or away from them". FVGs dismissed (Q: "fake value gaps").
- MINI GAP + ROLLOVER GAP: Q: "we have this Gap being filled this mini Gap here that we also discussed we have filled so what remains open is that rollover Gap so ... as one target is ... the fill of the roll over Gap". Outcome: Q: "we filled the roll over gaps as anticipated ... price arrived at my target".
D. Results: Q: "this one Mega trade put me back in the VIP lounge and generated $24,000 of profit" (FTMO, moved from 10th to 3rd); Q: "this trade had me waiting for three weeks"; Q: "The trade was extremely quick lasting only 4 days"; levels shared with students 3 weeks in advance.

## 28. 20241231_Campus_Fund_Explained__Get_Funded_Without_a_Challenge.txt
2024 year review + teaser for his own prop firm. Caption reads like a back-translation ("deal" = trade). D-heavy, plus claimed seasonal-roadmap hits.
D. Results (as stated)
- Q: "third place on the FTMO leaderboard ... a total of $500,000 in profit on my main trading account".
- Q: "I made it onto their leaderboard 120 times"; "absolute FTMO record holder of all time".
- RISK: Q: "I also increased my largest prop account to $2 million in funding, increasing my risk per deal from $10k to $ 20k" (= 1% of $1M -> 1% of $2M).
- Q: "I made $55,000 [caption; cf. file 24, ~ $550k] in profit from this account alone".
- MXN: Q: "During the Mexican election, I opened a short position on the peso and made $80,000 ... I mentioned this deal twice in a YouTube video weeks before it happened". (Part-1 trade = short MXN into the June 2024 election; file 04 = the follow-up bottom-catch long MXN.)
- Q: "I simultaneously took on six prop challenges and successfully completed them all".
C. Dow 2024 roadmap claims (from his January 2024 PDF/video; verify vs US30 2024):
- Q: "I was expecting a very 'bullish' April. Yes. Sell in May and walk away. There is a 'bullish' summer until August. ... That short shorts in early September. ... The best deal of the year from the end of October until the Christmas rally". Q: "I provided seven trading ideas in that PDF. All seven turned out to be correct."
- Election: Q: "I accurately predicted how the market would react to the election ... the bullish rally at the end of the year that followed".
- Style: Q: "my set-it-and-forget-it strategy".
- Nothing on tool parameters or zone rules.

## 29. 20250110_The_Trading_Habits_I_m_Leaving_Behind_in_2026.txt
"10 habits" video (published Jan 2025). A few testable statements.
C. Mexican-election back-test (testable): Q: "the Mexican pzo trade I would say 80% of the analysis made on this trade was back testing we will look looking all the way back to June 2006 ... I did the back testing for the three previous Mexican elections and each one of them had the same results as the previous one". => H: MXN path around Mexican presidential elections (2006, 2012, 2018) repeats in 2024 (exact pattern not described here; part 1 video is in another batch).
A/B. Two-stage strategy incl. CME gaps: Q: "my trading strategy is split into two stages Market fundamentals and applying technical such as supply and demand or targeting C[ME] gaps". Q: "what's the only two things we are looking for to have a successful trade Direction and time".
B. Impulse rule: Q: "when you see an Impulse move learn to respect it by waiting for the correction that follows and only then you can engage" (example: post-election Nov 2024 FOMO buyers Q: "ended up getting wrecked the following week").
B. Deep stop when COT is extreme (discretionary): Q: "you have solid fundamental proof like for example a massive spike in retail behavior on the c[OT] Index while the market is refusing to drop so you prepare a very deep stop loss hold onto your seat and embrace being in the red for as long as it takes".
B. Zone quality: Q: "look for institutional activity which appears on the chart as long candles"; Q: "if you waited at the high quality Zone ... either you will get filled and the trade will most likely be profitable or you will not get filled and you won't lose anything".
B. R:R: Q: "in day trading most trades have a risk reward ratio of one to one or one to2 at Best" (why he prefers swing).
B. HTF context: Q: "zooming in on Lower time frames without checking the daily or weekly Trend led to poor trades".
- Journal: 14 columns (open/close date, symbol, timeframe, direction, SL, entry, planned target, actual exit, R:R, win/loss, P&L, balance, notes).
- Nothing on COT/valuation/seasonality parameters.

## 30. 20250117_Supply___Demand__The_Action_Matrix_For_High-Probability_Trades.txt
S&D pro trader series: the ACTION MATRIX (location x direction x LTF zone). HIGH VALUE (codeable).
B. Top-down order: Q: "step one identifying the higher time frame location followed by step two assessing the trend Direction and step three performing the lower time frame zoning process to establish our setup". LTF example: Q: "the 240 minute chart for example".
B. MATRIX as stated (PM = profit margin, P = probability)
- LTF SUPPLY, HTF location high/very high: downtrend = Q: "the ideal profit margin scenario and the ideal probability of success"; sideways = Q: "profit margin is medium ... probability of success is slightly higher than the counter Trend trade"; uptrend = Q: "our profit margin would be limited or low and our probability of success would also be low".
- LTF DEMAND, HTF location low/very low: uptrend = ideal/ideal; sideways = medium/medium; downtrend = Q: "the minimal or low profit margin and low probability of success".
- EQUILIBRIUM: with trend = medium/medium (Q: "trading in equilibrium is allowed but not ideal if we are trading with the trend"; Q: "trading from an equilibrium location is permissible when aligned with a strong uptrend or downtrend"); sideways = forbidden (Q: "if more [lower] time frame zones are located in the context of bigger picture equilibrium and sideways Trend we are not allowed to set the trade").
- HARD BANS: Q: "we can never trade demand in a context of higher time frame location high"; Q: "we can never trade Supply in the context of higher time frame location law [low] even if we are trading with the trend".
- Permission statement: Q: "we are always allowed to trade lower time frame demand if we are in the context of HTF l[ow] and very low but the profit margin and probability of success changes depending on the trends". => counter-trend at an extreme location is ALLOWED (lowest grade), not forbidden.
- GAPS: demand-in-equilibrium-with-downtrend / supply-in-equilibrium-with-uptrend not explicitly stated (INF: not allowed, since only "aligned with" trend is permitted in equilibrium); "strong" trend undefined; no numeric mapping of "medium/low" to size or R:R.
- EVOLUTION NOTE: file 16 (2024-09-13) called equilibrium a blanket "no touch area"; this lesson (2025-01-17) allows equilibrium trades with the trend. Treat the matrix as the later, more complete rule.
- Nothing on COT / Valuation / Seasonality.

