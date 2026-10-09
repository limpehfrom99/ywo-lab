# Research protocol (overnight loop) — Your way out

Goal: find a mechanical, automatable edge that passes FTMO (or any reputable firm allowing EAs)
or earns monthly income. One edge is live: opening candle on TSLA/US100 (+0.10R/trade). Everything
here is tested the same way so results are comparable and honest.

## Rules of a test
1. Write the rule down BEFORE running it (entry, stop, target, exit time, filters). No tuning on the
   test data; if a parameter must be chosen, test a small fixed grid and report ALL cells.
2. Costs every trade: spread (gold SPREAD_BY_YEAR in bt/gold_m1.py; FTMO exports carry 'sp'),
   commission (gold 0.0007%/side, TSLA 0.002%/deal, US100/US500 none). Swap when holding overnight.
3. Baselines: coin flip at the same moments (random_dir), fake levels (shifted +0.37 ATR), or
   always-on/no-trigger version. The idea must beat its baseline, not just zero.
4. Report: n, avg R after costs, t-stat, win rate, early/late halves, per-year table, worst year,
   'last 60' trades. CANDIDATE = n>=200, both halves > 0, t>=2, avg >= +0.05R after costs,
   no year below -0.3R. Anything else = dead or watch (watch = positive but n too small / t<2).
5. Time limits: one idea <= ~45 min of compute; run long jobs with nohup + log file, poll.
6. Log every result, dead or alive, in research/log.md AND the Project doc claude/research-log.md
   (Projects tool: project_read, then project_write the full updated content). One block per idea:
   idea, source, exact rule, data, numbers, verdict, what would change the verdict.

## Data (all UTC index)
- gold M1 2012-2026: /home/claude/data/gold_m1_utc.pkl (open high low close vol sp). Built by
  bt/gold_m1.py load() from /home/claude/data/mt4/m5frommt4.csv (MT4 export; file is 1-minute).
