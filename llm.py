"""
The one place this project talks to Claude.

Every Claude call goes through one of two methods:

* `Claude.structured()` asks for an answer that must fit a Pydantic schema - used for
  reading a job description, judging a resume, and writing interview questions.
* `Claude.converse()` takes one step of a tool-using conversation - used by the chat turn.

Nothing else in the project builds an API request, so this file is also the seam the
tests use: they hand the agent a scripted stand-in with the same two methods and run
every conversation flow without a network or an API key.
"""
from __future__ import annotations

import os
import threading
from typing import TypeVar

import anthropic
from anthropic.types.beta import BetaMessage
from pydantic import BaseModel, ValidationError

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"
# On a safety-classifier refusal the API re-runs the request on Anthropic's recommended
# fallback model instead of returning nothing. "default" routes by refusal category.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_TOKENS = 16000

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Claude could not produce a usable answer (API failure, refusal, truncation)."""


class Claude:
    def __init__(self, model: str | None = None, effort: str | None = None,
                 client: anthropic.Anthropic | None = None):
        self.model = model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL
        self.effort = effort or os.environ.get("ANTHROPIC_EFFORT") or DEFAULT_EFFORT
        # Credentials come from the environment (ANTHROPIC_API_KEY or an `ant auth` profile).
        self.client = client or anthropic.Anthropic()
        # A key that spans several workspaces must name one on every request.
        workspace = (os.environ.get("ANTHROPIC_WORKSPACE_ID") or "").strip()
        self._workspace = {"workspace_id": workspace} if workspace else {}
        # Token totals for the session, so the chat can say what a conversation cost.
        self.usage = {"calls": 0, "input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
        self._usage_lock = threading.Lock()  # Round 2 calls Claude from several threads

    def structured(self, *, system: str, prompt: str, schema: type[T]) -> T:
        """One request whose answer is validated against `schema`."""
        response = self._request(self.client.beta.messages.parse, system=system, output_format=schema,
                                 messages=[{"role": "user", "content": prompt}])
        if response.parsed_output is None:
            raise LLMError(f"Claude's answer did not match the {schema.__name__} schema.")
        return response.parsed_output

    def converse(self, *, system: str, messages: list[dict], tools: list[dict]) -> BetaMessage:
        """One step of a tool-using conversation; the caller runs any tools it asks for."""
        return self._request(self.client.beta.messages.create, system=system, messages=messages, tools=tools,
                             cache_control={"type": "ephemeral"})

    def _request(self, method, **request) -> BetaMessage:
        """Send one request; every way it can fail comes back as an LLMError with a readable message."""
        try:
            response = method(model=self.model, max_tokens=MAX_TOKENS, output_config={"effort": self.effort},
                              betas=[FALLBACK_BETA], fallbacks="default", **self._workspace, **request)
        except anthropic.APIError as exc:
            raise LLMError(_describe_api_error(exc)) from exc
        except ValidationError as exc:  # parse() could not read a cut-off or malformed answer
            raise LLMError("Claude's answer was cut off or did not match the expected format.") from exc
        except TypeError as exc:
            if "authentication" not in str(exc):  # a genuine bug: let it surface
                raise
            raise LLMError("No Anthropic credentials found. Copy .env.example to .env and set "
                           "ANTHROPIC_API_KEY.") from exc
        self._record(response)
        _check_stop_reason(response)
        return response

    def _record(self, response: BetaMessage) -> None:
        u = response.usage
        with self._usage_lock:
            self.usage = {"calls": self.usage["calls"] + 1,
                          "input_tokens": self.usage["input_tokens"] + (u.input_tokens or 0),
                          "cache_read_input_tokens": self.usage["cache_read_input_tokens"]
                          + (u.cache_read_input_tokens or 0),
                          "output_tokens": self.usage["output_tokens"] + (u.output_tokens or 0)}


def _check_stop_reason(response: BetaMessage) -> None:
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        raise LLMError(f"Claude declined this request (category: {category or 'unspecified'}).")
    if response.stop_reason == "max_tokens":
        raise LLMError(f"Claude's answer was cut off at {MAX_TOKENS} tokens.")


def _describe_api_error(exc: anthropic.APIError) -> str:
    """A message a user can act on, most specific failure first."""
    if isinstance(exc, anthropic.AuthenticationError):
        return "The Anthropic API key was rejected. Check ANTHROPIC_API_KEY in your .env file."
    if isinstance(exc, anthropic.RateLimitError):
        return "Rate limited by the Anthropic API. Wait a minute and try again."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not reach the Anthropic API. Check your internet connection."
    if isinstance(exc, anthropic.APIStatusError):
        return f"The Anthropic API returned an error ({exc.status_code}): {exc.message}"
    return f"Anthropic API error: {exc}"
