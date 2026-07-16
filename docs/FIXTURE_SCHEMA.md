# Fixture Schema

Fixture files are JSON objects with a `cases` array.

Each case should include:

- `name`: human-readable scenario name.
- `input`: object describing files or parameters supplied to the skill.
- `expected_outputs`: list of artifacts or response shapes.
- `allowed_side_effects`: list of permitted local writes or `none`.
- `approval_required`: `required` when an allowed side effect can affect external systems.
- `verification`: command a maintainer can run locally.

