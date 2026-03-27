"""Prompt templates for all LLM calls."""

SYSTEM_PROMPT = (
    "You are a behavioral scientist specializing in information ecosystems. "
    "You analyze how different population segments react to and share narratives. "
    "Respond ONLY in the specified JSON format. Do not include any text outside the JSON."
)

NARRATIVE_EXTRACTION_PROMPT = """\
Analyze the following news event or claim and extract its key components:

"{seed_text}"

Respond with a JSON object containing:
{{
  "primary_claim": "the main claim or assertion",
  "secondary_claims": ["list of supporting or related claims"],
  "entities": ["people, organizations, or things mentioned"],
  "tone": "one of: alarming, neutral, hopeful, fearful, outraged, sensational",
  "category": "one of: health, politics, finance, technology, environment, social, general",
  "virality_estimate": <float 0.0-2.0, how likely this is to go viral, 1.0 = average>,
  "emotional_charge": <float 0.0-1.0, how emotionally charged this claim is>,
  "novelty_score": <float 0.0-1.0, how novel/surprising this claim is>
}}"""

ARCHETYPE_GENERATION_PROMPT = """\
Given the following news event:
"{seed_text}"

Generate {count} distinct behavioral archetypes representing how different segments of \
the population would react to and share this information.

For each archetype, provide a JSON object with these exact fields:
- "name": short persona name (e.g. "Skeptical Tech Worker")
- "description": 1-2 sentence description
- "susceptibility": float 0.0-1.0 (how likely to believe misinformation)
- "sharing_tendency": float 0.0-1.0 (how likely to share content)
- "trust_mainstream_media": float 0.0-1.0
- "trust_social_peers": float 0.0-1.0
- "emotional_reactivity": float 0.0-1.0
- "correction_receptiveness": float 0.0-1.0 (openness to changing mind)
- "mutation_style": one of "emotional_amplification", "conspiracy_framing", \
"decontextualization", "fabrication", "exaggeration", "political_reframing"
- "population_percentage": float (what % of the population this archetype represents)

Ensure archetypes cover the full spectrum: true believers, skeptics, active debunkers, \
passive consumers, and amplifiers. Population percentages must sum to 100.

Respond with a JSON object: {{"archetypes": [<list of archetype objects>]}}"""

NARRATIVE_MUTATION_PROMPT = """\
An agent with the following profile received this narrative and is retelling it:

Agent archetype: {archetype_name}
Agent description: {archetype_description}
Mutation style: {mutation_style}

Original narrative: "{narrative_content}"

How would this person retell the story? They would naturally {mutation_style_description}.

Respond with a JSON object:
{{
  "content": "the mutated version of the narrative as this person would tell it",
  "mutation_type": "{mutation_style}",
  "emotional_charge_delta": <float -1.0 to 1.0, change in emotional intensity>,
  "virality_delta": <float -1.0 to 1.0, change in shareability>
}}"""

REPORT_SYNTHESIS_PROMPT = """\
You are analyzing the results of a misinformation spread simulation. Generate a \
comprehensive report based on the following data:

Simulation Configuration:
- Seed narrative: "{seed_text}"
- Population: {population_size} agents
- Network topology: {topology}
- Duration: {total_ticks} ticks

Final Results:
- Susceptible: {final_s} ({pct_s:.1f}%)
- Misinformed: {final_m} ({pct_m:.1f}%)
- Informed: {final_i} ({pct_i:.1f}%)
- Resistant: {final_r} ({pct_r:.1f}%)

Key Metrics:
- Peak spread velocity: {peak_velocity:.4f}
- Total S→M transitions: {total_s_to_m}
- Total S→I transitions: {total_s_to_i}
- Total M→I corrections: {total_m_to_i}
- Total hardened (→R): {total_to_r}

Write a markdown report with these sections:
1. **Executive Summary** — what happened in 2-3 sentences
2. **Spread Dynamics** — how fast the narrative spread, peak velocity, cascade patterns
3. **Vulnerability Analysis** — which population segments were most affected
4. **Key Findings** — the most important takeaways
5. **Intervention Windows** — when corrections would have been most effective
6. **Recommendations** — actionable suggestions based on the simulation

Write the report directly in markdown. Be specific and reference the numbers."""

MUTATION_STYLE_DESCRIPTIONS: dict[str, str] = {
    "emotional_amplification": (
        "amplify the emotional impact, making it more fear-inducing"
    ),
    "conspiracy_framing": (
        "add conspiratorial elements, suggesting hidden agendas"
    ),
    "decontextualization": (
        "remove important context, making the claim seem more dramatic"
    ),
    "fabrication": (
        "add fabricated details that weren't in the original"
    ),
    "exaggeration": (
        "exaggerate the scale, impact, or certainty of the claims"
    ),
    "political_reframing": (
        "reframe the narrative through a political lens"
    ),
}
