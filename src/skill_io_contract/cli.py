from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .checker import check_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill-io-contract")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check a SKILL.md IO contract")
    check.add_argument("--skill", required=True, type=Path)
    check.add_argument("--fixtures", type=Path)
    check.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check":
        try:
            report = check_skill(args.skill, args.fixtures)
        except OSError as exc:
            option, path = _failed_input(exc, args.skill, args.fixtures)
            print(
                f"skill-io-contract: error: cannot read --{option} '{path}': {_io_error_detail(exc)}",
                file=sys.stderr,
            )
            return 2
        output = report.to_markdown()
        if args.report:
            try:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(output, encoding="utf-8")
            except OSError as exc:
                print(
                    f"skill-io-contract: error: cannot write --report '{args.report}': "
                    f"{_io_error_detail(exc, fallback='output is not writable')}",
                    file=sys.stderr,
                )
                return 2
        else:
            print(output, end="")
        return 0 if report.passed else 1
    return 2


def _failed_input(exc: OSError, skill_path: Path, fixture_path: Path | None) -> tuple[str, Path]:
    failed_path = Path(exc.filename) if exc.filename else skill_path
    if fixture_path is not None and failed_path == fixture_path:
        return "fixtures", fixture_path
    return "skill", skill_path


def _io_error_detail(exc: OSError, fallback: str = "input is not readable") -> str:
    if isinstance(exc, FileNotFoundError):
        return "file not found"
    if isinstance(exc, PermissionError):
        return "permission denied"
    if isinstance(exc, IsADirectoryError):
        return "is a directory"
    return fallback
