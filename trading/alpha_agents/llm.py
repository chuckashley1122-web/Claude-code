"""Adapter between the analyst layer and Claude.

The analysts never talk to a vendor SDK directly — they hold a
:class:`~alpha_agents.interfaces.LanguageModel`. That keeps them unit-testable
with a stub and confines provider specifics to this one file.

The whole system runs with no model at all: every analyst falls back to its
deterministic rules when handed ``None``. The LLM upgrades the *reasoning and
explanation*, it is not load-bearing for the pipeline to function.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

DEFAULT_MODEL = "claude-opus-5"


class LanguageModelError(RuntimeError):
    """Raised when the model could not produce a usable answer."""


class ModelRefusedError(LanguageModelError):
    """The model's safety classifiers declined the request."""


@dataclass
class AnthropicLanguageModel:
    """Claude-backed implementation of the ``LanguageModel`` protocol.

    ``anthropic`` is an optional dependency, imported lazily so that importing
    this package never fails on a machine that only wants the offline path.
    """

    model: str = DEFAULT_MODEL
    effort: str = "high"
    max_tokens: int = 4000
    api_key: str | None = None
    _client: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ImportError(
                "The Claude-backed analysts need the Anthropic SDK. "
                "Install it with `pip install anthropic`, or run with "
                "--no-llm to use the deterministic analysts."
            ) from exc
        # A bare constructor resolves ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN,
        # or an `ant auth login` profile — do not demand an explicit key.
        self._client = (
            anthropic.Anthropic(api_key=self.api_key)
            if self.api_key
            else anthropic.Anthropic()
        )
        return self._client

    def complete_json(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict,
        max_tokens: int | None = None,
    ) -> dict:
        client = self._get_client()

        response = client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            # Opus 5's classifiers can decline; "default" routes the retry to
            # Anthropic's recommended fallback rather than us pinning a model
            # we would then have to maintain.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=[
                {
                    "type": "text",
                    "text": system,
                    # The system prompt is identical across every symbol in a
                    # scan, so caching it turns N symbols into one cold write.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
            messages=[{"role": "user", "content": prompt}],
        )

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise ModelRefusedError(
                f"Model declined the request (category={category}). "
                "This is unexpected for market analysis — check the prompt."
            )

        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise LanguageModelError(
                f"No text content in response (stop_reason={response.stop_reason})"
            )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LanguageModelError(f"Model returned non-JSON output: {text[:200]}") from exc


@dataclass
class StubLanguageModel:
    """Deterministic stand-in used by the tests.

    Returns queued responses in order; raises once exhausted so a test that
    makes more calls than it expected fails loudly instead of silently reusing
    the last answer.
    """

    responses: list[dict]
    calls: list[dict] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.calls is None:
            self.calls = []

    def complete_json(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict,
        max_tokens: int | None = None,
    ) -> dict:
        self.calls.append({"system": system, "prompt": prompt, "schema": schema})
        if not self.responses:
            raise LanguageModelError("StubLanguageModel ran out of queued responses")
        return self.responses.pop(0)
