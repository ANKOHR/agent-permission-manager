import json
from agent_permission_manager.fixtures import generate, EXPECTED
from agent_permission_manager.cli import load
from agent_permission_manager.core import run

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path/"records.jsonl").read_text().startswith("# Synthetic")
    assert all(r["synthetic"] is True for r in load(tmp_path))
    for name in ("expectations.json","tiny.json"):
        assert json.loads((tmp_path/name).read_text())["synthetic"] is True

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    assert run(load(tmp_path))["totals"] == EXPECTED
    assert len(load(tmp_path/"tiny.json")) == 5
