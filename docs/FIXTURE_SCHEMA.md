# Fixture Schema

Fixture files are JSON objects with a `cases` array.

Each case should include:

- `name`: non-empty human-readable scenario name.
- `input`: object describing files or parameters supplied to the skill (an empty object is valid).
- `expected_outputs`: non-empty list of non-empty artifact or response-shape strings.
- `allowed_side_effects`: non-empty list of non-empty permitted-effect strings; use `["none"]` when there are none.
- `approval_required`: `required` when an allowed side effect can affect external systems.
- `verification`: non-empty command a maintainer can run locally.

The checker reports all field-shape errors for each case. Approval analysis runs only
when `allowed_side_effects` is a validated list; otherwise the approval-boundary check
fails with a diagnostic instead of interpreting the invalid value.
