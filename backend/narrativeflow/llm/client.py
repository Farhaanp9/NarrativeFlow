"""Unified async LLM client supporting Ollama (local) and cloud APIs."""

import structlog
from openai import AsyncOpenAI

from narrativeflow.config import Settings
from narrativeflow.llm.parser import (
    ArchetypeProfile,
    MutatedNarrative,
    NarrativeSeedOutput,
    parse_archetypes,
    parse_mutation,
    parse_narrative_seed,
)
from narrativeflow.llm.prompts import (
    ARCHETYPE_GENERATION_PROMPT,
    MUTATION_STYLE_DESCRIPTIONS,
    NARRATIVE_EXTRACTION_PROMPT,
    NARRATIVE_MUTATION_PROMPT,
    REPORT_SYNTHESIS_PROMPT,
    SYSTEM_PROMPT,
)

logger = structlog.get_logger()

# Default archetypes returned when LLM is unavailable
_DEFAULT_ARCHETYPES: list[dict[str, object]] = [
    {
        "name": "Credulous Consumer",
        "description": "Readily believes and shares sensational content without verification.",
        "susceptibility": 0.85, "sharing_tendency": 0.75,
        "trust_mainstream_media": 0.3, "trust_social_peers": 0.85,
        "emotional_reactivity": 0.8, "correction_receptiveness": 0.25,
        "mutation_style": "emotional_amplification", "population_percentage": 15.0,
    },
    {
        "name": "Skeptical Analyst",
        "description": "Questions claims, checks sources, and rarely shares unverified content.",
        "susceptibility": 0.15, "sharing_tendency": 0.2,
        "trust_mainstream_media": 0.8, "trust_social_peers": 0.25,
        "emotional_reactivity": 0.15, "correction_receptiveness": 0.9,
        "mutation_style": "decontextualization", "population_percentage": 10.0,
    },
    {
        "name": "Passive Observer",
        "description": "Consumes content but rarely shares. Moderate susceptibility.",
        "susceptibility": 0.5, "sharing_tendency": 0.15,
        "trust_mainstream_media": 0.5, "trust_social_peers": 0.5,
        "emotional_reactivity": 0.35, "correction_receptiveness": 0.55,
        "mutation_style": "exaggeration", "population_percentage": 30.0,
    },
    {
        "name": "Outrage Amplifier",
        "description": "Shares emotionally charged content to express anger or fear.",
        "susceptibility": 0.7, "sharing_tendency": 0.9,
        "trust_mainstream_media": 0.2, "trust_social_peers": 0.8,
        "emotional_reactivity": 0.9, "correction_receptiveness": 0.2,
        "mutation_style": "emotional_amplification", "population_percentage": 12.0,
    },
    {
        "name": "Conspiracy Theorist",
        "description": "Interprets events through conspiratorial frameworks.",
        "susceptibility": 0.8, "sharing_tendency": 0.85,
        "trust_mainstream_media": 0.05, "trust_social_peers": 0.7,
        "emotional_reactivity": 0.75, "correction_receptiveness": 0.1,
        "mutation_style": "conspiracy_framing", "population_percentage": 8.0,
    },
    {
        "name": "Active Debunker",
        "description": "Actively seeks to correct misinformation and share verified facts.",
        "susceptibility": 0.1, "sharing_tendency": 0.7,
        "trust_mainstream_media": 0.85, "trust_social_peers": 0.3,
        "emotional_reactivity": 0.3, "correction_receptiveness": 0.95,
        "mutation_style": "decontextualization", "population_percentage": 5.0,
    },
    {
        "name": "Partisan Sharer",
        "description": "Shares content aligned with political identity.",
        "susceptibility": 0.65, "sharing_tendency": 0.8,
        "trust_mainstream_media": 0.25, "trust_social_peers": 0.75,
        "emotional_reactivity": 0.7, "correction_receptiveness": 0.15,
        "mutation_style": "political_reframing", "population_percentage": 10.0,
    },
    {
        "name": "Casual Scroller",
        "description": "Engages superficially, occasionally shares without reading.",
        "susceptibility": 0.55, "sharing_tendency": 0.4,
        "trust_mainstream_media": 0.45, "trust_social_peers": 0.55,
        "emotional_reactivity": 0.45, "correction_receptiveness": 0.5,
        "mutation_style": "exaggeration", "population_percentage": 10.0,
    },
]

