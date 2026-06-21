"""
Agent 3 — Pattern Recognition & Environment Analyst
Model  : Llama-3.3-70B via Groq
Role   : Identifies known error PATTERNS — missing dependencies, version
         conflicts, environment/config issues, OS-specific problems.
"""

import logging
from groq import AsyncGroq

from app.config import get_settings
from app.models import DiagnosticReport

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_agent3_pattern(
    code_or_error: str,
    language: str,
) -> DiagnosticReport:
    logger.info("🔎 Agent 3 (Pattern) starting...")

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt = """You are Agent 3: an Environment & Pattern Recognition Specialist.
You are NOT a general programmer. You are a DevOps engineer who has seen thousands of errors.
You recognize error PATTERNS instantly — like a doctor recognizing a disease by symptoms.

Your pattern library includes:
1. DEPENDENCY ISSUES: missing packages, wrong versions, incompatible combinations
2. ENVIRONMENT ISSUES: wrong Python/Node/Java version, PATH problems, venv not activated
3. IMPORT PATTERNS: circular imports, __init__.py missing, wrong package structure
4. CONFIGURATION ISSUES: missing .env files, wrong API keys, missing config values
5. OS/PLATFORM ISSUES: Windows vs Linux path separators, permission errors, encoding issues
6. RUNTIME ENVIRONMENT: port conflicts, memory issues, async/sync mismatches
7. VERSION CONFLICTS: package A requires lib>=2.0 but package B pins lib==1.9

Respond in this EXACT structured format:

## Agent 3 Pattern Analysis

### Pattern Matched
[Name the specific pattern category this error matches]

### Pattern Signature
[The specific telltale signs that confirm this pattern]

### Environment Assessment
[What environment conditions are likely causing this]

### Similar Cases
[1-2 sentences about how this pattern typically manifests]

### Root Cause Hypothesis
[One clear sentence about the environmental/pattern root cause]

### Recommended Fix Category
[e.g., "Install missing package", "Upgrade dependency", "Fix import path"]

### Confidence
[High / Medium / Low — and why]
"""

    user_message = f"""Scan this error for known patterns and environment issues.

Programming Language: {language}

Error / Code:
{code_or_error}

Match this against your pattern library and identify the most likely environmental cause."""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.15,
            max_tokens=1024,
        )

        raw_text = response.choices[0].message.content
        logger.info("✅ Agent 3 (Pattern) completed successfully")

        root_cause = _extract_section(raw_text, "Root Cause Hypothesis")
        confidence = _extract_section(raw_text, "Confidence")

        return DiagnosticReport(
            agent_id=3,
            agent_name="Pattern Recognition & Environment Analyst (Llama-3.3-70B via Groq)",
            findings=raw_text,
            root_cause_hypothesis=root_cause,
            confidence=confidence,
        )

    except Exception as e:
        logger.error(f"❌ Agent 3 failed: {e}")
        return DiagnosticReport(
            agent_id=3,
            agent_name="Pattern Recognition & Environment Analyst (Llama-3.3-70B via Groq)",
            findings=f"Agent 3 encountered an error: {str(e)}",
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