from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from zipfile import ZipFile


SDIST_SUFFIXES = (
    "/SKILL.md",
    "/fixtures/cases.json",
)
WHEEL_SUFFIXES = (
    "share/skill-io-contract-skill/SKILL.md",
    "share/skill-io-contract-skill/fixtures/cases.json",
)


def require_members(names: list[str], archive: Path, suffixes: tuple[str, ...]) -> None:
    for suffix in suffixes:
        if not any(name.endswith(suffix) for name in names):
            raise SystemExit(f"{archive}: missing required artifact {suffix}")


def main() -> None:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    sdists = sorted(dist.glob("*.tar.gz"))
    wheels = sorted(dist.glob("*.whl"))
    if len(sdists) != 1 or len(wheels) != 1:
        raise SystemExit(f"expected one sdist and one wheel in {dist}")

    with tarfile.open(sdists[0], "r:gz") as archive:
        require_members(archive.getnames(), sdists[0], SDIST_SUFFIXES)
    with ZipFile(wheels[0]) as archive:
        require_members(archive.namelist(), wheels[0], WHEEL_SUFFIXES)

    with tempfile.TemporaryDirectory() as directory:
        environment = Path(directory) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        command = environment / ("Scripts/skill-io-contract.exe" if sys.platform == "win32" else "bin/skill-io-contract")
        subprocess.run([str(python), "-m", "pip", "install", "--no-deps", str(wheels[0].resolve())], check=True)
        subprocess.run([str(command), "check", "--bundled"], check=True)


if __name__ == "__main__":
    main()
