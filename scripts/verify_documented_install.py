from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


INSTALL_COMMAND = (
    "python -m pip install "
    '"skill-io-contract-skill @ '
    'git+https://github.com/rogerchappel/skill-io-contract-skill.git"'
)
INSTALL_URL = "git+https://github.com/rogerchappel/skill-io-contract-skill.git"


def main() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    if INSTALL_COMMAND not in readme:
        raise SystemExit("README Quickstart does not contain the supported GitHub install command")
    if "not yet published to PyPI" not in readme:
        raise SystemExit("README does not state the current PyPI publication status")

    with tempfile.TemporaryDirectory() as directory:
        environment = Path(directory) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        command = environment / (
            "Scripts/skill-io-contract.exe" if sys.platform == "win32" else "bin/skill-io-contract"
        )
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", INSTALL_URL],
            check=True,
        )
        subprocess.run([str(command), "check", "--bundled"], check=True)


if __name__ == "__main__":
    main()
