"""
Agent 1 — Visual & Structural Analyzer
Model  : Llama-3.3-70B via Groq
Role   : Analyzes code errors from a visual and structural perspective.
"""

import logging
from groq import AsyncGroq

from app.config import get_settings
from app.models import DiagnosticReport

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_agent1_visual(
    code_or_error: str,
    language: str,
    image_bytes: bytes | None = None,
) -> DiagnosticReport:
    logger.info("🔍 Agent 1 (Visual) starting...")

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt = """You are Agent 1: a Visual & Structural Diagnostic Specialist.
Your job is to analyze code errors from a VISUAL and STRUCTURAL perspective.

When analyzing, focus on:
1. VISUAL LAYOUT: indentation errors, misaligned brackets, missing colons visible at a glance
2. ERROR MESSAGE STRUCTURE: the exact error type, line number, file path
3. CODE CONTEXT: what the surrounding code suggests about intent vs. what went wrong
4. IMPORT / MODULE issues visible in the traceback

Respond in this EXACT structured format:

## Agent 1 Visual Analysis

### What I See
[Describe what you observe visually/structurally in the error]

### Error Type Identified
[The exact Python/JS/etc error class, e.g. ModuleNotFoundError, SyntaxError]

### Key Evidence
[Bullet points of the most important clues]

### Root Cause Hypothesis
[One clear sentence stating what you believe the root cause is]

### Confidence
[High / Medium / Low — and why]
"""

    if image_bytes:
        logger.info("Agent 1: Image noted — Groq is text-only, proceeding with text analysis")

    user_message = f"""Analyze this error from a visual and structural perspective.

Programming Language: {language}

Error / Code Text:
{code_or_error}

Examine the visual structure (indentation, brackets, spacing) and provide your structured diagnostic report."""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        raw_text = response.choices[0].message.content
        logger.info("✅ Agent 1 (Visual) completed successfully")

        root_cause = _extract_section(raw_text, "Root Cause Hypothesis")
        confidence = _extract_section(raw_text, "Confidence")

        return DiagnosticReport(
            agent_id=1,
            agent_name="Visual & Structural Analyzer (Llama-3.3-70B via Groq)",
            findings=raw_text,
            root_cause_hypothesis=root_cause,
            confidence=confidence,
        )

    except Exception as e:
        logger.error(f"❌ Agent 1 failed: {e}")
        return DiagnosticReport(
            agent_id=1,
            agent_name="Visual & Structural Analyzer (Llama-3.3-70B via Groq)",
            findings=f"Agent 1 encountered an error: {str(e)}",
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