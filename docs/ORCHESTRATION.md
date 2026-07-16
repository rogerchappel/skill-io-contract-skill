# Orchestration

## Inputs

- `SKILL.md`
- Optional `fixtures/cases.json`

## Steps

1. Run `skill-io-contract check --skill SKILL.md --fixtures fixtures/cases.json --report reports/io-contract.md`.
2. Review failed checks and update the skill or fixtures.
3. Re-run the command before opening a release-candidate PR.

## Outputs

- Markdown readiness report.
- Exit code `0` when all required checks pass.
- Exit code `1` when one or more required checks fail.

## Boundaries

The workflow is local-only. It does not execute fixture commands or mutate the target skill.

