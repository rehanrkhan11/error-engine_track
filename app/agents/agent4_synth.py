"""
Agent 4 — Synthesizer & Prompt Engineer
Model  : Llama-3.3-70B via Groq
Role   : Takes the 3 diagnostic reports, cross-references them,
         resolves conflicts, determines the definitive root cause,
         writes a human-friendly summary, and engineers a precision
         prompt for Agent 5 (the Executor).
"""

import logging
from groq import AsyncGroq

from app.config import get_settings
from app.models import DiagnosticReport, SynthesisResult

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_agent4_synthesizer(
    reports: list[DiagnosticReport],
    code_or_error: str,
    language: str,
) -> SynthesisResult:
    logger.info("⚗️  Agent 4 (Synthesizer) starting...")

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt = """You are Agent 4: the Master Synthesizer and Prompt Engineer.

You receive diagnostic reports from 3 specialist agents and your job is to:
1. CROSS-REFERENCE: Find where agents agree (high confidence) and where they disagree (conflict)
2. RESOLVE CONFLICTS: When agents disagree, use logical reasoning to determine who is correct
3. DETERMINE ROOT CAUSE: Produce the single, definitive root cause statement
4. WRITE USER SUMMARY: Explain the error in plain English a junior developer can understand
5. ENGINEER EXECUTOR PROMPT: Write a precise, structured prompt for a code-fixing AI agent

Your output MUST follow this EXACT format with these EXACT section headers:

## Synthesis Report

### Agreement Analysis
[Where do all 3 agents agree? What points are confirmed by multiple agents?]

### Conflict Resolution
[Where do agents disagree? Which agent is correct and why?]

### Definitive Root Cause
[Single authoritative sentence. No hedging. This IS the root cause.]

### Human Summary
[3-5 sentences in plain English. Explain: what went wrong, why it went wrong,
and what category of fix is needed. No jargon. Write for a junior developer.]

### Executor Prompt
[This section must be a self-contained, structured prompt for the code-fixing agent.
Include: the exact error, the confirmed root cause, specific instructions for the fix,
output format requirements (corrected code block + diff + terminal command if needed),
and any constraints like "preserve all existing logic, only fix the identified issue".]
"""

    reports_block = ""
    for report in reports:
        reports_block += f"""
{'='*60}
AGENT {report.agent_id}: {report.agent_name}
{'='*60}
{report.findings}

ROOT CAUSE HYPOTHESIS: {report.root_cause_hypothesis}
CONFIDENCE: {report.confidence}
"""

    user_message = f"""Synthesize these 3 diagnostic reports into a definitive diagnosis.

ORIGINAL ERROR / CODE:
{code_or_error}

PROGRAMMING LANGUAGE: {language}

--- AGENT REPORTS ---
{reports_block}

Now cross-reference all reports, resolve any conflicts, and produce your synthesis."""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.2,
            max_tokens=2048,
        )

        raw_text = response.choices[0].message.content
        logger.info("✅ Agent 4 (Synthesizer) completed successfully")

        human_summary = _extract_section(raw_text, "Human Summary")
        root_cause = _extract_section(raw_text, "Definitive Root Cause")
        executor_prompt = _extract_section(raw_text, "Executor Prompt")

        return SynthesisResult(
            human_summary=human_summary,
            root_cause=root_cause,
            optimized_executor_prompt=executor_prompt,
        )

    except Exception as e:
        logger.error(f"❌ Agent 4 failed: {e}")
        return _build_fallback_synthesis(reports, code_or_error, language)


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
    result = "\n".join(result_lines).strip()
    return result if result else f"[{section_name} could not be extracted]"


def _build_fallback_synthesis(
    reports: list[DiagnosticReport],
    code_or_error: str,
    language: str,
) -> SynthesisResult:
    import logging
    logging.getLogger(__name__).warning("⚠️  Agent 4 using fallback synthesis")

    hypotheses = [r.root_cause_hypothesis for r in reports]
    high_confidence = [r for r in reports if "high" in r.confidence.lower()]
    root_cause = high_confidence[0].root_cause_hypothesis if high_confidence else hypotheses[0]

    human_summary = (
        f"Three diagnostic agents analyzed your {language} error. "
        f"Agent 1 found: {hypotheses[0]}. "
        f"Agent 2 found: {hypotheses[1]}. "
        f"Agent 3 found: {hypotheses[2]}. "
        f"The most likely root cause is: {root_cause}."
    )

    executor_prompt = f"""Fix the following {language} error.

ORIGINAL ERROR:
{code_or_error}

CONFIRMED ROOT CAUSE:
{root_cause}

INSTRUCTIONS:
1. Identify the exact line(s) causing this error
2. Apply the minimal fix that resolves the root cause
3. Do not change any other logic
4. Output the complete corrected code block
5. Provide a git-style unified diff showing exactly what changed
6. If a package install command is needed, provide it as a terminal command

Output format:
- CORRECTED CODE: the full fixed code
- DIFF: unified diff format
- TERMINAL COMMAND: any shell command needed (or "None")
- EXPLANATION: step-by-step rationale for the fix"""

    return SynthesisResult(
        human_summary=human_summary,
        root_cause=root_cause,
        optimized_executor_prompt=executor_prompt,
    )