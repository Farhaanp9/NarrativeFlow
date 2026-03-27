"""Report retrieval endpoints."""

import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from narrativeflow.api.deps import get_db
from narrativeflow.api.models import ReportDataResponse, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{sim_id}", response_model=ReportResponse)
async def get_report(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> ReportResponse:
    """Get the generated markdown report for a simulation."""
    cursor = await db.execute(
        "SELECT content, generated_at FROM reports "
        "WHERE simulation_id = ?",
        (sim_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404, detail="Report not found"
        )

    return ReportResponse(
        simulation_id=sim_id,
        content=row[0],
        generated_at=row[1],
    )


@router.get("/{sim_id}/data", response_model=ReportDataResponse)
async def get_report_data(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> ReportDataResponse:
    """Get raw simulation data for export."""
    # Get config
    sim_cursor = await db.execute(
        "SELECT config FROM simulations WHERE id = ?", (sim_id,)
    )
    sim_row = await sim_cursor.fetchone()
    if sim_row is None:
        raise HTTPException(
            status_code=404, detail="Simulation not found"
        )

    config = json.loads(sim_row[0])

    # Get report raw data
    report_cursor = await db.execute(
        "SELECT raw_data FROM reports WHERE simulation_id = ?",
        (sim_id,),
    )
    report_row = await report_cursor.fetchone()
    if report_row is None or report_row[0] is None:
        raise HTTPException(
            status_code=404, detail="Report data not found"
        )

    raw = json.loads(report_row[0])

    # Get full metrics history
    metrics_cursor = await db.execute(
        "SELECT metrics FROM tick_metrics "
        "WHERE simulation_id = ? ORDER BY tick",
        (sim_id,),
    )
    metrics_rows = await metrics_cursor.fetchall()
    metrics_history = [json.loads(m[0]) for m in metrics_rows]

    return ReportDataResponse(
        simulation_id=sim_id,
        config=config,
        final_state_counts=raw.get("final_state_counts", {}),
        total_transitions=raw.get("total_transitions", {}),
        metrics_history=metrics_history,
    )
