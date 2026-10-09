# Nightly research loop — scheduled-task prompt

Schedule: every day 00:25 Asia/Kuala_Lumpur (cloud session, no laptop needed). Push notification on.
Paste the block below as the task prompt (claude.ai → scheduled tasks), or ask Claude to create it
and approve the request.

---
You are running Shen's nightly trading-research loop (project "Your way out"). Shen is asleep: do not ask questions; take the most reasonable reading of anything unclear and note it in the log.

Setup (every run starts fresh):
1. Call add_repo with owner "limpehfrom99", repo "ywo-lab", access "push". Then: git clone --depth 1 https://github.com/limpehfrom99/ywo-lab /home/claude/ywo-lab (use a 10-minute timeout). If the clone already exists and `git -C /home/claude/ywo-lab rev-parse HEAD` works, use it.
2. cd /home/claude/ywo-lab && pip install -q pandas numpy pyarrow --break-system-packages && python3 bt/bootstrap.py
3. Read research/PROTOCOL.md, research/backlog.md, quant/README.md and the "results" section of research/log.md.
   If data/x exists (the full ~110-symbol FTMO export), the [needs export] items can run; otherwise skip them.

Work (aim for 60-90 minutes of compute in total, then stop):
4. Take the first [queued] idea in research/backlog.md. Write its exact rule down in the log BEFORE running it. Test it per PROTOCOL.md: FTMO costs on every trade, a baseline it must beat (coin flip at the same moments / fake levels / always-on), n, avg R after costs, t-stat, win rate, early/late halves, per-year table, worst year. Verdict: CANDIDATE / WATCH / DEAD, with the one thing that would change the verdict. Long runs: nohup + a log file, poll with sleep.
5. Append the result block to research/log.md, mark the idea [done] in research/backlog.md, and if the idea came from an online source add the link. If a test needs data that is not in the repo, mark the idea [blocked] with what is missing and move on.
6. Repeat steps 4-5 while time allows (2-3 ideas is a good night). If the backlog has fewer than 3 queued ideas, spend 15 minutes on WebSearch for concrete, mechanical intraday or swing rules on gold, NASDAQ/S&P CFDs or large US stocks (queries like "gold intraday strategy backtest edge", "nasdaq intraday seasonality anomaly", "index futures intraday anomalies study") and add them to the backlog with sources.
7. Commit and push after every idea: git add -A && git commit -m "research: <idea> <verdict>" && git push. Set git user.name "cs" and user.email "limpehfrom99@gmail.com" first.
8. Update the Project doc claude/research-log.md with the Projects tool (project_read it, add one short block per idea under "Results so far" — idea, exact rule, key numbers, verdict — and refresh the "Queue" line; project_write the full content back). Keep it readable from a phone: short lines, numbers that matter.

Rules: never tune parameters on the test data (if a grid is needed, test a small fixed grid and report every cell); never delete or rewrite earlier log entries; never touch the live EA, the FTMO account or anything outside this repo and /home/claude. Reddit is blocked for this account: do not try to reach it by any route. Finish with a 3-5 line summary: one line per idea with verdict and key numbers, and what is next in the queue.
---
