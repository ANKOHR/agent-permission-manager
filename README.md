# Agent Permission Manager

A local Python CLI that computes permission limits from explicit boolean risk signals. It evaluates policy decisions; an agent runner must apply those decisions before executing actions. No network, model calls, GPU work, database, or inferred facts.

Hypothesis: deterministic permission decisions with planted ground truth provide a trustworthy policy component. Acceptance: 200 synthetic records, exact totals, all planted restrictions, zero false positives against fixture labels, and a demo under five seconds. This does not validate real-world risk accuracy.

## Quickstart

Python 3.10 or newer. Install locally with `python -m pip install --no-build-isolation --no-deps -e .`. If the user Scripts directory is absent from PATH, add it or replace `apm` with `python -m agent_permission_manager.cli` in all examples. Tests require pytest: `python -m pytest`. No network is needed when setuptools and pytest are already installed.

```powershell
apm fixtures --out demo
apm run --input demo
apm report --format md
```

For the five-record version: `apm run --input demo/tiny.json`. Results are stored atomically in `.apm-results.json`. Reports contain each computed decision and aggregate counts.

## Input format

A directory reads only `records*.json` and `records*.jsonl`, in sorted filename order. Explicit file paths support any JSON or JSONL filename. Other directory files are metadata and are not inputs. Empty directories produce zero counts. JSON accepts a list of records or an object containing `records`. JSONL accepts one record per line, with blank lines and `#` header comments permitted.

```json
{"id":"manual-1","synthetic":false,"requested":["read","write"],"signals":{"untrusted_input":true,"sensitive_data":false,"external_destination":false,"privileged_operation":false},"as_of":"2026-09-30","observed_on":"2026-09-29","description":"Henry entered this observation by hand"}
```

Fields: `id` is unique across the input, 1 to 256 characters; `synthetic` must be boolean; `requested` is a unique list drawn from read, write, network, execute; `signals` contains exactly the four boolean fields above. ISO dates are required. `observed_on` cannot exceed the explicit `as_of` date. This explicit evaluation date keeps historical runs deterministic; dates are not checked against the machine clock. Optional description allows 10000 characters. Unicode and Windows path strings work. Prohibited dash characters, unknown fields (including negative amount fields), unknown permissions, numeric boolean substitutes, duplicate IDs, extreme strings and schema drift are rejected, with no records silently dropped. Amounts are outside this domain. JSON schema errors name the file and record start line; JSON parse errors name the actual line. JSONL schema errors name the exact row.

## Policy and subcommands

Scores sum fixed weights and cap at 100: untrusted input 25, sensitive data 30, external destination 20, privileged operation 40. Scores 0 to 24 permit all four permissions; 25 to 49 permit read and write; 50 to 74 permit read; 75 to 100 permit none. Grants always intersect the requested permissions. Any denial marks a record restricted. The policy has no implicit overrides.

- `apm fixtures --out demo`: generate fixtures and expectations.
- `apm run --input demo --output results.json`: validate and compute decisions.
- `apm report --results results.json --format json --out report.json`: render a report; md is also supported.
- `apm check --input demo --id case-001`: explain a single record with reasons and provenance.
- `apm policy`: inspect weights and tier limits.

Every subcommand provides `--help` and an example. Named errors exit 2; success exits 0. Parse errors, missing inputs, schema errors, encoding errors and write failures never produce CLI tracebacks. Atomic replacement preserves an existing report on failure and removes temporary files. Fixture generation is not transactional across its three files.

## Architecture

```text
JSON/JSONL -> CLI validation -> pure core policy -> atomic results JSON
fixtures -> explicit records + independent expectations
results JSON -> report renderer -> Markdown/JSON with provenance
agent runner -> check decisions -> enforce permissions (external integration)
```

Reports read a local trusted result artifact from `run`. They check its record count, but are not an integrity or authenticity mechanism. Regenerate results after input changes. This tool cannot prevent an external runner from ignoring decisions, detect dishonest signals, or discover missing risks. Manual false declarations of provenance cannot be verified.

## Honesty boundary and fixture policy

All figures come from explicit inputs. Scores are illustrative policy weights, not measured probabilities or predictions. Time saved and money saved are unmeasured and not reported. Real records mean only that the input author declared `synthetic: false`; reports do not claim independent verification or Henry's authorship. Henry can enter his own data manually using the format above. Do not ship his trial data.

Fixtures have no random seed because generation uses no randomness. JSONL carries a synthetic header comment and every record has `synthetic: true`. JSON metadata carries `synthetic: true` and a synthetic label. JSON does not support header comments. The 200 rows cycle through scores 0, 25, 55, 95 with 50 rows per tier. Hand computation: grants = 50*(4+2+1+0) = 350; denials = 50*(0+2+3+4) = 450; restrictions = 150. The expectations file is excluded from workflow inputs. Corrupting a record's signals changes computed output; changing metadata expectations does not change decisions.

## Evidence and improvement hook

See EVIDENCE.md for measured local build results. After two weeks of real use, record the number of runs and hand-check at least 20 permission decisions against Henry's intended policy. Metric: mismatched decisions / checked decisions. If the measured error rate exceeds 10 percent, fix the largest observed failure cause and repeat the check. If there are no real runs, record that and kill the project. Measure any time savings against a timed baseline before reporting them. Trial results remain local.

Verdict is pending the two-week evidence window, not invented at build time. Record the date, sample, metric and reason in VERDICT.md: expand for daily use or revenue; integrate for substantial sibling overlap; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill for non-use or unmet acceptance criteria.
