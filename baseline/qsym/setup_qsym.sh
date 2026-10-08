#!/bin/bash
# QSYM rebuild + install script for hybrid-dse-scheduler
# Restores all 3 patched files (solver.cpp, solver.h, main.cpp), rebuilds, installs.

set -e

WORKSPACE="/workspace"
BUILD_DIR="/workdir/qsym/qsym/pintool"
INSTALLED_SO="/usr/local/lib/python2.7/dist-packages/qsym/pintool/obj-intel64/libqsym.so"
AFL_PY="/usr/local/lib/python2.7/dist-packages/qsym/afl.py"

for f in solver.cpp.fix solver.h.fix main.cpp.fix; do
  if [ ! -f "$WORKSPACE/$f" ]; then
    echo "ERROR: $WORKSPACE/$f not found"
    exit 1
  fi
done

echo "[1/4] Restoring patched sources..."
cp "$WORKSPACE/solver.cpp.fix" "$BUILD_DIR/solver.cpp"
cp "$WORKSPACE/solver.h.fix"   "$BUILD_DIR/solver.h"
cp "$WORKSPACE/main.cpp.fix"   "$BUILD_DIR/main.cpp"

echo "[2/4] Rebuilding libqsym.so (2-3 min)..."
cd "$BUILD_DIR"
make 2>&1 | tail -3

echo "[3/4] Installing libqsym.so..."
cp "$BUILD_DIR/obj-intel64/libqsym.so" "$INSTALLED_SO"

echo "[4/4] Restoring patched afl.py (QSYM Python race fix)..."
if [ -f "$WORKSPACE/milestone_5e2_rtn_cmov/afl.py.patched" ]; then
  cp "$WORKSPACE/milestone_5e2_rtn_cmov/afl.py.patched" "$AFL_PY"
  echo "  OK: afl.py race fix restored"
else
  echo "  WARN: afl.py.patched not found"
fi

echo ""
echo "Verify:"
strings "$INSTALLED_SO" | grep -c "rtn_cmov" && echo "  OK: rtn_cmov present" || echo "  WARN: rtn_cmov missing"
pip3 install pyyaml 2>&1 | tail -1
echo "Done. You can now run AFL + QSYM."
