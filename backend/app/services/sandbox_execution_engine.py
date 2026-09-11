"""Execute planner-generated commands inside a disposable sandbox copy."""

from __future__ import annotations

import os
import queue
import shlex
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import TextIO

from app.core.logging import get_logger
from app.models.execution_event import ExecutionEvent
from app.models.execution_plan import ExecutionPlan
from app.models.execution_result import ExecutionResult
from app.services.execution_event_publisher import ExecutionEventPublisher

logger = get_logger("sandbox_execution_engine")


class SandboxExecutionEngine:
    """Run validated commands against a temporary copy with live events."""

    DEFAULT_TIMEOUT_SECONDS = 300.0
    ALLOWED_EXECUTABLES = frozenset(
        {
            "python",
            "python3",
            "py",
            "pip",
            "pip3",
            "pipenv",
            "uvicorn",
            "flask",
            "django-admin",
            "jupyter",
            "conda",
        }
    )
    ALLOWED_PYTHON_MODULES = frozenset({"venv", "compileall", "nbconvert"})
    SHELL_TOKENS = frozenset({";", "&&", "||", "&", "|", ">", ">>", "<", "$"})

    def __init__(
        self,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        allowed_executables: frozenset[str] | None = None,
        sandbox_root: Path | None = None,
        event_publisher: ExecutionEventPublisher | None = None,
        reports_root: Path | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self._timeout_seconds = timeout_seconds
        self._allowed_executables = frozenset(
            item.lower() for item in (allowed_executables or self.ALLOWED_EXECUTABLES)
        )
        self._sandbox_root = Path(sandbox_root).resolve() if sandbox_root else None
        self._event_publisher = event_publisher
        self._reports_root = Path(reports_root or "reports").resolve()

    def execute(self, repository_path: Path, plan: ExecutionPlan) -> ExecutionResult:
        """Copy, execute, stream, log, and clean up a repository run."""
        source_path = self._validate_repository(repository_path)
        commands = self._build_commands(source_path, plan)
        parsed_commands = [self._validate_command(command) for command in commands]
        if not parsed_commands:
            raise ValueError("Execution plan contains no commands")

        started_at = time.monotonic()
        logs = ["Creating sandbox..."]
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        installed_dependencies: list[str] = []
        executed_command = ""
        sandbox_path = ""
        log_path = self._reports_root / source_path.name / "execution.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with log_path.open("w", encoding="utf-8") as log_file:
            try:
                self._emit(
                    "SANDBOX_CREATED", "RUNNING", "Creating sandbox...", 5, log_file
                )
                if self._sandbox_root:
                    self._sandbox_root.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(
                    prefix=f"{source_path.name}-", dir=self._sandbox_root
                ) as temporary_directory:
                    isolated_path = Path(temporary_directory) / source_path.name
                    sandbox_path = str(isolated_path)
                    self._emit(
                        "COPY_STARTED", "RUNNING", "Copying repository...", 10, log_file
                    )
                    shutil.copytree(source_path, isolated_path, symlinks=False)
                    self._emit(
                        "COPY_COMPLETED", "SUCCESS", "Repository copied.", 20, log_file
                    )

                    project_root, selected_entry_point = self._resolve_project_root(
                        isolated_path,
                        plan.entry_point,
                    )
                    logger.info(
                        "Execution context: extraction_dir=%s repository_root=%s resolved_project_root=%s candidate_entry_points=%s selected_entry_point=%s",
                        sandbox_path,
                        source_path,
                        str(project_root),
                        self._candidate_entry_points(isolated_path, plan.entry_point),
                        selected_entry_point,
                    )

                    if (
                        plan.entry_point
                        and plan.entry_point != "notebook"
                        and self._plan_references_entry_point(
                            parsed_commands, plan.entry_point
                        )
                    ):
                        entry_path = project_root / Path(plan.entry_point)
                        if not entry_path.is_file():
                            logger.warning(
                                "Missing entry point %s after nested project resolution. Checked project root %s.",
                                plan.entry_point,
                                project_root,
                            )
                            return self._finish(
                                self._result(
                                    "MISSING_ENTRY_POINT",
                                    False,
                                    -1,
                                    stdout_chunks,
                                    [f"Missing entry point: {plan.entry_point}"],
                                    logs,
                                    started_at,
                                    False,
                                    executed_command,
                                    installed_dependencies,
                                    sandbox_path,
                                    log_path,
                                ),
                                log_file,
                            )

                    self._emit(
                        "DEPENDENCY_DETECTION",
                        "SUCCESS",
                        "Dependency commands detected.",
                        25,
                        log_file,
                    )
                    for arguments in parsed_commands:
                        resolved = self._resolve_command(arguments)
                        executed_command = shlex.join(resolved)
                        dependency = self._is_dependency_command(resolved)
                        if dependency:
                            installed_dependencies.append(executed_command)
                            self._emit(
                                "INSTALL_STARTED",
                                "RUNNING",
                                "Installing dependencies...",
                                30,
                                log_file,
                            )
                        else:
                            self._emit(
                                "EXECUTION_STARTED",
                                "RUNNING",
                                f"Starting {executed_command}",
                                50,
                                log_file,
                            )

                        try:
                            return_code, timed_out, command_stdout, command_stderr = (
                                self._stream_process(resolved, project_root, log_file)
                            )
                        except (OSError, subprocess.SubprocessError) as exc:
                            message = f"Could not start command: {exc}"
                            self._emit(
                                "EXECUTION_FAILED",
                                "FAILED",
                                message,
                                50,
                                log_file,
                                "stderr",
                            )
                            return self._finish(
                                self._result(
                                    "SUBPROCESS_ERROR",
                                    False,
                                    -1,
                                    stdout_chunks,
                                    [message],
                                    logs,
                                    started_at,
                                    False,
                                    executed_command,
                                    installed_dependencies,
                                    sandbox_path,
                                    log_path,
                                ),
                                log_file,
                            )
                        stdout_chunks.append(command_stdout)
                        stderr_chunks.append(command_stderr)
                        if return_code != 0:
                            status = (
                                "TIMEOUT"
                                if timed_out
                                else (
                                    "DEPENDENCY_INSTALL_FAILED"
                                    if dependency
                                    else "SUBPROCESS_FAILED"
                                )
                            )
                            message = (
                                "Command timed out."
                                if timed_out
                                else (
                                    "Dependency installation failed."
                                    if dependency
                                    else "Execution failed."
                                )
                            )
                            self._emit(
                                "EXECUTION_FAILED", "FAILED", message, 70, log_file
                            )
                            return self._finish(
                                self._result(
                                    status,
                                    False,
                                    -1 if timed_out else return_code,
                                    stdout_chunks,
                                    stderr_chunks,
                                    logs,
                                    started_at,
                                    timed_out,
                                    executed_command,
                                    installed_dependencies,
                                    sandbox_path,
                                    log_path,
                                ),
                                log_file,
                            )
                        if dependency:
                            self._emit(
                                "INSTALL_COMPLETED",
                                "SUCCESS",
                                "Dependencies installed successfully.",
                                40,
                                log_file,
                            )

                    self._emit(
                        "EXECUTION_FINISHED",
                        "SUCCESS",
                        "Execution completed.",
                        90,
                        log_file,
                    )
                    result = self._result(
                        "COMPLETED",
                        True,
                        0,
                        stdout_chunks,
                        stderr_chunks,
                        logs,
                        started_at,
                        False,
                        executed_command,
                        installed_dependencies,
                        sandbox_path,
                        log_path,
                    )
                    return self._finish(result, log_file)
            except OSError as exc:
                logger.exception("Could not prepare sandbox for %s", source_path)
                self._emit(
                    "EXECUTION_FAILED",
                    "FAILED",
                    f"Sandbox preparation failed: {exc}",
                    0,
                    log_file,
                )
                result = self._result(
                    "SANDBOX_ERROR",
                    False,
                    -1,
                    stdout_chunks,
                    [str(exc)],
                    logs,
                    started_at,
                    False,
                    executed_command,
                    installed_dependencies,
                    sandbox_path,
                    log_path,
                )
                return self._finish(result, log_file)

    def _stream_process(
        self, arguments: list[str], cwd: Path, log_file: TextIO
    ) -> tuple[int, bool, str, str]:
        """Read stdout and stderr concurrently so each line is published immediately.

        The timeout branch must not return from inside the reader loop before the
        child process has been terminated and the reader threads have drained the
        pipe streams. On Windows this lets the TemporaryDirectory cleanup see an
        open file handle and misclassify the timeout as an execution error.
        """
        process = subprocess.Popen(
            arguments,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=False,
        )
        output_queue: queue.Queue[tuple[str, str]] = queue.Queue()

        def read_stream(stream: TextIO | None, name: str) -> None:
            if stream is None:
                return
            try:
                for line in iter(stream.readline, ""):
                    output_queue.put((name, line))
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        threads = [
            threading.Thread(
                target=read_stream, args=(process.stdout, "stdout"), daemon=True
            ),
            threading.Thread(
                target=read_stream, args=(process.stderr, "stderr"), daemon=True
            ),
        ]
        for thread in threads:
            thread.start()

        stdout: list[str] = []
        stderr: list[str] = []
        deadline = time.monotonic() + self._timeout_seconds
        timed_out = False

        try:
            while True:
                try:
                    stream, line = output_queue.get(timeout=0.05)
                except queue.Empty:
                    if process.poll() is None and time.monotonic() >= deadline:
                        timed_out = True
                        try:
                            process.terminate()
                        except Exception:
                            pass
                        try:
                            process.wait(timeout=1)
                        except subprocess.TimeoutExpired:
                            try:
                                process.kill()
                            except Exception:
                                pass
                            try:
                                process.wait(timeout=1)
                            except Exception:
                                pass

                    if process.poll() is not None and not any(
                        thread.is_alive() for thread in threads
                    ):
                        break
                    continue

                if stream == "stdout":
                    stdout.append(line)
                    self._emit(
                        "STDOUT",
                        "RUNNING",
                        line.rstrip("\r\n"),
                        60,
                        log_file,
                        "stdout",
                    )
                else:
                    stderr.append(line)
                    self._emit(
                        "STDERR",
                        "RUNNING",
                        line.rstrip("\r\n"),
                        60,
                        log_file,
                        "stderr",
                    )

                if process.poll() is not None and not any(
                    thread.is_alive() for thread in threads
                ):
                    break
        finally:
            # Give the reader threads a chance to finish draining the process pipes,
            # then close them explicitly. This prevents the temporary sandbox folder
            # from remaining locked by an orphaned worker thread on Windows.
            for thread in threads:
                thread.join(timeout=1)
            try:
                if process.stdout:
                    process.stdout.close()
            except Exception:
                pass
            try:
                if process.stderr:
                    process.stderr.close()
            except Exception:
                pass

        # Return code is intentionally normalized by the caller when the timeout
        # branch is detected, but this function must expose a consistent object:
        # status = TIMEOUT, timed_out = True, and a non-empty error collection.
        if timed_out:
            return -1, True, "".join(stdout), "".join(stderr)

        return process.returncode or 0, False, "".join(stdout), "".join(stderr)

    def _emit(
        self,
        stage: str,
        status: str,
        message: str,
        progress: int,
        log_file: TextIO,
        stream: str = "system",
    ) -> None:
        event = ExecutionEvent(
            stage=stage,
            status=status,
            message=message,
            progress=progress,
            stream=stream,
        )
        log_file.write(f"[{event.timestamp}] {stage} {status} {message}\n")
        log_file.flush()
        if self._event_publisher:
            self._event_publisher.publish(event)

    def _finish(self, result: ExecutionResult, log_file: TextIO) -> ExecutionResult:
        if result.installed_dependencies:
            result.logs.append("Dependencies installed successfully.")
        if result.timed_out:
            result.logs.append("Execution timed out.")
        result.logs.append("Cleaning sandbox...")
        result.logs.extend(["CLEANUP_STARTED", "CLEANUP_COMPLETED"])
        self._emit("CLEANUP_STARTED", "RUNNING", "Cleaning sandbox...", 95, log_file)
        self._emit(
            "CLEANUP_COMPLETED", "SUCCESS", "Sandbox cleanup complete.", 100, log_file
        )
        return result

    def _build_commands(self, source_path: Path, plan: ExecutionPlan) -> list[str]:
        commands = list(plan.commands)
        names = {path.name for path in source_path.iterdir() if path.is_file()}
        dependency_commands = [
            ("requirements.txt", "pip install -r requirements.txt"),
            ("pyproject.toml", "pip install -e ."),
            ("setup.py", "pip install -e ."),
            ("Pipfile", "pipenv install"),
            ("environment.yml", "conda env update -f environment.yml"),
        ]
        if not any(
            self._is_dependency_command(self._safe_split(command))
            for command in commands
        ):
            for filename, command in dependency_commands:
                if filename in names:
                    commands.insert(1 if commands else 0, command)
                    break
        return commands

    def _validate_repository(self, repository_path: Path) -> Path:
        source_path = Path(repository_path)
        if not source_path.exists():
            raise ValueError(f"Repository path does not exist: {source_path}")
        if not source_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {source_path}")
        for entry in source_path.rglob("*"):
            if entry.is_symlink():
                raise ValueError(f"Repository contains an unsupported symlink: {entry}")
        return source_path.resolve()

    @staticmethod
    def _resolve_command(arguments: list[str]) -> list[str]:
        if os.name == "nt":
            executable = arguments[0].lower()
            if (
                executable in {"python", "python3"}
                and shutil.which(executable) is None
                and shutil.which("py")
            ):
                return ["py", *arguments[1:]]
            if (
                executable in {"pip", "pip3"}
                and shutil.which(executable) is None
                and shutil.which("py")
            ):
                return ["py", "-m", "pip", *arguments[1:]]
        return arguments

    def _validate_command(self, command: str) -> list[str]:
        if not command.strip():
            raise ValueError("Execution plan contains an empty command")
        try:
            arguments = shlex.split(command, posix=True)
        except ValueError as exc:
            raise ValueError(f"Invalid execution command: {command}") from exc
        if not arguments:
            raise ValueError("Execution plan contains an empty command")
        if any(
            token in self.SHELL_TOKENS
            or any(char in token for char in (";", "&&", "||"))
            for token in arguments
        ):
            raise ValueError("Shell injection tokens are not allowed")
        executable = Path(arguments[0]).name.lower()
        if arguments[0] != executable and arguments[0].lower() not in {
            f"{executable}.exe",
            f"{executable}.cmd",
        }:
            raise ValueError(
                f"Command executable must be a bare allowlisted name: {arguments[0]}"
            )
        if executable not in self._allowed_executables:
            raise ValueError(f"Command executable is not allowed: {arguments[0]}")
        for index, argument in enumerate(arguments[1:], start=1):
            if argument in {"-c", "--command"}:
                raise ValueError("Inline code execution is not allowed")
            if argument == "-m" and (
                index + 1 >= len(arguments)
                or arguments[index + 1] not in self.ALLOWED_PYTHON_MODULES
            ):
                raise ValueError("Python module is not allowed")
            if self._is_path_outside_working_directory(argument):
                raise ValueError(f"Command argument may escape the sandbox: {argument}")
        return arguments

    def _resolve_project_root(
        self, extracted_root: Path, entry_point: str
    ) -> tuple[Path, str]:
        """Return the directory that best matches the repository’s real project metadata.

        We walk the extracted repository recursively and prefer folders that contain
        either a dependency manifest or an inferred entry-point file such as main.py,
        app.py, run.py, and then use that folder as the execution cwd for the
        generated command. This allows a nested repository slice like
        repository/research-demo/main.py to run without assuming the repository is
        flat at the extraction root.
        """
        if not extracted_root.exists():
            return extracted_root, entry_point

        candidates: list[Path] = []
        entry_candidates = []
        for file in sorted(extracted_root.rglob("*")):
            if not file.is_file():
                continue
            if file.name in {
                "requirements.txt",
                "pyproject.toml",
                "setup.py",
                "environment.yml",
            }:
                candidates.append(file.parent)
            if file.name in {
                "main.py",
                "app.py",
                "run.py",
                "manage.py",
                "server.py",
                "cli.py",
            }:
                entry_candidates.append(file)

        # Prefer the manifest-owning directory directly. If multiple candidates
        # exist, choose the nearest one to the entry file if there is any.
        chosen: Path | None = None
        if candidates:
            keyed = sorted(
                candidates,
                key=lambda p: (len(p.parts), str(p)),
            )
            chosen = keyed[0]

        # If an entry file already exists in a nested directory, prefer the
        # directory that owns the best matching conventional entry file and
        # also carries dependency metadata.
        if entry_candidates:
            for entry_file in sorted(
                entry_candidates, key=lambda p: (len(p.parts), str(p))
            ):
                parent = entry_file.parent
                if (
                    (parent / "requirements.txt").exists()
                    or (parent / "pyproject.toml").exists()
                    or (parent / "setup.py").exists()
                    or (parent / "environment.yml").exists()
                ):
                    chosen = parent
                    break
                if chosen is None and parent != extracted_root:
                    chosen = parent

        if chosen is not None:
            selected = entry_point
            if entry_point == "main.py" and (chosen / "main.py").exists():
                selected = str((chosen / "main.py").relative_to(extracted_root))
            elif entry_point == "app.py" and (chosen / "app.py").exists():
                selected = str((chosen / "app.py").relative_to(extracted_root))
            elif entry_point == "run.py" and (chosen / "run.py").exists():
                selected = str((chosen / "run.py").relative_to(extracted_root))
            return chosen.resolve(), selected

        return extracted_root.resolve(), entry_point

    def _candidate_entry_points(
        self, extracted_root: Path, entry_point: str
    ) -> list[str]:
        candidates: list[str] = []
        for file in sorted(extracted_root.rglob("*")):
            if file.is_file() and file.name in {
                "main.py",
                "app.py",
                "run.py",
                "manage.py",
                "server.py",
                "cli.py",
            }:
                candidates.append(file.relative_to(extracted_root).as_posix())
        if not candidates and entry_point:
            candidates.append(entry_point)
        return candidates

    @staticmethod
    def _plan_references_entry_point(
        commands: list[list[str]], entry_point: str
    ) -> bool:
        name = Path(entry_point).name
        return any(entry_point in command or name in command for command in commands)

    @staticmethod
    def _safe_split(command: str) -> list[str]:
        try:
            return shlex.split(command, posix=True)
        except ValueError:
            return []

    @staticmethod
    def _is_dependency_command(arguments: list[str]) -> bool:
        return bool(arguments) and (
            arguments[0].lower() in {"pip", "pip3", "pipenv", "conda"}
            or (
                len(arguments) > 2
                and arguments[0].lower() in {"py", "python", "python3"}
                and arguments[1:3] == ["-m", "pip"]
            )
        )

    @staticmethod
    def _is_path_outside_working_directory(argument: str) -> bool:
        normalized = argument.replace("\\", "/")
        return (
            normalized.startswith(("/", "//"))
            or (len(normalized) > 1 and normalized[1] == ":")
            or ".." in Path(normalized).parts
        )

    @staticmethod
    def _result(
        status: str,
        success: bool,
        exit_code: int,
        stdout: list[str],
        stderr: list[str],
        logs: list[str],
        started_at: float,
        timed_out: bool,
        executed_command: str,
        installed_dependencies: list[str],
        sandbox_path: str,
        log_path: Path,
    ) -> ExecutionResult:
        return ExecutionResult(
            status=status,
            success=success,
            exit_code=exit_code,
            stdout="".join(stdout),
            stderr="".join(stderr),
            execution_time=max(0.0, time.monotonic() - started_at),
            timed_out=timed_out,
            logs=logs,
            executed_command=executed_command,
            installed_dependencies=installed_dependencies,
            sandbox_path=sandbox_path,
            log_path=str(log_path),
        )
