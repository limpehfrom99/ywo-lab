"""Export price history from FTMO MT5 for the research lab (one click: Export-History.bat).

What it does
  1. Connects to the FTMO MT5 that is open and logged in on this PC. It only reads prices; it never trades.
  2. Downloads the bar history of every symbol in SYMBOLS below and saves one compact file per symbol and timeframe.
  3. Saves the specs of every symbol on the server (spread, swap, contract size, digits) and the list of all symbols.
  4. Packs everything into upload-sized zip parts in the exports_upload folder.

Usage   py -3 export_history.py          standard set (all groups below)
        py -3 export_history.py --m1     also 1-minute history for 5 key symbols (adds roughly 100 MB)
        py -3 export_history.py --csv    write MT5 "Export Bars" text files (.csv.gz) instead of the compact .npz files
If the window was closed or MT5 dropped out, just run it again: finished files are kept and skipped (for 2 days).
"""
import os, sys, time, json, gzip, csv, zipfile, datetime as dt

try:
    import numpy as np
    import MetaTrader5 as mt5
except ImportError as e:
    print(f"A Python package is missing ({e.name}). Fix: double-click Setup.bat in your lab folder, then run this again.")
    input("Press Enter to close"); sys.exit(1)

UTC = dt.timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports")
PARTS = os.path.join(HERE, "exports_upload")
PART_MB = 24                      # every zip part stays under the chat and GitHub upload limits
FMT = "ywo-bars-v1"
DATA_EXT = (".npz", ".csv.gz")
INFO_FILES = ("manifest.txt", "symbol_specs.csv", "symbols_available.txt", "account.txt")

