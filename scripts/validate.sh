#!/usr/bin/env bash
set -euo pipefail

python -m compileall src tests
python -m pytest
python -m skill_io_contract check --skill SKILL.md --fixtures fixtures/cases.json --report /tmp/skill-io-contract-report.md

