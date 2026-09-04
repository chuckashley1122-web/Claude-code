from __future__ import annotations

from typing import Any

from ..models import Lead


class SourceError(RuntimeError):
    """Raised when a source is unusable — missing key, bad response, etc."""


class Source:
    name = "base"
    #: True when the source touches LinkedIn data and therefore needs the
    #: caller to have a licence/export of their own. Surfaced by `sources`.
    linkedin_data = False

    def available(self) -> tuple[bool, str]:
        """(usable?, human-readable reason). Never raises."""
        return True, "ready"

    def search(self, icp: dict[str, Any], limit: int = 100) -> list[Lead]:
        raise NotImplementedError
