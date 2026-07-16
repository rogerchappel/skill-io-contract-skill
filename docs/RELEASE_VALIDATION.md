# Release Validation

## 2026-07-16

- `python3 -m venv .venv`: pass
- `. .venv/bin/activate && python -m pip install -e ".[dev]"`: pass
- `npm test`: pass, 3 tests
- `npm run check`: pass
- `npm run smoke`: pass
- `bash scripts/validate.sh`: pass

## Generated Evidence

The smoke command writes `/tmp/skill-io-contract-report.md` and validates the bundled `SKILL.md` plus `fixtures/cases.json`.

