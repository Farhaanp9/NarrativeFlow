"""Tests for LLM output parsing — no LLM required."""

import json

import pytest

from narrativeflow.llm.parser import (
    ArchetypeProfile,
    MutatedNarrative,
    MutationStyle,
    NarrativeSeedOutput,
    parse_archetypes,
    parse_json_response,
    parse_mutation,
    parse_narrative_seed,
)

# --- JSON extraction ---


def test_parse_plain_json() -> None:
    data = parse_json_response('{"key": "value"}')
    assert data == {"key": "value"}


def test_parse_json_from_markdown_fence() -> None:
    text = '```json\n{"key": "value"}\n```'
    data = parse_json_response(text)
    assert data == {"key": "value"}


def test_parse_json_with_surrounding_text() -> None:
    text = 'Here is the result:\n{"key": "value"}\nThat is all.'
    data = parse_json_response(text)
    assert data == {"key": "value"}


def test_parse_json_array() -> None:
    data = parse_json_response('[1, 2, 3]')
    assert data == [1, 2, 3]


def test_parse_invalid_json_raises() -> None:
    with pytest.raises(ValueError, match="Could not extract valid JSON"):
        parse_json_response("this is not json at all")


# --- Archetype parsing ---


VALID_ARCHETYPE = {
    "name": "Test Persona",
    "description": "A test archetype for unit testing.",
    "susceptibility": 0.5,
    "sharing_tendency": 0.3,
    "trust_mainstream_media": 0.7,
    "trust_social_peers": 0.4,
    "emotional_reactivity": 0.6,
    "correction_receptiveness": 0.8,
    "mutation_style": "exaggeration",
    "population_percentage": 50.0,
}


def test_parse_archetype_wrapped() -> None:
    """Parse archetypes from {archetypes: [...]} wrapper."""
    other = {**VALID_ARCHETYPE, "name": "Other", "population_percentage": 50.0}
    text = json.dumps({"archetypes": [VALID_ARCHETYPE, other]})
    result = parse_archetypes(text)
    assert len(result) == 2
    assert result[0].name == "Test Persona"
    assert result[1].name == "Other"


def test_parse_archetype_bare_list() -> None:
    """Parse archetypes from a bare JSON array."""
    text = json.dumps([VALID_ARCHETYPE])
    result = parse_archetypes(text)
    assert len(result) == 1
    assert isinstance(result[0], ArchetypeProfile)


def test_archetype_field_ranges() -> None:
    """All float fields should be within [0, 1]."""
    profile = ArchetypeProfile.model_validate(VALID_ARCHETYPE)
    assert 0.0 <= profile.susceptibility <= 1.0
    assert 0.0 <= profile.sharing_tendency <= 1.0
    assert 0.0 <= profile.trust_mainstream_media <= 1.0
    assert 0.0 <= profile.trust_social_peers <= 1.0
    assert 0.0 <= profile.emotional_reactivity <= 1.0
    assert 0.0 <= profile.correction_receptiveness <= 1.0
    assert 0.0 <= profile.population_percentage <= 100.0


def test_archetype_invalid_range_raises() -> None:
    """Values out of range should cause validation error."""
    bad = {**VALID_ARCHETYPE, "susceptibility": 1.5}
    with pytest.raises(ValueError):
        ArchetypeProfile.model_validate(bad)


def test_all_mutation_styles_accepted() -> None:
    """Every MutationStyle enum value should be valid."""
    for style in MutationStyle:
        data = {**VALID_ARCHETYPE, "mutation_style": style.value}
        profile = ArchetypeProfile.model_validate(data)
        assert profile.mutation_style == style


def test_archetype_population_pct_sum() -> None:
    """Parsed archetypes should have population_pct roughly summing to 100."""
    archetypes_data = [
        {**VALID_ARCHETYPE, "name": f"Type{i}", "population_percentage": p}
        for i, p in enumerate([30, 25, 20, 15, 10])
    ]
    text = json.dumps({"archetypes": archetypes_data})
    result = parse_archetypes(text)
    total = sum(a.population_percentage for a in result)
    assert abs(total - 100.0) < 1.0


# --- Narrative seed parsing ---


def test_parse_narrative_seed() -> None:
    data = {
        "primary_claim": "New study links sweetener to cancer",
        "secondary_claims": ["Study conducted over 10 years"],
        "entities": ["FDA", "Aspartame"],
        "tone": "alarming",
        "category": "health",
        "virality_estimate": 1.5,
        "emotional_charge": 0.8,
        "novelty_score": 0.7,
    }
    result = parse_narrative_seed(json.dumps(data))
    assert isinstance(result, NarrativeSeedOutput)
    assert result.primary_claim == "New study links sweetener to cancer"
    assert result.tone == "alarming"
    assert 0.0 <= result.virality_estimate <= 2.0


def test_parse_narrative_seed_defaults() -> None:
    """Minimal input should use defaults for optional fields."""
    data = {"primary_claim": "Something happened"}
    result = parse_narrative_seed(json.dumps(data))
    assert result.tone == "neutral"
    assert result.virality_estimate == 1.0


# --- Mutation parsing ---


def test_parse_mutation() -> None:
    data = {
        "content": "BREAKING: The sweetener is actually DEADLY",
        "mutation_type": "exaggeration",
        "emotional_charge_delta": 0.3,
        "virality_delta": 0.2,
    }
    result = parse_mutation(json.dumps(data))
    assert isinstance(result, MutatedNarrative)
    assert result.mutation_type == MutationStyle.EXAGGERATION
    assert result.emotional_charge_delta == 0.3


# --- Edge cases ---


def test_parse_json_with_code_fence_no_language() -> None:
    text = '```\n{"key": "value"}\n```'
    data = parse_json_response(text)
    assert data == {"key": "value"}


def test_parse_archetypes_from_markdown_response() -> None:
    """Simulate a real LLM response with markdown fences."""
    payload = json.dumps({"archetypes": [VALID_ARCHETYPE]})
    text = f"Here are the archetypes:\n```json\n{payload}\n```\nDone."
    result = parse_archetypes(text)
    assert len(result) == 1
