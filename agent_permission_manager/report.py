"""Render only computed figures with explicit provenance."""
import json

def render(result, format="md"):
    p = result["provenance"]
    banner = (f"Data provenance: {p['synthetic_records']} synthetic fixture records; "
              f"{p['real_records_declared_by_input']} real records declared by the input author (not independently verified).")
    if format == "json":
        return json.dumps({**result, "provenance_banner": banner}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    totals = result["totals"]
    lines = ["# Agent Permission Manager", "", banner, "", result["honesty"], "",
             "Policy scores are illustrative risk weights fixed by policy, not measured risk probabilities.", "",
             *[f"- {key}: {totals[key]}" for key in ("records", "restricted_records", "granted_permissions", "denied_permissions")], "",
             "| Tier | Records |", "| --- | ---: |", *[f"| {t} | {n} |" for t, n in totals["tiers"].items()], "",
             "## Decisions", ""]
    for d in result["decisions"]:
        lines.append(json.dumps(d, ensure_ascii=False, sort_keys=True))
    return "\n".join(lines) + "\n"
