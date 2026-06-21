from pydantic import BaseModel
from typing import Optional
from enum import Enum


class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    BOTH = "both"


# ── Request shape ──────────────────────────────────────────────────────────────
class DiagnoseRequest(BaseModel):
    """
    The frontend sends this. `code_or_error` is always text.
    If the user also uploads an image, it arrives as a separate
    multipart file field (handled in the route, not here).
    """
    code_or_error: str
    language: Optional[str] = None       # e.g. "python", "javascript"
    input_type: InputType = InputType.TEXT


# ── Per-agent report (Phase 1) ─────────────────────────────────────────────────
class DiagnosticReport(BaseModel):
    agent_id: int
    agent_name: str
    findings: str                        # Raw markdown from the agent
    root_cause_hypothesis: str
    confidence: str                      # "High" | "Medium" | "Low"


# ── Synthesizer output (Agent 4) ──────────────────────────────────────────────
class SynthesisResult(BaseModel):
    human_summary: str                   # Friendly explanation for the user
    root_cause: str                      # The resolved, definitive root cause
    optimized_executor_prompt: str       # The engineered prompt for Agent 5


# ── Executor output (Agent 5) ─────────────────────────────────────────────────
class ExecutorResult(BaseModel):
    corrected_code: str                  # The fixed code block
    diff_explanation: str                # Git-style unified diff as text
    terminal_command: Optional[str]      # e.g. "pip install numpy==1.26"
    explanation: str                     # Step-by-step rationale


# ── Final pipeline response ────────────────────────────────────────────────────
class PipelineResponse(BaseModel):
    diagnostic_reports: list[DiagnosticReport]   # From agents 1-3
    synthesis: SynthesisResult                    # From agent 4
    execution: ExecutorResult                     # From agent 5
    total_duration_seconds: float