- gold M5 + TSLA/AAPL/US100/US500 M5 2021-2026: /home/claude/data/{sym}_m5.pkl via bt/smc_data.py
  (adds nyd, nym, wd, atr; attrs comm). FTMO exports in /home/claude/data/assets/*.csv
  (server time = New York + 7h). BTC M30 2020-2026 and *_M30 (2015/2017-2026) in the same folder.
- News: /home/claude/news/news_usd.csv (server time = UTC + 3h); lab/news.py load_calendar, fed_days.
- Engines: bt/sr_diag.py (levels + touch/confirm/stop/target simulator, random_dir, be_r,
  stop_atr_k), bt/period_levels.py, bt/smc.py (pivots, killzones, SMC), bt/ict.py, bt/regimes.py,
  bt/strategies_gold.py (opening_candle, vwap_fade), lab/lab.py (opening_candle, stats, split_stats),
  lab/ftmo_sim.py (daily_returns, challenge, funded, scenarios).

## Rebuild after a container reset (if /home/claude is empty)
1. mkdir -p /home/claude/data/mt4 /home/claude/data/assets /home/claude/news /home/claude/lab /home/claude/bt
2. unzip /mnt/user-data/uploads/m5frommt4.zip -d /home/claude/data/mt4;
   unzip /mnt/user-data/uploads/multiple_assets.zip -d /home/claude/data/assets;
   unzip /mnt/user-data/uploads/news_usd.zip -d /home/claude/news
3. cp /mnt/skills/plugins/ftmo-strategy-lab/scripts/*.py /home/claude/lab/
4. Re-create bt/gold_m1.py, bt/smc_data.py (short; see log.md 'code' section) and run them to
   rebuild the pickles. If the uploads are gone too, stop and leave a note for Shen in the Project doc.

## Loop mechanics
- Backlog: research/backlog.md (status: queued / running / done / blocked). Take the first queued.
- After each idea: append to log.md, update the Project doc, mark done, then schedule the next
  wake-up with mcp__claude-code-remote__send_later (delay 45-60 min) carrying the same loop message.
- Stop condition: local time (Asia/Kuala_Lumpur) >= 09:00, or Shen has written in the chat.
  Then write "Morning summary" at the top of the Project doc and stop scheduling.
- Shen is asleep: never ask questions; take the most reasonable reading and note it in the log.

## Repo (added 2026-10-09 03:10 MYT)
The lab lives at https://github.com/limpehfrom99/ywo-lab (private). After logging an idea, also:
  cd /home/claude/ywo-lab && cp /home/claude/research/*.md research/ && cp /home/claude/bt/*.py bt/ \
  && cp /home/claude/bt/*.csv results/ 2>/dev/null; git add -A && git commit -qm "research: <idea> <verdict>" && git push -q
If /home/claude/ywo-lab does not exist: git clone --depth 1 https://github.com/limpehfrom99/ywo-lab /home/claude/ywo-lab
(then python3 bt/bootstrap.py rebuilds /home/claude/data if it is missing — faster than the uploads route).

## Full export + cross-market battery (added 2026-10-09 16:20 MYT)
Shen exports every market with tools/export (Export-History.bat): ~110 symbols, M5 (FX M15) + D1 from 2015, compact
.npz files (lab/ftmo_data.py load_any reads them), plus symbol_specs.csv (real swaps) — uploaded as exports_partN.zip.
Then: python3 -I quant/ingest.py <zips> -> /home/claude/data/x, and the steps in quant/README.md.
Fill traps found while building it (all handled in quant/intraday.py):
- Opening-range breakout: skipping days where one bar breaks BOTH sides of the range inflated ORB30 by ~+0.08R/trade on
  30-min bars (dry run: 4 fake "survivors"). Count such bars as a stopped trade.
- Long-only daily rules vs a coin flip look great on assets that went up; the daily baseline is the same direction and
  holding time from a random entry day.
- The repo copy of research/*.md is the source of truth (other chats push directly). Before copying /home/claude/research
  into the repo, pull first and copy the repo files back, or the loop overwrites newer results.

## Strategy videos (added 2026-10-09 20:50 MYT)
Shen can attach a downloaded video or a screen recording (RedNote, YouTube, Instagram). Links can't be opened: the
workspace can't reach those sites and the web tools only read page text. Run
  python3 tools/video/video_notes.py VIDEO OUT    (timestamped transcript + frame contact sheets; --frame SECONDS for one full frame)
Speech-to-text is offline: sherpa-onnx SenseVoice (zh/en/yue/ja/ko) + Silero VAD; setup() re-downloads the models from
GitHub releases into /home/claude/models after a container reset (pip install --break-system-packages sherpa-onnx).
Then write the rules down, confirm them with Shen (videos are usually partly discretionary), and test as usual.

## Candle clock and exit resolution (added 2026-10-09 22:54 MYT, research #39)
- FTMO's candles are cut on the server clock (00:00 server = 17:00 New York = 21:00/22:00 UTC). H1 and below are the same as
  UTC; H4 and D1 are not. Build H4 for anything an EA will trade with data_standard_check.h4_server(), and before calling a
  4-hour (or daily) rule a candidate, run it on all four hourly grid starts (bt/h4_phase_check.py pattern). #35 went from
  +0.13R to +0.02-0.13R depending only on the start hour (+0.06R on FTMO's clock).
- FTMO's MT5 gold feed and the MT4 feed differ by ~$0.06 per bar and give 82-92% the same SMC trades — feed choice is minor.
- Limit entries: exit on 1-minute bars. 15-minute exits flatter results by ~+0.05R because the fill bar's order is unknown.

## Video batches and coarse exits (added 2026-10-10 00:05 MYT)
- Every processed video is in research/videos/index.csv (sha1, length, author, title, log entry, verdict, frame hash) with its
  transcript in research/videos/transcripts/. For a batch: python3 -I tools/video/batch.py <zip or folder> <out dir> -> transcripts,
  contact sheets, exact/near duplicates (5-character-shingle overlap >= 60% of the shorter transcript; frame hashes for silent
  clips), topic tags, batch_report.md. Add the new videos to the index after testing them.
- When exits can only run on 15/30-minute bars (FTMO exports for forex/indices before the M1/M5 window), use the conservative fill
  rule in bt/fx_cross_check.exit_conservative: in the bar where a limit fills, the stop counts and the target doesn't; the coin flip
  (other side) skips the fill bar. On gold it reproduces the 1-minute results.
- Speed: np.searchsorted on datetime64 arrays with a key of another unit copies the whole array per call (minutes on 5M bars). Search
  int64 nanoseconds (values.astype("datetime64[ns]").view("i8")).


## Every rule on every market and timeframe (Shen's standing instruction, 10 Oct 2026)
Shen, verbatim: "make sure to always test and optimise across asset and across timeframe and across strategies, act as hedge fund
and quant, test out all different asset and timeframe eventhough if the strategy says 4h with 5min, test all since you have the data".
- Write each new rule as rule(S, ctx) -> list of Fill (LONG in its frame; the harness mirrors prices for the short side) in a
  bt/xrules_*.py module (bt/xrules.py, xrules_video.py, xrules_bernd.py are the patterns) and run it with bt/xrun.py on every asset
  and timeframe available: `python3 bt/xrun.py <rule-name prefix> --module <module>` (data in hand: gold M5-D1, 3 FX pairs, US100,
  US500, TSLA, AAPL, BTCUSD at M30-D1) and `--export` once data/x exists (every symbol in the FTMO export, one at a time).
- The source's own market/timeframe is the pre-registered primary cell. Every other cell is reported too, never dropped.
- Report the per-rule summary from xrun.py (cells, share of cells positive, pooled R and t, cells passing the CANDIDATE bar vs the
  ~2.5% expected by luck) plus pooled R by timeframe and by asset group. A rule that passes in 1-2 cells out of 38 is luck.
- Any H4 or D1 result: rerun with --h4-offset 1, 2, 3 (H4 candles started 1-3 hours after FTMO's) before it counts.
- Optimising = a small grid written down BEFORE running (e.g. 1.5/2/3R, break-even at 1R or not, timeframe), chosen on data before
  2024, checked on 2024-26 only, every cell reported. A cross-market basket (one rule, many symbols) beats a tuned single cell.
- Baselines: coin flip (same moment, other side, same distances) and, for limit orders at levels, a plain-level baseline (bt/xrules_bernd
  Z0: the same entry mechanics at levels with no quality test) — the coin is not fair for limit entries at levels.

## Same-bar look-ahead in limit entries (added 2026-10-10 01:15 MYT, log #57)
On the bar where a pending limit/stop order would fill, nothing from that bar (its high beyond the stop, its close beyond the level)
may decide whether the order exists. Check the fill FIRST; the bar's close can only cancel the order for LATER bars. Only the bar's
OPEN may cancel it on that bar (a pending order can be pulled at the open). #33's "ran through the high first: no trade" and #35's
"closed above the block: no trade" both dropped bars that filled and then lost — look-ahead that removes losers. When an exit series
is coarser than 1 minute, the harness counts the stop (not the target) inside the fill bar; the rule must not pre-filter those bars.

## Robustness checks (added 2026-10-10 01:40 MYT, log #60; bt/robust.py, pattern in bt/robust_check.py)
Every rule that clears rule 4's CANDIDATE bar, and every live rule after each new data export, also gets:
1. Selection-aware permutation test (robust.permute_bars + robust.mcpt_select): shuffle the rule's bars across days WITHIN their
   time-of-day slot (keeps the intraday volatility pattern, removes all order information) and re-run EVERY cell tried for the idea
   (all symbols x settings, the xrun.py grid included), >= 1,000 shuffles. Report p_alone, p_best (the honest p-value for a cell picked
   because it looked best) and skill = real - average best shuffled cell. Daily/swing rules: random entry days with the same holding
   periods. Direction-only tests: shuffle direction labels across days; the opposite trade keeps the SAME stop distance (never the
   candle's near end - tiny stops make the null meaningless).
2. CSCV probability of backtest overfitting (robust.cscv_pbo, 10 blocks) whenever an idea has >= 4 cells: report PBO and the in-sample
   winner's average out-of-sample result. A PBO near 100% with every cell positive means the settings are indistinguishable, not dead.
3. BCa 95% lower bound of mean R (robust.bca_bounds, 20,000 resamples).
4. Before risking money: drawdown bound at the planned risk (robust.drawdown_bound, 95th pct and 90% confidence; mode="start" for
   FTMO's static max loss) over 3 and 12 months.
CANDIDATE now also needs p_best <= 0.10 and a BCa lower bound > 0; p_alone <= 0.05 with p_best > 0.10 = WATCH. Size and quote pass
odds on skill (so far about half the backtest edge), not on the backtest average.
The C++ originals: bash tools/get_masters.sh (builds into /home/claude/vendor/bin); python3 tools/verify_masters.py re-checks
robust.py against them (CSCV must match exactly, BCa within bootstrap noise).

## FTMO export data checks (added 2026-10-10 03:35 MYT, log #61, #65, #67)
quant/universe.load fixes these on every load; re-check them on any new export before testing:
- Index and stock files before 2021-22 are one bar a day (or hourly bars) under an M1/M5 label: cut each file to where it is really
  intraday (bt/xgrid.full_intraday_start) and drop days with < 50% of the usual bars; the battery's session matrices drop them anyway.
- The second batch of stock CFDs (AMD, AVGO, BA, CVX, DIS, INTC, JNJ, JPM, KO, MSTR, NKE, PLTR, QCOM, XOM) is stamped 1 hour early until
  late Jan 2026 (universe.fix_stock_clock) and its pre-2026 bars are thin (little tick volume, flat bars): do not trust limit-order
  results that appear only on these symbols.
- Whole-day bars stamped 00:00 server sit inside the intraday history of metals 2015-20, crypto 2018-21 and forex 2019
  (universe.drop_daily_artifacts): any pending order "fills" on them.
- Stock CFDs open at 9:35 New York since 2024.
- Pooled harness statistics across groups: report them without crypto too (2018-21 coins give single trades of +100R with tiny stops).

