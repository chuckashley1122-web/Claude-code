"""Print SET or MISSING for every environment variable this pilot reads. Never prints a value."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402


def env_report(environ: dict | None = None) -> list[tuple[str, str]]:
    env = os.environ if environ is None else environ
    return [(name, "SET" if (env.get(name) or "").strip() else "MISSING") for name in config.ENV_VARS]


def main(environ: dict | None = None) -> int:
    for name, state in env_report(environ):
        print(f"{name}: {state}")
    env_file = config.PROJECT_ROOT / ".env"
    print(f".env file: {'PRESENT (must not be committed)' if env_file.exists() else 'absent'}")
    print("No values are printed. Unset variables fall back to the safe defaults in config.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