# group: (symbols, timeframes, first year). Symbols this server doesn't have are skipped automatically.
SYMBOLS = {
    "US stocks": (["TSLA", "NVDA", "AMD", "META", "AMZN", "AAPL", "MSFT", "GOOG", "GOOGL", "NFLX", "AVGO", "ORCL", "ADBE",
                   "CRM", "INTC", "MU", "QCOM", "PLTR", "COIN", "MSTR", "UBER", "SHOP", "ZM", "BABA", "NIO", "PYPL", "DIS",
                   "BA", "JPM", "BAC", "GS", "V", "MA", "WMT", "COST", "KO", "PEP", "MCD", "NKE", "XOM", "CVX", "PFE",
                   "JNJ", "LLY", "UNH", "T"], ["M5", "D1"], 2015),
    "Indices":   (["US100.cash", "US500.cash", "US30.cash", "US2000.cash", "GER40.cash", "UK100.cash", "EU50.cash",
                   "FRA40.cash", "SPN35.cash", "N25.cash", "JP225.cash", "AUS200.cash", "HK50.cash", "DXY.cash"], ["M5", "D1"], 2015),
    "Metals":    (["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "XCUUSD"], ["M5", "D1"], 2015),
    "Energy":    (["USOIL.cash", "UKOIL.cash", "NATGAS.cash"], ["M5", "D1"], 2015),
    "Softs":     (["COCOA.c", "COFFEE.c", "CORN.c", "COTTON.c", "SOYBEAN.c", "SUGAR.c", "WHEAT.c"], ["M5", "D1"], 2015),
    "Crypto":    (["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "LTCUSD", "ADAUSD", "DOGEUSD"], ["M5", "D1"], 2018),
    "Forex":     (["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURGBP", "EURJPY", "EURAUD",
                   "EURNZD", "EURCAD", "EURCHF", "GBPJPY", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF", "AUDJPY", "AUDNZD",
                   "AUDCAD", "AUDCHF", "NZDJPY", "NZDCAD", "NZDCHF", "CADJPY", "CADCHF", "CHFJPY"], ["M15", "D1"], 2015),
}
M1_SYMBOLS = ["US100.cash", "US500.cash", "XAUUSD", "TSLA", "NVDA"]
D1_FROM = 2000                    # daily bars are cheap: take everything the server has
TF = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
      "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1}


def connect():
    if mt5.initialize(): return True
    try:
        cfg = json.load(open(os.path.join(HERE, "config.json")))
        if cfg.get("mt5_path") and mt5.initialize(path=cfg["mt5_path"]): return True
    except Exception: pass
    for p in (r"C:\Program Files\FTMO MetaTrader 5\terminal64.exe", r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe"):
        if os.path.exists(p) and mt5.initialize(path=p): return True
    return False


def rates(sym, tf, a, b):
    r = mt5.copy_rates_range(sym, TF[tf], a, b)
    if r is None and mt5.last_error()[0] <= -10000:      # lost the link to the terminal: reconnect once and retry
        time.sleep(3); connect(); r = mt5.copy_rates_range(sym, TF[tf], a, b)
    return r


def fetch(sym, tf, y0, warm=False):
    """Whole range in one request. MT5 may still be downloading older history from the server, so ask again until the
    bar count stops growing. warm=True: this symbol's history was just loaded for another timeframe, so a shorter check."""
    a = dt.datetime(y0, 1, 1, tzinfo=UTC); b = dt.datetime.now(UTC) + dt.timedelta(days=2)
    best, stable, misses = None, 0, 0
    for _ in range(90):                                    # stops as soon as the count is steady; 3 minutes at most
        r = rates(sym, tf, a, b)
        n = 0 if r is None else len(r)
        misses = misses + 1 if n == 0 else 0
        if best is None and misses >= 5: break             # refused or empty 5 times running: try year by year below
        if best is not None and n <= len(best): stable += 1
        else:
            stable = 0
            if n: best = r
        if best is not None and (stable >= (1 if warm else 2) or best["time"][0] <= a.timestamp() + 7 * 86400): break
        time.sleep(2)
    if best is None:                                       # some terminals refuse one huge request: go year by year
        parts = [r for y in range(y0, dt.datetime.now(UTC).year + 1)
                 for r in [rates(sym, tf, dt.datetime(y, 1, 1, tzinfo=UTC), dt.datetime(y + 1, 1, 1, tzinfo=UTC))] if r is not None and len(r)]
        if parts:
            best = np.concatenate(parts); best = best[np.unique(best["time"], return_index=True)[1]]
    return best


def encode(r, digits):
    """Lossless integer encoding (prices in points, as differences) so the files are ~2-3x smaller than zipped CSV."""
    sc = 10.0 ** digits
    t = r["time"].astype(np.int64)
    o, h, l, c = (np.rint(r[k] * sc).astype(np.int64) for k in ("open", "high", "low", "close"))
    pc = np.concatenate([[0], c[:-1]])
    cols = {"dt": np.diff(t, prepend=t[0]), "o_pc": o - pc, "c_o": c - o, "h_x": h - np.maximum(o, c),
            "x_l": np.minimum(o, c) - l, "tv": r["tick_volume"].astype(np.int64), "rv": r["real_volume"].astype(np.int64),
            "sp": r["spread"].astype(np.int64)}
    for k, v in cols.items():
        if v.size and np.abs(v).max() < 2**31 - 1: cols[k] = v.astype(np.int32)
    return cols, int(t[0])


def decode(z, meta):
    t = meta["t0"] + np.cumsum(z["dt"].astype(np.int64))
    o_pc, c_o = z["o_pc"].astype(np.int64), z["c_o"].astype(np.int64)
    o = np.cumsum(o_pc) + np.cumsum(c_o) - c_o; c = o + c_o
    h = np.maximum(o, c) + z["h_x"].astype(np.int64); l = np.minimum(o, c) - z["x_l"].astype(np.int64)
    return t, o, h, l, c


def write_npz(sym, tf, r, digits, server):
    t0 = dt.datetime.fromtimestamp(int(r["time"][0]), UTC); t1 = dt.datetime.fromtimestamp(int(r["time"][-1]), UTC)
    name = f"{sym}_{tf}_{t0:%Y%m%d%H%M}_{t1:%Y%m%d%H%M}.npz"; path = os.path.join(OUT, name)
    cols, t_first = encode(r, digits)
    meta = {"format": FMT, "symbol": sym, "tf": tf, "digits": int(digits), "t0": t_first, "bars": int(len(r)), "server": server,
            "clock": "MT5 server time", "exported": f"{dt.datetime.now():%Y-%m-%d %H:%M}"}
    np.savez_compressed(path, meta=np.frombuffer(json.dumps(meta).encode(), dtype=np.uint8), **cols)
    with np.load(path) as z:                               # self-check: read the file back and compare with what MT5 sent
        m = json.loads(bytes(z["meta"]).decode()); t, o, h, l, c = decode(z, m); sc = 10.0 ** digits
        ok = (len(t) == len(r) and np.array_equal(t, r["time"].astype(np.int64))
              and all(np.abs(x / sc - r[k]).max() <= 0.51 / sc for x, k in ((o, "open"), (h, "high"), (l, "low"), (c, "close")))
              and np.array_equal(z["tv"].astype(np.int64), r["tick_volume"].astype(np.int64))
              and np.array_equal(z["sp"].astype(np.int64), r["spread"].astype(np.int64)))
    if not ok:                                             # should never happen; fall back to the plain text format
        os.remove(path); return write_csv(sym, tf, r, digits)
    return name, t0, t1, os.path.getsize(path)


def write_csv(sym, tf, r, digits, server=None):
    t0 = dt.datetime.fromtimestamp(int(r["time"][0]), UTC); t1 = dt.datetime.fromtimestamp(int(r["time"][-1]), UTC)
    name = f"{sym}_{tf}_{t0:%Y%m%d%H%M}_{t1:%Y%m%d%H%M}.csv.gz"; path = os.path.join(OUT, name); f = f"{{:.{digits}f}}"
    with gzip.open(path, "wt", newline="") as g:
        g.write("<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n")
        for x in r:
            t = dt.datetime.fromtimestamp(int(x["time"]), UTC)       # MT5 bar times are broker server time, written as-is
            g.write(f"{t:%Y.%m.%d}\t{t:%H:%M:%S}\t{f.format(x['open'])}\t{f.format(x['high'])}\t{f.format(x['low'])}\t"
                    f"{f.format(x['close'])}\t{int(x['tick_volume'])}\t{int(x['real_volume'])}\t{int(x['spread'])}\n")
    return name, t0, t1, os.path.getsize(path)


def prepare_out(maxbars):
    """Keep finished files from a run started in the last 2 days with the same MT5 setting; otherwise start clean."""
    os.makedirs(OUT, exist_ok=True); os.makedirs(PARTS, exist_ok=True)
    info_p = os.path.join(OUT, "run_info.json")
    try: prev = json.load(open(info_p))
    except Exception: prev = {}
    resume = prev.get("maxbars") == maxbars and time.time() - prev.get("started", 0) < 2 * 86400
    if not resume:
        for d in (OUT, PARTS):
            for f in os.listdir(d):
                if f.endswith(DATA_EXT + (".zip", ".txt", ".csv", ".json")): os.remove(os.path.join(d, f))
        json.dump({"maxbars": maxbars, "started": time.time()}, open(info_p, "w"))
    return resume


def existing(sym, tf):
    for f in os.listdir(OUT):
        if f.startswith(f"{sym}_{tf}_") and f.endswith(DATA_EXT): return f
    return None


def pack():
    """Zip the files that haven't been packed yet into new parts (a second run, e.g. --m1, only adds new parts)."""
    log_p = os.path.join(PARTS, "packed.txt")
    done = set(open(log_p).read().split()) if os.path.exists(log_p) else set()
    nums = [int(f[12:-4]) for f in os.listdir(PARTS) if f.startswith("exports_part") and f.endswith(".zip") and f[12:-4].isdigit()]
    part = max(nums, default=0) + 1
    data = sorted(f for f in os.listdir(OUT) if f.endswith(DATA_EXT) and f not in done)
    if not data: return []
    info = [f for f in INFO_FILES if os.path.exists(os.path.join(OUT, f))]
    new, z, size = [], None, 0
    for f in info + data:
        p = os.path.join(OUT, f); s = os.path.getsize(p)
        if z is None or (size > 0 and size + s > PART_MB * 1e6):
            if z: z.close()
            name = f"exports_part{part}.zip"; z = zipfile.ZipFile(os.path.join(PARTS, name), "w", zipfile.ZIP_STORED)
            new.append(name); part += 1; size = 0
        z.write(p, f); size += s
    z.close()
    with open(log_p, "a") as g: g.write("\n".join(data) + "\n")
    return new


def save_specs(allsyms, ai, ti):
    with open(os.path.join(OUT, "symbols_available.txt"), "w", encoding="utf-8") as f:
        for s in allsyms: f.write(f"{s.name}\t{s.path}\t{s.digits}\t{s.description}\n")
    rows = [s._asdict() for s in allsyms if hasattr(s, "_asdict")]
    if rows:
        with open(os.path.join(OUT, "symbol_specs.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(OUT, "account.txt"), "w", encoding="utf-8") as f:      # no login number or name
        for k in ("company", "server", "currency", "leverage", "trade_mode", "margin_so_mode"):
            f.write(f"{k}\t{getattr(ai, k, getattr(ti, k, ''))}\n")
        f.write(f"maxbars\t{ti.maxbars}\n")


def main():
    with_m1, as_csv = "--m1" in sys.argv, "--csv" in sys.argv
    if not connect():
        print("Could not connect to MT5:", mt5.last_error()); print("Open FTMO MT5, log in, then run this again.")
        input("Press Enter to close"); return
    ti = mt5.terminal_info(); ai = mt5.account_info(); server = ai.server if ai else "?"
    print(f"Connected: {ti.company} | server {server} | max bars in chart {ti.maxbars:,}")
    if ti.maxbars < 5_000_000:
        print("\n!! MT5 'Max bars in chart' is limited, so the history will be cut short (that is why earlier exports stopped at 100,000 bars).")
        print("   Fix: in MT5 click Tools > Options > Charts, set 'Max bars in chart' to Unlimited, click OK,")
        print("        close MT5 completely, open it again, then run this again.")
        if input("   Continue anyway with the short history? (y/N) ").strip().lower() != "y": return
    resume = prepare_out(ti.maxbars)
    allsyms = mt5.symbols_get() or []; names = {s.name for s in allsyms}
    save_specs(allsyms, ai, ti)
    jobs = [(g, sym, tf, D1_FROM if tf == "D1" else y0) for g, (syms, tfs, y0) in SYMBOLS.items() for sym in syms for tf in tfs]
    if with_m1: jobs += [("1-minute", sym, "M1", 2015) for sym in M1_SYMBOLS]
    print(f"{len(jobs)} files to make ({sum(1 for j in jobs if j[1] in names)} on this server). "
          f"{'Continuing the earlier run. ' if resume else ''}This takes a while: leave MT5 and this window open.\n")
    manifest, t_start, loaded = [], time.time(), set()
    write = write_csv if as_csv else write_npz
    for i, (g, sym, tf, y0) in enumerate(jobs, 1):
        tag = f"[{i}/{len(jobs)}] {sym:12s} {tf:3s}"
        if sym not in names:
            print(f"{tag} not on this server, skipped"); manifest.append((g, sym, tf, "missing", "", "", 0, 0)); continue
        f = existing(sym, tf) if resume else None
        if f:
            print(f"{tag} already done ({f})"); manifest.append((g, sym, tf, "ok", f.split("_")[-2][:8], f.split("_")[-1][:8], 0, os.path.getsize(os.path.join(OUT, f))))
            continue
        try:
            if not mt5.symbol_select(sym, True): raise RuntimeError(f"symbol_select failed {mt5.last_error()}")
            info = mt5.symbol_info(sym)
            r = fetch(sym, tf, y0, warm=sym in loaded); loaded.add(sym)
            if r is None or len(r) == 0:
                print(f"{tag} no bars returned"); manifest.append((g, sym, tf, "empty", "", "", 0, 0)); continue
            name, t0, t1, size = write(sym, tf, r, info.digits, server)
            print(f"{tag} {len(r):>9,} bars  {t0:%Y-%m-%d} -> {t1:%Y-%m-%d}  {size / 1e6:5.1f} MB   ({(time.time() - t_start) / 60:.0f} min so far)")
            manifest.append((g, sym, tf, "ok", f"{t0:%Y-%m-%d}", f"{t1:%Y-%m-%d}", len(r), size))
        except Exception as e:
            print(f"{tag} error: {e}"); manifest.append((g, sym, tf, f"error: {e}", "", "", 0, 0))
    with open(os.path.join(OUT, "manifest.txt"), "w") as f:
        f.write(f"exported {dt.datetime.now():%Y-%m-%d %H:%M} | server {server} | max bars {ti.maxbars} | m1 {with_m1}\n")
        f.write("group\tsymbol\ttf\tstatus\tfirst\tlast\tbars\tbytes\n")
        for m in manifest: f.write("\t".join(str(x) for x in m) + "\n")
    mt5.shutdown()
    new = pack(); ok = sum(1 for m in manifest if m[3] == "ok")
    print(f"\nDone in {(time.time() - t_start) / 60:.0f} min: {ok} files.")
    if new:
        print(f"Upload these {len(new)} file(s) from {PARTS} to the Claude chat:")
        for n in new: print(f"   {n}  ({os.path.getsize(os.path.join(PARTS, n)) / 1e6:.0f} MB)")
    else:
        print(f"Nothing new to pack. Earlier parts are still in {PARTS}")
    if hasattr(os, "startfile"): os.startfile(PARTS)
    input("Press Enter to close")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Run it again to continue where it left off."); input("Press Enter to close")
    except Exception as e:
        print(f"\nUnexpected error: {e!r}\nTake a screenshot of this window and send it to Claude."); input("Press Enter to close")
