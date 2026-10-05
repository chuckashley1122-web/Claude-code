"""Shared test helpers: put the build root on sys.path and build into temp roots."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_temp_root() -> Path:
    """A throwaway build root holding copies of the committed config and env template."""
    tmp = Path(tempfile.mkdtemp(prefix="caj-ht-test-"))
    (tmp / "config").mkdir()
    shutil.copy2(ROOT / "config" / "build_config.json", tmp / "config" / "build_config.json")
    shutil.copy2(ROOT / ".env.example", tmp / ".env.example")
    return tmp


def built_temp_root() -> Path:
    from tools import build_all
    tmp = make_temp_root()
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        status = build_all.run(tmp)
    if status != 0:
        raise AssertionError(f"build_all.run returned {status} for {tmp}")
    return tmp
