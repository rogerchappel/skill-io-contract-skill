# Skill IO Contract Skill

Validate that an agent skill has an explicit input/output contract before it is shared or reused.

`skill-io-contract` is a local-first checker for `SKILL.md` files and their fixture cases. It looks for explicit Markdown section headings that agents need in order to route a skill safely, then compares JSON fixture cases against a small contract schema. The default mode is read-only and emits a Markdown report.

## Quickstart

```bash
python -m pip install -e ".[dev]"
skill-io-contract check --skill SKILL.md --fixtures fixtures/cases.json --report report.md
```

Run the bundled smoke check:

```bash
npm run smoke
```

## What It Checks

- Required `SKILL.md` headings for triggers, inputs, outputs, side effects, approvals, examples, and validation. Accepted heading names include the variants demonstrated in the bundled `SKILL.md`; keywords in prose or fenced code do not satisfy this check.
- Fixture cases that name the input, expected output shape, allowed side effects, and verification command.
- Missing approval boundaries when a fixture permits an unqualified write or an
  external action such as pushing, publishing, sending, or using a connector.
  Explicitly local report and file writes do not require approval metadata.
- A concise release-readiness score that can be pasted into a PR.

## Safety Notes

The CLI never writes to the skill or fixture files. It writes only the requested report path. It does not call external services, read credentials, or execute fixture commands.

## Exit Status and Input Errors

The `check` command exits with status `0` when every contract check passes, `1`
when the generated report contains a failed check, and `2` when a CLI input
cannot be read. Input errors are written to stderr without a Python traceback,
for example:

```text
skill-io-contract: error: cannot read --skill 'missing.md': file not found
```

## Limitations

The checker is intentionally conservative. It verifies documentation structure and fixture metadata, not the semantic correctness of the skill itself.
