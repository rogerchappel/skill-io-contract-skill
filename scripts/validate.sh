#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall src tests
python3 -m pytest
python3 -m skill_io_contract check --skill SKILL.md --fixtures fixtures/cases.json --report /tmp/skill-io-contract-report.md
