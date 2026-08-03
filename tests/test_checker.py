from pathlib import Path
import json

import pytest

from skill_io_contract import check_skill
from skill_io_contract.cli import main


VALID_FIXTURES = Path("fixtures/cases.json")


def test_bundled_skill_passes_contract():
    report = check_skill(Path("SKILL.md"), VALID_FIXTURES)
    assert report.passed, report.to_markdown()


def test_report_marks_missing_fixtures():
    report = check_skill(Path("SKILL.md"))
    assert not report.passed
    assert "fixtures provided" in report.to_markdown()


def test_external_side_effects_require_approval():
    report = check_skill(Path("SKILL.md"), Path("fixtures/bad-cases.json"))
    assert not report.passed
    assert "external side effect needs approval_required" in report.to_markdown()


def test_fixture_fields_require_documented_types_and_values(tmp_path):
    fixtures = tmp_path / "invalid-fields.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": " ",
                        "input": [],
                        "expected_outputs": [""],
                        "allowed_side_effects": "push",
                        "verification": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = check_skill(Path("SKILL.md"), fixtures)
    markdown = report.to_markdown()

    assert not report.passed
    assert "name must be a non-empty string" in markdown
    assert "input must be an object" in markdown
    assert "expected_outputs entries must be non-empty strings" in markdown
    assert "allowed_side_effects must be a non-empty list" in markdown
    assert "verification must be a non-empty string" in markdown
    assert "approval boundary not analyzed" in markdown


def test_external_push_with_false_approval_fails_cli(tmp_path, capsys):
    fixtures = tmp_path / "false-approval.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "external push",
                        "input": {},
                        "expected_outputs": ["branch"],
                        "allowed_side_effects": ["push branch to external repo"],
                        "approval_required": False,
                        "verification": "git status --short",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["check", "--skill", "SKILL.md", "--fixtures", str(fixtures)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "approval_required must be 'required' when present" in output
    assert "external side effect needs approval_required" in output


def test_valid_fixture_shapes_pass(tmp_path):
    fixtures = tmp_path / "valid.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "local check",
                        "input": {},
                        "expected_outputs": ["report"],
                        "allowed_side_effects": ["none"],
                        "verification": "python3 -m pytest",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = check_skill(Path("SKILL.md"), fixtures)

    assert report.passed, report.to_markdown()


@pytest.mark.parametrize(
    "side_effect",
    [
        "write local report",
        "write local file",
        "write report file",
        "write report when --report is provided",
    ],
)
def test_explicit_local_writes_do_not_require_approval(tmp_path, side_effect):
    fixtures = tmp_path / "local-write.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "local output",
                        "input": {},
                        "expected_outputs": ["report"],
                        "allowed_side_effects": [side_effect],
                        "verification": "test -f report.md",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = check_skill(Path("SKILL.md"), fixtures)

    assert report.passed, report.to_markdown()


@pytest.mark.parametrize(
    "side_effect",
    [
        "write",
        "write configuration",
        "push branch",
        "publish package",
        "send message",
        "call external API",
        "invoke connector action",
    ],
)
def test_unqualified_writes_and_external_actions_require_approval(tmp_path, side_effect):
    fixtures = tmp_path / "approval-required.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "effect requiring approval",
                        "input": {},
                        "expected_outputs": ["result"],
                        "allowed_side_effects": [side_effect],
                        "verification": "true",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = check_skill(Path("SKILL.md"), fixtures)

    assert not report.passed
    assert "external side effect needs approval_required" in report.to_markdown()


@pytest.mark.parametrize("side_effect", ["sendable report", "publisher metadata", "pushbutton input", "externality score"])
def test_external_action_keywords_require_word_boundaries(tmp_path, side_effect):
    fixtures = tmp_path / "boundary.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "keyword substring",
                        "input": {},
                        "expected_outputs": ["result"],
                        "allowed_side_effects": [side_effect],
                        "verification": "true",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = check_skill(Path("SKILL.md"), fixtures)

    assert report.passed, report.to_markdown()


def test_keywords_in_prose_and_code_fences_do_not_count_as_sections(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """# Skill

This prose mentions when to use, inputs, outputs, side effects, approval,
examples, and validation without documenting their contracts.

```markdown
## Required Inputs
## Outputs
## Side-Effect Boundaries
## Approval Requirements
## Examples
## Validation Workflow
```
""",
        encoding="utf-8",
    )

    report = check_skill(skill, VALID_FIXTURES)

    section_checks = [check for check in report.checks if check.name.startswith("skill section:")]
    assert section_checks
    assert all(not check.passed for check in section_checks)
    assert all(check.detail == "missing heading" for check in section_checks)


def test_absent_heading_has_clear_failure(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """# Skill

## When to Use
## Required Inputs
## Outputs
## Side-Effect Boundaries
## Approval Requirements
## Examples

```text
example
```
""",
        encoding="utf-8",
    )

    report = check_skill(skill, VALID_FIXTURES)

    validation = next(check for check in report.checks if check.name == "skill section: validation")
    assert not validation.passed
    assert validation.detail == "missing heading"


def test_valid_heading_variants_are_accepted(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """# Skill

Trigger
-------
### Inputs
## Artifact
Boundaries
----------
### Ask for Explicit
## Example
Smoke
-----

```text
example
```
""",
        encoding="utf-8",
    )

    report = check_skill(skill, VALID_FIXTURES)

    assert report.passed, report.to_markdown()
