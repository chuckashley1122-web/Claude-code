"""Video / voice / image generation interface (HeyGen, Creatomate, ElevenLabs,
Sora / Runway, image generation stand-in): writes a stub .json job record and
renders nothing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from adapters.base import LiveAdapter, MockAdapter, stable_id

PROVIDERS = {"heygen", "creatomate", "elevenlabs", "sora", "openai_images"}
STATUS_STUB = "dry_run_complete"


class VideoGenClient(Protocol):
    def create_job(self, provider: str, kind: str, payload: dict) -> dict: ...
    def status(self, job_id: str) -> dict: ...


@dataclass
class MockVideoGen(MockAdapter):
    service: str = "video_gen"

    def create_job(self, provider: str, kind: str, payload: dict) -> dict:
        self._guard("create_job", provider=provider, kind=kind)
        if provider not in PROVIDERS:
            raise ValueError(f"unknown video provider {provider!r}")
        job_id = stable_id(f"{provider}-{kind}", payload)
        record = {
            "job_id": job_id, "provider": provider, "kind": kind, "payload": payload,
            "status": STATUS_STUB, "rendered": False, "output_url": None,
            "note": "Stub job record. Nothing was rendered, uploaded, or charged.",
        }
        (self._out("video_jobs") / f"{job_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return {"job_id": job_id, "status": STATUS_STUB}

    def status(self, job_id: str) -> dict:
        self._guard("status", job_id=job_id)
        path = self.out_dir / "video_jobs" / f"{job_id}.json"
        if not path.is_file():
            raise LookupError(f"unknown job {job_id}")
        record = json.loads(path.read_text(encoding="utf-8"))
        return {"job_id": job_id, "status": record["status"], "output_url": record["output_url"],
                "stub_record": str(path)}


class LiveVideoGen(LiveAdapter):
    service = "video_gen"
    credential_env = ("HEYGEN_API_KEY", "CREATOMATE_API_KEY", "ELEVENLABS_API_KEY", "OPENAI_API_KEY")

    def create_job(self, provider: str, kind: str, payload: dict) -> dict:
        self._refuse("create_job")

    def status(self, job_id: str) -> dict:
        self._refuse("status")
