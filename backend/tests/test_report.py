"""Tests for report generation module."""

import pytest

from narrativeflow.config import Settings
from narrativeflow.engine.metrics import TickMetrics
from narrativeflow.engine.report import generate_report
from narrativeflow.engine.simulation import SimulationConfig
from narrativeflow.llm.client import LLMClient


def _make_config() -> SimulationConfig:
    return SimulationConfig(
        seed_text="Test headline about a health scare",
        population_size=500,
        max_ticks=100,
    )


def _make_metrics() -> list[TickMetrics]:
    return [
        TickMetrics(
            tick=i,
            state_counts={
                "S": max(0, 500 - i * 5),
                "M": min(250, i * 3),
                "I": min(100, i),
                "R": min(150, i * 2),
            },
            spread_rate=0.03 if i < 50 else 0.01,
            peak_velocity=0.05,
            active_narratives=1,
        )
        for i in range(100)
    ]


def _make_transitions() -> dict[str, int]:
    return {"S_to_M": 200, "S_to_I": 50, "M_to_I": 30, "to_R": 150}


@pytest.mark.asyncio
async def test_report_has_expected_sections() -> None:
    """Report should contain key section headers."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    llm = LLMClient(settings)

    report = await generate_report(
        llm=llm,
        config=_make_config(),
        metrics_history=_make_metrics(),
        total_transitions=_make_transitions(),
    )

    assert "# Simulation Report" in report
    assert "Executive Summary" in report
    assert "Spread Dynamics" in report
    assert "500" in report  # population size


@pytest.mark.asyncio
async def test_report_contains_seed_text() -> None:
    """Report should reference the original seed text."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    llm = LLMClient(settings)

    report = await generate_report(
        llm=llm,
        config=_make_config(),
        metrics_history=_make_metrics(),
        total_transitions=_make_transitions(),
    )

    assert "health scare" in report


@pytest.mark.asyncio
async def test_report_contains_final_counts() -> None:
    """Report should include the final state distribution."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    llm = LLMClient(settings)

    report = await generate_report(
        llm=llm,
        config=_make_config(),
        metrics_history=_make_metrics(),
        total_transitions=_make_transitions(),
    )

    # Should contain transition counts
    assert "200" in report  # S_to_M count
    assert "Susceptible" in report or "S" in report


@pytest.mark.asyncio
async def test_empty_metrics_returns_placeholder() -> None:
    """Empty metrics should produce a placeholder report."""
    settings = Settings(
        llm_base_url="http://localhost:99999/v1",
        llm_api_key="test",
        llm_model="nonexistent",
    )
    llm = LLMClient(settings)

    report = await generate_report(
        llm=llm,
        config=_make_config(),
        metrics_history=[],
        total_transitions={},
    )

    assert "no results" in report.lower()
