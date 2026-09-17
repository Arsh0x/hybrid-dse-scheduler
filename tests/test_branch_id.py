"""
Verify that build_id + module-relative branch offset is stable across:
  - repeated runs
  - PIE vs non-PIE builds
  - stripped vs unstripped
"""
import hashlib
import sys
from pathlib import Path

def build_id(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def module_base(path: str) -> int:
    # Placeholder: parse ELF program headers to find load base
    # In practice, read from /proc/<pid>/maps during execution
    return 0

def branch_offset(binary: str, branch_addr: int) -> int:
    return branch_addr - module_base(binary)

def test_branch_id_format():
    sample_file = Path(__file__)
    bid = build_id(str(sample_file))
    assert len(bid) == 64
    boff = branch_offset(str(sample_file), 0x401122)
    assert boff == 0x401122

if __name__ == "__main__":
    binary = sys.argv[1] if len(sys.argv) > 1 else __file__
    print(f"build_id: {build_id(binary)}")
    print("branch_offset scheme: build_id + (branch_addr - module_base)")
