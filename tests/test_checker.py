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


@pytest.mark.parametrize(
    ("missing_option", "expected_path"),
    [
        ("skill", "missing-skill.md"),
        ("fixtures", "missing-fixtures.json"),
    ],
)
def test_cli_reports_missing_input_without_traceback(tmp_path, capsys, missing_option, expected_path):
    skill = tmp_path / "skill.md"
    skill.write_text(Path("SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
    fixtures = tmp_path / "fixtures.json"
    fixtures.write_text(VALID_FIXTURES.read_text(encoding="utf-8"), encoding="utf-8")
    missing = tmp_path / expected_path

    if missing_option == "skill":
        skill = missing
    else:
        fixtures = missing

    exit_code = main(["check", "--skill", str(skill), "--fixtures", str(fixtures)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == f"skill-io-contract: error: cannot read --{missing_option} '{missing}': file not found\n"
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("unreadable_option", ["skill", "fixtures"])
def test_cli_reports_unreadable_input_without_traceback(tmp_path, capsys, unreadable_option):
    skill = Path("SKILL.md")
    fixtures = VALID_FIXTURES
    unreadable = tmp_path / f"{unreadable_option}-directory"
    unreadable.mkdir()

    if unreadable_option == "skill":
        skill = unreadable
    else:
        fixtures = unreadable

    exit_code = main(["check", "--skill", str(skill), "--fixtures", str(fixtures)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == f"skill-io-contract: error: cannot read --{unreadable_option} '{unreadable}': is a directory\n"
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("invalid_option", ["skill", "fixtures"])
def test_cli_reports_invalid_utf8_input_without_traceback(tmp_path, capsys, invalid_option):
    skill = tmp_path / "skill.md"
    skill.write_text(Path("SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
    fixtures = tmp_path / "fixtures.json"
    fixtures.write_text(VALID_FIXTURES.read_text(encoding="utf-8"), encoding="utf-8")
    invalid = tmp_path / f"invalid-{invalid_option}"
    invalid.write_bytes(b"\xff")

    if invalid_option == "skill":
        skill = invalid
    else:
        fixtures = invalid

    exit_code = main(["check", "--skill", str(skill), "--fixtures", str(fixtures)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == (
        f"skill-io-contract: error: cannot read --{invalid_option} '{invalid}': invalid UTF-8\n"
    )
    assert "Traceback" not in captured.err


def test_cli_reports_directory_used_as_report_without_traceback(tmp_path, capsys):
    report_path = tmp_path / "report-directory"
    report_path.mkdir()

    exit_code = main(
        ["check", "--skill", "SKILL.md", "--fixtures", str(VALID_FIXTURES), "--report", str(report_path)]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == f"skill-io-contract: error: cannot write --report '{report_path}': is a directory\n"
    assert "Traceback" not in captured.err


def test_cli_reports_report_parent_creation_failure_without_traceback(tmp_path, capsys, monkeypatch):
    report_path = tmp_path / "missing-parent" / "report.md"
    original_mkdir = Path.mkdir

    def fail_for_report_parent(path, *args, **kwargs):
        if path == report_path.parent:
            raise PermissionError(13, "Permission denied", path)
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_for_report_parent)

    exit_code = main(
        ["check", "--skill", "SKILL.md", "--fixtures", str(VALID_FIXTURES), "--report", str(report_path)]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == f"skill-io-contract: error: cannot write --report '{report_path}': permission denied\n"
    assert "Traceback" not in captured.err


def test_cli_stdout_and_file_reports_are_identical(tmp_path, capsys):
    args = ["check", "--skill", "SKILL.md", "--fixtures", str(VALID_FIXTURES)]

    assert main(args) == 0
    stdout_report = capsys.readouterr().out

    report_path = tmp_path / "reports" / "contract.md"
    assert main([*args, "--report", str(report_path)]) == 0
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""
    assert report_path.read_text(encoding="utf-8") == stdout_report


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
        "pushing branch",
        "pushed branch",
        "publish package",
        "publishing package",
        "published package",
        "send message",
        "sending message",
        "sent message",
        "call external API",
        "communicate externally",
        "invoke connector action",
        "invoke connectors",
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


@pytest.mark.parametrize(
    "side_effect",
    [
        "delete a GitHub release artifact",
        "remove a GitHub release",
        "create a repository issue",
        "update a pull request",
        "edit an external account",
    ],
)
def test_external_resource_mutations_require_approval(tmp_path, side_effect):
    fixtures = tmp_path / "external-mutation.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "external mutation",
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


@pytest.mark.parametrize(
    "side_effect",
    [
        "delete a local report file",
        "remove a local cache file",
        "read a GitHub release artifact",
        "list repository issues",
        "inspect a pull request",
    ],
)
def test_local_mutations_and_external_reads_do_not_require_approval(tmp_path, side_effect):
    fixtures = tmp_path / "safe-actions.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "safe action",
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


@pytest.mark.parametrize(
    "side_effect",
    [
        "sendable report",
        "sender metadata",
        "publisher metadata",
        "pushbutton input",
        "externality score",
        "connectorized workflow",
    ],
)
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


@pytest.mark.parametrize(
    "side_effect",
    [
        "push branch",
        "pushing branch",
        "pushed branch",
        "publish package",
        "publishing package",
        "published package",
        "send message",
        "sending message",
        "sent message",
        "call external API",
        "communicate externally",
        "invoke connector action",
        "invoke connectors",
    ],
)
def test_external_action_forms_pass_with_required_approval(tmp_path, side_effect):
    fixtures = tmp_path / "approval-present.json"
    fixtures.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "approved external effect",
                        "input": {},
                        "expected_outputs": ["result"],
                        "allowed_side_effects": [side_effect],
                        "approval_required": "required",
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


@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ("```markdown", "~~~"),
        ("~~~~markdown", "~~~"),
        ("```markdown", ""),
    ],
)
def test_mismatched_or_unmatched_fences_hide_headings_and_do_not_count_as_examples(
    tmp_path, opening, closing
):
    skill = tmp_path / "SKILL.md"
    skill.write_text(f"# Skill\n\n{opening}\n## Inputs\n{closing}\n", encoding="utf-8")

    report = check_skill(skill, VALID_FIXTURES)

    inputs = next(check for check in report.checks if check.name == "skill section: inputs")
    examples = next(check for check in report.checks if check.name == "examples are fenced")
    assert not inputs.passed
    assert not examples.passed
    assert examples.detail == "found 0 fenced blocks"


@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ("```text", "```"),
        ("~~~text", "~~~"),
        ("```text", "````"),
        ("~~~text", "~~~~"),
    ],
)
def test_matching_fences_count_as_examples_and_reveal_following_headings(
    tmp_path, opening, closing
):
    skill = tmp_path / "SKILL.md"
    skill.write_text(f"# Skill\n\n{opening}\n## Hidden\n{closing}\n## Inputs\n", encoding="utf-8")

    report = check_skill(skill, VALID_FIXTURES)

    inputs = next(check for check in report.checks if check.name == "skill section: inputs")
    examples = next(check for check in report.checks if check.name == "examples are fenced")
    assert inputs.passed
    assert examples.passed
    assert examples.detail == "found 1 fenced blocks"
