# Bernd Skorupinski transcripts, batch 00 (32 files, 2023-02-28 to 2023-09-30)

# SYNTHESIS (batch 00)

Files are cited by upload-date prefix (unique in this batch). Every file in the list was read in full.
Content: 32 files. About 12 carry method content; the rest are mindset or prop-firm promotion. Four are machine re-translations with punctuation (0319, 0401, 0627, 0803): there "underrated/underestimated" = undervalued, "fall-base-rise" = DBR, "deal" = trade.
Tool names over time: "Smart money Index" / "Smart Money Campus index" / "smart money index with the COT index" (COT); "campus valuation tool" (valuation); "seasonal forecasting tool" = "campus algo forecast" = "hybrid AI" (seasonality). The tools run on TradeStation (0930: "our indicators right they run on trade station").

## 1. Indicator evidence table

| Setting | What he says (EXPLICIT unless marked) | Files |
|---|---|---|
| VAL reference markets | Equity indices and US stocks: Treasury bonds come first ("very important we use in our evaluation model we use the treasury bonds"). All three references for indices: "purple is the dollar yellow is gold blue are the treasury bonds". | 0309, 0319, 0401, 0930 |
| VAL references by market | Gold vs USD ("we want to enter gold once gold is undervalued versus the dollar"). Platinum vs USD ("the purple line is the US dollar which is important"). CHF futures (6S) vs GOLD ("using gold in the valuation model to compare it with the Swiss franc"). Silver vs gold (student). | 0930, 0926, 0529, 0601 |
| VAL thresholds/display | One line per reference, plotted on the daily chart. "close to the green horizontal line which means undervalued ... close to that red horizontal line we're overvalued"; "everything above that red horizontal line means strongly overvalued"; "around the mean". No number for lookback, period or threshold appears in this batch. | 0930, 0529 |
| VAL strength | "undervalued versus all three assets ... almost a self-fulfilling prophecy ... can be almost used as a timing tool". Indices: "the valuation tool is the most important tool for me". | 0930 |
| VAL near-threshold | He counted readings that had NOT crossed the line. YM 2022-07-13: "not yet underrated [undervalued], but we are almost" -> "three out of three". Gold 2023-08-21: "very close not yet fully undervalued" -> "valuation perfect". | 0401, 0930 |
| VAL as exit | "once prices overvalued I exit the trade" (platinum vs USD). "get out either once price hits the target ... or once price gets overvalued versus the dollar ... one of the tools that I use also to Trail". | 0926, 0930 |
| COT groups | Blue = "smart money ... banks and institutions" (commercials). Red = "retail" (small specs). Third line: "remove the Orange Line because the Orange is not important" (INFERENCE: large specs). The report type is never named; three groups fit the legacy report (INFERENCE). | 0319, 0401, 0529, 0930 |
| COT thresholds | "when the line ... is down [below] the horizontal red line ... bearish ... up [above] the green line ... bullish". Retail "above the green horizontal line ... and even up to that white horizontal line ... extremely bullish" = two upper levels. No numbers given. | 0401, 0529, 0930 |
| COT normalisation | "It's always important to look at smart money in relation to their previous Behavior". This fits a lookback index; the 157 weeks and 20/80 are NOT stated in this batch. | 0926 |
| COT timeframe/role | Read on the weekly chart. "this is not a timing tool ... more like to get a bias"; "icing on the cake"; "it took some time"; horizon "one or two weekly green candles". Most weight on commodities: "very important especially trading Commodities here gold silver". | 0529, 0926, 0930, 0319 |
| COT best setup | Commercials at a bullish extreme AND retail at a bearish extreme, "close to the perfect scenario" (gold, 2023-08-23); compared with the COVID 2020 low (YM, 2022-07). A retail-only extreme was used alone on 6S. | 0401, 0930, 0529 |
| SEAS lookback | Student: "the last 5 or 10 or 15 years" (so the tool has 5/10/15-year options). Averaging and detrending: never stated. | 0408 |
| SEAS output | Timing only: "it doesn't forecast the price points ... I can stretch this ... forecasting the approximate low ... and the next approximate high". | 0522, 0930 |
| SEAS "dynamic" | "Dynamic it might change slightly according to price movement ... learning from the current price movement ... hybrid AI"; "it's basically AI". | 0522, 0408 |
| SEAS horizon | The BTC forecast made at the end of November 2022 showed a low in December and a high "around April", so it runs at least 4-5 months ahead. His trade readings look 2 weeks ahead: YM "next two weeks", 6S "14 days", gold "top around after the first week of September". | 0522, 0401, 0529, 0930 |
| COMBINATION | "two out of three ... in terms of my set of rules that's enough"; all neutral -> "I'm staying away". 3/3 = "All Stars aligned" / "three out of three ... screamed bullish". No override rule. Stocks need their index to agree; index longs need ES, NQ and YM all in demand. | 0309, 0529, 0930, 0319, 0926 |

**Contradictions/refinements to our reconstruction:**
- (a) VAL: the three references DXY/ZB/GC and the threshold lines are CONFIRMED. The numbers 480 / ±0.75 / 10 are NOT confirmed here. The reference that matters depends on the market, so "any 1 of 3" is wrong as a general rule. Two showcased entries were taken *before* the line was crossed, so a hard ±0.75 gate is stricter than what he did. Add the overvalued-exit rule to tests.
- (b) SEAS: 15 years is plausible. "30 days ahead" understates what he displays (months on BTC), although his trade horizon is about 2 weeks. A static 15-year average cannot "change slightly according to price movement". Re-anchoring the curve to the latest bar, or including the current year, would explain it (INFERENCE).
- (c) COT: a weekly, history-relative index is consistent. Note the extra upper "white" level (an extreme band beyond green) and the ignored third group.

**Readings to check our implementation against** (date = his chart "today"):
- NQ 2023-01-05: VAL undervalued vs bonds; SEAS low on 01-06 then up; COT neutral. Long 01-06 -> 01-12 (0309).
- AAPL and NQ 2022-10-12: VAL undervalued vs bonds (both); SEAS AAPL up for a few days, then sideways, down, up; NQ bottom in, a dip later, then the "real bottom"; NQ COT aligned bullish (0319).
- YM 2022-07-13: COT commercials super-bullish and retail extreme-bearish; SEAS up steeply for 2 weeks, peak around 07-27; VAL "almost" undervalued vs bonds (0401).
- BTC: forecast low Dec 2022 and high Apr 2023; as of 2023-05-22, low expected in the 3rd-4th week of June 2023 (0522).
- 6S 2023-05-02: forecast down until about 05-16; VAL overvalued vs gold (above the red line); COT retail at the white line (0529).
- Platinum 2023-08-15/20: COT "very bullish", "even more bullish ... than ... February March"; VAL rising from undervalued vs USD; 08-25 "around the mean" (0926, 0930).
- Gold 2023-08-21..24: VAL close to undervalued vs USD; COT smart money very bullish, retail near very bearish; forecast top "after the first week of September" (0930).
- Dow 2023-08-25: "under valued versus all of these three assets" (0930).

## 2. S&D rules as if-then (gaps marked)
1. ZONE: IF price ranges or balances (the base, the "origin") AND then leaves with an "explosive ... decisive" move, not "stair stepping", THEN box the base and extend 2 lines right (0918, 0930). Named patterns: DBR, RBR, and "level on top of level" (DBR then RBR) (0309, 0319, 0401, 0930). RBD/DBD appear only as "supply". GAPS: base-candle definition (body vs range, count), leg-in, proximal/distal by wick or body, numeric leg-out size.
2. QUALITY: "fresh" is praised (0319, 0401, 0529); a supply "tested once" is treated as weaker (0926). GAPS: a precise freshness or invalidation rule; flip zones, originality and the action matrix are not mentioned in this batch.
3. BIG/SMALL BROTHER: IF a lower-TF zone lies inside a same-direction higher-TF zone ("the daily ... covered by the weekly"), THEN quality is higher. Pairs: weekly->daily, daily->120-min (0319, 0610, 0926).
4. INDEX/STOCK SYNC: IF trading a US index, require ES, NQ and YM all in demand ("based on my rules I'm not allowed to go along") (0926). IF trading a stock, require its index in demand and the bias tools to agree (0319, 0719).
5. ENTRY: a limit order at the proximal line, placed in advance ("set and forget"), with a market order if price is already inside the zone (0423, 0529, 0803, 0926). REFINEMENT: a lower-TF zone (240/120/60-min) inside the higher-TF zone moves only the entry; "the stop loss can never vary" (0601). Execution timeframe is 60-min to daily. "I never went lower than a 240 minute interval" (0423) contradicts "the lowest ... 60 minutes" (0408). Pin bar and engulfing candles are context only; there is no confirmation-entry rule and no "3 entry models" in this batch.
6. STOP: just beyond the distal line ("stop loss below the demand Zone"; EURUSD 1.0823/1.0778 "this defines our Zone") (0423, 0810). GAP: buffer size.
7. TARGET: just before the opposing higher-TF zone (0309, 0401), "a few Pips ... before your profit Target" (0307). Normal R:R is 3-4:1 (0307); the YM trade made 3.5-4:1 (0401); the minimum average is 1:2 (0430, 0509). Prop challenge: 1:1 (0423, 0712). Alternatives: no target plus a trail for trend trades, with the trail method unstated (0810); exit when overvalued (0926); exit at a seasonal turn date (0401).
8. MANAGEMENT: move to breakeven "at a certain point" (vague, 0319). "don't move your stop-loss don't manually exit in the red" (0926). Discretionary early closes to finish a challenge (0930).
9. RISK: a fixed $ amount ($1,500 on 100k, 0423); 1% ($2k on 200k, 0401). Challenge 2% then verification 1% (0408, 0423, 0712). Correlated trades at 1-1.5% each (0408, 0423), yet he ran 3%+3% = 6% himself (0930). 1% at a 6% max-DD firm (0529); about 0.5% on a $1M account (0601).
10. NEWS: ignored (NFP, 0309). On FOMC days he only watches lower-TF reversals (0926).

