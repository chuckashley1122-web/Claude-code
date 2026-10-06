"""Environment loading with fail-closed behaviour.

Rules:
- Values come from ``os.environ`` (optionally merged with a local ``.env`` file,
  which is gitignored). Nothing here hardcodes a secret.
- Values are never logged; only ``SET`` / ``MISSING`` is ever reported.
- ``DRY_RUN`` defaults to true. If it is false, the run is refused unless a
  human has also set ``ALLOW_LIVE=1``. Even then, every live adapter in
  ``adapters/`` refuses to call out (see ``adapters.base.LiveCallBlocked``).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, TextIO

from config import constants

ROOT = Path(__file__).resolve().parents[1]


class MissingCredential(RuntimeError):
    """Raised when a credential is required but absent. Human action required."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"BLOCKED: credential {name} is MISSING. Human action required: "
            f"obtain it through the approval process in docs/COST-AND-APPROVALS.md "
            f"and set it in a local .env (never commit it)."
        )


class LiveModeRefused(SystemExit):
    """Raised (as a non-zero SystemExit) when DRY_RUN=false without ALLOW_LIVE=1."""


@dataclass(frozen=True)
class EnvVar:
    name: str
    used_by: str
    gate: str
    approval_required: bool


# Exactly the env var names from spec section 6.
ENV_VARS: tuple[EnvVar, ...] = (
    EnvVar("DRY_RUN", "settings.py", "default true; false refuses to run without ALLOW_LIVE=1", False),
    EnvVar("ALLOW_LIVE", "settings.py", "human-only", True),
    EnvVar("OPENAI_API_KEY", "01-08", "paid - approval required", True),
    EnvVar("N8N_BASE_URL", "import/ops", "account creation - approval required", True),
    EnvVar("N8N_API_KEY", "import/ops", "account creation - approval required", True),
    EnvVar("VAPI_API_KEY", "01", "paid + number purchase - approval required", True),
    EnvVar("TWILIO_ACCOUNT_SID", "01", "paid + number purchase - approval required", True),
    EnvVar("TWILIO_AUTH_TOKEN", "01", "paid + number purchase - approval required", True),
    EnvVar("APIFY_TOKEN", "02,03,04", "paid + scraping ToS review - approval required", True),
    EnvVar("HEYGEN_API_KEY", "03,04,05,08", "paid - approval required", True),
    EnvVar("ELEVENLABS_API_KEY", "03,04,05,08", "paid - approval required", True),
    EnvVar("CREATOMATE_API_KEY", "03,04,05,08", "paid - approval required", True),
    EnvVar("AYRSHARE_API_KEY", "04,05,08", "paid + platform TOS - approval required", True),
    EnvVar("GOOGLE_CLIENT_ID", "01,07", "OAuth grant - human", True),
    EnvVar("GOOGLE_CLIENT_SECRET", "01,07", "OAuth grant - human", True),
    EnvVar("GOOGLE_REFRESH_TOKEN", "01,07", "OAuth grant - human", True),
    EnvVar("SMTP_HOST", "02", "sending identity - human", True),
    EnvVar("SMTP_PORT", "02", "sending identity - human", True),
    EnvVar("SMTP_USER", "02", "sending identity - human", True),
    EnvVar("SMTP_PASS", "02", "sending identity - human", True),
    EnvVar("HUBSPOT_TOKEN", "01,02", "free tier OK, account needed", True),
    EnvVar("SUPABASE_URL", "02,03,05,07", "account needed", True),
    EnvVar("SUPABASE_SERVICE_KEY", "02,03,05,07", "account needed", True),
    EnvVar("AIRTABLE_TOKEN", "02,03,05,07", "account needed", True),
    EnvVar("PINECONE_API_KEY", "06", "paid tier for vector - approval required", True),
    EnvVar("SLACK_WEBHOOK_URL", "01,06,08", "human-owned workspace", True),
    EnvVar("HUNTER_API_KEY", "02,04", "paid - approval required", True),
    EnvVar("INSTANTLY_API_KEY", "02,04", "paid - approval required", True),
    EnvVar("PERPLEXITY_API_KEY", "02,04", "paid - approval required", True),
    EnvVar("GHL_LOCATION_ID", "reference only", "must equal the build location id in config/constants.py; GHL is UI-only", False),
    EnvVar("WEBHOOK_SHARED_SECRET", "internal HMAC", "generated locally, never committed", False),
)

ENV_VAR_NAMES: tuple[str, ...] = tuple(v.name for v in ENV_VARS)

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def parse_bool(value: Optional[str], default: bool) -> bool:
    """Parse a boolean env value. Unknown/blank values fall back to ``default``."""
    if value is None:
        return default
    v = value.strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    return default


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal ``KEY=VALUE`` .env file. Comments and blanks ignored."""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key.strip()] = value
    return result


def load_environ(environ: Optional[Mapping[str, str]] = None,
                 env_file: Optional[Path] = None) -> dict[str, str]:
    """Merge a .env file (lower priority) with the process environment."""
    merged: dict[str, str] = {}
    if env_file is None:
        env_file = ROOT / ".env"
    merged.update(parse_env_file(env_file))
    merged.update(dict(os.environ if environ is None else environ))
    return merged


@dataclass(frozen=True)
class Settings:
    dry_run: bool
    allow_live: bool
    env: Mapping[str, str] = field(repr=False)

    def get(self, name: str) -> Optional[str]:
        value = self.env.get(name)
        return value if value else None

    def status(self, name: str) -> str:
        return "SET" if self.get(name) else "MISSING"


def load_settings(environ: Optional[Mapping[str, str]] = None,
                  env_file: Optional[Path] = None) -> Settings:
    env = load_environ(environ, env_file)
    return Settings(
        dry_run=parse_bool(env.get("DRY_RUN"), constants.DRY_RUN),
        allow_live=env.get("ALLOW_LIVE", "").strip() == "1",
        env=env,
    )


def env_status(settings: Settings, names: tuple[str, ...] = ENV_VAR_NAMES) -> dict[str, str]:
    """Return ``{name: "SET"|"MISSING"}``. Never returns values."""
    return {name: settings.status(name) for name in names}


def require_credential(name: str, settings: Optional[Settings] = None) -> str:
    """Return a credential value or raise :class:`MissingCredential` (fail closed)."""
    settings = settings or load_settings()
    value = settings.get(name)
    if not value:
        raise MissingCredential(name)
    return value


def ghl_location_mismatch(settings: Settings) -> Optional[str]:
    """If GHL_LOCATION_ID is set but differs (case-sensitive), return a message."""
    value = settings.get("GHL_LOCATION_ID")
    if value is not None and value != constants.GHL_BUILD_LOCATION_ID:
        return ("GHL_LOCATION_ID does not match the locked build location id "
                "(comparison is case-sensitive). GHL is reference-only.")
    return None


REFUSAL_BANNER = (
    "=" * 64 + "\n"
    "REFUSED: DRY_RUN is false but ALLOW_LIVE=1 is not set.\n"
    "Live operation requires explicit human approval. No call was made.\n"
    "See docs/COST-AND-APPROVALS.md.\n" + "=" * 64
)


def enforce_run_mode(settings: Settings, stream: TextIO | None = None) -> None:
    """Exit non-zero if live mode is requested without ALLOW_LIVE=1."""
    if not settings.dry_run and not settings.allow_live:
        print(REFUSAL_BANNER, file=stream or sys.stderr)
        raise LiveModeRefused(2)