# Default narrative extraction when LLM is unavailable
_DEFAULT_NARRATIVE = {
    "primary_claim": "",
    "secondary_claims": [],
    "entities": [],
    "tone": "neutral",
    "category": "general",
    "virality_estimate": 1.0,
    "emotional_charge": 0.5,
    "novelty_score": 0.5,
}

MAX_RETRIES = 3


class LLMClient:
    """Unified async LLM client. Works with Ollama (local) or cloud APIs via base_url swap."""

    def __init__(self, settings: Settings) -> None:
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
        self.model = settings.llm_model
        self._available: bool | None = None

    async def _chat(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        json_mode: bool = True,
    ) -> str:
        """Send a chat completion request with retry logic.

        Args:
            user_prompt: The user message.
            system_prompt: The system message.
            json_mode: If True, request JSON structured output from the LLM.
        """
        last_error: Exception | None = None
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=0.7,
                    extra_body=(
                        {"response_format": {"type": "json_object"}}
                        if json_mode
                        else None
                    ),
                )
                content: str = response.choices[0].message.content or ""
                if not content:
                    raise ValueError("LLM returned empty content")
                self._available = True
                return content
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_call_failed",
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES,
                    error=str(e),
                )
        self._available = False
        raise RuntimeError(
            f"LLM call failed after {MAX_RETRIES} attempts: {last_error}"
        )

    async def extract_narrative(self, seed_text: str) -> NarrativeSeedOutput:
        """Extract structured narrative components from seed text."""
        try:
            prompt = NARRATIVE_EXTRACTION_PROMPT.format(seed_text=seed_text)
            response = await self._chat(prompt)
            return parse_narrative_seed(response)
        except Exception:
            logger.warning("narrative_extraction_fallback", seed_text=seed_text[:100])
            fallback = {**_DEFAULT_NARRATIVE, "primary_claim": seed_text}
            return NarrativeSeedOutput.model_validate(fallback)

    async def generate_archetypes(
        self, seed_text: str, count: int
    ) -> list[ArchetypeProfile]:
        """Generate behavioral archetypes for the given seed narrative."""
        try:
            prompt = ARCHETYPE_GENERATION_PROMPT.format(
                seed_text=seed_text, count=count
            )
            response = await self._chat(prompt)
            archetypes = parse_archetypes(response)
            # Normalize population percentages to sum to 100
            total_pct = sum(a.population_percentage for a in archetypes)
            if total_pct > 0 and abs(total_pct - 100.0) > 1.0:
                for a in archetypes:
                    a.population_percentage = a.population_percentage * 100.0 / total_pct
            return archetypes
        except Exception:
            logger.warning("archetype_generation_fallback", count=count)
            return _get_default_archetypes(count)

    async def mutate_narrative(
        self,
        archetype_name: str,
        archetype_description: str,
        mutation_style: str,
        narrative_content: str,
    ) -> MutatedNarrative:
        """Generate a narrative mutation based on archetype behavior."""
        try:
            style_desc = MUTATION_STYLE_DESCRIPTIONS.get(
                mutation_style, "retell the story in their own way"
            )
            prompt = NARRATIVE_MUTATION_PROMPT.format(
                archetype_name=archetype_name,
                archetype_description=archetype_description,
                mutation_style=mutation_style,
                narrative_content=narrative_content,
                mutation_style_description=style_desc,
            )
            response = await self._chat(prompt)
            return parse_mutation(response)
        except Exception:
            logger.warning("mutation_fallback", archetype=archetype_name)
            return MutatedNarrative(
                content=f"[Mutated by {archetype_name}]: {narrative_content}",
                mutation_type=mutation_style,  # type: ignore[arg-type]
                emotional_charge_delta=0.1,
                virality_delta=0.1,
            )

    async def generate_report(
        self,
        seed_text: str,
        population_size: int,
        topology: str,
        total_ticks: int,
        final_counts: dict[str, int],
        peak_velocity: float,
        total_transitions: dict[str, int],
    ) -> str:
        """Generate a markdown report summarizing simulation results."""
        total = sum(final_counts.values()) or 1
        try:
            prompt = REPORT_SYNTHESIS_PROMPT.format(
                seed_text=seed_text,
                population_size=population_size,
                topology=topology,
                total_ticks=total_ticks,
                final_s=final_counts.get("S", 0),
                final_m=final_counts.get("M", 0),
                final_i=final_counts.get("I", 0),
                final_r=final_counts.get("R", 0),
                pct_s=final_counts.get("S", 0) / total * 100,
                pct_m=final_counts.get("M", 0) / total * 100,
                pct_i=final_counts.get("I", 0) / total * 100,
                pct_r=final_counts.get("R", 0) / total * 100,
                peak_velocity=peak_velocity,
                total_s_to_m=total_transitions.get("S_to_M", 0),
                total_s_to_i=total_transitions.get("S_to_I", 0),
                total_m_to_i=total_transitions.get("M_to_I", 0),
                total_to_r=total_transitions.get("to_R", 0),
            )
            report_system = (
                "You are an expert analyst writing a report on "
                "misinformation spread simulation results. "
                "Write in clear, professional markdown."
            )
            return await self._chat(
                prompt, system_prompt=report_system, json_mode=False
            )
        except Exception:
            logger.warning("report_generation_fallback")
            return _generate_fallback_report(
                seed_text, population_size, topology, total_ticks,
                final_counts, peak_velocity, total_transitions,
            )


