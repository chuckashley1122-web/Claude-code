"""Execute each n8n workflow graph node by node against the mock adapters, offline.

How it works:

- Loads ``workflows/0N_*.json`` (n8n export shape: nodes, connections, settings,
  pinData, meta).
- Starts at every trigger node, feeding it the workflow's ``pinData`` (synthetic
  items), then walks ``connections`` depth-first, dispatching on each node's
  ``type`` to a handler in ``HANDLERS``. IF nodes split items across their
  true/false outputs; loops are cut after ``--loop-iterations`` passes.
- External calls go only to mock adapters (``adapters/mock_*.py``). Outbound
  text passes ``guardrails`` before any mock "send". Socket connections are
  blocked for the whole run, so any network egress attempt fails the run.
- If a node raises, the shared ``_common_error_handler`` workflow is executed
  (writing a JSON error record to data/out/errors/) and the run is marked failed.
- One JSON report per workflow is written to ``data/out/runs/``.

Exit code 0 only if every selected workflow completed.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import socket
import sys
from collections import deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.base import FIXTURES_DIR, stable_id  # noqa: E402
from adapters.mock_apify import LiveApify, MockApify  # noqa: E402
from adapters.mock_calendar import LiveCalendar, MockCalendar  # noqa: E402
from adapters.mock_crm import LiveCRM, MockCRM  # noqa: E402
from adapters.mock_mailer import LiveMailer, MockMailer  # noqa: E402
from adapters.mock_openai import LiveOpenAI, MockOpenAI  # noqa: E402
from adapters.mock_publisher import LivePublisher, MockPublisher  # noqa: E402
from adapters.mock_video_gen import LiveVideoGen, MockVideoGen  # noqa: E402
from adapters.mock_youtube import LiveYouTube, MockYouTube  # noqa: E402
from config import constants  # noqa: E402
from config.settings import enforce_run_mode, load_settings  # noqa: E402
from guardrails import claim_guard, meeting_first, pricing_guard  # noqa: E402
from scripts import render_prompts  # noqa: E402

WORKFLOWS_DIR = ROOT / "workflows"
ERROR_WORKFLOW = "_common_error_handler"
MAX_STEPS = 2000


class WorkflowError(RuntimeError):
    pass


class UnsupportedNode(WorkflowError):
    pass


class ExpressionError(WorkflowError):
    pass


class NetworkBlocked(ConnectionError):
    pass


# --------------------------------------------------------------------- network block

@dataclass
class EgressCounter:
    attempts: int = 0


@contextmanager
def no_network(counter: EgressCounter):
    """Block socket connects and DNS for the duration of the run."""
    def refuse(*_a, **_k):
        counter.attempts += 1
        raise NetworkBlocked("network egress is blocked during dry runs")

    saved = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection, socket.getaddrinfo)
    socket.socket.connect = refuse
    socket.socket.connect_ex = refuse
    socket.create_connection = refuse
    socket.getaddrinfo = refuse
    try:
        yield counter
    finally:
        (socket.socket.connect, socket.socket.connect_ex,
         socket.create_connection, socket.getaddrinfo) = saved


# --------------------------------------------------------------------- adapters

@dataclass
class Adapters:
    openai: Any
    calendar: Any
    crm: Any
    mailer: Any
    video: Any
    apify: Any
    publisher: Any
    youtube: Any

    def all(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def make_adapters(dry_run: bool, out_dir: Path, fixtures_dir: Path = FIXTURES_DIR) -> Adapters:
    if not dry_run:
        # Live adapters exist only to refuse; every call raises LiveCallBlocked.
        return Adapters(LiveOpenAI(), LiveCalendar(), LiveCRM(), LiveMailer(), LiveVideoGen(),
                        LiveApify(), LivePublisher(), LiveYouTube())
    kw = {"dry_run": True, "out_dir": out_dir, "fixtures_dir": fixtures_dir}
    return Adapters(MockOpenAI(**kw), MockCalendar(**kw), MockCRM(**kw), MockMailer(**kw),
                    MockVideoGen(**kw), MockApify(**kw), MockPublisher(**kw), MockYouTube(**kw))


# --------------------------------------------------------------------- expressions

class _Today:
    def __init__(self, d: date):
        self.d = d

    def plusDays(self, n: int) -> str:  # noqa: N802 (mirrors n8n/Luxon naming)
        return (self.d + timedelta(days=int(n))).isoformat()

    def __str__(self) -> str:
        return self.d.isoformat()


_EXPR = re.compile(r"\{\{(.*?)\}\}", re.S)
_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b}


def eval_expression(expr: str, item: dict, ctx: "RunContext") -> Any:
    """Evaluate a restricted n8n-style expression: ``$json.a.b``, ``$json.list[0]``,
    ``$vars.NAME``, ``$today``, ``$today.plusDays(n)``, ``$now``, literals, + - * /."""
    src = expr.strip().replace("$json", "_json").replace("$vars", "_vars")
    src = src.replace("$today", "_today").replace("$now", "_now")
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"bad expression {expr!r}: {exc.msg}") from None
    names = {"_json": item, "_vars": ctx.vars, "_today": _Today(ctx.today),
             "_now": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in names:
                raise ExpressionError(f"unknown name {node.id!r} in {expr!r}")
            return names[node.id]
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise ExpressionError(f"private attribute access not allowed in {expr!r}")
            base = ev(node.value)
            if isinstance(base, dict):
                return base.get(node.attr)
            if isinstance(base, _Today) and node.attr == "plusDays":
                return base.plusDays
            if base is None:
                return None
            raise ExpressionError(f"cannot read .{node.attr} in {expr!r}")
        if isinstance(node, ast.Subscript):
            base, key = ev(node.value), ev(node.slice)
            try:
                return base[key] if base is not None else None
            except (IndexError, KeyError, TypeError):
                return None
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            a, b = ev(node.left), ev(node.right)
            if isinstance(a, _Today):
                a = str(a)
            if isinstance(b, _Today):
                b = str(b)
            if isinstance(node.op, ast.Add) and (isinstance(a, str) or isinstance(b, str)):
                return ("" if a is None else str(a)) + ("" if b is None else str(b))
            if a is None or b is None:
                return None
            try:
                return _BINOPS[type(node.op)](a, b)
            except ZeroDivisionError:
                return None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.Call) and not node.keywords:
            fn = ev(node.func)
            if getattr(fn, "__func__", None) is _Today.plusDays:
                return fn(*[ev(a) for a in node.args])
        raise ExpressionError(f"unsupported syntax in expression {expr!r}")

    value = ev(tree)
    return str(value) if isinstance(value, _Today) else value


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def resolve(value: Any, item: dict, ctx: "RunContext") -> Any:
    """Resolve n8n-style parameters: strings starting with '=' are expressions."""
    if isinstance(value, dict):
        return {k: resolve(v, item, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, item, ctx) for v in value]
    if not (isinstance(value, str) and value.startswith("=")):
        return value
    body = value[1:]
    whole = re.fullmatch(r"\s*\{\{(.*?)\}\}\s*", body, re.S)
    if whole:
        return eval_expression(whole.group(1), item, ctx)
    return _EXPR.sub(lambda m: _stringify(eval_expression(m.group(1), item, ctx)), body)


# --------------------------------------------------------------------- run context

@dataclass
class RunContext:
    workflow_name: str
    adapters: Adapters
    out_dir: Path
    run_id: str
    dry_run: bool = True
    synthetic: bool = True
    loop_iterations: int = 1
    vars: dict = field(default_factory=constants.workflow_vars)
    today: date = field(default_factory=date.today)
    memory: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def _p(node: dict, item: dict, ctx: RunContext) -> dict:
    return resolve(node.get("parameters", {}), item, ctx)


def _first(items: list[dict]) -> dict:
    return items[0] if items else {}


# --------------------------------------------------------------------- handlers
# Each handler: (node, items, ctx) -> list of outputs, each output a list of items.

def h_trigger(node, items, ctx):
    return [items]


def h_noop(node, items, ctx):
    return [items]


def h_openai(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        item = dict(item)
        resource, op = p.get("resource", "text"), p.get("operation", "message")
        llm = ctx.adapters.openai
        if resource == "text" and op == "message":
            prompt = render_prompts.load_prompt(p["promptId"])
            variables = p.get("promptVariables", {})
            text = render_prompts.render(prompt, variables)
            reply = llm.complete(prompt.id, text, variables)
            if p.get("jsonOutput"):
                try:
                    value = json.loads(reply)
                except ValueError as exc:
                    raise WorkflowError(f"model output for {prompt.id} is not JSON: {exc}") from None
            else:
                value = reply
            if p.get("mergeOutput") and isinstance(value, dict):
                item.update(value)
            else:
                item[p.get("outputField", "output")] = value
        elif resource == "audio" and op == "transcribe":
            item[p.get("outputField", "transcript")] = llm.transcribe(p["mediaRef"])
        elif resource == "assistant" and op == "fileSearch":
            chunks = llm.file_search(p["query"], p["knowledgeBase"], int(p.get("topK", 3)))
            item[p.get("outputField", "retrieved")] = [asdict(c) for c in chunks]
            item[p.get("textField", "retrieved_text")] = "\n".join(c.as_text() for c in chunks)
            item[p.get("confidenceField", "confidence")] = chunks[0].score if chunks else 0.0
        else:
            raise UnsupportedNode(f"openAi resource/operation {resource}/{op} not supported")
        out.append(item)
    return [out]


def _cond(op: str, left: Any, right: Any) -> bool:
    if op == "isNotEmpty":
        return left not in (None, "", [], {})
    if op == "isEmpty":
        return left in (None, "", [], {})
    if op == "isTrue":
        return left is True
    if op == "isFalse":
        return not left
    if op == "equals":
        return left == right
    if op == "notEquals":
        return left != right
    if op == "oneOf":
        return left in (right or [])
    if op == "containsAny":
        text = _stringify(left).lower()
        return any(str(w).lower() in text for w in (right or []))
    if op in ("gt", "gte", "lt", "lte"):
        if left is None or right is None:
            return False
        return {"gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}[op]
    raise UnsupportedNode(f"IF operator {op!r} not supported")


def h_if(node, items, ctx):
    true_items, false_items = [], []
    for item in items:
        p = _p(node, item, ctx)
        results = [_cond(c["operator"], c.get("leftValue"), c.get("rightValue")) for c in p["conditions"]]
        ok = all(results) if p.get("combinator", "and") == "and" else any(results)
        (true_items if ok else false_items).append(item)
    return [true_items, false_items]


def h_set(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        new = dict(item) if p.get("keepOtherFields", True) else {}
        new.update(p.get("assignments", {}))
        out.append(new)
    return [out]


def h_limit(node, items, ctx):
    n = int(_p(node, _first(items), ctx)["maxItems"])
    if len(items) > n:
        ctx.notes.append(f"{node['name']}: capped {len(items)} items to {n}")
    return [items[:n]]


def h_split_out(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        field_name = p["fieldToSplitOut"]
        dest = p.get("destinationFieldName", field_name)
        values = item.get(field_name)
        if isinstance(values, dict) and len(values) == 1:
            values = next(iter(values.values()))
        if not isinstance(values, list):
            raise WorkflowError(f"{node['name']}: field {field_name!r} is not a list")
        base = {k: v for k, v in item.items() if k != field_name}
        out.extend({**base, dest: v} for v in values)
    return [out]


def h_aggregate(node, items, ctx):
    p = _p(node, _first(items), ctx)
    include = p.get("include")
    rows = [{k: i.get(k) for k in include} if include else dict(i) for i in items]
    return [[{p.get("outputField", "data"): rows}]]


def h_wait(node, items, ctx):
    p = _p(node, _first(items), ctx)
    ctx.notes.append(f"{node['name']}: dry run skips a wait of {p.get('amount')} {p.get('unit')}")
    return [[{**i, "_waited": f"{p.get('amount')} {p.get('unit')} (skipped in dry run)"} for i in items]]


def h_calendar(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        item = dict(item)
        if p["operation"] == "availability":
            slots = ctx.adapters.calendar.availability(p["date"])
            field_name = p.get("outputField", "free_slots")
            item[field_name] = slots
            item[field_name + "_text"] = ", ".join(slots) if slots else "none available"
        elif p["operation"] == "create":
            item[p.get("outputField", "event")] = ctx.adapters.calendar.create_event(
                p["date"], p["time"], p["attendee"], p["summary"])
        else:
            raise UnsupportedNode(f"googleCalendar operation {p['operation']!r}")
        out.append(item)
    return [out]


def h_gmail(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        item = dict(item)
        if p["operation"] == "send":
            # The mailer re-checks; checking here too means a violation names the node.
            pricing_guard.assert_clean(p["subject"], f"{node['name']} subject")
            pricing_guard.assert_clean(p["message"], f"{node['name']} body")
            item[p.get("outputField", "email_record")] = ctx.adapters.mailer.send(
                p["sendTo"], p["subject"], p["message"], p["fromInbox"])
        elif p["operation"] == "getReplies":
            item[p.get("outputField", "replied")] = ctx.adapters.mailer.has_reply(p["from"])
        else:
            raise UnsupportedNode(f"gmail operation {p['operation']!r}")
        out.append(item)
    return [out]


def h_hubspot(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        contact = ctx.adapters.crm.upsert_contact(p.get("email"), p.get("properties", {}))
        out.append({**item, "crm_contact_id": contact["contact_id"]})
    return [out]


def h_airtable(node, items, ctx):
    crm = ctx.adapters.crm
    p0 = _p(node, _first(items), ctx)
    if p0["operation"] == "search":
        rows, seen = [], set()
        for item in items or [{}]:
            p = _p(node, item, ctx)
            for row in crm.query(p["table"], p.get("filter", [])):
                if row["_key"] not in seen:
                    seen.add(row["_key"])
                    rows.append(row)
        return [rows]
    if p0["operation"] != "upsert":
        raise UnsupportedNode(f"airtable operation {p0['operation']!r}")
    out = []
    for item in items:
        p = _p(node, item, ctx)
        fields = p.get("fields")
        if fields is None:
            fields = {k: v for k, v in item.items() if not k.startswith("_")}
        row = crm.upsert_record(p["table"], p["key"], fields, tuple(p.get("increment", ())))
        out.append({**item, **{k: v for k, v in row.items() if k != "_key"}, "_key": row["_key"]})
    return [out]


def h_slack(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        rec = ctx.adapters.publisher.notify(p.get("channel", "#ops"), p["text"])
        out.append({**item, "notification": rec["status"]})
    return [out]


def h_apify(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        rows = ctx.adapters.apify.run_actor(p["actorId"], p.get("actorInput", {}))
        out.extend({**item, **row} for row in rows)
    return [out]


def h_respond(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        rec = ctx.adapters.publisher.reply(p["sessionId"], p["responseBody"])
        out.append({**item, "reply_record": rec["status"]})
    return [out]


def h_guardrails(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        if p.get("workflowId") != "caj_guardrails":
            raise UnsupportedNode(f"executeWorkflow target {p.get('workflowId')!r} not available offline")
        item = dict(item)
        guard = p["guard"]
        if guard == "pricing":
            for f in p["fields"]:
                pricing_guard.assert_clean(_stringify(item.get(f)), f"{node['name']}:{f}")
        elif guard == "claims":
            for f in p["fields"]:
                claim_guard.assert_no_claims(_stringify(item.get(f)), f"{node['name']}:{f}")
        elif guard == "meeting_first":
            routing = meeting_first.route(_stringify(item.get(p["inboundField"])))
            item[p.get("intentField", "pricing_intent")] = routing.pricing_intent
            if routing.pricing_intent:
                item[p["replyField"]] = routing.reply
        else:
            raise UnsupportedNode(f"guard {guard!r} not supported")
        item.setdefault("_guards_passed", [])
        item["_guards_passed"] = item["_guards_passed"] + [f"{guard}@{node['name']}"]
        out.append(item)
    return [out]


def _safe_out_path(ctx: RunContext, base_dir: str, file_name: str) -> Path:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", file_name).strip("._") or "record.json"
    target = (ctx.out_dir / base_dir / name).resolve()
    if ctx.out_dir.resolve() not in target.parents:
        raise WorkflowError(f"refusing to write outside data/out: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def h_write_file(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        if p.get("operation") != "write":
            raise UnsupportedNode("readWriteFile supports operation=write only")
        data = item.get(p["dataField"]) if p.get("dataField") else item
        path = _safe_out_path(ctx, p.get("baseDir", "files"), p["fileName"])
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        out.append({**item, "written_file": str(path)})
    return [out]


def h_memory(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        window = ctx.memory.setdefault(p["sessionKey"], [])
        window.append(p["message"])
        del window[: -int(p.get("contextWindowLength", 5))]
        out.append({**item, "memory": list(window)})
    return [out]


# httpRequest routing: (host, path prefix) -> callable(ctx, params, item) -> list of items
def _video(provider: str, kind: str):
    def call(ctx, p, item):
        job = ctx.adapters.video.create_job(provider, kind, p.get("jsonBody", {}))
        return [{**item, p.get("responseField", "response"): job}]
    return call


def _heygen_status(ctx, p, item):
    status = ctx.adapters.video.status(p.get("queryParameters", {})["video_id"])
    return [{**item, p.get("responseField", "response"): status}]


def _ayrshare_post(ctx, p, item):
    body = p.get("jsonBody", {})
    rec = ctx.adapters.publisher.post(body["platforms"], body["post"], body.get("mediaRef"))
    return [{**item, p.get("responseField", "response"): rec}]


def _ayrshare_analytics(ctx, p, item):
    rec = ctx.adapters.publisher.analytics(p.get("jsonBody", {})["id"])
    return [{**item, p.get("responseField", "response"): rec}]


def _twilio_transfer(ctx, p, item):
    body = p.get("jsonBody", {})
    rec = ctx.adapters.publisher.transfer_call(body["call_id"], body.get("reason", ""))
    return [{**item, p.get("responseField", "response"): rec}]


def _youtube_search(ctx, p, item):
    q = p.get("queryParameters", {})
    rows = ctx.adapters.youtube.search(q["q"], q.get("order", "viewCount"), q.get("publishedAfter"),
                                       int(q.get("maxResults", 50)))
    return [{**item, **row} for row in rows]


def _hunter(ctx, p, item):
    email = ctx.adapters.crm.find_email(p.get("queryParameters", {})["domain"])
    return [{**item, p.get("responseField", "response"): {"email": email}}]


HTTP_ROUTES: tuple[tuple[str, str, Callable], ...] = (
    ("api.heygen.com", "/v2/video/generate", _video("heygen", "avatar")),
    ("api.heygen.com", "/v1/video_status.get", _heygen_status),
    ("api.creatomate.com", "/v1/renders", _video("creatomate", "render")),
    ("api.elevenlabs.io", "/v1/text-to-speech", _video("elevenlabs", "voiceover")),
    ("api.openai.com", "/v1/videos", _video("sora", "video")),
    ("api.openai.com", "/v1/images/generations", _video("openai_images", "image")),
    ("api.ayrshare.com", "/api/post", _ayrshare_post),
    ("api.ayrshare.com", "/api/analytics/post", _ayrshare_analytics),
    ("api.twilio.com", "/2010-04-01/Accounts", _twilio_transfer),
    ("www.googleapis.com", "/youtube/v3/search", _youtube_search),
    ("api.hunter.io", "/v2/domain-search", _hunter),
)


def route_http(url: str) -> Callable:
    parsed = urlparse(url)
    for host, prefix, fn in HTTP_ROUTES:
        if parsed.hostname == host and parsed.path.startswith(prefix):
            return fn
    raise UnsupportedNode(f"no offline adapter for HTTP endpoint {parsed.hostname}{parsed.path}")


def h_http(node, items, ctx):
    out = []
    for item in items:
        p = _p(node, item, ctx)
        out.extend(route_http(p["url"])(ctx, p, item))
    return [out]


HANDLERS: dict[str, Callable] = {
    "n8n-nodes-base.webhook": h_trigger,
    "n8n-nodes-base.scheduleTrigger": h_trigger,
    "n8n-nodes-base.manualTrigger": h_trigger,
    "n8n-nodes-base.errorTrigger": h_trigger,
    "@n8n/n8n-nodes-langchain.chatTrigger": h_trigger,
    "@n8n/n8n-nodes-langchain.openAi": h_openai,
    "@n8n/n8n-nodes-langchain.memoryBufferWindow": h_memory,
    "n8n-nodes-base.if": h_if,
    "n8n-nodes-base.set": h_set,
    "n8n-nodes-base.limit": h_limit,
    "n8n-nodes-base.splitOut": h_split_out,
    "n8n-nodes-base.aggregate": h_aggregate,
    "n8n-nodes-base.wait": h_wait,
    "n8n-nodes-base.noOp": h_noop,
    "n8n-nodes-base.googleCalendar": h_calendar,
    "n8n-nodes-base.gmail": h_gmail,
    "n8n-nodes-base.hubspot": h_hubspot,
    "n8n-nodes-base.airtable": h_airtable,
    "n8n-nodes-base.slack": h_slack,
    "@apify/n8n-nodes-apify.apify": h_apify,
    "n8n-nodes-base.httpRequest": h_http,
    "n8n-nodes-base.executeWorkflow": h_guardrails,
    "n8n-nodes-base.respondToWebhook": h_respond,
    "n8n-nodes-base.readWriteFile": h_write_file,
}
TRIGGER_TYPES = {"n8n-nodes-base.webhook", "n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.manualTrigger",
                 "@n8n/n8n-nodes-langchain.chatTrigger"}
ERROR_TRIGGER = "n8n-nodes-base.errorTrigger"
SUPPORTED_TYPES = frozenset(HANDLERS)


# --------------------------------------------------------------------- graph walk

def _targets(wf: dict, name: str) -> list[list[str]]:
    outputs = wf.get("connections", {}).get(name, {}).get("main", [])
    return [[c["node"] for c in (branch or [])] for branch in outputs]


def _reachable(wf: dict, start: str) -> set[str]:
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        for branch in _targets(wf, n):
            for t in branch:
                if t not in seen:
                    seen.add(t)
                    stack.append(t)
    return seen


def _pin_items(wf: dict, node_name: str) -> list[dict]:
    pins = wf.get("pinData", {}).get(node_name)
    if not pins:
        return [{}]
    return [dict(p.get("json", {})) for p in pins]


def _adapter_call_count(ctx: RunContext) -> dict[str, int]:
    return {k: len(getattr(a, "calls", [])) for k, a in ctx.adapters.all().items()}


def execute(wf: dict, ctx: RunContext, trigger_items: Optional[dict[str, list[dict]]] = None,
            error_workflow: Optional[dict] = None) -> dict:
    """Walk ``wf`` node by node. Returns a report dict (status success|error)."""
    nodes = {n["name"]: n for n in wf["nodes"]}
    triggers = [n for n in wf["nodes"]
                if n["type"] in (TRIGGER_TYPES if trigger_items is None else {ERROR_TRIGGER} | TRIGGER_TYPES)
                and (trigger_items is None or n["name"] in trigger_items)]
    if not triggers:
        raise WorkflowError(f"workflow {wf.get('name')!r} has no trigger node")
    reach = {name: _reachable(wf, name) for name in nodes}
    steps: list[dict] = []
    back_edges_taken: dict[tuple[str, str], int] = {}
    executed: set[str] = set()
    report = {"workflow": wf.get("name"), "run_id": ctx.run_id, "dry_run": ctx.dry_run,
              "synthetic": ctx.synthetic, "status": "success", "steps": steps, "terminal_items": {},
              "loops_halted": [], "error": None}
    base_today = ctx.today
    for trig in triggers:
        items = (trigger_items or {}).get(trig["name"]) or _pin_items(wf, trig["name"])
        # Synthetic pinData may pin the clock so dry runs are reproducible.
        first = items[0] if items else {}
        pinned = first.get("_simulated_today")
        offset = int(first.get("_simulated_today_offset_days") or 0)
        for it in items:
            it.pop("_simulated_today", None)
            it.pop("_simulated_today_offset_days", None)
        start = date.fromisoformat(pinned) if pinned else base_today
        ctx.today = start + timedelta(days=offset)
        stack = deque([(trig["name"], items)])
        while stack:
            name, in_items = stack.popleft()
            node = nodes.get(name)
            if node is None:
                raise WorkflowError(f"connection to unknown node {name!r}")
            if len(steps) >= MAX_STEPS:
                raise WorkflowError("step limit reached; possible unbounded loop")
            handler = HANDLERS.get(node["type"])
            before = _adapter_call_count(ctx)
            step = {"seq": len(steps) + 1, "node": name, "type": node["type"], "items_in": len(in_items)}
            steps.append(step)
            try:
                if handler is None:
                    raise UnsupportedNode(f"node type {node['type']!r} has no offline handler")
                outputs = handler(node, [dict(i) for i in in_items], ctx)
            except Exception as exc:  # noqa: BLE001 - every failure routes to the error workflow
                step["status"] = "error"
                step["error"] = f"{type(exc).__name__}: {exc}"
                report["status"] = "error"
                report["error"] = {"node": name, "type": type(exc).__name__, "message": str(exc)}
                if error_workflow is not None:
                    report["error_handler"] = run_error_handler(error_workflow, wf, ctx, name, exc)
                ctx.today = base_today
                return report
            after = _adapter_call_count(ctx)
            step["adapter_calls"] = [f"{k}x{after[k] - before[k]}" for k in after if after[k] != before[k]]
            step["outputs"] = [len(o) for o in outputs]
            step["status"] = "ok"
            executed.add(name)
            targets = _targets(wf, name)
            if not any(targets):
                report["terminal_items"].setdefault(name, []).extend(outputs[0] if outputs else [])
            pending = []
            for idx, branch in enumerate(targets):
                branch_items = outputs[idx] if idx < len(outputs) else []
                if not branch_items:
                    continue
                for target in branch:
                    # A back-edge re-enters a node that already ran and can reach this one (a loop).
                    if target in executed and (name in reach.get(target, set()) or target == name):
                        key = (name, target)
                        taken = back_edges_taken.get(key, 0)
                        if taken + 1 >= ctx.loop_iterations:
                            report["loops_halted"].append(
                                f"{name} -> {target} after {ctx.loop_iterations} iteration(s)")
                            continue
                        back_edges_taken[key] = taken + 1
                    pending.append((target, branch_items))
            # depth-first, keeping branch order (n8n v1 execution order)
            for entry in reversed(pending):
                stack.appendleft(entry)
    ctx.today = base_today
    return report


def run_error_handler(handler_wf: dict, failed_wf: dict, ctx: RunContext, node_name: str, exc: Exception) -> dict:
    trigger = next(n for n in handler_wf["nodes"] if n["type"] == ERROR_TRIGGER)
    payload = {
        "execution": {"id": f"{ctx.run_id}-{re.sub(r'[^a-z0-9]+', '-', (failed_wf.get('name') or '').lower()).strip('-')}",
                      "lastNodeExecuted": node_name,
                      "error": {"message": str(exc), "type": type(exc).__name__},
                      "mode": "dry_run", "synthetic": ctx.synthetic},
        "workflow": {"name": failed_wf.get("name")},
    }
    hctx = RunContext(ERROR_WORKFLOW, ctx.adapters, ctx.out_dir, ctx.run_id, ctx.dry_run, ctx.synthetic)
    sub = execute(handler_wf, hctx, {trigger["name"]: [payload]}, None)
    files = [i.get("written_file") for items in sub["terminal_items"].values() for i in items]
    return {"status": sub["status"], "error_records": [f for f in files if f]}


# --------------------------------------------------------------------- CLI

def load_workflow(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def workflow_files(directory: Path = WORKFLOWS_DIR) -> list[Path]:
    return sorted(p for p in directory.glob("0*.json"))


def run_one(path: Path, out_dir: Path, loop_iterations: int = 1, dry_run: bool = True) -> tuple[dict, Path]:
    wf = load_workflow(path)
    handler = load_workflow(path.parent / f"{ERROR_WORKFLOW}.json")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    ctx = RunContext(wf["name"], make_adapters(dry_run, out_dir), out_dir, run_id,
                     dry_run=dry_run, loop_iterations=loop_iterations)
    counter = EgressCounter()
    with no_network(counter):
        report = execute(wf, ctx, None, handler)
    report.update({
        "file": path.name,
        "network_egress_attempts": counter.attempts,
        "notes": ctx.notes,
        "adapter_calls": {k: [asdict(c) for c in getattr(a, "calls", [])] for k, a in ctx.adapters.all().items()},
    })
    if counter.attempts:
        report["status"] = "error"
    runs = out_dir / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    report_path = runs / f"{path.stem}.{run_id}.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report, report_path


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workflow", action="append", help="workflow file stem to run (default: all eight)")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "out")
    ap.add_argument("--loop-iterations", type=int, default=1)
    args = ap.parse_args(argv)
    settings = load_settings()
    enforce_run_mode(settings)
    files = workflow_files()
    if args.workflow:
        files = [f for f in files if f.stem in args.workflow]
    if not files:
        print("FAIL: no workflows selected")
        return 1
    failures = 0
    for path in files:
        report, report_path = run_one(path, args.out_dir, args.loop_iterations, settings.dry_run)
        ok = report["status"] == "success"
        failures += 0 if ok else 1
        print(f"{'OK  ' if ok else 'FAIL'} {path.name}: {len(report['steps'])} node executions, "
              f"egress attempts {report['network_egress_attempts']}, report {report_path.relative_to(args.out_dir)}")
        if not ok:
            print(f"     error at {report['error']['node']}: {report['error']['message']}")
    print(f"{len(files) - failures}/{len(files)} workflows completed offline")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
