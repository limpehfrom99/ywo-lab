"""Pack whatever the exporter has finished into upload-sized zips, without MT5 and without waiting for the export to end.
Double-click Pack-Now.bat. It finds the exports folder by itself (the one Export-History.bat made), skips any file that is
still being written or is damaged, and only packs files that aren't packed yet. Safe to run while the export is running."""
import os, sys, time, zipfile

PART_MB = 24
DATA_EXT = (".npz", ".csv.gz")
INFO_FILES = ("manifest.txt", "symbol_specs.csv", "symbols_available.txt", "account.txt")
SKIP_DIRS = {"AppData", "node_modules", "$Recycle.Bin", "Windows", "Program Files", "Program Files (x86)"}


def find_exports():
    here = os.path.dirname(os.path.abspath(__file__)); home = os.path.expanduser("~")
    roots = [here, os.path.dirname(here)] + [os.path.join(home, p) for p in
             ("Desktop", "Downloads", "Documents", r"OneDrive\Desktop", r"OneDrive\Documents")] + [r"C:\ywo-lab", r"C:\Shen"]
    found = set()
    for r in roots:
        if not os.path.isdir(r): continue
        for dirpath, dirnames, filenames in os.walk(r):
            if dirpath[len(r):].count(os.sep) >= 5: dirnames[:] = []; continue
            if os.path.basename(dirpath) == "exports" and "run_info.json" in filenames: found.add(os.path.normpath(dirpath))
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
    if found: return max(found, key=os.path.getmtime)
    try:
        import tkinter as tk
        from tkinter import filedialog
        tk.Tk().withdraw()
        d = filedialog.askdirectory(title="Pick the folder that has Export-History.bat in it")
        if d and os.path.isdir(os.path.join(d, "exports")): return os.path.normpath(os.path.join(d, "exports"))
    except Exception:
        pass
    return None


def healthy(p):
    if time.time() - os.path.getmtime(p) < 60: return False          # may still be being written
    if p.endswith(".npz"):
        try:
            with zipfile.ZipFile(p) as z: return z.testzip() is None
        except Exception: return False
    return True


def pack(out, parts):
    os.makedirs(parts, exist_ok=True)
    log_p = os.path.join(parts, "packed.txt")
    done = set(open(log_p).read().split()) if os.path.exists(log_p) else set()
    nums = [int(f[12:-4]) for f in os.listdir(parts) if f.startswith("exports_part") and f.endswith(".zip") and f[12:-4].isdigit()]
    part = max(nums, default=0) + 1
    files = sorted(f for f in os.listdir(out) if f.endswith(DATA_EXT) and f not in done)
    data = [f for f in files if healthy(os.path.join(out, f))]
    skipped = sorted(set(files) - set(data))
    if not data: return [], skipped
    info = [f for f in INFO_FILES if os.path.exists(os.path.join(out, f))]
    new, z, size = [], None, 0
    for f in info + data:
        p = os.path.join(out, f); s = os.path.getsize(p)
        if z is None or (size > 0 and size + s > PART_MB * 1e6):
            if z: z.close()
            name = f"exports_part{part}.zip"; z = zipfile.ZipFile(os.path.join(parts, name), "w", zipfile.ZIP_STORED)
            new.append(name); part += 1; size = 0
        z.write(p, f); size += s
    z.close()
    with open(log_p, "a") as g: g.write("\n".join(data) + "\n")
    return new, skipped


def main():
    out = find_exports()
    if not out:
        print("Couldn't find the exports folder. Put Pack-Now.bat next to Export-History.bat and run it again."); input("Press Enter to close"); return
    parts = os.path.join(os.path.dirname(out), "exports_upload")
    print(f"Exports folder: {out}")
    n_files = sum(1 for f in os.listdir(out) if f.endswith(DATA_EXT))
    new, skipped = pack(out, parts)
    print(f"{n_files} data files in the folder.")
    if skipped: print(f"Skipped for now (still being written or damaged): {', '.join(skipped)}")
    if new:
        print(f"\nAttach these {len(new)} new file(s) from {parts} to the Claude chat:")
        for n in new: print(f"   {n}  ({os.path.getsize(os.path.join(parts, n)) / 1e6:.0f} MB)")
    else:
        print(f"\nNothing new to pack. Earlier parts are in {parts}")
    if hasattr(os, "startfile"): os.startfile(parts)
    input("Press Enter to close")


if __name__ == "__main__":
    main()
