import "dotenv/config";

const DEFAULT_BASE_URL = "https://services.leadconnectorhq.com";
const DEFAULT_API_VERSION = "2021-07-28";

export interface GhlClientOptions {
  apiKey?: string;
  locationId?: string;
  baseUrl?: string;
  apiVersion?: string;
  fetchImpl?: typeof fetch;
}

export interface RequestOptions {
  query?: Record<string, string | number | boolean | undefined | null>;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export class GhlApiError extends Error {
  readonly status: number;
  readonly url: string;
  readonly body: unknown;

  constructor(message: string, status: number, url: string, body: unknown) {
    super(message);
    this.name = "GhlApiError";
    this.status = status;
    this.url = url;
    this.body = body;
  }
}

export class GhlClient {
  readonly locationId: string;
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly apiVersion: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: GhlClientOptions = {}) {
    const apiKey = options.apiKey ?? process.env.GHL_API_KEY;
    const locationId = options.locationId ?? process.env.GHL_LOCATION_ID;

    if (!apiKey) {
      throw new Error(
        "Missing GHL_API_KEY. Set it in .env or pass apiKey to GhlClient.",
      );
    }
    if (!locationId) {
      throw new Error(
        "Missing GHL_LOCATION_ID. Set it in .env or pass locationId to GhlClient.",
      );
    }

    this.apiKey = apiKey;
    this.locationId = locationId;
    this.baseUrl = (options.baseUrl ?? process.env.GHL_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.apiVersion = options.apiVersion ?? process.env.GHL_API_VERSION ?? DEFAULT_API_VERSION;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async request<T = unknown>(
    method: string,
    path: string,
    opts: RequestOptions = {},
  ): Promise<T> {
    const url = new URL(path.startsWith("/") ? path : `/${path}`, this.baseUrl);
    if (opts.query) {
      for (const [key, value] of Object.entries(opts.query)) {
        if (value === undefined || value === null) continue;
        url.searchParams.set(key, String(value));
      }
    }

    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      Version: this.apiVersion,
      Accept: "application/json",
      ...opts.headers,
    };

    let body: string | undefined;
    if (opts.body !== undefined) {
      headers["Content-Type"] ??= "application/json";
      body = typeof opts.body === "string" ? opts.body : JSON.stringify(opts.body);
    }

    const init: RequestInit = { method, headers };
    if (body !== undefined) init.body = body;
    if (opts.signal) init.signal = opts.signal;

    const response = await this.fetchImpl(url.toString(), init);

    const raw = await response.text();
    const parsed: unknown = raw.length === 0
      ? undefined
      : tryParseJson(raw);

    if (!response.ok) {
      throw new GhlApiError(
        `GHL ${method} ${path} failed: ${response.status} ${response.statusText}`,
        response.status,
        url.toString(),
        parsed ?? raw,
      );
    }

    return parsed as T;
  }

  get<T = unknown>(path: string, opts: Omit<RequestOptions, "body"> = {}) {
    return this.request<T>("GET", path, opts);
  }

  post<T = unknown>(path: string, body?: unknown, opts: Omit<RequestOptions, "body"> = {}) {
    return this.request<T>("POST", path, { ...opts, body });
  }

  put<T = unknown>(path: string, body?: unknown, opts: Omit<RequestOptions, "body"> = {}) {
    return this.request<T>("PUT", path, { ...opts, body });
  }

  delete<T = unknown>(path: string, opts: Omit<RequestOptions, "body"> = {}) {
    return this.request<T>("DELETE", path, opts);
  }
}

function tryParseJson(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}
