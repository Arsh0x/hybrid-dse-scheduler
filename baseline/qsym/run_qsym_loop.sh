#!/bin/bash
# QSYM restart wrapper: handles the AFL queue race condition by restarting on crash.
# Usage: run_qsym_loop.sh <afl_name> <output_dir> <qsym_name> <target...>

while true; do
  run_qsym_afl.py "$@" >> /tmp/qsym_loop.log 2>&1
  echo "$(date): QSYM exited with code $?, restarting in 2s" >> /tmp/qsym_loop.log
  sleep 2
done
