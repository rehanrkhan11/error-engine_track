"""
Agent 2 — Logical & Syntactic Analyzer
Model  : Llama-3.3-70B via Groq (free tier)
Role   : Parses the error from a purely logical/syntactic perspective.
         Traces execution flow, identifies type mismatches, scope issues,
         and logical contradictions in the code.
"""

import logging
from groq import AsyncGroq

from app.config import get_settings
from app.models import DiagnosticReport

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_agent2_logical(
    code_or_error: str,
    language: str,
) -> DiagnosticReport:
    """
    Agent 2 performs deep logical/syntactic analysis using Llama-3 on Groq.
    Groq's inference is extremely fast — ideal for the parallel phase.
    """
    logger.info("🧠 Agent 2 (Logical) starting...")

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt = """You are Agent 2: a Logic & Syntax Diagnostic Specialist.
You analyze code errors with pure logical reasoning — like a compiler or interpreter would.

When analyzing, focus on:
1. EXECUTION FLOW: trace the call stack from bottom to top
2. TYPE ANALYSIS: are there type mismatches, wrong argument counts, or incorrect returns?
3. SCOPE & NAMESPACE: are variables defined before use? Are imports at the right level?
4. SYNTAX RULES: does the code violate language-specific syntax rules?
5. LOGICAL CONTRADICTIONS: does the code attempt something impossible?

Respond in this EXACT structured format:

## Agent 2 Logical Analysis

### Execution Flow Trace
[Step-by-step trace of what Python/the runtime tried to do before failing]

### Logic Error Identified
[The specific logical or syntactic violation]

### Key Evidence
[Bullet points — specific line numbers, variable names, function signatures]

### Root Cause Hypothesis
[One clear sentence stating the root cause from a logical perspective]

### Confidence
[High / Medium / Low — and why]
"""

    user_message = f"""Perform a deep logical and syntactic analysis of this error.

Programming Language: {language}

Error / Code:
{code_or_error}

Trace the execution flow and identify the exact logical failure point."""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Groq free tier model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.1,        # Very low — we want deterministic logic
            max_tokens=1024,
        )

        raw_text = response.choices[0].message.content
        logger.info("✅ Agent 2 (Logical) completed successfully")

        root_cause = _extract_section(raw_text, "Root Cause Hypothesis")
        confidence = _extract_section(raw_text, "Confidence")

        return DiagnosticReport(
            agent_id=2,
            agent_name="Logical & Syntactic Analyzer (Llama-3.3-70B via Groq)",
            findings=raw_text,
            root_cause_hypothesis=root_cause,
            confidence=confidence,
        )

    except Exception as e:
        logger.error(f"❌ Agent 2 failed: {e}")
        return DiagnosticReport(
            agent_id=2,
            agent_name="Logical & Syntactic Analyzer (Llama-3.3-70B via Groq)",
            findings=f"Agent 2 encountered an error: {str(e)}",
            root_cause_hypothesis="Unable to determine — agent failed",
            confidence="Low",
        )


def _extract_section(text: str, section_name: str) -> str:
    lines = text.split("\n")
    capturing = False
    result_lines = []

    for line in lines:
        if section_name.lower() in line.lower() and line.startswith("#"):
            capturing = True
            continue
        if capturing:
            if line.startswith("#"):
                break
            result_lines.append(line)

    result = " ".join(result_lines).strip()
    return result if result else f"[{section_name} not found in response]"
