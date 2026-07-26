# Skill IO Contract

## When to Use

Use this skill when preparing, reviewing, or releasing an agent skill and you need proof that the skill states its input and output contract clearly.

## Required Inputs

- Path to a `SKILL.md` file.
- Optional JSON fixture file containing example cases.
- Optional output path for the generated Markdown report.

## Outputs

- A Markdown report containing a pass/fail result and check score.
- An optional report file when `--report` is provided.

## Side-Effect Boundaries

This skill is read-only for source artifacts. It may write a report file only when the user or automation explicitly provides `--report`.

## Approval Requirements

External account writes, package publishing, repository pushes, or live connector actions are outside this skill. Ask for explicit approval before taking those actions in a separate workflow.

## Examples

```bash
skill-io-contract check --skill SKILL.md --fixtures fixtures/cases.json
skill-io-contract check --skill ../my-skill/SKILL.md --report io-contract.md
```

## Validation Workflow

Run `npm test`, `npm run check`, and `npm run smoke`. Attach the generated report to the release-candidate PR.
