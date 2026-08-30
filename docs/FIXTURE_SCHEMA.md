# Fixture Schema

Fixture files are JSON objects with a `cases` array.

Each case should include:

- `name`: non-empty human-readable scenario name.
- `input`: object describing files or parameters supplied to the skill (an empty object is valid).
- `expected_outputs`: non-empty list of non-empty artifact or response-shape strings.
- `allowed_side_effects`: non-empty list of non-empty permitted-effect strings; use `["none"]` when there are none.
- `approval_required`: `required` when an allowed side effect can affect external systems.
  The checker treats common forms of `push` (`push`, `pushing`, `pushed`),
  `publish` (`publish`, `publishing`, `published`), and `send` (`send`, `sending`,
  `sent`) as whole-word external actions. External resources and connectors require
  an affirmative mutating action in the same clause. Negated actions using `not`,
  `never`, `without`, or common contractions (for example, `does not publish`,
  `never updates a pull request`, and `won't send`) are not mutations. An affirmative
  action in the same or a separate clause still requires approval. Unrelated substrings such
  as `publisher` and `pushbutton` are not indicators. Unqualified `write`, `writes`,
  `writing`, `wrote`, and `written` forms also require approval; explicitly local
  forms such as `write local report`, `writing a local file`, `write report file`,
  and `write report when --report is provided` do not. Analysis is clause-scoped:
  a separate read-only GitHub clause does not turn a local mutation into an external
  one, while an external write or another unqualified write still requires
  `approval_required`.
- `verification`: non-empty command a maintainer can run locally.

The checker reports all field-shape errors for each case. Approval analysis runs only
when `allowed_side_effects` is a validated list; otherwise the approval-boundary check
fails with a diagnostic instead of interpreting the invalid value.
