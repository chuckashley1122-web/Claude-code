"""Reference inquiry handler + generator for out/server_functions/inquiry.ts.

Flow: rate limit -> byte cap -> parse -> normalize -> validate -> idempotency
claim -> adapter call bounded by UPSTREAM_TIMEOUT_S -> truthful status mapping.

* 201 only when the adapter confirmed a save AND returned a reference; the
  public body carries an opaque inquiry reference, never the CRM ID.
* 202 only when the adapter has a real durable queue and reported "queued";
  text reads "received for processing", never "saved to CRM".
* Transient upstream failures are retried at most MAX_RETRIES times with
  exponential backoff, honouring upstream Retry-After, with the same
  submission_id. Validation, permission and unconfigured-integration errors
  are never retried.
* Raw PII never reaches logs (redact_pii) or public responses.

Note: a timed-out upstream call is ambiguous (the CRM may have saved it).
Retries reuse the same submission_id so the CRM-side contact upsert and the
submission_id custom field can de-duplicate; that CRM behaviour is
NEEDS_EVIDENCE until work order 005-005 confirms it.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import inquiry_validator as V  # noqa: E402
from src.ghl_adapter import (AdapterResult, LiveCallBlocked, UpstreamError,  # noqa: E402
                             UpstreamTimeout)
from src.idempotency_store import IdempotencyStore  # noqa: E402
from src.inquiry_contract import UI_TEXT  # noqa: E402
from tools.paths import Paths, default_paths  # noqa: E402
from tools.state import STATUS, emit  # noqa: E402


@dataclass
class Response:
    status: int
    body: dict
    headers: dict = field(default_factory=dict)


class FixedWindowRateLimiter:
    """In-memory limiter for local tests. Not a claim that the platform endpoint is protected
    (RATE_LIMIT_CONFIG is NEEDS_EVIDENCE)."""

    def __init__(self, limit: int, window_s: float, clock: Callable[[], float] = time.monotonic):
        self.limit, self.window_s, self.clock = limit, window_s, clock
        self._hits: dict[str, list[float]] = {}

    def __call__(self, key: str) -> bool:
        now = self.clock()
        hits = [t for t in self._hits.get(key, []) if now - t < self.window_s]
        allowed = len(hits) < self.limit
        if allowed:
            hits.append(now)
        self._hits[key] = hits
        return allowed


def opaque_reference(submission_id: str, crm_reference: str) -> str:
    return "inq_" + hashlib.sha256(f"{submission_id}:{crm_reference}".encode()).hexdigest()[:16]


def _failure(status: int, code: str, ui_key: str, extra: dict | None = None) -> dict:
    body = {"status": "error", "error": code, "message": UI_TEXT[ui_key],
            "retain_form_values": True, "fallback_booking_url": C.BOOKING_URL}
    body.update(extra or {})
    return body


class InquiryHandler:
    def __init__(self, adapter, store: IdempotencyStore, config: dict | None = None,
                 server_config: dict | None = None, sleep: Callable[[float], None] = time.sleep,
                 logger: Callable[[dict], None] | None = None, rate_limiter: Callable[[str], bool] | None = None,
                 timeout_s: float = C.UPSTREAM_TIMEOUT_S, max_retries: int = C.MAX_RETRIES,
                 backoff_base_s: float = 0.5, max_retry_after_s: float = 30.0):
        self.adapter = adapter
        self.store = store
        self.config = {**V.default_config(), **(config or {})}
        self.server_config = server_config if server_config is not None else {"location_id": C.GHL_LOCATION_ID}
        self.sleep = sleep
        self.log_records: list[dict] = []
        self.logger = logger or self.log_records.append
        self.rate_limiter = rate_limiter
        self.timeout_s = timeout_s
        self.max_retries = min(max_retries, C.MAX_RETRIES)
        self.backoff_base_s = backoff_base_s
        self.max_retry_after_s = max_retry_after_s

    # -------------------------------------------------------------- logging
    def _log(self, event: str, **data) -> None:
        self.logger(V.redact_pii({"event": event, **data}))

    # -------------------------------------------------------------- upstream call
    def _call_once(self, record: dict, submission_id: str) -> AdapterResult:
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            future = pool.submit(self.adapter.save_inquiry, record, submission_id, self.timeout_s)
            try:
                return future.result(timeout=self.timeout_s)
            except FutureTimeout as exc:
                raise UpstreamTimeout(f"no upstream answer within {self.timeout_s} s") from exc
        finally:
            pool.shutdown(wait=False)

    def _call_with_retries(self, record: dict, submission_id: str) -> tuple[AdapterResult | None, Exception | None, int]:
        attempts = 0
        last_exc: Exception | None = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                return self._call_once(record, submission_id), None, attempts
            except LiveCallBlocked as exc:
                return None, exc, attempts
            except UpstreamError as exc:
                last_exc = exc
                self._log("upstream_error", submission_id=submission_id, attempt=attempts,
                          error=type(exc).__name__, retryable=exc.retryable)
                if not exc.retryable or attempts > self.max_retries:
                    break
                if exc.retry_after is not None and exc.retry_after > self.max_retry_after_s:
                    break  # upstream asked for longer than we may hold the request; report honestly
                delay = max(self.backoff_base_s * (2 ** (attempts - 1)), exc.retry_after or 0)
                self.sleep(delay)
            except Exception as exc:  # unexpected adapter failure: never a success
                last_exc = exc
                self._log("upstream_unexpected", submission_id=submission_id, attempt=attempts,
                          error=type(exc).__name__)
                break
        return None, last_exc, attempts

    # -------------------------------------------------------------- main entry
    def handle(self, raw_body: bytes | str, client_key: str = "anonymous") -> Response:
        if isinstance(raw_body, str):
            raw_body = raw_body.encode("utf-8")
        if self.rate_limiter is not None and not self.rate_limiter(client_key):
            self._log("throttled")
            return Response(C.STATUS_THROTTLED, _failure(C.STATUS_THROTTLED, "throttled", "throttled"),
                            {"Retry-After": "60"})
        if len(raw_body) > self.config["max_payload_bytes"]:
            self._log("rejected", reason="payload_too_large", size=len(raw_body))
            return Response(C.STATUS_BAD_REQUEST, _failure(400, "payload_too_large", "invalid"))
        try:
            fields = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._log("rejected", reason="malformed_json")
            return Response(C.STATUS_BAD_REQUEST, _failure(400, "malformed_json", "invalid"))
        if not isinstance(fields, dict):
            return Response(C.STATUS_BAD_REQUEST, _failure(400, "not_an_object", "invalid"))

        fields = V.normalize(fields)
        ok, errors = V.validate(fields, self.config)
        if not ok:
            self._log("rejected", reason="validation", errors=errors)
            return Response(C.STATUS_INVALID, _failure(422, "validation_failed", "invalid", {"errors": errors}))

        submission_id = fields["submission_id"]
        claimed, prior = self.store.begin(submission_id)
        if not claimed:
            if prior.state == "in_flight":
                self._log("duplicate_in_flight", submission_id=submission_id)
                return Response(C.STATUS_UPSTREAM_FAIL,
                                _failure(503, "submission_in_progress", "upstream"), {"Retry-After": "2"})
            self._log("idempotent_replay", submission_id=submission_id, state=prior.state)
            return Response(prior.response_status, prior.response_body, {"Idempotent-Replay": "true"})

        record = {k: fields.get(k) for k in C.INQUIRY_ALLOWED_FIELDS if k in fields}
        record.update(self.server_config)  # privileged values from server configuration only
        result, exc, attempts = self._call_with_retries(record, submission_id)
        response = self._map(result, exc, submission_id)
        state = {201: "saved", 202: "queued"}.get(response.status, "failed")
        crm_ref = result.reference if (result and state in ("saved", "queued")) else None
        self.store.complete(submission_id, state, response.status, response.body, crm_ref)
        self._log("completed", submission_id=submission_id, status=response.status, attempts=attempts)
        return response

    def _map(self, result: AdapterResult | None, exc: Exception | None, submission_id: str) -> Response:
        if isinstance(exc, LiveCallBlocked):
            return Response(C.STATUS_UPSTREAM_FAIL, _failure(503, "crm_integration_not_configured", "upstream"))
        if exc is not None:
            status = getattr(exc, "status", C.STATUS_UPSTREAM_BAD)
            headers = {}
            if getattr(exc, "retry_after", None):
                headers["Retry-After"] = str(int(exc.retry_after))
            return Response(status, _failure(status, "upstream_" + type(exc).__name__, "upstream"), headers)
        assert result is not None
        if result.outcome == "saved" and result.reference:
            return Response(C.STATUS_SAVED, {"status": "saved",
                                             "inquiry_reference": opaque_reference(submission_id, result.reference),
                                             "message": UI_TEXT["saved"], "next_step": C.BOOKING_URL})
        if result.outcome == "queued" and result.reference and getattr(self.adapter, "durable_queue", False):
            return Response(C.STATUS_QUEUED, {"status": "received_for_processing",
                                              "inquiry_reference": opaque_reference(submission_id, result.reference),
                                              "message": UI_TEXT["queued"], "next_step": C.BOOKING_URL})
        # claimed success without confirmation, or "queued" with no durable queue: never a false success
        return Response(C.STATUS_UPSTREAM_BAD, _failure(502, "upstream_unconfirmed", "upstream"))


# ====================================================================== TypeScript emission
TS_TEMPLATE = r'''// out/server_functions/inquiry.ts
// GENERATED by src/inquiry_handler.py - regenerate rather than hand-edit.
// Paste-ready server function source mirroring the Python reference handler.
// Authored guidance, NOT a platform contract: the AI Studio server-function signature, the GHL API
// contract and the durable idempotency store are NEEDS_EVIDENCE (work orders 005-002, 005-004, 005-005).
// Credentials and configuration are read from environment variables BY NAME ONLY. This file contains no
// secret value and no hard-coded location, pipeline or stage ID.

export const BOUNDS = {
  maxNameLen: __MAX_NAME_LEN__,
  maxMessageLen: __MAX_MESSAGE_LEN__,
  maxServiceAreaLen: __MAX_NAME_LEN__,
  maxPayloadBytes: __MAX_PAYLOAD_BYTES__,
  upstreamTimeoutMs: __TIMEOUT_MS__,
  maxRetries: __MAX_RETRIES__,
  idempotencyRetentionHours: __RETENTION_HOURS__,
};

export const BOOKING_URL = "__BOOKING_URL__";
const ALLOWED_FIELDS: string[] = __ALLOWED_FIELDS__;
const PRIVILEGED_FIELDS: string[] = __PRIVILEGED_FIELDS__;
const UI_TEXT: Record<string, string> = __UI_TEXT__;

export interface InquiryResponse {
  status: number;
  body: Record<string, unknown>;
  headers: Record<string, string>;
}

export interface CrmResult {
  outcome: "saved" | "queued";
  reference: string | null;
}

export interface CrmAdapter {
  durableQueue: boolean;
  saveInquiry(record: Record<string, unknown>, submissionId: string, signal: AbortSignal): Promise<CrmResult>;
}

export interface StoredOutcome {
  state: "in_flight" | "saved" | "failed" | "queued";
  status: number | null;
  body: Record<string, unknown> | null;
}

export interface IdempotencyStore {
  // Must be durable (survive restarts) and atomic. The platform's storage option is NEEDS_EVIDENCE.
  begin(submissionId: string): Promise<{ claimed: boolean; prior: StoredOutcome | null }>;
  complete(submissionId: string, outcome: StoredOutcome): Promise<void>;
}

export interface HandlerConfig {
  serviceAllowlist: string[];
  allowedSourceOrigins: string[];
}

export class UpstreamError extends Error {
  retryable: boolean;
  status: number;
  retryAfterS: number | null;
  constructor(message: string, retryable: boolean, status: number, retryAfterS: number | null = null) {
    super(message);
    this.retryable = retryable;
    this.status = status;
    this.retryAfterS = retryAfterS;
  }
}

export class IntegrationNotConfirmed extends Error {}

function readEnv(name: string): string {
  const value = process.env[name];
  return typeof value === "string" ? value.trim() : "";
}

function listFromEnv(name: string): string[] {
  return readEnv(name).split(",").map((s) => s.trim()).filter((s) => s.length > 0);
}

export function configFromEnv(): HandlerConfig {
  return {
    serviceAllowlist: listFromEnv("SERVICE_ALLOWLIST"),
    allowedSourceOrigins: listFromEnv("ALLOWED_SOURCE_ORIGINS"),
  };
}

export function serverConfigFromEnv(): Record<string, string> {
  // Privileged values come from server configuration only, never from the client.
  return {
    location_id: readEnv("GHL_LOCATION_ID"),
    pipeline_id: readEnv("GHL_PIPELINE_ID"),
    stage_id: readEnv("GHL_STAGE_ID"),
  };
}

export function createGhlAdapterFromEnv(): CrmAdapter {
  const token = process.env.GHL_ACCESS_TOKEN;
  return {
    durableQueue: false,
    async saveInquiry(): Promise<CrmResult> {
      if (!token) {
        throw new IntegrationNotConfirmed("GHL_ACCESS_TOKEN is not available to the server");
      }
      // The GHL base URL, API version, endpoint path, scopes, matching rule and field IDs are unverified.
      // Do not guess them. Replace this throw only after work order 005-005 records the confirmed contract.
      throw new IntegrationNotConfirmed("TODO: confirm the GHL contact upsert contract before implementing");
    },
  };
}

const EMAIL_RE = /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/;
const PHONE_RE = /^\+?\d{10,15}$/;
const SUBMISSION_ID_RE = /^[A-Za-z0-9_-]{8,128}$/;
const SINGLE_LINE = ["submission_id", "name", "email", "phone", "service_interest", "service_area", "source_page"];
const TEXT_FIELDS = SINGLE_LINE.concat(["message"]);

export function normalizeInquiry(fields: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, raw] of Object.entries(fields)) {
    let value: unknown = raw;
    if (TEXT_FIELDS.includes(key) && typeof value === "string") {
      let s: string = value;
      if (SINGLE_LINE.includes(key)) {
        s = s.replace(/\s+/g, " ").trim();
      } else {
        s = s.replace(/\r\n?/g, "\n").replace(/[ \t\f\v]+/g, " ").replace(/ *\n */g, "\n").replace(/\n{3,}/g, "\n\n").trim();
      }
      if (key === "email") s = s.toLowerCase();
      if (key === "phone") {
        const plus = s.startsWith("+");
        s = (plus ? "+" : "") + s.replace(/\D/g, "");
        if (s === "+") s = "";
      }
      value = s;
    } else if (key === "consent" && typeof value === "string") {
      const v = value.trim().toLowerCase();
      if (["true", "1", "yes", "on"].includes(v)) value = true;
      else if (["false", "0", "no", "off", ""].includes(v)) value = false;
    }
    out[key] = value;
  }
  return out;
}

function originOf(url: string): string | null {
  try {
    const u = new URL(url);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return (u.protocol + "//" + u.host).toLowerCase();
  } catch {
    return null;
  }
}

export function validateInquiry(fields: Record<string, unknown>, config: HandlerConfig): { ok: boolean; errors: { field: string; code: string }[] } {
  const errors: { field: string; code: string }[] = [];
  const err = (field: string, code: string) => errors.push({ field, code });
  for (const key of Object.keys(fields)) {
    if (PRIVILEGED_FIELDS.includes(key)) err(key, "privileged_field_rejected");
    else if (!ALLOWED_FIELDS.includes(key)) err(key, "unknown_field");
  }
  for (const key of TEXT_FIELDS) {
    const v = fields[key];
    if (v !== undefined && v !== null && typeof v !== "string") err(key, "must_be_string");
  }
  if ("consent" in fields && typeof fields.consent !== "boolean") err("consent", "must_be_boolean");
  const text = (key: string): string => (typeof fields[key] === "string" ? (fields[key] as string) : "");
  for (const key of ["name", "submission_id"]) {
    if (!text(key)) err(key, "required");
  }
  if (text("submission_id") && !SUBMISSION_ID_RE.test(text("submission_id"))) err("submission_id", "invalid_format");
  if (text("name").length > BOUNDS.maxNameLen) err("name", "too_long");
  if (text("message").length > BOUNDS.maxMessageLen) err("message", "too_long");
  if (text("service_area").length > BOUNDS.maxServiceAreaLen) err("service_area", "too_long");
  const email = text("email");
  const phone = text("phone");
  if (email && !(email.length <= 254 && EMAIL_RE.test(email))) err("email", "invalid");
  if (phone && !PHONE_RE.test(phone)) err("phone", "invalid");
  if (!email && !phone) err("contact", "one_contact_method_required");
  const service = text("service_interest");
  if (!service) err("service_interest", "required");
  else if (config.serviceAllowlist.length === 0) err("service_interest", "service_allowlist_unconfigured");
  else if (!config.serviceAllowlist.includes(service)) err("service_interest", "not_in_allowlist");
  const source = text("source_page");
  if (source) {
    const origin = originOf(source);
    const allowed = config.allowedSourceOrigins.map((o) => o.replace(/\/+$/, "").toLowerCase());
    if (origin === null) err("source_page", "invalid_url");
    else if (allowed.length === 0) err("source_page", "source_origins_unconfigured");
    else if (!allowed.includes(origin)) err("source_page", "origin_not_allowed");
  }
  return { ok: errors.length === 0, errors };
}

function failure(status: number, code: string, uiKey: string, extra: Record<string, unknown> = {}): Record<string, unknown> {
  return Object.assign({ status: "error", error: code, message: UI_TEXT[uiKey], retain_form_values: true, fallback_booking_url: BOOKING_URL }, extra);
}

async function opaqueReference(submissionId: string, crmReference: string): Promise<string> {
  const data = new TextEncoder().encode(submissionId + ":" + crmReference);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const hex = Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
  return "inq_" + hex.slice(0, 16);
}

function redact(event: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(event)) {
    out[k] = ["name", "email", "phone", "message", "service_area"].includes(k) ? "[REDACTED]" : v;
  }
  return out;
}

export interface HandlerDeps {
  adapter: CrmAdapter;
  store: IdempotencyStore | null;
  config: HandlerConfig;
  serverConfig: Record<string, string>;
  sleep: (ms: number) => Promise<void>;
  log: (event: Record<string, unknown>) => void;
  rateLimit?: (clientKey: string) => boolean;
}

export function defaultDeps(): HandlerDeps {
  return {
    adapter: createGhlAdapterFromEnv(),
    store: null, // NEEDS_EVIDENCE: wire the platform's durable storage here; without it the handler refuses.
    config: configFromEnv(),
    serverConfig: serverConfigFromEnv(),
    sleep: (ms: number) => new Promise((resolve) => setTimeout(resolve, ms)),
    log: (event: Record<string, unknown>) => console.log(JSON.stringify(redact(event))),
  };
}

async function callWithTimeout(adapter: CrmAdapter, record: Record<string, unknown>, submissionId: string): Promise<CrmResult> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new UpstreamError("upstream timeout", true, 503));
    }, BOUNDS.upstreamTimeoutMs);
  });
  try {
    return await Promise.race([adapter.saveInquiry(record, submissionId, controller.signal), timeout]);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

export async function handleInquiry(rawBody: string, deps: HandlerDeps = defaultDeps(), clientKey: string = "anonymous"): Promise<InquiryResponse> {
  if (deps.rateLimit && !deps.rateLimit(clientKey)) {
    return { status: 429, body: failure(429, "throttled", "throttled"), headers: { "Retry-After": "60" } };
  }
  if (new TextEncoder().encode(rawBody).length > BOUNDS.maxPayloadBytes) {
    return { status: 400, body: failure(400, "payload_too_large", "invalid"), headers: {} };
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawBody);
  } catch {
    return { status: 400, body: failure(400, "malformed_json", "invalid"), headers: {} };
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { status: 400, body: failure(400, "not_an_object", "invalid"), headers: {} };
  }
  const fields = normalizeInquiry(parsed as Record<string, unknown>);
  const { ok, errors } = validateInquiry(fields, deps.config);
  if (!ok) {
    deps.log({ event: "rejected", errors });
    return { status: 422, body: failure(422, "validation_failed", "invalid", { errors }), headers: {} };
  }
  if (!deps.store) {
    deps.log({ event: "idempotency_store_missing" });
    return { status: 503, body: failure(503, "idempotency_store_not_configured", "upstream"), headers: {} };
  }
  const submissionId = fields.submission_id as string;
  const { claimed, prior } = await deps.store.begin(submissionId);
  if (!claimed && prior) {
    if (prior.state === "in_flight") {
      return { status: 503, body: failure(503, "submission_in_progress", "upstream"), headers: { "Retry-After": "2" } };
    }
    return { status: prior.status ?? 502, body: prior.body ?? {}, headers: { "Idempotent-Replay": "true" } };
  }
  const record: Record<string, unknown> = {};
  for (const key of ALLOWED_FIELDS) if (key in fields) record[key] = fields[key];
  Object.assign(record, deps.serverConfig);

  let response: InquiryResponse | null = null;
  let crmResult: CrmResult | null = null;
  for (let attempt = 1; attempt <= BOUNDS.maxRetries + 1; attempt++) {
    try {
      crmResult = await callWithTimeout(deps.adapter, record, submissionId);
      break;
    } catch (e) {
      if (e instanceof IntegrationNotConfirmed) {
        response = { status: 503, body: failure(503, "crm_integration_not_configured", "upstream"), headers: {} };
        break;
      }
      const err = e instanceof UpstreamError ? e : new UpstreamError("unexpected upstream failure", false, 502);
      deps.log({ event: "upstream_error", submission_id: submissionId, attempt, retryable: err.retryable });
      const retryAfter = err.retryAfterS ?? 0;
      if (!err.retryable || attempt > BOUNDS.maxRetries || retryAfter > 30) {
        const headers: Record<string, string> = retryAfter ? { "Retry-After": String(Math.trunc(retryAfter)) } : {};
        response = { status: err.status, body: failure(err.status, "upstream_failure", "upstream"), headers };
        break;
      }
      await deps.sleep(Math.max(500 * 2 ** (attempt - 1), retryAfter * 1000));
    }
  }
  if (response === null) {
    if (crmResult && crmResult.outcome === "saved" && crmResult.reference) {
      response = { status: 201, body: { status: "saved", inquiry_reference: await opaqueReference(submissionId, crmResult.reference), message: UI_TEXT.saved, next_step: BOOKING_URL }, headers: {} };
    } else if (crmResult && crmResult.outcome === "queued" && crmResult.reference && deps.adapter.durableQueue) {
      response = { status: 202, body: { status: "received_for_processing", inquiry_reference: await opaqueReference(submissionId, crmResult.reference), message: UI_TEXT.queued, next_step: BOOKING_URL }, headers: {} };
    } else {
      response = { status: 502, body: failure(502, "upstream_unconfirmed", "upstream"), headers: {} };
    }
  }
  const state = response.status === 201 ? "saved" : response.status === 202 ? "queued" : "failed";
  await deps.store.complete(submissionId, { state, status: response.status, body: response.body });
  deps.log({ event: "completed", submission_id: submissionId, status: response.status });
  return response;
}
'''


def render_ts() -> str:
    replacements = {
        "__MAX_NAME_LEN__": str(C.MAX_NAME_LEN),
        "__MAX_MESSAGE_LEN__": str(C.MAX_MESSAGE_LEN),
        "__MAX_PAYLOAD_BYTES__": str(C.MAX_PAYLOAD_BYTES),
        "__TIMEOUT_MS__": str(C.UPSTREAM_TIMEOUT_S * 1000),
        "__MAX_RETRIES__": str(C.MAX_RETRIES),
        "__RETENTION_HOURS__": str(C.IDEMPOTENCY_RETENTION_HOURS),
        "__BOOKING_URL__": C.BOOKING_URL,
        "__ALLOWED_FIELDS__": json.dumps(C.INQUIRY_ALLOWED_FIELDS),
        "__PRIVILEGED_FIELDS__": json.dumps(C.INQUIRY_PRIVILEGED_FIELDS_REJECTED),
        "__UI_TEXT__": json.dumps(UI_TEXT),
    }
    text = TS_TEMPLATE
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def build(paths: Paths | None = None) -> Path:
    paths = paths or default_paths()
    text = render_ts()
    for forbidden in (C.GHL_LOCATION_ID, C.DISALLOWED_LOCATION_ID):
        if forbidden in text:
            raise ValueError("inquiry.ts must not hard-code a location ID")
    return emit("server_function_inquiry_ts", paths.out / "server_functions" / "inquiry.ts", text, STATUS.DRAFT,
                paths, source="src/inquiry_handler.py")


if __name__ == "__main__":
    print(build())
