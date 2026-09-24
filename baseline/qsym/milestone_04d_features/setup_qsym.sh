#!/bin/bash
# QSYM rebuild + install script for hybrid-dse-scheduler
# Run this after every container restart.

set -e

PATCHED_SRC="/workspace/solver.cpp.4d"
SOLVER_PATH="/workdir/qsym/qsym/pintool/solver.cpp"
BUILD_DIR="/workdir/qsym/qsym/pintool"
INSTALLED_SO="/usr/local/lib/python2.7/dist-packages/qsym/pintool/obj-intel64/libqsym.so"

if [ ! -f "$PATCHED_SRC" ]; then
  echo "ERROR: patched solver.cpp not found at $PATCHED_SRC"
  echo "Did you mount /workspace?"
  exit 1
fi

echo "[1/3] Restoring patched solver.cpp..."
cp "$PATCHED_SRC" "$SOLVER_PATH"

echo "[2/3] Rebuilding libqsym.so (2-3 min)..."
cd "$BUILD_DIR"
make 2>&1 | tail -3

echo "[3/3] Installing to Python package path..."
cp "$BUILD_DIR/obj-intel64/libqsym.so" "$INSTALLED_SO"

echo ""
echo "Verify:"
strings "$INSTALLED_SO" | grep -c "candidate_id" && echo "  OK: candidate_id present" || echo "  WARN: candidate_id missing"
echo "Done. You can now run AFL + QSYM."
