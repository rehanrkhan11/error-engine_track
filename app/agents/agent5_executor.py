"""
Agent 5 — The Executor
Model  : Llama-3.3-70B via Groq (chain-of-thought system prompt)
Role   : Takes the master prompt from Agent 4 + the original broken code,
         and outputs:
           - The exact corrected code block
           - A git-style unified diff explanation
           - A one-click terminal command (if needed)
           - A step-by-step rationale for every change made
"""

import logging
import re
from groq import AsyncGroq

from app.config import get_settings
from app.models import ExecutorResult

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_agent5_executor(
    optimized_prompt: str,
    code_or_error: str,
    language: str,
) -> ExecutorResult:
    logger.info("⚙️  Agent 5 (Executor) starting...")

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt = f"""You are Agent 5: the Code Execution and Repair Specialist.
You are the final agent in a multi-agent diagnostic pipeline. You receive:
1. A precision-engineered prompt describing the confirmed root cause
2. The original broken code or error

Your job is to produce the EXACT fix using chain-of-thought reasoning.

THINKING PROCESS (do this internally before writing output):
- Step 1: Re-read the root cause. What EXACTLY is broken?
- Step 2: Identify the minimum change needed. Do not refactor. Do not improve unrelated code.
- Step 3: Write the corrected code mentally. Verify it fixes ONLY the identified issue.
- Step 4: Generate the diff showing precisely what changed.
- Step 5: Determine if a terminal command is needed (pip install, npm install, etc.)

OUTPUT FORMAT — you MUST use these exact section headers:

### CORRECTED CODE
```{language}
[The complete corrected code file or block. Must be runnable as-is.]
```

### DIFF
```diff
[Git-style unified diff. Use - for removed lines, + for added lines]
```

### TERMINAL COMMAND
```bash
[The exact shell command to run, e.g.: pip install requests==2.31.0]
```
(Write NONE if no terminal command is needed)

### EXPLANATION
[Numbered step-by-step explanation of every change made and WHY.
Be specific: mention exact line numbers, variable names, function signatures.]

CRITICAL RULES:
- Never change logic unrelated to the identified bug
- If only a package install is needed, CORRECTED CODE should show original code unchanged
- Always produce a real diff, even if the fix is just an install command
- The explanation must justify EVERY line in the diff
"""

    user_message = f"""Execute the fix based on this diagnostic synthesis:

--- MASTER DIAGNOSTIC PROMPT FROM SYNTHESIZER ---
{optimized_prompt}

--- ORIGINAL BROKEN CODE / ERROR ---
Language: {language}
{code_or_error}

Now apply your chain-of-thought reasoning and produce the complete fix."""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        raw_text = response.choices[0].message.content
        logger.info("✅ Agent 5 (Executor) completed successfully")

        corrected_code = _extract_code_block(raw_text, "CORRECTED CODE")
        diff = _extract_code_block(raw_text, "DIFF")
        terminal_command = _extract_terminal_command(raw_text)
        explanation = _extract_section(raw_text, "EXPLANATION")

        return ExecutorResult(
            corrected_code=corrected_code,
            diff_explanation=diff,
            terminal_command=terminal_command,
            explanation=explanation,
        )

    except Exception as e:
        logger.error(f"❌ Agent 5 failed: {e}")
        return ExecutorResult(
            corrected_code=f"# Agent 5 encountered an error: {str(e)}\n# Original code preserved below:\n{code_or_error}",
            diff_explanation="Could not generate diff — see error above",
            terminal_command=None,
            explanation=f"Agent 5 failed with error: {str(e)}",
        )


def _extract_code_block(text: str, section_name: str) -> str:
    section_pattern = rf"###\s+{re.escape(section_name)}\s*\n"
    section_match = re.search(section_pattern, text, re.IGNORECASE)
    if not section_match:
        return f"[{section_name} section not found in response]"
    after_section = text[section_match.end():]
    code_pattern = r"```(?:\w+)?\n(.*?)```"
    code_match = re.search(code_pattern, after_section, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    next_section = re.search(r"\n###", after_section)
    if next_section:
        return after_section[:next_section.start()].strip()
    return f"[Could not extract {section_name} content]"


def _extract_terminal_command(text: str) -> str | None:
    section_pattern = r"###\s+TERMINAL COMMAND\s*\n"
    section_match = re.search(section_pattern, text, re.IGNORECASE)
    if not section_match:
        return None
    after_section = text[section_match.end():]
    first_line = after_section.strip().split("\n")[0].strip()
    if first_line.upper() == "NONE":
        return None
    code_match = re.search(r"```(?:bash|sh|cmd)?\n(.*?)```", after_section, re.DOTALL)
    if code_match:
        command = code_match.group(1).strip()
        return command if command.upper() != "NONE" else None
    return None


def _extract_section(text: str, section_name: str) -> str:
    lines = text.split("\n")
    capturing = False
    result_lines = []
    for line in lines:
        if section_name.lower() in line.lower() and line.startswith("#"):
            capturing = True
            continue
        if capturing:
            if line.startswith("###"):
                break
            result_lines.append(line)
    result = "\n".join(result_lines).strip()
    return result if result else f"[{section_name} not found in response]"