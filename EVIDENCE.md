# Build evidence

Measured locally on 2026-10-01, Python 3.12.10, CPU only.

- pytest: 29 tests passed in 0.34 seconds.
- Installed CLI demo: fixtures, run and Markdown report completed in 0.623 seconds total, including process startup. Acceptance threshold: under 5 seconds.
- 200 synthetic records; 150 restricted; 350 granted permissions; 450 denied permissions; 50 records in each tier.
- Planted restricted IDs matched exactly: 150 true positives, zero false positives and zero false negatives against synthetic policy labels.
- Reversed input order and repeated CLI runs produced byte-identical reports/results.
- Corrupted input risk signals changed totals, proving computation is input-dependent.
- Real-use accuracy, threat detection, time savings and money savings are unmeasured.

The installed apm.exe Scripts directory is not in this machine's PATH. Add the Python user Scripts directory to PATH to invoke `apm` by name, or use `python -m agent_permission_manager.cli` with identical arguments. The measured demo invoked the installed entry point by absolute path.
