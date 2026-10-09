YWO price export - pulls years of bar history out of FTMO MT5 so Claude can test strategies on every market.
It only reads prices. It never places trades.

1. In FTMO MT5: Tools > Options > Charts > "Max bars in chart" = Unlimited > OK. Close MT5 and open it again, log in.
2. Double-click Export-History.bat. Leave MT5 and the black window open until it says Done (roughly 20-60 minutes).
3. A folder called exports_upload opens. Attach every exports_partN.zip file to the Claude chat.

Optional, after step 3: double-click Export-History-with-1min.bat to add 1-minute history for US100, US500, gold, TSLA
and NVDA. It keeps what is already done and only makes new parts: attach just the new ones.
If the window closes or MT5 drops out, run the same .bat again: it continues where it stopped.
Needs about 5 GB of free disk for MT5's history download.
