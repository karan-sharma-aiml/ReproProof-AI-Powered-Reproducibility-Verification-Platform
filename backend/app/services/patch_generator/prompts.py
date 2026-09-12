"""Reusable prompt templates for patch-generation providers."""

PATCH_GENERATOR_SYSTEM_PROMPT = """You generate a minimal code patch for a reproducibility failure.
Use only the supplied repository evidence. Do not apply the patch, execute code,
or modify files. Preserve unrelated code and return a reviewable unified diff.
If the evidence is insufficient for a safe deterministic change, return no patch
and explain what human information is missing.
"""

PATCH_GENERATOR_USER_TEMPLATE = """Execution ID: {execution_id}
Repository path: {repository_path}
Problematic file: {problematic_file}
Root cause: {root_cause}
Human explanation: {human_explanation}
Suggested fix: {suggested_fix}
Environment: {environment}

Repository tree:
{repository_tree}

requirements.txt:
{requirements}

Error message:
{error_message}

Stacktrace:
{stacktrace}

Execution logs:
{execution_logs}
"""


def build_patch_prompt(evidence: dict[str, object]) -> str:
    """Render a provider-neutral patch-generation prompt."""
    return PATCH_GENERATOR_USER_TEMPLATE.format(
        execution_id=evidence.get("execution_id", ""),
        repository_path=evidence.get("repository_path", ""),
        problematic_file=evidence.get("problematic_file", ""),
        root_cause=evidence.get("root_cause", ""),
        human_explanation=evidence.get("human_explanation", ""),
        suggested_fix=evidence.get("suggested_fix", ""),
        environment=evidence.get("environment", {}),
        repository_tree="\n".join(evidence.get("repository_tree", [])),
        requirements=evidence.get("requirements", ""),
        error_message=evidence.get("error_message", ""),
        stacktrace=evidence.get("stacktrace", ""),
        execution_logs=evidence.get("execution_logs", ""),
    )
