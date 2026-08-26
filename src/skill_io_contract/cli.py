from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .checker import InputDecodeError, check_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill-io-contract")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check a SKILL.md IO contract")
    source = check.add_mutually_exclusive_group(required=True)
    source.add_argument("--skill", type=Path)
    source.add_argument(
        "--bundled",
        action="store_true",
        help="check the contract and fixtures shipped with this installation",
    )
    check.add_argument("--fixtures", type=Path)
    check.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check":
        if args.bundled:
            resources = _bundled_resources()
            return _run_check(resources / "SKILL.md", resources / "fixtures/cases.json", args.report)
        return _run_check(args.skill, args.fixtures, args.report)
    return 2


def _bundled_resources() -> Path:
    installed = Path(sys.prefix) / "share/skill-io-contract-skill"
    if installed.is_dir():
        return installed
    return Path(__file__).resolve().parents[2]


def _run_check(skill_path: Path, fixture_path: Path | None, report_path: Path | None) -> int:
    try:
        report = check_skill(skill_path, fixture_path)
    except (OSError, InputDecodeError) as exc:
        option, path = _failed_input(exc, skill_path, fixture_path)
        print(
            f"skill-io-contract: error: cannot read --{option} '{path}': {_io_error_detail(exc)}",
            file=sys.stderr,
        )
        return 2
    output = report.to_markdown()
    if report_path:
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(output, encoding="utf-8")
        except OSError as exc:
            print(
                f"skill-io-contract: error: cannot write --report '{report_path}': "
                f"{_io_error_detail(exc, fallback='output is not writable')}",
                file=sys.stderr,
            )
            return 2
    else:
        print(output, end="")
    return 0 if report.passed else 1


def _failed_input(
    exc: OSError | InputDecodeError, skill_path: Path, fixture_path: Path | None
) -> tuple[str, Path]:
    if isinstance(exc, InputDecodeError):
        failed_path = exc.path
    else:
        failed_path = Path(exc.filename) if exc.filename else skill_path
    if fixture_path is not None and failed_path == fixture_path:
        return "fixtures", fixture_path
    return "skill", skill_path


def _io_error_detail(
    exc: OSError | InputDecodeError, fallback: str = "input is not readable"
) -> str:
    if isinstance(exc, InputDecodeError):
        return "invalid UTF-8"
    if isinstance(exc, FileNotFoundError):
        return "file not found"
    if isinstance(exc, PermissionError):
        return "permission denied"
    if isinstance(exc, IsADirectoryError):
        return "is a directory"
    return fallback
