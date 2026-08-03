from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any


REQUIRED_SECTIONS = {
    "when to use": ("when to use", "use this skill", "trigger"),
    "inputs": ("required inputs", "inputs"),
    "outputs": ("outputs", "report", "artifact"),
    "side effects": ("side-effect", "side effect", "side-effect boundaries", "boundaries"),
    "approvals": ("approval", "approval requirements", "ask for explicit"),
    "examples": ("examples", "example"),
    "validation": ("validation", "validation workflow", "verify", "smoke"),
}

EXTERNAL_ACTION_RE = re.compile(r"\b(?:push|publish|send|external|connector)\b", re.IGNORECASE)
WRITE_ACTION_RE = re.compile(r"\bwrite\b", re.IGNORECASE)
LOCAL_WRITE_RE = re.compile(
    r"\bwrite\b.*(?:\blocal\s+(?:report|file)\b|\breport\s+file\b|--report\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class SkillReport:
    skill_path: Path
    fixture_path: Path | None
    checks: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def score(self) -> str:
        total = len(self.checks)
        passed = sum(1 for check in self.checks if check.passed)
        return f"{passed}/{total}"

    def to_markdown(self) -> str:
        lines = [
            "# Skill IO Contract Report",
            "",
            f"- Skill: `{self.skill_path}`",
            f"- Fixtures: `{self.fixture_path}`" if self.fixture_path else "- Fixtures: not provided",
            f"- Score: {self.score}",
            f"- Result: {'pass' if self.passed else 'fail'}",
            "",
            "## Checks",
            "",
        ]
        for check in self.checks:
            marker = "PASS" if check.passed else "FAIL"
            lines.append(f"- {marker}: {check.name} - {check.detail}")
        lines.append("")
        return "\n".join(lines)


def check_skill(skill_path: Path, fixture_path: Path | None = None) -> SkillReport:
    text = skill_path.read_text(encoding="utf-8")
    checks: list[CheckResult] = []
    checks.extend(_check_skill_text(text))
    if fixture_path:
        checks.extend(_check_fixtures(fixture_path))
    else:
        checks.append(CheckResult("fixtures provided", False, "no fixture JSON was provided"))
    return SkillReport(skill_path=skill_path, fixture_path=fixture_path, checks=tuple(checks))


def _check_skill_text(text: str) -> list[CheckResult]:
    headings = _markdown_headings(text)
    checks: list[CheckResult] = []
    for name, needles in REQUIRED_SECTIONS.items():
        found = any(needle in headings for needle in needles)
        checks.append(CheckResult(f"skill section: {name}", found, "found heading" if found else "missing heading"))
    fenced_blocks = len(re.findall(r"```", text))
    checks.append(CheckResult("examples are fenced", fenced_blocks >= 2, f"found {fenced_blocks} fence markers"))
    return checks


def _markdown_headings(text: str) -> set[str]:
    headings: set[str] = set()
    lines = text.splitlines()
    in_fence = False
    previous: str | None = None

    for line in lines:
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            previous = None
            continue
        if in_fence:
            continue

        atx = re.match(r"^\s{0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if atx:
            headings.add(atx.group(1).strip().lower())
            previous = None
            continue

        if previous and re.match(r"^\s{0,3}(?:=+|-+)\s*$", line):
            headings.add(previous.strip().lower())
            previous = None
            continue

        previous = line if line.strip() else None

    return headings


def _check_fixtures(fixture_path: Path) -> list[CheckResult]:
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [CheckResult("fixture JSON parses", False, str(exc))]

    cases = payload.get("cases") if isinstance(payload, dict) else None
    checks = [CheckResult("fixture JSON parses", True, "valid JSON")]
    checks.append(CheckResult("fixtures contain cases", isinstance(cases, list) and bool(cases), "cases list present" if cases else "cases list missing"))
    if not isinstance(cases, list):
        return checks

    for index, case in enumerate(cases, start=1):
        checks.append(_check_case_schema(index, case))
        checks.append(_check_external_approval(index, case))
    return checks


def _check_case_schema(index: int, case: Any) -> CheckResult:
    errors: list[str] = []
    if not isinstance(case, dict):
        errors.append("case must be an object")
    else:
        _require_non_empty_string(case, "name", errors)
        if not isinstance(case.get("input"), dict):
            errors.append("input must be an object")
        _require_non_empty_string_list(case, "expected_outputs", errors)
        _require_non_empty_string_list(case, "allowed_side_effects", errors)
        _require_non_empty_string(case, "verification", errors)
        if "approval_required" in case and case["approval_required"] != "required":
            errors.append("approval_required must be 'required' when present")

    detail = "all fields have valid types and values" if not errors else "; ".join(errors)
    return CheckResult(f"fixture case {index} schema", not errors, detail)


def _require_non_empty_string(case: dict[str, Any], field: str, errors: list[str]) -> None:
    value = case.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")


def _require_non_empty_string_list(case: dict[str, Any], field: str, errors: list[str]) -> None:
    value = case.get(field)
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty list")
    elif any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{field} entries must be non-empty strings")


def _check_external_approval(index: int, case: Any) -> CheckResult:
    if not isinstance(case, dict):
        return CheckResult(f"fixture case {index} approval boundary", False, "case is not an object")
    allowed_side_effects = case.get("allowed_side_effects")
    if not isinstance(allowed_side_effects, list) or any(not isinstance(item, str) or not item.strip() for item in allowed_side_effects):
        return CheckResult(
            f"fixture case {index} approval boundary",
            False,
            "approval boundary not analyzed: allowed_side_effects must be a list of non-empty strings",
        )
    external = any(_requires_approval(item) for item in allowed_side_effects)
    passed = not external or case.get("approval_required") == "required"
    detail = "approval boundary explicit" if passed else "external side effect needs approval_required"
    return CheckResult(f"fixture case {index} approval boundary", passed, detail)


def _requires_approval(effect: str) -> bool:
    if EXTERNAL_ACTION_RE.search(effect):
        return True
    return bool(WRITE_ACTION_RE.search(effect) and not LOCAL_WRITE_RE.search(effect))
