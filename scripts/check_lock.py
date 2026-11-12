"""Fail if any installed package is missing from requirements.lock or differs from its pin.

pip's -c only constrains packages it's told about, so a new transitive dependency
would otherwise install at whatever version is latest. Run via `make check-lock`.
"""

import re
import sys
from importlib.metadata import distributions
from pathlib import Path

LOCK = Path(__file__).resolve().parent.parent / "requirements.lock"
# Installer tooling that lives in every venv and isn't an app dependency.
IGNORED = {"pip", "setuptools", "wheel"}


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> int:
    pins = {}
    for line in LOCK.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            name, _, version = line.partition("==")
            pins[normalize(name)] = version.strip()

    problems = []
    for dist in distributions():
        name = normalize(dist.metadata["Name"])
        if name in IGNORED:
            continue
        if name not in pins:
            problems.append(f"{name}=={dist.version} is installed but not pinned")
        elif pins[name] != dist.version:
            problems.append(f"{name}=={dist.version} is installed but pinned to {pins[name]}")

    for problem in sorted(problems):
        print(problem, file=sys.stderr)
    if problems:
        print(f"Update {LOCK.name} (see its header).", file=sys.stderr)
        return 1
    print(f"All installed packages match {LOCK.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
