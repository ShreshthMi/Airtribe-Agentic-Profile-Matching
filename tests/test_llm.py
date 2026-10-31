"""The Claude wrapper in llm.py: request shape, stop reasons, error messages and usage totals."""
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from pydantic import BaseModel, ValidationError

from llm import DEFAULT_MODEL, FALLBACK_BETA, Claude, LLMError

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


class Answer(BaseModel):
    value: int


def response(stop_reason: str = "end_turn", parsed=Answer(value=1), category: str | None = None):
    return SimpleNamespace(stop_reason=stop_reason, parsed_output=parsed, content=[],
                           stop_details=SimpleNamespace(category=category) if category else None,
                           usage=SimpleNamespace(input_tokens=100, cache_read_input_tokens=None, output_tokens=20))


class FakeMessages:
    def __init__(self, result):
        self.result, self.calls = result, []

    def _call(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    parse = create = _call


def claude_with(result, **kwargs) -> tuple[Claude, FakeMessages]:
    messages = FakeMessages(result)
    return Claude(client=SimpleNamespace(beta=SimpleNamespace(messages=messages)), **kwargs), messages


def test_structured_request_carries_model_effort_schema_and_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_WORKSPACE_ID", raising=False)
    claude, messages = claude_with(response())

    assert claude.structured(system="s", prompt="p", schema=Answer) == Answer(value=1)

    [call] = messages.calls
    assert call["model"] == DEFAULT_MODEL == "claude-opus-5-5"
    assert call["output_format"] is Answer and call["output_config"] == {"effort": "medium"}
    assert call["betas"] == [FALLBACK_BETA] and call["fallbacks"] == "default"
    assert call["messages"] == [{"role": "user", "content": "p"}] and "workspace_id" not in call


def test_settings_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("ANTHROPIC_EFFORT", "low")
    monkeypatch.setenv("ANTHROPIC_WORKSPACE_ID", " wrkspc_123 ")
    claude, messages = claude_with(response())

    claude.converse(system="s", messages=[], tools=[])

    [call] = messages.calls
    assert (call["model"], call["output_config"], call["workspace_id"]) == ("claude-sonnet-5-5", {"effort": "low"},
                                                                             "wrkspc_123")
    assert call["cache_control"] == {"type": "ephemeral"}


@pytest.mark.parametrize("result, message", [
    (response(stop_reason="refusal", category="cyber"), r"declined this request \(category: cyber\)"),
    (response(stop_reason="max_tokens"), "cut off at 16000 tokens"),
    (response(parsed=None), "did not match the Answer schema"),
])
def test_unusable_answers_raise_llm_error(result, message):
    claude, _ = claude_with(result)

    with pytest.raises(LLMError, match=message):
        claude.structured(system="s", prompt="p", schema=Answer)


@pytest.mark.parametrize("error, message", [
    (anthropic.AuthenticationError("x", response=httpx2.Response(401, request=REQUEST), body=None),
     "API key was rejected"),
    (anthropic.RateLimitError("x", response=httpx2.Response(429, request=REQUEST), body=None), "Rate limited"),
    (anthropic.APIConnectionError(request=REQUEST), "Could not reach the Anthropic API"),
    (anthropic.InternalServerError("boom", response=httpx2.Response(500, request=REQUEST), body=None),
     r"returned an error \(500\): boom"),
])
def test_api_errors_become_messages_a_user_can_act_on(error, message):
    claude, _ = claude_with(error)

    with pytest.raises(LLMError, match=message):
        claude.converse(system="s", messages=[], tools=[])


def test_usage_is_totalled_across_calls_including_refused_ones():
    claude, messages = claude_with(response())
    claude.structured(system="s", prompt="p", schema=Answer)
    messages.result = response(stop_reason="refusal")
    with pytest.raises(LLMError):
        claude.converse(system="s", messages=[], tools=[])

    assert claude.usage == {"calls": 2, "input_tokens": 200, "cache_read_input_tokens": 0, "output_tokens": 40}


def test_an_answer_parse_cannot_read_becomes_an_llm_error():
    try:
        Answer.model_validate_json('{"value": ')
    except ValidationError as exc:
        broken = exc
    claude, _ = claude_with(broken)

    with pytest.raises(LLMError, match="cut off or did not match the expected format"):
        claude.structured(system="s", prompt="p", schema=Answer)


def test_missing_credentials_become_an_llm_error_but_other_type_errors_surface():
    claude, messages = claude_with(TypeError("Could not resolve authentication method. Expected api_key ..."))
    with pytest.raises(LLMError, match="No Anthropic credentials found"):
        claude.converse(system="s", messages=[], tools=[])

    messages.result = TypeError("unexpected keyword argument 'tolls'")
    with pytest.raises(TypeError, match="tolls"):
        claude.converse(system="s", messages=[], tools=[])
