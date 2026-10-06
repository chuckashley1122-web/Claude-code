"""A tiny parser for the flat YAML subset used by ``config/pricing.yaml``.

Supported (and nothing else, by design):

    # comment
    key: scalar
    listkey:
      - field: scalar
        field: scalar
      - field: scalar

Scalars: ``null``/``~``, ``true``/``false``, integers, floats, and single- or
double-quoted or bare strings. Anything outside this subset raises
:class:`YamlLiteError` so a malformed price table fails closed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_INT = re.compile(r"^-?\d+$")
_FLOAT = re.compile(r"^-?\d+\.\d+$")
_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s+(.*))?$")


class YamlLiteError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    out, quote = [], None
    for ch in line:
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def parse_scalar(text: str) -> Any:
    t = text.strip()
    if t in ("null", "~", ""):
        return None
    if t == "true":
        return True
    if t == "false":
        return False
    if _INT.match(t):
        return int(t)
    if _FLOAT.match(t):
        return float(t)
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    if t[0] in "[{&*!|>":
        raise YamlLiteError(f"unsupported YAML construct: {t!r}")
    return t


def loads(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list: list | None = None
    current_item: dict | None = None
    item_indent = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise YamlLiteError(f"line {lineno}: tabs are not allowed")
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if indent == 0:
            m = _KEY.match(body)
            if not m:
                raise YamlLiteError(f"line {lineno}: expected 'key: value'")
            key, value = m.group(1), m.group(2)
            if key in data:
                raise YamlLiteError(f"line {lineno}: duplicate key {key!r}")
            if value is None or value == "":
                data[key] = current_list = []
                current_item = None
            else:
                data[key] = parse_scalar(value)
                current_list = None
            continue
        if current_list is None:
            raise YamlLiteError(f"line {lineno}: indented line outside a list")
        if body.startswith("- "):
            current_item = {}
            current_list.append(current_item)
            item_indent = indent + 2
            body = body[2:].strip()
        elif current_item is None or indent != item_indent:
            raise YamlLiteError(f"line {lineno}: bad indentation")
        m = _KEY.match(body)
        if not m:
            raise YamlLiteError(f"line {lineno}: expected 'field: value' in list item")
        field, value = m.group(1), m.group(2)
        if field in current_item:
            raise YamlLiteError(f"line {lineno}: duplicate field {field!r}")
        current_item[field] = parse_scalar(value or "")
    return data


def load(path: Path) -> dict[str, Any]:
    return loads(Path(path).read_text(encoding="utf-8"))
