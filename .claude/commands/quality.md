---
description: Run the quality gate (format check, lint, tests with coverage) and report the results
allowed-tools: Bash(ruff *), Bash(pytest *)
---
Run the project's quality gate. Run these steps in order and stop at the first step that fails:

1. Format check: `ruff format --check .`
2. Lint: `ruff check .`
3. Tests with coverage: `pytest -q --cov=app --cov-report=term-missing`

For each step, show the command and its output.
If a step fails, explain the cause and propose a fix, but do not change any files.
Finish with a table of the three steps, each marked PASS or FAIL, and the total coverage percentage.
