#!/usr/bin/env bash
# Fetch Timothy Masters' book code ("Testing and Tuning Market Trading Systems", Apress 2018) and build it on Linux.
# Licence: freeware for personal use only (no commercial use) -- so the book's source is NOT stored in this repo;
# this script downloads it. Output: $VENDOR/bin (20 demo programs + verify_cscv, verify_bca).
# Usage: bash tools/get_masters.sh        (VENDOR defaults to /home/claude/vendor)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
V=${VENDOR:-/home/claude/vendor}
mkdir -p "$V/bin"
[ -d "$V/ttmts" ] || git clone -q --depth 1 https://github.com/Apress/testing-and-tuning-market-trading-systems "$V/ttmts"
rm -rf "$V/build_src" && cp -r "$V/ttmts" "$V/build_src" && rm -rf "$V/build_src/.git"
for f in "$V"/build_src/*/*.CPP "$V"/build_src/*/*.cpp; do [ -f "$f" ] && sed -i 's/^void main *(/int main (/' "$f"; done
ln -sf HEADERS.H "$V/build_src/DEV_MA/headers.h"
F="-O2 -w -fpermissive -I$HERE/compat -include $HERE/compat/compat.h"
cd "$V/build_src"
for d in */; do
  d=${d%/}; [ "$d" = CSCV_MKT ] && continue
  srcs=$(ls "$d"/*.CPP "$d"/*.cpp 2>/dev/null || true); [ -z "$srcs" ] && continue
  g++ $F -I"$d" -o "$V/bin/$(echo "$d" | tr 'A-Z' 'a-z')" $srcs -lm && echo "built $d"
done
g++ $F -o "$V/bin/cscv" CSCV_MKT/CSCV.CPP CSCV_MKT/CSCV_CORE.CPP CSCV_MKT/CRITER.CPP -lm && echo "built cscv"
g++ $F -o "$V/bin/cscv_mkt" CSCV_MKT/CSCV_MKT.CPP CSCV_MKT/CSCV_CORE.CPP CSCV_MKT/CRITER.CPP -lm && echo "built cscv_mkt"
g++ $F -o "$V/bin/verify_cscv" "$HERE/verify_cscv.cpp" CSCV_MKT/CSCV_CORE.CPP CSCV_MKT/CRITER.CPP -lm && echo "built verify_cscv"
g++ $F -IBOOT_RATIO -o "$V/bin/verify_bca" "$HERE/verify_bca.cpp" BOOT_RATIO/BOOT_CONF.CPP BOOT_RATIO/STATS.CPP \
    BOOT_RATIO/QSORTD.CPP BOOT_RATIO/UNIFRAND.CPP -lm && echo "built verify_bca"
