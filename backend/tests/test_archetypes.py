"""Tests for archetype generation — uses mock fallback (CI-safe)."""

import pytest

from narrativeflow.config import Settings
from narrativeflow.llm.client import LLMClient, _get_default_archetypes
from narrativeflow.llm.parser import ArchetypeProfile, MutationStyle

# --- Default archetype tests (no LLM needed) ---


def test_default_archetypes_valid() -> None:
    """Default archetypes should all be valid ArchetypeProfile objects."""
    defaults = _get_default_archetypes(8)
    assert len(defaults) == 8
    for arch in defaults:
        assert isinstance(arch, ArchetypeProfile)
        assert 0.0 <= arch.susceptibility <= 1.0
        assert 0.0 <= arch.sharing_tendency <= 1.0
        assert 0.0 <= arch.correction_receptiveness <= 1.0
        assert arch.mutation_style in MutationStyle


def test_default_archetypes_sum_to_100() -> None:
    """Default archetype population percentages should sum to 100."""
    defaults = _get_default_archetypes(8)
    total = sum(a.population_percentage for a in defaults)
    assert abs(total - 100.0) < 1.0


def test_default_archetypes_subset_renormalized() -> None:
    """Requesting fewer than available should return subset with re-normalized percentages."""
    subset = _get_default_archetypes(3)
    assert len(subset) == 3
    total = sum(a.population_percentage for a in subset)
    assert abs(total - 100.0) < 1.0


def test_default_archetypes_cover_spectrum() -> None:
    """Defaults should include both high and low susceptibility archetypes."""
    defaults = _get_default_archetypes(8)
    susceptibilities = [a.susceptibility for a in defaults]
    assert min(susceptibilities) <= 0.2, "Should have low-susceptibility archetype"
    assert max(susceptibilities) >= 0.7, "Should have high-susceptibility archetype"


def test_default_archetypes_diverse_mutation_styles() -> None:
    """Defaults should cover multiple mutation styles."""
    defaults = _get_default_archetypes(8)
    styles = {a.mutation_style for a in defaults}
    assert len(styles) >= 3, f"Only {len(styles)} mutation styles in defaults"


# --- LLM client fallback tests ---


@pytest.mark.asyncio
async def test_generate_archetypes_fallback() -> None:
    """When LLM is unavailable, should return valid default archetypes."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",  # intentionally unreachable
        llm_api_key="test",
        llm_model="nonexistent",
    )
    client = LLMClient(settings)
    archetypes = await client.generate_archetypes("Test headline about climate change", count=10)

    assert len(archetypes) > 0
    for arch in archetypes:
        assert isinstance(arch, ArchetypeProfile)
        assert 0.0 <= arch.susceptibility <= 1.0

    total_pct = sum(a.population_percentage for a in archetypes)
    assert abs(total_pct - 100.0) < 1.0


@pytest.mark.asyncio
async def test_extract_narrative_fallback() -> None:
    """When LLM is unavailable, should return default narrative extraction."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    client = LLMClient(settings)
    seed_text = "New study links popular sweetener to cancer risk"
    result = await client.extract_narrative(seed_text)

    assert result.primary_claim == seed_text
    assert 0.0 <= result.virality_estimate <= 2.0
    assert 0.0 <= result.emotional_charge <= 1.0


@pytest.mark.asyncio
async def test_mutate_narrative_fallback() -> None:
    """When LLM is unavailable, should return a basic mutation."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    client = LLMClient(settings)
    result = await client.mutate_narrative(
        archetype_name="Test Archetype",
        archetype_description="A test persona",
        mutation_style="exaggeration",
        narrative_content="Original claim about something",
    )

    assert "Original claim" in result.content
    assert result.mutation_type == MutationStyle.EXAGGERATION


@pytest.mark.asyncio
async def test_generate_report_fallback() -> None:
    """When LLM is unavailable, should return a fallback markdown report."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    client = LLMClient(settings)
    report = await client.generate_report(
        seed_text="Test headline",
        population_size=500,
        topology="barabasi_albert",
        total_ticks=100,
        final_counts={"S": 200, "M": 100, "I": 50, "R": 150},
        peak_velocity=0.05,
        total_transitions={"S_to_M": 150, "S_to_I": 50, "M_to_I": 30, "to_R": 150},
    )

    assert "# Simulation Report" in report
    assert "Executive Summary" in report
    assert "500" in report  # population size
    assert "Test headline" in report
