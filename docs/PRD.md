# PRD: Skill IO Contract Skill

## Status

in-progress

## Problem

Agent skills often describe when to run, but omit precise inputs, expected outputs, write boundaries, and fixture expectations. That makes reuse risky and release review slow.

## Users

- Maintainers publishing reusable Codex or OpenClaw skills.
- Agents assembling release-candidate PRs.
- Reviewers checking whether a skill is safe to run in automation.

## MVP

- CLI command that validates one `SKILL.md`.
- Optional JSON fixture validation.
- Markdown report with pass/fail checks and next actions.
- Tests and fixture-backed smoke command.

## Non-Goals

- Running the target skill.
- Publishing or approving skill proposals.
- Contacting live connectors.

## Classification

ship when tests pass and the release-candidate PR contains a generated report.

