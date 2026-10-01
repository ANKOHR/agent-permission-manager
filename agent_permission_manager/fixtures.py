"""Synthetic deterministic fixtures with manually enumerated expectations. No randomness."""
import json
from pathlib import Path
from .core import WEIGHTS

# Hand computation: 50 each at scores 0, 25, 55, 95.
# Grants per row: 4, 2, 1, 0; denials per row: 0, 2, 3, 4.
EXPECTED = {"records": 200, "restricted_records": 150, "granted_permissions": 350,
            "denied_permissions": 450, "tiers": {"low": 50, "moderate": 50, "high": 50, "critical": 50}}

def records(count=200):
    patterns = ((), ("untrusted_input",), ("untrusted_input", "sensitive_data"),
                ("untrusted_input", "sensitive_data", "privileged_operation"))
    return [{"id": f"case-{i:03d}", "synthetic": True, "requested": ["read", "write", "network", "execute"],
             "signals": {s: s in patterns[i % 4] for s in WEIGHTS}, "as_of": "2026-09-30",
             "observed_on": "2026-09-29", "description": "Synthetic planted policy case"} for i in range(count)]

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "records.jsonl").write_text("# Synthetic fixture data; not real observations\n" +
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records()), encoding="utf-8")
    (out / "expectations.json").write_text(json.dumps({"synthetic": True, "label": "Synthetic hand-computed ground truth",
        "totals": EXPECTED, "restricted_ids": [f"case-{i:03d}" for i in range(200) if i % 4]}, indent=2) + "\n", encoding="utf-8")
    (out / "tiny.json").write_text(json.dumps({"synthetic": True, "label": "Synthetic five-record example; explicitly select this file",
        "records": records(5)}, indent=2) + "\n", encoding="utf-8")
