"""
Pipeline Orchestrator — COMPLETE (all 5 agents)
Phase 1: Agents 1-3 in parallel  (asyncio.gather)
Phase 2: Agent 4 synthesizes
Phase 3: Agent 5 executes the fix
"""

import asyncio
import logging
import time

from app.models import DiagnosticReport, PipelineResponse
from app.agents.agent1_visual import run_agent1_visual
from app.agents.agent2_logical import run_agent2_logical
from app.agents.agent3_pattern import run_agent3_pattern
from app.agents.agent4_synth import run_agent4_synthesizer
from app.agents.agent5_executor import run_agent5_executor

logger = logging.getLogger(__name__)


async def run_pipeline(
    code_or_error: str,
    language: str,
    image_bytes: bytes | None = None,
) -> PipelineResponse:
    """
    Complete 5-agent pipeline:

    ┌─────────────────────────────────────────────────────────┐
    │  PHASE 1 (parallel)                                     │
    │  Agent1 ──┐                                             │
    │  Agent2 ──┼──▶ asyncio.gather() ──▶ [report1, 2, 3]   │
    │  Agent3 ──┘                                             │
    ├─────────────────────────────────────────────────────────┤
    │  PHASE 2 (sequential)                                   │
    │  [report1,2,3] ──▶ Agent4 ──▶ synthesis                │
    │                     (cross-reference + prompt engineer) │
    ├─────────────────────────────────────────────────────────┤
    │  PHASE 3 (sequential)                                   │
    │  synthesis.optimized_prompt ──▶ Agent5 ──▶ execution   │
    │                                  (corrected code + diff)│
    └─────────────────────────────────────────────────────────┘
    """
    start = time.monotonic()

    # ── PHASE 1: Agents 1, 2, 3 in parallel ───────────────────────────────────
    logger.info("🚀 Phase 1 — Parallel diagnostic agents launching...")
    phase1_start = time.monotonic()

    reports: list[DiagnosticReport] = await asyncio.gather(
        run_agent1_visual(code_or_error, language, image_bytes),
        run_agent2_logical(code_or_error, language),
        run_agent3_pattern(code_or_error, language),
        return_exceptions=False,
    )

    phase1_duration = time.monotonic() - phase1_start
    logger.info(f"✅ Phase 1 complete in {phase1_duration:.2f}s")
    for r in reports:
        logger.info(f"   Agent {r.agent_id}: confidence={r.confidence}")

    # ── PHASE 2: Agent 4 Synthesizer ──────────────────────────────────────────
    logger.info("⚗️  Phase 2 — Synthesizer starting...")
    phase2_start = time.monotonic()

    synthesis = await run_agent4_synthesizer(
        reports=reports,
        code_or_error=code_or_error,
        language=language,
    )

    phase2_duration = time.monotonic() - phase2_start
    logger.info(f"✅ Phase 2 complete in {phase2_duration:.2f}s")
    logger.info(f"   Root cause: {synthesis.root_cause[:80]}...")

    # ── PHASE 3: Agent 5 Executor ─────────────────────────────────────────────
    logger.info("⚙️  Phase 3 — Executor starting...")
    phase3_start = time.monotonic()

    execution = await run_agent5_executor(
        optimized_prompt=synthesis.optimized_executor_prompt,
        code_or_error=code_or_error,
        language=language,
    )

    phase3_duration = time.monotonic() - phase3_start
    logger.info(f"✅ Phase 3 complete in {phase3_duration:.2f}s")
    logger.info(f"   Terminal command: {execution.terminal_command or 'None needed'}")

    total_duration = time.monotonic() - start
    logger.info(f"🏁 Full pipeline complete in {total_duration:.2f}s")
    logger.info(f"   Breakdown → P1: {phase1_duration:.1f}s | P2: {phase2_duration:.1f}s | P3: {phase3_duration:.1f}s")

    return PipelineResponse(
        diagnostic_reports=reports,
        synthesis=synthesis,
        execution=execution,
        total_duration_seconds=round(total_duration, 2),
    )
