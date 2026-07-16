from pathlib import Path

from skill_io_contract import check_skill


def test_bundled_skill_passes_contract():
    report = check_skill(Path("SKILL.md"), Path("fixtures/cases.json"))
    assert report.passed, report.to_markdown()


def test_report_marks_missing_fixtures():
    report = check_skill(Path("SKILL.md"))
    assert not report.passed
    assert "fixtures provided" in report.to_markdown()

