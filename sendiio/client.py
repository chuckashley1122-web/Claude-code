import json
import urllib.error
import urllib.request
from typing import Any


class SendiioError(RuntimeError):
    pass


class SendiioClient:
    def __init__(self, token: str, secret: str, base_url: str = "https://sendiio.com/api/v1"):
        if not token or not secret:
            raise SendiioError("SENDIIO_TOKEN and SENDIIO_SECRET are required")
        self.token = token
        self.secret = secret
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("token", self.token)
        req.add_header("secret", self.secret)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise SendiioError(f"{method} {path} -> HTTP {e.code}: {e.read().decode('utf-8', 'replace')}") from e
        except urllib.error.URLError as e:
            raise SendiioError(f"{method} {path} -> network error: {e.reason}") from e
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise SendiioError(f"{method} {path} returned non-JSON body: {raw[:200]}") from e

    def check_credentials(self) -> dict[str, Any]:
        return self._request("POST", "/auth/check")

    def subscribe_email(self, list_id: str, email: str, first_name: str = "", last_name: str = "",
                        extra: dict[str, Any] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "list_id": list_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
        if extra:
            body.update(extra)
        return self._request("POST", "/lists/subscribe-email", body)

    def send_broadcast(self, list_id: str, subject: str, html_body: str, from_name: str,
                       from_email: str, reply_to: str | None = None) -> dict[str, Any]:
        # NOTE: exact endpoint path/field names need to be confirmed from the
        # logged-in SendIIO docs (sendiio.com/pages/view/sendiio-api). The shape
        # below is the placeholder I'll refine once those details are pasted in.
        body = {
            "list_id": list_id,
            "subject": subject,
            "html": html_body,
            "from_name": from_name,
            "from_email": from_email,
            "reply_to": reply_to or from_email,
        }
        return self._request("POST", "/broadcasts/send-email", body)
