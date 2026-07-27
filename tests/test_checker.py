from pathlib import Path

from skill_io_contract import check_skill


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
