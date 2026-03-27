"""Pydantic models for structured LLM output and parsing utilities."""

import json
import re
from enum import StrEnum

from pydantic import BaseModel, Field


class MutationStyle(StrEnum):
    """How an archetype typically mutates narratives."""

    EMOTIONAL_AMPLIFICATION = "emotional_amplification"
    CONSPIRACY_FRAMING = "conspiracy_framing"
    DECONTEXTUALIZATION = "decontextualization"
    FABRICATION = "fabrication"
    EXAGGERATION = "exaggeration"
    POLITICAL_REFRAMING = "political_reframing"


class ArchetypeProfile(BaseModel):
    """LLM-generated behavioral archetype for a population segment."""

    name: str = Field(description="Short persona name, e.g. 'Skeptical Tech Worker'")
    description: str = Field(description="1-2 sentence description of this archetype")
    susceptibility: float = Field(ge=0.0, le=1.0)
    sharing_tendency: float = Field(ge=0.0, le=1.0)
    trust_mainstream_media: float = Field(ge=0.0, le=1.0)
    trust_social_peers: float = Field(ge=0.0, le=1.0)
    emotional_reactivity: float = Field(ge=0.0, le=1.0)
    correction_receptiveness: float = Field(ge=0.0, le=1.0)
    mutation_style: MutationStyle = MutationStyle.EXAGGERATION
    population_percentage: float = Field(ge=0.0, le=100.0)


class ArchetypeListOutput(BaseModel):
    """Wrapper for a list of archetypes from LLM output."""

    archetypes: list[ArchetypeProfile]


class NarrativeSeedOutput(BaseModel):
    """Structured extraction of a seed narrative from user text."""

    primary_claim: str = Field(description="The main claim or assertion")
    secondary_claims: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    tone: str = Field(
        default="neutral",
        description="emotional tone: alarming, neutral, hopeful, etc.",
    )
    category: str = Field(
        default="general",
        description="topic: health, politics, finance, technology, etc.",
    )
    virality_estimate: float = Field(default=1.0, ge=0.0, le=2.0)
    emotional_charge: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty_score: float = Field(default=0.5, ge=0.0, le=1.0)


class MutatedNarrative(BaseModel):
    """LLM-generated narrative mutation."""

    content: str = Field(description="The mutated narrative text")
    mutation_type: MutationStyle
    emotional_charge_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
    virality_delta: float = Field(default=0.0, ge=-1.0, le=1.0)


class ReportSection(BaseModel):
    """A single section of the generated report."""

    title: str
    content: str


class ReportOutput(BaseModel):
    """Structured report from LLM synthesis."""

    sections: list[ReportSection]


def parse_json_response(text: str) -> dict[str, object] | list[object]:
    """Extract and parse JSON from an LLM response that may contain markdown fences."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass

    # Try finding first { or [ to end of matching bracket
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        # Find matching closing bracket
        depth = 0
        for i in range(start, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])  # type: ignore[no-any-return]
                    except json.JSONDecodeError:
                        break

    raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}")


def parse_archetypes(text: str) -> list[ArchetypeProfile]:
    """Parse LLM response into a list of ArchetypeProfile objects."""
    data = parse_json_response(text)
    if isinstance(data, dict) and "archetypes" in data:
        return ArchetypeListOutput.model_validate(data).archetypes
    if isinstance(data, list):
        return [ArchetypeProfile.model_validate(item) for item in data]
    raise ValueError(f"Unexpected archetype response structure: {type(data)}")


def parse_narrative_seed(text: str) -> NarrativeSeedOutput:
    """Parse LLM response into a NarrativeSeedOutput."""
    data = parse_json_response(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict for narrative seed, got {type(data)}")
    return NarrativeSeedOutput.model_validate(data)


def parse_mutation(text: str) -> MutatedNarrative:
    """Parse LLM response into a MutatedNarrative."""
    data = parse_json_response(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict for mutation, got {type(data)}")
    return MutatedNarrative.model_validate(data)
