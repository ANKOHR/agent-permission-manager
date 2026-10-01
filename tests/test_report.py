import json
from agent_permission_manager.core import run
from agent_permission_manager.fixtures import records, EXPECTED
from agent_permission_manager.report import render

def test_report_matches_ground_truth_exact():
    assert json.loads(render(run(records()),"json"))["totals"] == EXPECTED

def test_report_zero_false_positives():
    ds=json.loads(render(run(records()),"json"))["decisions"]
    assert {d["id"] for d in ds if d["denied"]} == {f"case-{i:03d}" for i in range(200) if i%4}

def test_report_carries_provenance_banner():
    rs=records(2); rs[0]["synthetic"]=False
    for fmt in ("md","json"):
        output=render(run(rs),fmt)
        assert "1 synthetic fixture records" in output
        assert "1 real records declared" in output

def test_hypothetical_figures_labelled():
    out=render(run(records()),"md")
    assert "illustrative" in out
    assert "unmeasured and not reported" in out

def test_no_em_dashes_in_outputs():
    for fmt in ("md","json"):
        assert chr(0x2014) not in render(run(records()),fmt)

def test_determinism_byte_identical():
    for fmt in ("md","json"):
        assert render(run(records()),fmt).encode() == render(run(list(reversed(records()))),fmt).encode()