def _get_default_archetypes(count: int) -> list[ArchetypeProfile]:
    """Return default archetypes when LLM is unavailable, scaled to requested count."""
    defaults = [ArchetypeProfile.model_validate(d) for d in _DEFAULT_ARCHETYPES]
    if count >= len(defaults):
        return defaults
    # Return first N, re-normalize percentages
    subset = defaults[:count]
    total_pct = sum(a.population_percentage for a in subset)
    for a in subset:
        a.population_percentage = a.population_percentage * 100.0 / total_pct
    return subset


def _generate_fallback_report(
    seed_text: str,
    population_size: int,
    topology: str,
    total_ticks: int,
    final_counts: dict[str, int],
    peak_velocity: float,
    total_transitions: dict[str, int],
) -> str:
    """Generate a basic report without LLM."""
    total = sum(final_counts.values()) or 1
    return f"""# Simulation Report

## Executive Summary

A misinformation spread simulation was run with {population_size} agents over \
{total_ticks} ticks using a {topology} network topology.

**Seed narrative:** "{seed_text}"

## Spread Dynamics

- **Peak spread velocity:** {peak_velocity:.4f}
- **Total misinformed transitions (S→M):** {total_transitions.get('S_to_M', 0)}
- **Total informed transitions (S→I):** {total_transitions.get('S_to_I', 0)}
- **Total corrections (M→I):** {total_transitions.get('M_to_I', 0)}
- **Total hardened (→R):** {total_transitions.get('to_R', 0)}

## Final State Distribution

| State | Count | Percentage |
|-------|-------|-----------|
| Susceptible | {final_counts.get('S', 0)} | {final_counts.get('S', 0)/total*100:.1f}% |
| Misinformed | {final_counts.get('M', 0)} | {final_counts.get('M', 0)/total*100:.1f}% |
| Informed | {final_counts.get('I', 0)} | {final_counts.get('I', 0)/total*100:.1f}% |
| Resistant | {final_counts.get('R', 0)} | {final_counts.get('R', 0)/total*100:.1f}% |

## Key Findings

- Misinformation reached {final_counts.get('M', 0) + final_counts.get('R', 0)} agents \
({(final_counts.get('M', 0) + final_counts.get('R', 0))/total*100:.1f}% of population)
- {final_counts.get('S', 0)} agents ({final_counts.get('S', 0)/total*100:.1f}%) remained \
unexposed

## Recommendations

- Early intervention is critical — misinformation spread accelerates rapidly in the first ticks
- Focus corrections on high-influence bridge nodes to maximize counter-narrative reach
- Network structure significantly affects vulnerability — communities with fewer cross-group \
connections are more susceptible to echo chamber effects
"""
