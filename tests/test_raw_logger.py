import tempfile
from pathlib import Path
import src.feature_extraction.raw_logger as rl

def test_append_only(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "RAW_DIR", tmp_path)
    rl.log_candidate("run1", "branchA", 0, hit_count=3)
    rl.log_candidate("run1", "branchB", 0, hit_count=5)
    rows = (tmp_path / "candidates.csv").read_text().strip().splitlines()
    assert len(rows) == 3  # header + 2 rows
    assert "branchA" in rows[1]
    assert "branchB" in rows[2]

def test_outcome_label(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "RAW_DIR", tmp_path)
    rl.log_outcome("run1", "branchA", "SAT", 12.5, True, True, 100, 103)
    rows = (tmp_path / "outcomes.csv").read_text().strip().splitlines()
    assert "coverage_useful" in rows[0]
    assert "3" in rows[1]  # new_edges
