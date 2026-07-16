from __future__ import annotations

import argparse
from pathlib import Path

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
        report = check_skill(args.skill, args.fixtures)
        output = report.to_markdown()
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(output, encoding="utf-8")
        else:
            print(output)
        return 0 if report.passed else 1
    return 2