## 3. Other testable hypotheses (exact definitions)
- **H1 Globex breakout trap** (0627; student 0601): ES/NQ/YM/RTY on ET exchange time. ETH runs 18:00-09:30; take its high (GH) and low (GL). After 09:30, IF price trades below GL into a quality demand zone that lies below GL and was "created between 8:00 and 11:00 AM", THEN buy at the zone. Mirror the rule for GH and supply. Zones inside [GL, GH] are invalid. Target 1R (student's rule; Bernd states none). GAPS: zone TF, stop buffer, end-of-day exit, trend/location filter.
- **H2 Pre-election Q4** (0905): long DJIA from Oct 19 to the last December session in years with year mod 4 = 3. Claim: 11 of the last 12 positive (only 2007 negative), mean +4.95%. Also claimed, 1900-2022 yearly DJIA averages: pre-election +9.03%, post-election +4.7%, midterm +0.66%. Seasonal path = average of the last 12 pre-election years (up in H1, decline to mid/late October, buy in the 3rd week of October).
- **H3** Indices: long when VAL is undervalued vs all of DXY, GC and ZB at once (0930).
- **H4** COT double extreme: weekly commercials above the upper line AND small specs below the lower line; horizon 1-2 weeks (0401, 0930).
- **H5** Exit a long when VAL crosses into overvalued vs USD (metals) (0926, 0930).
- **H6** Seasonal timing: enter at the projected seasonal low, exit near the projected high (0401, 0522).
- **H7** "Mini gap" (0926, platinum daily): "we had that mini Gap filled ... that was supposed to happen". Undefined in this batch.
- NOT FOUND in this batch: decennial cycle, 50-year Dow cycle, open interest, gold Dec-Jan seasonal, the optimizer (only "in the pipeline", 0601).

## 4. Five most useful quotes for coding the tools
1. 20230930: "for the equity indices the valuation tool is the most important tool for me and every time we undervalued versus the treasury bonds this is a big big Buy Signal and if we undervalued versus all three assets treasury bonds gold and dollar then this is like almost a self-fulfilling prophecy" + "purple is the dollar yellow is gold blue are the treasury bonds".
2. 20230930: "if we are close to the green horizontal line which means undervalued if we close to that red horizontal line we're overvalued versus dollar".
3. 20230926: "It's always important to look at smart money in relation to their previous Behavior" (+ 20230930: "the Blue Line represents the smart money the red line represents the retail Traders ... the Orange is not important").
4. 20230522: "it doesn't forecast the price points ... I can stretch this ... what it does is forecasting the approximate low ... and the next approximate high" + "that tool is also Dynamic it might change slightly according to price movement".
5. 20230309: "I have basically two out of three of our tools flashing green ... in terms of my set of rules that's enough".

## D. Results / realism (for checks)
- FTMO: "$170,000 in ... 5 months" on 200k, then 400k in months 4-5; about 80 trades in about 100 days, "four trades per week" (0309, 0516).
- First funded month: 26 trades, +$15k gross (0401).
- "10 to 15 trades a month" (0803).
- Claimed KPIs: average R:R at least 1:2 with a 40-60% win rate (0430, 0509). Expect "10 to 15 [losers] ... in a row" (0415).
- Holding times: 3.5-15 days (AAPL 5d, NQ 6d, YM 15d).
- Prop capital: $2.4M (after the SurgeTrader $1M), then a VisionStar $1M. "3.4 million" is said once (0727), but later intros still say 2.4M.

---

# Per-file notes (written as read, in list order)

Conventions: quotes are verbatim caption text (mis-hearings kept, my corrections in [brackets]).
"EXPLICIT" = he states it; "INFERENCE" = my reading. "vague" = he gives no rule/number.

## 01. 20230228_The_7_Things_Pro_Traders_Fix_Before_Strategy (mindset, no indicators)
- No COT / valuation / seasonality / S&D mechanics in this file.
- D (routine): EXPLICIT max 1 hour/day of chart work: "spend maximum one hour a day examining them and determining your next trace [trade]"; "that's what I call set and forget and get a life".
- D (frequency): "a month of just a few trades can be enough to grow your trading account".
- Rule-following: "I'm unaware of which trade setup will win or lose so I must take every trade that matches my trading plan without questioning it".
- No news: "don't waste time looking for online news articles or seeking validation from others".
- Context: video ends with "visit our website onlinetradingcampus.com" (Online Trading Campus = Sam Seiden's S&D school; his S&D framework is OTC-derived at this date).

## 02. 20230307_Why_Most_Traders_Can_t_Grow_Their_Account (mindset / money management, no indicators)
- No COT / valuation / seasonality in this file.
- B targets: EXPLICIT front-run the target: "exit a trade a few Pips ticks or cents before your profit Target"; "when setting your profit Target be less precise ... aim for slightly lower level".
- B R:R: "instead of targeting a four to one or three to one try aiming for two to one reward for your first few trades" (so his normal targets are 3:1-4:1; 2:1 = beginner setting).
- B risk: fixed amount per trade: "start by determining the specific amount to risk per trade and stick with it until you have a track record of profitability"; only scale after 3 months: "if you can't demonstrate an ability to increase your Capital over at least three months consistently it is not wise to risk more money".
- D yearly goal: "aim for a total return of 20 to 24 hour units over a year" (probably "20 to 24 R units" per year; caption unclear).
- Markets (universe): "focus on the most liquid and widely followed markets such as the major Forex pairs made sure you stock in the Seas [major US stock indices?] Blue Chip stocks gold and oil"; "I personally like to focus on U.S stock indices all relevant stocks and precious metals"; avoid exotics ("Turkish lira").
- Randomness: "no one can predict which traits [trades] will be winners and which will be losers they are distributed randomly over time".

## 03. 20230309_The_NASDAQ_Trade_That_Made_Me__66_000 (KEY: 3 tools + 2-of-3 rule + worked trade)
- D results: "I made over 170 000 trading with ftmo ... in five months of trading"; "I took over all 80 trades" in ~100 trading days; "on average I take maybe one trade per day maximum"; "I only took four trades per week based on my official fdmo statistics".
- Process: EXPLICIT "two-step mechanical process": step 1 = bias from 3 "proprietary" tools, step 2 = timing with S&D: "step one determines whether I'm going to be bullish bearish or neutral ... timing the market is step two ... For timing the market I use supply and demand analysis".
- A VALUATION (EXPLICIT): equity index vs treasury bonds, daily chart: "our campus valuation tool ... whether we are undervalued or overvalued on the equity indices here in particular on the NASDAQ versus the treasury bonds very important we use in our evaluation model we use the treasury bonds"; "on anonastic [a NASDAQ] on a daily chart ... once it's down here it's undervalued and once it's up here it's overvalued"; "when we are overvalued we rather look too short or get out of our long position". He eyeballs past signals ("even in a downtrend once we are undervalued we are getting a nice retracement") = valuation signals retracements, not only trend turns. No numbers (period/threshold) given.
  - READING: NASDAQ (NQ) daily, 2023-01-05: undervalued vs treasury bonds ("this is the fifth ... so we are undervalued").
- A SEASONALITY (EXPLICIT): called "our seasonal forecasting tool", plotted as a forward projection from the last candle: "imagine today is the fifth of January that's the last candle here and it gives us here a forecast to the Future"; he reads turning points: "from tomorrow you see here it should make a low and then we should go higher". No years/length stated.
  - READING: NASDAQ seasonal, as of 2023-01-05: low due 2023-01-06, then higher.
- A COT (EXPLICIT, name at this date = "Smart money Index"): "our third tool is the Smart money Index ... if the big Banks and institutions are also in an extreme bullish or bearish but here you see basically right now they are neutral". So COT signal = commercials ("big banks and institutions") at an EXTREME; otherwise neutral. No lookback/threshold stated.
  - READING: NASDAQ COT ("smart money") 2023-01-05: neutral.
- A COMBINATION (EXPLICIT): 2 of 3 is enough: "I have basically two out of three of our tools flashing green ... in terms of my set of rules that's enough that's perfect ... two out of the three tools are bullish so I'm getting bullish". Neutral -> no trade: "If my forecasting tools are neutral I'm staying away".
- B entry: 60-min DBR demand formed AFTER bias, limit-style entry on return: "this is now the 660 [60] minute chart ... I waited for this demand Zone to be created it was a nice job based rally [drop-base-rally] and then I bought once price came back into the demand Zoom [zone]"; stop below the zone ("my stop was ... below here obviously well protected"); "it went deep into the demand Zone I took a little bit heat".
- B target: exit before opposing HTF zone: "if we go to a daily chart ... we were approaching an opposing ... Supply zone so I exited ... before that opposing Supply zone".
- B news: ignored ("I think this was non-farm payroll ... I couldn't care less about the news").
- D trade: NQ long, entry 2023-01-06 (NFP day), exit 2023-01-12, "+66 000" on FTMO account. Holding ~6 days.

## 04. 20230319_How_I_Made__18_000_on_ONE_Apple_Trade_as_FTMO_s__1_Trader (KEY: correlation rule, COT two-line display, big/small brother)
(This caption is a machine re-translation with punctuation: "underrated/underestimated/understatement" = undervalued, "fall-base-rise" = DBR, "rise-base-rise"/"growth-base-growth" = RBR, "older and younger sibling" = big brother/small brother, "deal" = trade.)
- D: "number one trader on the world leaderboard ... first in November, December and January" (2022-11 to 2023-01); "$170,000 in the last 5 months trading with FTMO".
- D trade: AAPL CFD long, entry 2022-10-13, exit 2022-10-18, held over weekend, "$18,000 ... in just 5 days".
- C/B CORRELATION RULE (EXPLICIT): stock must be in sync with its index in BOTH steps: "when we trade stocks, the specific index here, the Nasdaq, has to be in sync with Apple"; later "also on supply and demand ... we have to be in sync with Nasdaq".
- A SEASONALITY readings (as of 2022-10-12, day before entry): AAPL "predicts that Apple will go up ... For a few days before it goes sideways a bit, then down, then up again"; NASDAQ "the bottom has already formed and we will continue to grow, at least for a few more days ... then we might go a little lower again, but then we'll have a real bottom". He reads the projected path shape (zigzags), not a single number.
- A VALUATION (EXPLICIT): stocks AND stock indices vs Treasury bonds: "our valuation model here compared to Treasury bonds, which is very, very important for stocks and stock indices". READINGS 2022-10-12: AAPL undervalued ("We are underrated [undervalued]"); NASDAQ "close to being underestimated [undervalued] ... and we're undervalued". Again only visual zones ("down here, underrated"); no numbers.
- A COT (EXPLICIT display): two lines, "the blue line represents the 'smart money,' the big banks and institutions. So when they're up here, they're extremely optimistic. And the red line represents a retail trader who usually loses money ... when they're down here, they're pessimistic ... we want to trade against retail traders and together with the 'smart money'". So the tool plots commercials (blue) and small speculators/retail (red), both apparently on an oscillator scale with extremes. Status: "this is a little gem, this is the icing on the cake" = COT used as a confirmation, not a primary signal, at this date. READING 2022-10-12: NASDAQ COT "also aligned" (bullish). AAPL itself has no COT (none mentioned).
- A COMBINATION: tools on Apple and Nasdaq must "speak the same language" -> "we're definitely not bearish ... not neutral, so we're bullish".
- B ZONES: AAPL daily DBR "Extremely high quality"; weekly RBR containing it: "The weekly pattern of 'rise-base-rise', actually superimposed on 'fall-base-rise' ... level on level ... the daily schedule is covered by the weekly schedule ... the older and younger sibling principle [big brother / small brother]". INFERENCE: big brother/small brother = lower-TF zone nested inside (overlapping) a higher-TF zone in same direction. NASDAQ: daily DBR + weekly "fresh" RBR above it ("We are just getting closer to it").
- B entry: set-and-forget pending order placed the day before: "It was a 'set it and forget it' deal ... I set it up and placed it in advance"; filled on a gap open "deep in the demand zone, but still in the demand zone".
- B management: one action, stop to breakeven at an unspecified point (vague): "just move the stop loss to the breakeven level at a certain point, and that was it".

## 05. 20230324_This_Is_How_You_Trade_From_Anywhere__Set_and_Forget_ (lifestyle; little method)
- No indicator content.
- D bio: "full-time Trader hedge fund manager and a verified funded ft[mo] prop Trader I've been trading for over 10 years"; teaches at "online trading campus" ("the trade from anywhere concept that we teach at online trading campus").
- B timeframes (vague, general): "trading higher time frames like daily weekly or monthly can help you become a set and forget and get a live Trader ... check the charts once a day"; "by focusing on higher time frames like daily weekly or monthly you'll enter smaller number of Trades".
- B management: no monitoring after entry: "try setting and forgetting your trades once you enter them it'll allow the market to do the heavy lifting".
- B risk: vague: "keep your risk per trade at the manageable level that won't cause too much anxiety".
- Method label: "mechanically analyze and identify trading opportunities based on supply and demand"; "low risk High reward and high probability" (= OTC "odds enhancers" vocabulary; no numbers given here).

## 06. 20230401_How_One_Supply___Demand_Earned_My_First_FTMO_Payout (KEY: COT display with 2 threshold lines; both-groups-extreme setup; 1% risk)
(Machine re-translation; "assessment tool" = valuation tool, "underrated/underestimated" = undervalued, "fall of the base rally" = DBR, "deal" = trade.)
- D: FTMO 200k two-step passed; first funded month "26 trades and made $15,000 ... before profit sharing and $12,000 after ... 80/20"; "The first month was also my weakest month".
- EXPLICIT: analyse the futures, execute the CFD: "YM, Dow Jones futures ... executed ... on a CFD ... US30 ... we always analyze futures, which is really important because it's the underlying asset".
- Tool names at this date: "Smart Money Campus index" (COT), "algorithmic campus forecast, which is our seasonal ... algorithmic forecast", "campus assessment [valuation] tool".
- A COT DISPLAY (EXPLICIT): "two lines ... the blue line that represents Smart Money ... the banks and institutions, and ... the retailers ... a horizontal green line and a red line. So when the line ... is down, [below] the horizontal red line, that means they have a bearish sentiment, and when the line ... is up, [above] the green line, that means they have a bullish sentiment"; "they're not just crossing the green line now, they're right up here. So they are super optimistic". => oscillator per group with an upper (green) and lower (red) threshold; levels not stated here (consistent with an index with 20/80-type bands, but no numbers given).
- A COT SETUP (EXPLICIT): strongest = commercials extreme bullish AND retail extreme bearish at the same time; he compares to the 2020 COVID low: "the last time we had this kind of mood ... This was during the coronavirus ... when banks and institutions started being super bullish and retail traders were super bearish, the price started to rise and ... went up like a rocket". (Caption at one point says retail "very, very optimistic/bullish" - context and the COVID comparison show he means bearish; zero-sum logic: "if they're optimistic and buying, they have to buy it from someone ... retail traders".)
  - READING: YM (Dow) COT ~2022-07-13/15: commercials "super optimistic" (well above upper line), retail extreme bearish; last comparable extreme = COVID 2020.
- A SEASONALITY READING: YM as of 2022-07-13: "over the next two weeks the price will focus on this line, which will go up steeply". Also apparently used for exit timing: "I know when I need to get out roughly, right? 27. Then the price should stop and perhaps go down a little" (= seasonal peak ~2022-07-27; he exited 2022-07-29). INFERENCE: seasonal projection length >= 2 weeks; he reads turning dates from it.
- A VALUATION READING: YM vs Treasury bonds 2022-07-13: "we're progressively undervalued ... We are not yet underrated, but we are almost underrated" -> he still scored it bullish: "So for me it's about three out of three". => a reading approaching (not beyond) the threshold was counted as agreeing. Contradiction risk for a hard -0.75 cutoff.
- A COMBINATION: "now I have two of the three tools telling me it's already bullish" (COT + seasonal) -> then valuation "almost" -> "three out of three".
- B entry: "Very nice fresh fall of the base rally [DBR]" demand; set-and-forget order placed 2022-07-13 for fill 07-14; timeframe vague (he says "if we look at the daily chart"; also "in 1 hour" which may be "1 hour a day").
- B target/R:R: exit at opposing supply: "entering the opposite zone, which is the supply zone ... I made about $8,000, risked $2,000. So about 4 to 1 ... 3.5 to 1 or so".
- D risk: $2,000 on a $200,000 account = 1.0% per trade (EXPLICIT numbers). Holding 2022-07-14 -> 2022-07-29 (15 days).
- B management: "Your entire set process, stop, entry, target, should be objective and pre-planned ... let the trade unfold without interfering and changing your stop loss or target prematurely".

## 07. 20230408_The__1_Hour_A_Day__Trading_Routine_That_Works (podcast with OTC student "Francois"; tool names; seasonal lookbacks; challenge risk 2%)
- Tool list (EXPLICIT, Bernd): "we have the valuation tool we have the seasonal algo forecasting tool we have the smart money index with the cut Index [COT index]" -> COT tool at this date = "smart money index / COT index".
- A SEASONALITY (student, not Bernd): "the seasonality indicator ... gives a bit of a historical view of the last 5 or 10 or 15 years of ... the particular trade [market] you're looking at" => tool offers 5/10/15-year lookbacks (consistent with a "15" setting).
- A SEASONALITY (Bernd, IMPORTANT caveat): "the seasonality forecasting tool it's not just the normal seasonality tool right it's like um it's basically AI that anticipates the future right it shows you what's happening in the next few days in the next few weeks". => in Apr 2023 he markets it as "algo/AI" forecast, projection horizon "next few days ... next few weeks". Vague on method; could mean something beyond a plain average path. Flag for the reconstruction.
- A usage (student): seasonal + S&D as timing: "I look at the seasonality too and see you know are there any um good Longs or good shorts coming up and then I would do that together with the uh supply and demand ... entry point"; made money on "Mexican peso" with the seasonal tool; valuation used for "stocks and Equity indices to see ... is it undervalued or is it overvalued".
- B timeframes (Bernd, EXPLICIT): challenges/verifications: "the lowest time frames I also went for myself in 60 minutes right but most of the trades 240 minute daily time frames the execution time frame". Student: daily + 240-min, "sometimes as low as 60 minutes".
- B S&D role (Bernd): S&D for "timing the market to place your entry to place your stop loss and then ... your targets".
- D/B RISK (Bernd, EXPLICIT): "when I did all the challenges and verifications I always used two percent risk so I have to have only five winners"; correlated trades: "if you take two percent on ... NASDAQ long and an apple long ... you have four percent risk exposure ... I would also then lower my risk to one percent or 1.5 risk if I take highly correlated trades"; and he RECOMMENDS correlated trades in challenges: "I can recommend to everyone who is doing a challenge ... to take highly correlated trades ... to get to that ten percent ... but then ... lower the risk from two percent to 1.5 or 1".
- FTMO rules as he states them: "30-day time period ... achieve 10 Roi ... Max drawdown limit and the daily drawdown limits".
- Student stats (realism check, not Bernd): one month $17,000, "win loss ratio ... 75 percent", "21 hours [21R]" in the month, 1% risk, "three or four trades a week", "80 [%] of those trades ... were set up on a Sunday".
- Bernd bio: "I started trading more than 10 years ago"; uses "daily daily targets weekly targets" = nonsense; process over money.

## 08. 20230415_Why_Most_Traders_Fail__The_Honest_Truth_ (generic; no proprietary tools)
- No COT / valuation / seasonality content.
- Losing streaks (realism): "imagining losing 10 to 15 trades out of 100 trades in a row can you handle that emotionally".
- Demo rule: "demonstrate [demo trade] for one to three months"; "taking 20 to 50 trades in the demo account ... If you're not able to be profitable ... after taking 20 to 50 trades give me one reason why you should ... risk your real ... money".
- Anti-indicator: "conventional indicators can actually do more harm than good ... Master the art of trading with just supply and demand"; "focusing on the fundamental data which is price".
- B timeframes (generic): "focus on trading only the higher time frame charts ... daily weekly and monthly"; "you've got to understand the context of the weekly and monthly charts too". 1-5 min charts = "waste of time".
- Losses: "good loss" = rule-following statistical loss; "bad loss" = rule break / overtrading; "only trade when your Edge is clear and obvious".

## 09. 20230423_How_To_Pass_A_Prop_Firm_Challenge_With_Just_5_Trades (KEY: challenge R:R 1:1 at 2%; zone = entry-to-stop; fixed $ risk)
- B "set" = "set stop entry Target ... The set must be pre-planned".
- B ZONE DEFINES ENTRY AND STOP (EXPLICIT example): "buy euro dollar at 1.0823 and put our stop loss at 1.0778 this defines our Zone our buy area we buy when price comes back to our predefined Zone this Zone defines our risk". INFERENCE: entry at proximal line, stop at/just beyond distal line; buffer not mentioned (vague). Zone height here 45 pips.
- D risk (EXPLICIT, personal): "I don't use percentage risk but a fixed dollar risk amount by the way that's how I personally do it so ... based on 100K funded ftmo account you could say I risk a thousand five hundred dollars per trade" (= 1.5%).
- B/D CHALLENGE RULES (EXPLICIT): "I personally recommend within the entire evaluation phase one-to-one risk to reward targets ... I say two percent risk per trade ... your target is two percent as well"; "five winning trades are enough to pass the 30-day challenge ... even if you have two to three losers it is still reasonable to get the 10 [%]".
- B correlated trades (EXPLICIT): recommended (FX pairs sharing USD/EUR; Dow, S&P, Nasdaq; "Apple and NASDAQ at the same time") but "lower my percentages either to one percent or ... 1.5 risk on those trades".
- B timeframes (EXPLICIT): "don't scalp you don't have to go lower than a 60 Minute time frame"; "you in fact can trade intervals between 240 minutes and daily for my challenge I never went lower than a 240 minute interval". CONTRADICTION with file 07 (2023-04-08: "the lowest time frames I also went for myself in 60 minutes").
- "I've never met a consistent scalper in my entire 10 years of professional full-time trading career".

## 10. 20230430_The_Trader_s_Roadmap__Without_Quitting_Your_Job_ (generic; strategy KPIs)
- No proprietary-tool content.
- D strategy KPIs (EXPLICIT): "you must be able to achieve an average risk to reward ratio of one to two in conjunction with the win-loss ratio of 40 60 [40-60%] with your strategy".
- B timeframes: "your strategy must be tradable on all time frames I recommend focusing on everything higher than 240 minutes slash four hour charts".
- B: "all trades must be pre-planned and set I call this process set and forget and get a life".
- Anti-indicator: MACD, moving averages, stochastics, Bollinger Bands, RSI: "personally speaking I'm using none of these tools for my own trades" (they are "lagging").
- Business: "we'll be launching our own prop trading firm".

## 11. 20230509_Why_a_30__Win_Rate_Beats_80___Most_Traders_Get_This_Wrong_ (KPIs; R:R thinking)
- No proprietary-tool content.
- D bio: "over 10 years of experience as a full-time professional Trader manage funds the seven figure range and I'm the CEO of a licensed investment consultancy based in Dubai".
- B example set (illustrative, not a real trade): "buy euro dollar at 1.0823 stop loss at 1.0778 and Target at 1.1048" = 1:5 ("for every dollar you risk you make five dollars"). Chasing a missed entry (1.0913) with unchanged stop/target turns it into 1:1 -> do not chase.
- Illustrative "Trader A" rule: "only taking trades with a risk to reward potential of at least one to five" (example only; not stated as his own minimum).
- D KPI minimum (EXPLICIT): "if you achieve that minimum of an average one to two risk to reward ratio and an average win loss ratio of 40 60 ... you are highly profitable"; "you could even have a 30 70 or 2080 win-loss ratio if you average risk to reward ratio exceeds one to three".
- D realism: claims of >=70% win rate over a year = "scammer"; Goldman Sachs daily trading revenue wins "around 80 to 85 percent" of days.
- D risk: fixed $ risk; changing risk after a win/loss "is purely emotional and not recommended".

## 12. 20230516_How_To_Make_Your_First__100K_In_Trading__Realistic_Case_Study_ (KPIs, scaling)
- No proprietary-tool content.
- D case study (illustrative): "average risk to reward ratio of one to two considering only winning trades combined with a 40 winning ratio"; "10 trades in four weeks that's a reasonable average if you focus on swing trading"; month = +2R.
- D risk: "trading a 50k prop trading account with one percent risk per trade"; "our risk is always one meaning we have to keep our risk constant"; scale only after consistency: "increase your risk after for instance the third month".
- D results (EXPLICIT): "I made over 171k in only five months trading with my ftml account and only in months four and five I had a 400k account before I was trading at 200k account".
- Same KPI minimum as file 11 ("average of one to two risk to reward ratio and an average win loss ratio of 40 60"; "30 70 or 2080 ... if your average risk reward ratio exceeds one [to] three").

## 13. 20230522_My_Bitcoin_Forecast_Tool_Called_This_Low (KEY: "campus algo forecast" = seasonal forecast tool; timing-only; long projection; "dynamic")
- A NAME: "the hybrid AI tool that we developed in-house called the campus algo forecast"; "forecasting the seasonal lows and the seasonal highs the time of it in the future". INFERENCE: same tool as the "seasonal (algo) forecasting tool" in files 03/06/07 (he calls it "seasonal" throughout).
- A OUTPUT = TIMING ONLY, NOT PRICE (EXPLICIT): "it doesn't forecast the price points ... if you look at the y-axis I can stretch this ... what it does is forecasting the approximate low ... and the next approximate high so ... the seasonal lows and the seasonal highs". => y-scale arbitrary; he overlays it on price and stretches it; only the dates of turning points matter.
- A "DYNAMIC" (EXPLICIT, unclear mechanism): "that tool is also Dynamic it might change slightly according to price movement ... it's learning from the price movement from the current price movement and that's why we would refer to it as hybrid AI". INFERENCE (not stated): consistent with a seasonal average that is recomputed as new data arrives (e.g. includes the current year / rolling window) or re-anchored to the latest price; NOT evidence of ML. Flag: a fixed "average of last 15 years" would barely change day to day, so "change slightly according to price movement" needs explaining (re-anchoring to current price would do it).
- A PROJECTION LENGTH (IMPORTANT vs our "30 days"): his BTC backtest, made "pretend it's basically end of November" 2022, shows the forecast "literally forecasting that we gonna get the low here and ... the high ... right around April" => projection visible >= ~4-5 months ahead on BTC (daily chart). As of the video (~2023-05-22) he reads a low "third week fourth week of June" (~1 month ahead) followed by "another very significant move" up. So the display extends well beyond 30 days, at least for BTC. Contradicts/refines "15, 30 = 30 days ahead" (unless the 30 is something else or BTC uses different settings).
  - READINGS (BTC): forecast as of ~2022-11-30: seasonal low ~Dec 2022, seasonal high ~Apr 2023 (he says both happened); as of ~2023-05-22: wait for seasonal low ~3rd-4th week of June 2023, then strong rally; "we all have to wait until we are around mid June end of June and then we can start buying Bitcoin".
- A use rule (EXPLICIT): buy only at/after a forecast seasonal low: "we have to wait for seasonal law [low] because why to buy now if the tool is basically not necessarily forecasting a rally".
- BTC context: "bitcoin's movement is closely linked to its halving Cycles" (no rule; only "we have only finished three Cycles").
- D: "I just received another one million dollars in funding from search Trader [SurgeTrader?] now managing 2.4 million US dollars in total".

## 14. 20230529_How_I_Got_Funded__1_Million__Full_Breakdown_ (KEY: valuation reference = GOLD for CHF; COT green+white levels, weekly; USDCHF trade)
- D: SurgeTrader $1M audition passed; "now managing a total of 2.4 million US dollar in proper [prop] funds"; "four days later ... up by seven thousand dollars"; "I took 14 trades to pass the one million dollar audition".
- D risk (EXPLICIT, depends on max-DD): SurgeTrader "five percent daily drawdown limit and six percent max trading [drawdown]" + 10% target -> "having a six percent drawdown limit I recommend only one percent risk for trade" vs 2% with FTMO's 10% max DD.
- EXPLICIT: analyse futures (6S = CHF/USD, inverse of USDCHF) because "the campus smart money index ... is basically using Futures data".
- A SEASONAL/ALGO READING: 6S as of 2023-05-02: "our campus algo forecast is still anticipating a strong move down ... roughly until the 16th of May ... another two weeks 14 days of downside potential ... according to our Dynamic forecasting tool" => bearish CHF / bullish USDCHF.
- A VALUATION (EXPLICIT reference choice): "using gold in the valuation model to compare it with the Swiss franc ... every time we are getting overvalued here on that daily chart ... everything above that red horizontal line means strongly overvalued versus gold". => for CHF futures the comparison market is GOLD (GC); daily chart; overvalued = above a red horizontal threshold line.
  - READING: 6S (CHF) daily, 2023-05-02: "now we are again overvalued" vs gold -> bearish CHF.
- A COT (EXPLICIT display detail): "the Red Line This is the retail money ... every time they're above the ... green horizontal line they're getting [bullish] and even up to that white horizontal line if they are touching that white horizontal line they're extremely bullish super super bullish and we know they are wrong most of the times so you want to do the opposite"; "this is a weekly chart". => at least two upper levels: green (bullish/extreme zone start) and white (most extreme), i.e. graded thresholds; read on the WEEKLY chart; here the RETAIL (small speculator) line is the signal, faded. Past examples: retail super bullish -> "big drop", "it took some time ... no tool in the world ... is always 100 accurate".
  - READING: 6S COT ~2023-05-02: retail "super bullish" (at the white line) -> bearish CHF.
- A COMBINATION: all three aligned = "All Stars aligned trade setup"; "I have already two of our three tools telling me become bearish" before checking COT.
- B entry: USDCHF (spot FX) DAILY demand: "here's no demands only on the daily chart I go all the way to the left and look what I found here super nice ... fresh demand Zone"; set-and-forget limit ("waiting for price to come down here"); entry ~2023-05-03. Called "anticipatory Trend reversal trade" ("it's not necessarily always about following the trend").
- B: step 2 = "supply and demand analysis combined with a little bit of conventional price action" (vague).

## 15. 20230601_He_Runs_a_Hotel_and_Trades_FTMO___Here_s_How_He_Does_Both (podcast with OTC student "Jan"; KEY: refinement rule "stop never changes", Globex trap, valuation refs silver->gold)
Speaker attribution matters: most rules here are the STUDENT's (Jan), endorsed by Bernd ("perfect"). Bernd's own statements marked (Bernd).
- A tool list (Bernd): "we have three of them right we have the the smart money index we have the [campus] algo forecasts and we have the evaluation [valuation] tool right we have some more but let's stick to those three". Also (Bernd): "depending on the market some of them are more ... important on a certain Market than others" (vague: no per-market weighting given).
- A VALUATION references (student): Dow: "the valuation uh where I'm comparing to interest rates [bonds]"; "if I'm looking at uh silver I'm comparing it to Gold if I'm looking at um equities is obviously the valuation [vs bonds]". => silver vs GOLD; equities vs bonds.
- A COT use (student): smart money matters most for "the metals uh the energies"; "follow the smart money ... and trade against the retail ... that's a hundred percent uh Rule"; "sometimes even just you don't see an extreme in ... the smart money but you've seen extreme in the dumb money the retail money and you can just trade against them". => a retail-only extreme can be enough (consistent with file 14).
- A combination (student's own checklist): "about five uh fundamental rules as long as four are aligned I'm usually happy" (student-specific; 4 of 5).
- B top-down (student): "I start with my monthly ... then I go into my weekly and then I go into my daily"; "you're undervalued and you're already at the ... weekly low Zone and you're undervalued then you're gonna look for an entry on a daily".
- B zone size / refinement (student + Bernd, KEY): "if I find a small Zone on weekly it's not too big I will just trade the weekly zone ... if it's too big I will always look for a daily"; "the daily is a bit big I want to reduce it ... [to] a 240 even 60 minutes ... especially if the risk reward one to two to the next ... Zone higher up is not enough then I will definitely reduce my zone if I can but my stop loss that never changes". Bernd: "the stop loss can never vary right this is fixed it's just the entry if you want to get a little bit in deeper to get more risk to reward ... or ... a little bit higher to ... increase the likelihood to be in that trade". => RULE: stop stays at the HTF zone's distal line; a LTF zone inside it only moves the ENTRY.
- B minimum R:R (student, endorsed): "I will not trade if there's not a possibility of getting a one to two risk to reward ratio" (to the next opposing zone). Student best = 1:4; win rate "not more than 40 accurate".
- B "level on level" (student): "if I have a Zone on Zone I always take the second Zone that's just my technical rule ... I call this level on top of level" (vague which is "second"; likely the deeper/older one).
- B price action veto (student): watch for "a hammer candle" etc. that would invalidate before fill (vague).
- C GLOBEX TRAP day-trade (student's description; Bernd: "I definitely have to do a video about that"): "you have a Globex low before the U.S Market opens ... you have a Globex low and a Zone below that which is a previous U.S market [RTH session zone] ... if that zone is very close ... before the Market opens that is called a trap if it's high quality it's a high quality trap if the market then goes further down and you are already on an uptrend there is a high probability that it will go into that area most retail Traders will get stopped out ... and it will go up"; target: "my zone must always be a 1R and I will always take a 1R no matter what"; result "about two [R] in a week on Globex"; he checks "4 30 PM" Dubai, "U.S Market opens at 5 30 PM" (= 09:30 ET). INFERENCE as a rule: in an uptrend, a fresh demand zone built during the prior US RTH session that lies just below the overnight (Globex) low; limit buy at its proximal at/near the open, stop below distal, TP = 1R. Mirror for shorts. Taught by OTC mentor "Clemens".
- D student stats: FTMO challenge at 2% risk, win rate 50%, 21 trading days; verification 2% risk, win rate 30%, 10 trading days; "minus three [R] in one shot". Markets used to pass: Dow, NASDAQ, S&P 500, palladium, silver, oil.
- D (Bernd) risk on large accounts: "you will not take one or two percent risk right you will take 0.5 risk or so" on a $1M account.
- News (student): failed first challenge partly from "trading during an fomc meeting".
- (Bernd) pipeline: "the optimizer ... it's like Siri or it's like Alexa for trading"; tools are "not sharing them publicly or ... on a subscription base".

## 16. 20230610_Passing_the_Challenge_Is_Easy._Verification_Is_Where_You_Fail_ (podcast with student "Lars"; mostly mindset; big/small-brother TF pairs; verification risk)
- No COT/valuation/seasonality numbers in this file.
- Campus terminology (Bernd): "weekly income" = swing trading, "daily income" = day trading. Bernd: "day trading is not a reasonable and realistic goal ... start with swing trading ... if swing trading is not working out for you then day trading is also not working out for you".
- B BIG BROTHER TF PAIRS (student, Bernd explains term): "is it covered by weekly and then I find the entry on The Daily or is my big brother that isn't [is the] covered by the daily and then I find my entry on the 120 minute". => pairs used: weekly zone -> daily entry; daily zone -> 120-min entry. Execution TF "60 minutes and daily I don't go lower than 60 Minutes" (rarely 15-min).
- C GLOBEX TRAPS again (student): watches US cash open "3 30" Spain time (= 09:30 ET); "daily income" trades are more often 1:1 ("my risk to reward ... is dropping because I take more one-to-ones").
- D student: challenge at 2% risk passed in 15 days; verification failed by keeping 2%; lesson: "go from two percent which I also think is best for the challenge go down to one" in verification.
- D (Bernd): "now I'm trading 2.4 million right now as we speak right just prop money"; full-time trader since at least 2017 ("back then in 2017 obviously I was already full-time Trader ... free weekly Outlook"); campus launched 2019.
- Routine (Bernd): "the one hour a day mindset ... really boil it down to what we would actually need it's like 15 minutes 30 minutes a day".
- Management (Bernd): shares targets and trade-management plan with a colleague for accountability: "I tell him basically where I put my targets and where I want to get out of the trade and how I'm planning to do my trade management" (no rules given). "never change a running system".

## 17. 20230614_Why_Your__1_000_Account_Will_Never_Make_You_Rich (prop-firm promo; no method)
- No indicator or S&D content.
- D: "I signed yet another one million dollar prop trading account with Samuel the co-founder of vision star trades" (VisionStar Trades, ~2023-06).
- Claims only: prop firms keep "at least 80 percent of the profits"; "transformed your 500 investment into 100K trading account".

## 18. 20230621_What_It_s_Like_To_Be_The__1_Funded_Trader (VisionStar signing; little method)
- No indicator or S&D mechanics.
- D: "it took me only four months to climb up the ranks ... to be the number one trade[r] on the global leaderboard for November December and January" (FTMO); VisionStar: "in a less than four months I was once again their top performing Trader" ($1M account).
- Universe/one-rulebook (EXPLICIT): "for every product that I trade I apply the same set of rules it's really important that's why I can trade everything"; wants "stocks ... the equity indices all the Commodities ... natural gas copper".
- Scalping with big capital = "myth" (Bernd + prop CEO).

## 19. 20230627_The_Day_Trading_Strategy_I_Use_Every_Morning_at_the_Open (KEY: "Globex breakout trap" full rule set)
(Machine re-translation with punctuation; "Cloex/Clobex/Clovex/GlobeEx" = Globex; "offer/bid zone" = supply zone; "deal" = trade. The opening clip "I work about 2 hours a week on Globex ... on the FTMO account" is re-used from student Jan's podcast (file 15) where it was "two R's in a week".)
- Markets (EXPLICIT): "applicable to all US stock indices: Dow Jones, S&P 500, NASDAQ and Russell. You can use futures or CFDs"; "This applies to ES, NQ, RTY, YM and their CFDs"; "this is a game mainly for stock indices".
- Sessions (EXPLICIT, ET): Globex/ETH "from 6:00 PM to 9:30 AM Eastern Time"; RTH "At 09:30 AM ... lasting until 17:15 Eastern Time" (sic; CME index futures RTH actually ends 16:15 ET - his number). "please make sure that your chart settings also match the exchange time".
- C RULES (EXPLICIT 7 steps): "Step one: Check the GlobeEx opening time ... 6:00 PM ... Step Two: ... Clobex close ... 9:30 a.m. ... Step Three: Identify the highest price reached during extended trading hours as the Clobex high. Step Four: ... lowest price ... Clobex low. Step five: look for supply zones above the Clobex maximum ... If there are no high-quality zones, we will not enter ... Step Six: Identify demand zones below the Clobex minimum ... Step Seven: Prepare for trades ... by setting stop orders, entry, target, and position size."
- C ZONE TIME WINDOW (EXPLICIT): "Identify any [supply] zones above the GlobeEx maximum that are ideally located within your 8:00 AM to 11:00 AM time window of opportunity. Your quality zone on the lower timeframe should be in your window of opportunity"; summary: "Which zone is ideal? This is a zone outside the Globex high and low and created between 8:00 and 11:00 AM ... And which zone is bad? This is the zone between the maximum and minimum." Examples: "look to the left, you see a dedicated [supply] area that was created in our window of opportunity from 8:00 AM to 11:00 AM".
- C TRIGGER/ACTION (EXPLICIT): bear trap: "Step one ... trigger. The price breaks through the minimum Clobex [Globex low] ... The trap condition is when they sell at a demand level below the Globex minimum ... We will buy ... directly in the demand zone, which is located in our time window of opportunity." Bull trap = mirror (break above Globex high into a supply zone above it -> short). Breakout must happen after the RTH open ("Once the regular trading session starts again at 9:30 AM ... when the price breaks through the Globex low").
- C FILTERS (vague, EXPLICIT that they matter): failed example explained by "was it at a low point? ... a high point? ... equilibrium ... Was this a quality supply area? What was the trend?"; "Am I at a high or very high point? If so, the chances ... are much higher" (location in HTF curve + trend + zone quality; no numbers).
- GAPS: zone timeframe ("lower timeframe" unspecified), whether the 8-11 window refers to the prior day's or same day's zones (examples are "to the left", formed before the trade), stop buffer, TARGET not stated here (student in file 15: always 1R), time stop/EOD exit not stated.
- D claim: "the same day trading strategy that helps me manage $2.4 million in prop firm capital".

## 20. 20230705_How_A_7-Figure_Prop_Trader_Actually_Thinks (mindset; little method)
- No indicator content.
- D: "trading full-time for 10 years now I manage 2.4 million dollars [prop] capital".
- B (vague): KPI-improving habits include "holding trades for a longer period of time and placing stops at a safe distance" (no distance rule).
- Style: "adding swing trading as this is how most successful Traders consistently make profits ... there are not enough high probability trading opportunities every day" for scalping.
- Risk: "keep your position size at a dollar amount that you're willing to potentially lose per trade".

## 21. 20230712_They_Passed_The_Challenge___Then_Failed_The_Easy_Part (prop-phase risk recipe)
- No indicator content.
- D/B PROP RECIPE (EXPLICIT summary): "two percent risk in the challenge phase [with] one-to-one risk to reward ratio and one percent in the verification stage with also one-to-one risk to re[ward] ratio". Lars "employed a strategy of using a two percent risk and a one-to-one risk to reward ratio for every trade ... he could pass the challenge after winning only five trades" (passed "in less than 25 days").
- Realism: another student "losing eight percent during the verification".
- D: "I managed 2.4 million dollars in [prop] funds and also Mentor hundreds of students globally".

## 22. 20230719_He_Was_Hopeless._Now_He_s_a_Certified_FTMO_Trader. (podcast with student "Nada"; stock-vs-index rule; valuation = main driver for stocks)
(Student statements unless marked Bernd.)
- A tools as confirmation layers (student): "comes the indicators and then three layers three additional layers of validation that could probably bring this up to 90 to 95 percent probability" (student's unrealistic claim; shows tools used as filters on S&D setups). Tools introduced to campus ~2022 ("I came back at an exciting time ... with the introduction of the proprietary indicators").
- C/A STOCK RULE (student, consistent with Bernd file 04): NVDA long: "I made sure that the indices are in a demand Zone ... because of the cross-asset correlation"; "the most important Drive was the evaluation [valuation] tool ... for the stocks"; "making sure that I'm engaging in a demand area making sure that the indices are in demand and making sure that the stock was undervalued"; result "three to one".
- B entries (student): "around 80 [%] of my [trades] are ... pre-planned ... limit orders" + some "price action" confirmation entries; refines daily/weekly zones to improve R:R ("I would still refine it in a way to capitalize on the risk to reward").
- D student prop stats: challenge "three percent risk ... one-to-one", never below 240-min, 25-26 working days; verification "one and a half percent", some "two to one or three to one", ~30 days. Markets: crude oil, natural gas, palladium, platinum, NVDA.
- D (Bernd): scaling psychology - "if you trade now a 200k account with one percent risk per trade this is 2K risk per trade"; mentions upcoming "campus fund".
- Fixed $ risk emphasised (student: "setting the fixed risk").

## 23. 20230727_Stop_Trading_For_Money__Do_This_Instead_ (mindset; no method)
- No indicator content.
- D: "full-time Trader with 10 years [experience] and manage 3.4 million dollars of [prop] Capital" (2023-07; up from 2.4M after the VisionStar $1M).
- B management (vague): "most Pros let the trade play out without interference ... sure there might be instances when exiting early is wise".

## 24. 20230803_Why_I_Refuse_To_Use_Trade_Copiers__And_What_I_Do_Instead_ (execution workflow; trade frequency)
(Machine re-translation: "warrant/deferred" = pending order, "equity firms" = prop firms.)
- D frequency (EXPLICIT): "I only make 10 to 15 trades a month. So I can easily copy these transactions manually between my accounts"; "$2.4 million in [prop] capital across three different [prop] firms".
- B entry type (EXPLICIT): pending limit at the zone, set-and-forget: "you've found a good set-it-and-forget-it swing trade setup for gold XAUUSD. Let's look at the demand zone ... Entry at 1925, stop loss at 1890 [later 1889] ... This is not an instant order ... We are waiting for the price to come to us ... a buy limit". (Illustrative; zone height ~35-36 USD on gold; no stop buffer rule stated.)
- D risk choices shown: "1% risk", "0.5% risk", "this might be a challenge, so I'm a little more aggressive and take a 2% risk"; for a personal account "take a 5% risk, because this is your real account" (probably a translation error for 0.5%; unclear).
- Tool: MT5 "Position Sizer" EA (earnforex) for sizing across accounts; charts/analysis in TradingView.

## 25. 20230810_How_I_Trade_Full-Time_From_Koh_Samui (vlog; one live-session clip with a trailing-target remark)
- No indicator content.
- B STOP + TRAILING (EXPLICIT, short live-session clip on the Dow): "we place our entry our stop loss below the demand Zone and I would recommend not having a Target we can Trail a Target because um if we make new highs then we have a risk to reward proposition there at least 4 five or even 6 [to] 1 ... you can place this trade on all the other Equity indices as well". => stop just below the demand zone (buffer size not given); for this trend trade NO fixed target, trail instead (trail method not given = vague). Date of the clip ~July 2023 (vlog filmed in July).
- Routine: wakes 06:00-06:30 local, "I check the charts ... I do my analysis for the day" ~2h incl. admin + live session; Koh Samui: "US Stock Market opens at 8:30 p.m. and it closes 3:30 a.m.".
- D: "$2.4 million" (repeated by his daughter); "two screens are more than enough".

## 26. 20230819_Trading_Goals_Are_Killing_Your_Profits (mindset; no method)
- No indicator or S&D content. Only: "$2.4 million of [prop] Capital"; focus on "trading strategy and weekly routine" over goals.

## 27. 20230828_How_Institutions_Actually_Buy_Any_Market__Supply___Demand_Lesson_1_ (S&D concept only)
- No mechanical rules; conceptual (content mirrors classic OTC/Sam Seiden lesson: IBM/Buffett 2011 case).
- Concept: "on a volume basis 90 plus% is traded by institutions"; institutions cannot fill at once ("he will scale in a little at a time") -> leave "footprints" = zones; "if institutions are buying you better be ... buying".
- Example numbers (illustrative): Buffett bought "$10.7 billion" IBM from March 2011, "67 million shares" vs "average daily volume ... roughly 6 million shares per day".
- "I rely on my two-step mechanical process" (step 1 bias tools, step 2 S&D timing).

## 28. 20230905_Michael_Burry_Bet_On_A_Crash._I_Stayed_Long. (KEY: presidential/election 4-year cycle; pre-election Q4 seasonal with numbers)
- C 4-YEAR CYCLE (EXPLICIT): "the four-year cycle also known as the election cycle is one of the most vital Cycles on the U.S stock market ... it's all about the year of the presidency".
- C NUMBERS (EXPLICIT): "in the past 123 years between 1900 and 2022 the Dow Jones recorded ... average gains during the pre-election years ... 9.03 percent ... post-election years trail behind with only 4.7 percent and midterm election years ... point six six percent" (election-year figure not given).
- C CYCLE-SEASONAL METHOD (EXPLICIT): "I've analyzed the average course of the 12 years leading up to every U.S presidential election [= the last 12 pre-election years] ... it's like a seasonal chart with a Twist ... only every fourth year is considered". => average intra-year path of the last 12 pre-election years (1975...2019). (Note: here the seasonal is built from 12 cycle-years, not 15 consecutive years.)
- C PATTERN (EXPLICIT): "Sensational gains in the first half of the year ... the second half of the year brings a decline ... until mid end of October ... the third week of October the sweet spot for buying stocks and Equity indices ... when the legendary year end r[all]y begins".
- C TESTABLE CLAIM (EXPLICIT): "over the past 12 pre-election years my predictions have been accurate at ... 91.67 [%] of the time ... just one single negative fourth quarter in 2007" (= 11/12); "the average gain from October 19th until the year end for the Dow Jones in pre-election years stands ... at ... 4.95 [%]".
  - HYPOTHESIS: long DJIA from Oct 19 (or next session) to last session of Dec in years with (year mod 4 == 3); last 12 such years (1975-2019) -> 11/12 positive, mean +4.95%.
- READING/plan: "2023 is a pre-election year ... I will be long [in] equity [indic]es and some stocks from around Middle October" (2023).
- Claims to have predicted the 2023 rally in "December 2022"; campus publishes a yearly "stock market roadmap". Also: "ranked the number one trade[r] on [VisionStar?] ... this month".

## 29. 20230911_I_Recorded_Every_Single_Day_Of_My_Prop_Firm_Challenge (intro to his own FundedNext 200k challenge series)
- No indicator or S&D mechanics.
- D setup of the documented challenge: FundedNext "two-step Stellar challenge ... 200 000 dollars"; "maximum daily loss is five percent and the maximum overall loss is 10 percent"; "phase one target ... eight percent"; balance-based drawdown; "no time limit"; "minimum trading days five ... I just fill them ... with micro lot trades".
- Style: "I prefer swing trading so weekend holding is ... important".

## 30. 20230918_Find_Institutional_Zones_On_Any_Chart__Supply___Demand_Lesson_2_ (S&D basics: "origin" = base before a strong move)
- B ZONE DEFINITION (EXPLICIT but qualitative): sideways/balanced price ("it's in a Range ... we cannot identify institutional activity at this stage") followed by a "big strong drop in price ... instead of stair stepping drop with small red candles" -> "we identified the origin we highlight the origin with the yellow box to visualize the area where price left with a very strong move we take this area of imbalance ... and draw two horizontal lines to the right". Demand = mirror ("big rise ... instead of stair stepping move with small green candles").
  - => zone = the range/base the strong move left from; proximal/distal = the two horizontal lines of that box (whether wicks or bodies define them: NOT stated - vague). No count of base candles, no numeric leg-out size. Leg-in not discussed here.
- B quality (EXPLICIT, qualitative): "generally the bigger the imbalance the higher the number of unfilled orders" (stronger leg-out = better).
- B entry (EXPLICIT): "when price comes back to that area we want to go short sell to enter we place our set and walk away" (limit order at the zone, set-and-forget).
- Theory: "price can only change when one force buyers or sellers ... becomes zero at a specific price"; "unfilled orders cause price to turn ... filled orders facilitate price movement". (Classic OTC wording.)

## 31. 20230926_I_Documented_Every_Trade_of_My__200K_Challenge___Week_1 (KEY: live diary 2023-08-14..20; COT "relative to previous behaviour"; valuation vs USD with exit rule; all-3-indices-in-demand rule; mini gap)
Dates: day 1 = Mon 2023-08-14 ("day two ... Tuesday the 15th of August"), day 3 = 2023-08-16 (FOMC minutes), day 5 recorded Sun 2023-08-20.
- D risk: "went for a three percent risk from the get-go" (FundedNext 200k phase 1; target 8%, max DD 10%).
- B management rules (EXPLICIT): "don't move your stop-loss don't manually exit in the red even if it meant a bigger loss".
- PLATINUM swing long (he says "Platinum"; caption "xpd" = palladium ticker - metal uncertain, he says platinum throughout):
  - B zone (EXPLICIT): "a trade that is covered by weekly demand and daily demand" (big brother weekly + daily). On this account entered AT MARKET inside the zone ("entered here Market because price was Meandering within that zone"); on other accounts entered "beginning of last week" (~2023-08-07). Stop/targets "pre-planned" and identical across accounts. "it's a swing trade so the zone is obviously a little bit bigger".
  - A COT (EXPLICIT, KEY for normalisation): "the blue line is a smart money smart money is very bullish ... It's always important to look at smart money in relation to their previous Behavior ... every time there were that bullish compared to their previous Behavior like now We [r]allied"; weekly chart; COVID lows = "super bullish compared to their previous Behavior". => the COT reading is RELATIVE to the group's own history (index/percentile over a lookback), not absolute net. READINGS: platinum COT (commercials) 2023-08-15 "very bullish"; 2023-08-20 "even more bullish now than we were back in February March [2023]".
  - A role (EXPLICIT): "this is not a timing tool ... it's more like to get a bias"; "even if it doesn't work I will have on my watch list and I will buy the next uh daily demand Zone because ... I'm so bullish on that ... smart money behavior".
  - A VALUATION (EXPLICIT, reference = US DOLLAR; EXIT RULE): "fundamentally so we are coming from being undervalued the purple line is the US dollar which is important so you see once we're overvalued we see price dropping"; "when it comes to Target setting here I clearly wait for price to be overvalued versus the dollar here on Platinum ... once prices overvalued I exit the trade". => tool plots one line per reference market (purple = USD); for platinum USD is the key reference; overvalued vs USD = exit/target. READING: platinum ~2023-08-20 coming up from undervalued vs USD.
  - C MINI GAP (first mention, undefined): 2023-08-17 platinum daily "we had that mini Gap ... we had that mini Gap filled right that was supposed to happen" => he expects mini gaps to get filled (definition not given in this file).
  - B price-action context (vague): daily "Supply ... plus [parallel] channel plus downtrend" overhead; hoped for "daily bullish engulfing"; weekly "pin bar a reversal candle" read as confirmation; channel breakout. Targets "only here" at prior highs, beyond a supply "that has been tested once".
  - Result in week 1: -2.5% at worst (2023-08-15/16), back to -0.5% by 2023-08-20 ("because of the heavy swap"; CFD swap cost).
- B INDEX SYNC RULE (EXPLICIT): "what I want is to enter the equity indices so all of them NASDAQ Dow Jones and s p to be all in demand so all of them to be sync ... since only the s p is in demand and the Dao and the NASDAQ not yet based on my rules I'm not allowed to go along". NASDAQ zone = "high quality weekly demand". 2023-08-17: "S P 500 ... daily chart ... in demand ... NASDAQ ... Weekly demand ... Dao is also on demand all of them in demand" -> waiting for deeper "high quality" S&P level.
- C Globex trap used as swing entry: "on the S P anyway I want to trade the clobex Trap long ... I want to trade not the first one here I want to trade combined ... as a swing trade these two levels".
- News (EXPLICIT habit): "when we have some volatile news I always look ... for lower time frame revers[als]" (60-min) - observation only, no entry.

## 32. 20230930_Why_I_Risked_6__on_ONE_Direction____200K_Challenge__Week_2_ (KEY: valuation = 3 coloured lines DXY/GC/ZB with green/red thresholds; "undervalued vs all three"; COT 3rd (orange) line ignored; tools run on TradeStation; 6% correlated risk)
Dates: day 6 = Mon 2023-08-21 (gold entry), reviews 08-22, 08-23, 08-24, 08-25 (Powell/Jackson Hole), day 10 recorded Sun 2023-08-27.
- D RISK (EXPLICIT, contradicts his own correlated-risk advice in files 07/09): gold "also 3% risk exposure" while long platinum at 3%: "I was long on Platinum and gold at the same time that's 6% of risk moving in the same direction".
- A VALUATION GOLD (EXPLICIT; reference = USD; threshold lines): "I only want to show the valuation versus the dollar ... we want to enter gold once gold is undervalued versus the dollar"; "if we are close to the green horizontal line which means undervalued if we close to that red horizontal line we're overvalued versus dollar" (daily chart). Uses it for counter-trend corrections too ("in this downtrend we got this nice move to the upside").
  - READING: gold vs USD 2023-08-21/22: "now we are very close not yet fully undervalued but close to undervalued" -> still counted as bullish ("valuation perfect").
- A COT GOLD (EXPLICIT; weekly; three lines): "we have the green horizontal line here and the red horizontal line here now let me remove the Orange Line because the Orange is not important ... the Blue Line represents the smart money the red line represents the retail Traders"; "if the blue line is all the way up here ... they are bullish ... if the red line is down here ... they are bearish so we want obviously the retailers to be bearish". => tool plots 3 groups; ORANGE (INFERENCE: large speculators / non-commercials) is ignored. "smart money index also very important especially trading Commodities here gold silver". Signal horizon: "it's a swing trade so we just need one or two weekly green candles"; "nothing is 100%"; sometimes "the retailers were actually right".
  - READING: gold COT 2023-08-23: smart money "getting very bullish again and the retailers are close to very bearish ... close to the perfect scenario because the retailers are not fully bearish yet".
- A ALGO/SEASONAL FORECAST GOLD (EXPLICIT): "our campus algo forecasting tool which can predict the future ... not necessarily price but the movement of price ... I can stretch this up and down so it doesn't predict the price points but more like the time when we can see highs or lows". READING 2023-08-24: "we still anticipate a move higher ... we might hit a top around after the first week of September ... and then we can anticipate a drop".
- A COMBINATION: "three out of three indicators they screamed bullish so I went bullish and I timed the market".
- A PLATFORM (EXPLICIT): "trade station charts ... our indicators right they run on trade station".
- A VALUATION EQUITY INDICES (EXPLICIT, KEY): "for the equity indices the valuation tool is the most important tool for me and every time we undervalued versus the treasury bonds this is a big big Buy Signal and if we undervalued versus all three assets treasury bonds gold and dollar then this is like almost a self-fulfilling prophecy"; "purple is the dollar yellow is gold blue are the treasury bonds"; "once we are undervalued versus all three assets it can be almost used as a timing tool". => confirms the 3 reference markets DXY, GC, ZB, one line each; signal strength = number of references in agreement; for indices ZB is primary.
  - READING: Dow (YM/US30) ~2023-08-25: "now look at again here under valued versus all of these three assets" -> long.
- A VALUATION AS EXIT/TRAIL (EXPLICIT): platinum "valuation tool again purple this is the US dollar so we have to get out either once price hits the target ideally right or once price gets overvalued versus the dollar ... this is one of the tools that I use also to Trail or to know when to exit the market". READING: platinum vs USD 2023-08-25 "around the mean".
- B ZONE QUALITY (EXPLICIT): "stair stepping is never good why because stair stepping um is retail behavior and we need some institutional Behavior institutional Behavior would be something explosive something decisive"; new zones formed in the move = "obstacles ... demand zones on the way up which is protection for our position". Platinum daily: "classical ... bottom reversal drop base rally followed by r[ally] base rally a level on top of level".
- B ENTRY US30: "daily demand ... drop base rally" set-and-forget limit, filled 2023-08-25 (shown on 4-hour chart: "sniper entry"); stop below zone; target set "because of our fundamentals our valuation tool" (exact target rule not given).
- B MANAGEMENT (EXPLICIT, discretionary): closed gold + platinum on 2023-08-25 (+"a little bit more than 10 K" = ~+5% on 200k) BEFORE their targets so the US30 target would complete the 8% phase target ("we have to do this a little bit strategically"). => challenge-driven discretionary exits; not a mechanical rule.
- Platinum also tracked on a "120 Minutes ... chart ... Channel formation".
