"""Pure policy logic. Risk scores are policy weights, not measured probabilities."""
from datetime import date

PERMISSIONS = ("read", "write", "network", "execute")
WEIGHTS = {"untrusted_input": 25, "sensitive_data": 30, "external_destination": 20, "privileged_operation": 40}
FIELDS = {"id", "synthetic", "requested", "signals", "as_of", "observed_on", "description"}

class SchemaError(ValueError):
    """An explicit input violates the documented schema."""

def validate(record):
    if not isinstance(record, dict):
        raise SchemaError("record: expected object")
    unknown = set(record) - FIELDS
    if unknown:
        raise SchemaError("unknown fields: " + ", ".join(sorted(unknown)))
    for field in ("id", "synthetic", "requested", "signals", "as_of", "observed_on"):
        if field not in record:
            raise SchemaError(field + ": required field")
    if not isinstance(record["id"], str) or not 1 <= len(record["id"]) <= 256:
        raise SchemaError("id: expected 1 to 256 characters")
    if type(record["synthetic"]) is not bool:
        raise SchemaError("synthetic: expected boolean")
    desc = record.get("description", "")
    if not isinstance(desc, str) or len(desc) > 10000:
        raise SchemaError("description: expected at most 10000 characters")
    if "\u2014" in record["id"] or "\u2014" in desc:
        raise SchemaError("text: prohibited dash character")
    req = record["requested"]
    if not isinstance(req, list) or any(not isinstance(x, str) or x not in PERMISSIONS for x in req) or len(set(req)) != len(req):
        raise SchemaError("requested: unique permissions from read, write, network, execute required")
    sig = record["signals"]
    if not isinstance(sig, dict) or set(sig) != set(WEIGHTS) or any(type(v) is not bool for v in sig.values()):
        raise SchemaError("signals: all four documented boolean fields required")
    dates = []
    for field in ("as_of", "observed_on"):
        value = record[field]
        try:
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError()
            dates.append(date.fromisoformat(value))
        except (ValueError, TypeError):
            raise SchemaError(field + ": expected YYYY-MM-DD") from None
    if dates[1] > dates[0]:
        raise SchemaError("observed_on: future date relative to as_of")
    return record

def evaluate(record):
    validate(record)
    score = min(100, sum(weight for signal, weight in WEIGHTS.items() if record["signals"][signal]))
    tier = "low" if score < 25 else "moderate" if score < 50 else "high" if score < 75 else "critical"
    allowed = {"low": PERMISSIONS, "moderate": ("read", "write"), "high": ("read",), "critical": ()}[tier]
    requested = [p for p in PERMISSIONS if p in record["requested"]]
    return {"id": record["id"], "synthetic": record["synthetic"], "score": score, "tier": tier,
            "granted": [p for p in requested if p in allowed], "denied": [p for p in requested if p not in allowed],
            "reasons": [s for s in WEIGHTS if record["signals"][s]]}

def run(records):
    decisions, seen = [], set()
    for record in records:
        decision = evaluate(record)
        if decision["id"] in seen:
            raise SchemaError("id: duplicate " + decision["id"])
        seen.add(decision["id"])
        decisions.append(decision)
    decisions.sort(key=lambda d: d["id"])
    return {"schema_version": 1, "decisions": decisions,
            "totals": {"records": len(decisions), "restricted_records": sum(bool(d["denied"]) for d in decisions),
                       "granted_permissions": sum(len(d["granted"]) for d in decisions),
                       "denied_permissions": sum(len(d["denied"]) for d in decisions),
                       "tiers": {t: sum(d["tier"] == t for d in decisions) for t in ("low", "moderate", "high", "critical")}},
            "provenance": {"synthetic_records": sum(d["synthetic"] for d in decisions),
                           "real_records_declared_by_input": sum(not d["synthetic"] for d in decisions)},
            "honesty": "Scores are policy weights, not predictions. Time and money saved are unmeasured and not reported."}
