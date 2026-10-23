# Release Validation

Run the complete local release-readiness check with:

```sh
python3 -m pip install -e '.[dev]' build
python3 - <<'PY'
import tomllib
from pathlib import Path

config = tomllib.loads(Path("pyproject.toml").read_text())
for command in config["tool"]["skill-io-contract"]["release-check"]["commands"]:
    print(f"$ {command}", flush=True)
    import subprocess
    subprocess.run(command, shell=True, check=True)
PY
```

This compiles and tests the project, runs the bundled skill/fixture smoke check,
and builds a wheel locally. It does not upload or publish any distribution.

## 2026-07-16

- `python3 -m venv .venv`: pass
- `. .venv/bin/activate && python -m pip install -e ".[dev]"`: pass
- `npm test`: pass, 3 tests
- `npm run check`: pass
- `npm run smoke`: pass
- `bash scripts/validate.sh`: pass

## Generated Evidence

The smoke command writes `/tmp/skill-io-contract-report.md` and validates the bundled `SKILL.md` plus `fixtures/cases.json`.

