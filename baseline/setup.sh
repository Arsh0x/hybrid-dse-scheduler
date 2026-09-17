#!/usr/bin/env bash
set -euo pipefail

# Record environment
echo "=== Environment Record ===" | tee baseline/environment.md
uname -a | tee -a baseline/environment.md
lsb_release -a 2>/dev/null | tee -a baseline/environment.md || true
gcc --version | head -n 1 | tee -a baseline/environment.md
clang --version 2>/dev/null | head -n 1 | tee -a baseline/environment.md || true
python3 --version | tee -a baseline/environment.md
cmake --version 2>/dev/null | head -n 1 | tee -a baseline/environment.md || true
echo "CPU: $(nproc) cores" | tee -a baseline/environment.md
free -h | tee -a baseline/environment.md
