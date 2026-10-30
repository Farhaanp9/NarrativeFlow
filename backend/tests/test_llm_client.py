"""Tests for LLM client retry and unavailability handling (no LLM needed)."""

import httpx
import pytest
from openai import APIConnectionError

from narrativeflow.config import Settings
from narrativeflow.llm import client as client_module
from narrativeflow.llm.client import MAX_RETRIES, LLMClient


def _client_with_failing_create(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> tuple[LLMClient, list[int]]:
    """Return a client whose completion call always raises, and a call log."""
    client = LLMClient(Settings(llm_base_url="http://test/v1"))
    calls: list[int] = []

    async def failing_create(**_: object) -> object:
        calls.append(1)
        raise error

    monkeypatch.setattr(client.client.chat.completions, "create", failing_create)
    return client, calls


def _connection_error() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "http://test/v1"))


@pytest.mark.asyncio
async def test_unreachable_llm_is_tried_once_then_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A connection error is not retried, and later calls go straight to fallbacks."""
    client, calls = _client_with_failing_create(monkeypatch, _connection_error())

    first = await client.extract_narrative("Seed one")
    second = await client.extract_narrative("Seed two")
    await client.mutate_narrative("A", "A", "exaggeration", "Seed two")

    assert len(calls) == 1
    assert first.primary_claim == "Seed one"
    assert second.primary_claim == "Seed two"


@pytest.mark.asyncio
async def test_llm_is_tried_again_after_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Once the cooldown has passed, the client calls the LLM again."""
    monkeypatch.setattr(client_module, "UNAVAILABLE_COOLDOWN_S", 0.0)
    client, calls = _client_with_failing_create(monkeypatch, _connection_error())

    await client.extract_narrative("Seed")
    await client.extract_narrative("Seed")

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_other_llm_errors_are_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Errors other than an unreachable server keep the full retry budget."""
    client, calls = _client_with_failing_create(monkeypatch, ValueError("bad reply"))

    await client.extract_narrative("Seed")

    assert len(calls) == MAX_RETRIES
