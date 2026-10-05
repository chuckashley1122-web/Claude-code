"""Small shared helpers for the generators (no business logic lives here)."""
from __future__ import annotations

import html
from pathlib import Path
import sys

BUILD_ROOT = Path(__file__).resolve().parents[1]
if str(BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILD_ROOT))

from config import constants as C  # noqa: E402

OFFER_VERSION = "CAJ-HT-HVAC-OFFER-v0.1-draft"
PROOF_BLOCK_START = "<!-- DO-NOT-USE-AS-PROOF:START -->"
PROOF_BLOCK_END = "<!-- DO-NOT-USE-AS-PROOF:END -->"


def prefix(config: dict) -> str:
    return C.OBJECT_PREFIX_MAP[config.get("build_mode", C.BUILD_MODE)]


def niche_label(config: dict) -> str:
    return "real estate" if config.get("build_mode") == "SOURCE_REAL_ESTATE" else "HVAC"


def md_table(headers: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/") for c in r) + " |")
    return out


def proof_block(lines: list[str]) -> list[str]:
    return [PROOF_BLOCK_START, "**Do not use as proof.** Source claims below are unverified and are not CA-J results.", ""] \
        + lines + [PROOF_BLOCK_END]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def html_page(title: str, sections: list[tuple[str, str]], note: str) -> str:
    """Self-contained static HTML: inline CSS only, no scripts, no external resources."""
    body = []
    for heading, inner in sections:
        body.append(f"<section>\n<h2>{esc(heading)}</h2>\n{inner}\n</section>")
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex, nofollow\">\n"
        f"<title>{esc(title)}</title>\n"
        "<style>body{font-family:Arial,Helvetica,sans-serif;color:#000;background:#fff;max-width:760px;margin:2rem auto;"
        "padding:0 1rem;line-height:1.5}h1,h2{color:#000}section{border-top:1px solid #ccc;padding-top:.5rem}"
        ".draft{border:2px dashed #000;padding:.5rem}.slot{background:#f2f2f2;padding:1rem}footer{font-size:.8rem;margin-top:2rem}</style>\n"
        "</head>\n<body>\n"
        f"<p class=\"draft\">{esc(note)}</p>\n<h1>{esc(title)}</h1>\n"
        + "\n".join(body)
        + f"\n<footer>{esc(C.BRAND_NAME)} &middot; {esc(C.OWNER_NAME)} &middot; {esc(C.OWNER_PHONE)} &middot; "
        f"<a href=\"mailto:{esc(C.OWNER_EMAIL)}\">{esc(C.OWNER_EMAIL)}</a></footer>\n</body>\n</html>\n"
    )


def ul(items: list[str]) -> str:
    return "<ul>\n" + "\n".join(f"<li>{esc(i)}</li>" for i in items) + "\n</ul>"
