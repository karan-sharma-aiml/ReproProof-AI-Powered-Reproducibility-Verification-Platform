"""Reusable prompt templates for a future model-backed troubleshooter."""

TROUBLESHOOTING_SYSTEM_PROMPT = """You are a reproducibility troubleshooting agent.
Analyze only the supplied repository evidence and execution artifacts.
Do not modify files, invent traceback details, or claim that a fix was applied.
Return a structured diagnosis with root cause, diagnostic_confidence, severity, explanation,
possible fixes, and whether manual action is required.
"""

TROUBLESHOOTING_USER_TEMPLATE = """Execution ID: {execution_id}
Repository path: {repository_path}
Python version: {python_version}
Exit code: {exit_code}
Execution time: {execution_time:.3f}s

Repository tree:
{repository_tree}

requirements.txt:
{requirements}

stdout:
{stdout}

stderr:
{stderr}

traceback:
{traceback}

execution log:
{execution_log}
"""


def build_troubleshooting_prompt(evidence: dict[str, object]) -> str:
    """Render the reusable user prompt without embedding diagnosis logic."""
    return TROUBLESHOOTING_USER_TEMPLATE.format(
        execution_id=evidence.get("execution_id", ""),
        repository_path=evidence.get("repository_path", ""),
        python_version=evidence.get("python_version", ""),
        exit_code=evidence.get("exit_code", ""),
        execution_time=float(evidence.get("execution_time", 0.0)),
        repository_tree="\n".join(evidence.get("repository_tree", [])),
        requirements=evidence.get("requirements", ""),
        stdout=evidence.get("stdout", ""),
        stderr=evidence.get("stderr", ""),
        traceback=evidence.get("traceback", ""),
        execution_log=evidence.get("execution_log", ""),
    )
