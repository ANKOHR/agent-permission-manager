"""Local-only CLI with named errors and atomic result writes."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, WEIGHTS, evaluate, run
from .fixtures import generate
from .report import render

class InputError(ValueError):
    pass

def load(path):
    path = Path(path)
    if not path.exists():
        raise InputError(f"MissingInput: {path}; use apm fixtures --out demo or supply an existing input")
    paths = sorted(path.glob("records*.json*")) if path.is_dir() else [path]
    result = []
    for file in paths:
        if file.suffix not in (".json", ".jsonl"):
            raise InputError(f"SchemaError: {file}:1: unsupported format; use JSON or JSONL")
        content = file.read_text(encoding="utf-8-sig")
        chunks = [(i, line) for i, line in enumerate(content.splitlines(), 1) if line.strip() and not line.lstrip().startswith("#")] if file.suffix == ".jsonl" else [(1, content)]
        for lineno, chunk in chunks:
            try:
                data = json.loads(chunk)
            except json.JSONDecodeError as exc:
                raise InputError(f"ParseError: {file}:{lineno + exc.lineno - 1}: {exc.msg}") from None
            rows = [data] if file.suffix == ".jsonl" else data.get("records") if isinstance(data, dict) else data
            if not isinstance(rows, list):
                raise InputError(f"SchemaError: {file}:{lineno}: records must be a list")
            for row in rows:
                try:
                    evaluate(row)
                    if any(r["id"] == row["id"] for r in result):
                        raise SchemaError("id: duplicate " + row["id"])
                except SchemaError as exc:
                    raise InputError(f"SchemaError: {file}:{lineno}: {exc}") from None
                result.append(row)
    return result

def atomic_write(path, content):
    path = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Compute permission limits from explicit inputs. No runtime enforcement.")
    subs = parser.add_subparsers(dest="command", required=True)
    f = subs.add_parser("fixtures", help="Generate labelled synthetic data", epilog="Example: apm fixtures --out demo")
    f.add_argument("--out", required=True)
    r = subs.add_parser("run", help="Evaluate all input records", epilog="Example: apm run --input demo")
    r.add_argument("--input", required=True)
    r.add_argument("--output", default=".apm-results.json")
    rep = subs.add_parser("report", help="Render computed results and provenance", epilog="Example: apm report --format md")
    rep.add_argument("--format", choices=("md", "json"), default="md")
    rep.add_argument("--results", default=".apm-results.json")
    rep.add_argument("--out")
    check = subs.add_parser("check", help="Evaluate one record by ID", epilog="Example: apm check --input demo --id case-001")
    check.add_argument("--input", required=True)
    check.add_argument("--id", required=True)
    subs.add_parser("policy", help="Show policy weights and permission limits", epilog="Example: apm policy")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 synthetic records, hand-computed expectations, and synthetic five-record example.")
        elif args.command == "run":
            result = run(load(args.input))
            atomic_write(args.output, render(result, "json"))
            print(f"Computed {result['totals']['records']} records. " + json.loads(render(result, "json"))["provenance_banner"])
        elif args.command == "report":
            path = Path(args.results)
            if not path.exists():
                raise InputError(f"MissingInput: {path}; run apm run --input <dir> first")
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
                # Reconcile persisted decisions before rendering, without inventing signals.
                ds = result["decisions"]
                if result["totals"]["records"] != len(ds):
                    raise ValueError("record count mismatch")
                output = render(result, args.format)
            except (ValueError, KeyError, TypeError) as exc:
                raise InputError(f"ResultError: {path}:1: {exc}") from None
            if args.out:
                atomic_write(args.out, output)
            else:
                sys.stdout.write(output)
        elif args.command == "check":
            rows = load(args.input)
            matches = [r for r in rows if r["id"] == args.id]
            if not matches:
                raise InputError("MissingRecord: id not found")
            sys.stdout.write(render(run(matches), "json"))
        else:
            print(json.dumps({"weights": WEIGHTS, "score_label": "Illustrative policy weights, not measured probabilities",
                "limits": {"0-24": ["read", "write", "network", "execute"], "25-49": ["read", "write"], "50-74": ["read"], "75-100": []}}, indent=2))
        return 0
    except (InputError, SchemaError, OSError, UnicodeError) as exc:
        name = "WriteOrReadError" if isinstance(exc, OSError) else "EncodingError" if isinstance(exc, UnicodeError) else "InputError"
        print(f"{name}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
