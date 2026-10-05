"""A deliberately small YAML-subset parser (stdlib only).

Supported:
    # comments (full-line, and trailing after whitespace on unquoted values)
    key: scalar                      top-level scalars
    key:                             top-level list of flat mappings:
      - name: x
        amount: 0
Scalars: int, float, true/false, null/~, 'single' or "double" quoted strings,
and bare strings. Anything else (nested mappings, flow style, anchors,
multi-line strings, tabs) raises MiniYamlError rather than being guessed at.
"""
from __future__ import annotations

import re


class MiniYamlError(ValueError):
    pass


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s+(.*))?$")


def parse_scalar(raw: str):
    s = raw.strip()
    if not s:
        return None
    if s[0] in "'\"":
        q = s[0]
        if len(s) < 2 or s[-1] != q:
            raise MiniYamlError(f"unterminated quoted string: {raw!r}")
        return s[1:-1]
    s = re.sub(r"\s+#.*$", "", s)
    if s[0] in "[{&*|>!":
        raise MiniYamlError(f"unsupported YAML syntax: {raw!r}")
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


def loads(text: str) -> dict:
    result: dict = {}
    current_list: list | None = None
    current_item: dict | None = None
    item_indent = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise MiniYamlError(f"line {lineno}: tabs are not allowed for indentation")
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            m = _KEY_RE.match(stripped)
            if not m:
                raise MiniYamlError(f"line {lineno}: expected 'key: value', got {stripped!r}")
            key, value = m.group(1), m.group(2)
            if key in result:
                raise MiniYamlError(f"line {lineno}: duplicate key {key!r}")
            if value is None or value.strip() == "" or value.strip().startswith("#"):
                current_list = []
                result[key] = current_list
            else:
                result[key] = parse_scalar(value)
                current_list = None
            current_item = None
            continue
        if current_list is None:
            raise MiniYamlError(f"line {lineno}: indented line outside a list")
        if stripped.startswith("- ") or stripped == "-":
            current_item = {}
            current_list.append(current_item)
            item_indent = indent + 2
            stripped = stripped[1:].strip()
            if not stripped:
                continue
        elif current_item is None or indent != item_indent:
            raise MiniYamlError(f"line {lineno}: bad indentation")
        m = _KEY_RE.match(stripped)
        if not m:
            raise MiniYamlError(f"line {lineno}: expected 'key: value' inside list item")
        key, value = m.group(1), m.group(2)
        if value is None:
            raise MiniYamlError(f"line {lineno}: nested structures are not supported")
        if key in current_item:
            raise MiniYamlError(f"line {lineno}: duplicate key {key!r} in list item")
        current_item[key] = parse_scalar(value)
    return result
