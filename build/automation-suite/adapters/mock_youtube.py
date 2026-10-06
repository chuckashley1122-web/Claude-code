"""YouTube Data API v3 interface: serves data/fixtures/youtube_top.sample.json.

The search mirrors the source's call (order=viewCount, publishedAfter, maxResults)
over synthetic fixture rows only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from adapters.base import LiveAdapter, MockAdapter, load_json_fixture


class YouTubeClient(Protocol):
    def search(self, query: str, order: str = "viewCount", published_after: Optional[str] = None,
               max_results: int = 50) -> list[dict]: ...


@dataclass
class MockYouTube(MockAdapter):
    service: str = "youtube"

    def search(self, query: str, order: str = "viewCount", published_after: Optional[str] = None,
               max_results: int = 50) -> list[dict]:
        self._guard("search", query=query, order=order)
        if order not in ("viewCount", "date"):
            raise ValueError(f"unsupported order {order!r}")
        items = [dict(i) for i in load_json_fixture("youtube_top.sample.json", self.fixtures_dir)["items"]]
        if published_after:
            items = [i for i in items if i["published_at"] >= published_after]
        key = "views" if order == "viewCount" else "published_at"
        items.sort(key=lambda i: i[key], reverse=True)
        return items[: max(0, int(max_results))]


class LiveYouTube(LiveAdapter):
    service = "youtube"
    credential_env = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN")

    def search(self, query, order="viewCount", published_after=None, max_results=50):
        self._refuse("search")
