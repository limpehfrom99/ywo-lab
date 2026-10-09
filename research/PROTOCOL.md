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

