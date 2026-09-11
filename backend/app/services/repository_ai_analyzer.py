"""Static reproducibility-risk analysis for extracted repositories."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from app.core.logging import get_logger
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis, RepositoryIssue

logger = get_logger("repository_ai_analyzer")


class RepositoryAIAnalyzer:
    """Detect reproducibility issues without importing or executing code."""

    FRAMEWORKS = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "streamlit": "Streamlit",
        "gradio": "Gradio",
        "torch": "PyTorch",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "scikit-learn": "Scikit-Learn",
        "sklearn": "Scikit-Learn",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "typer": "Typer",
        "click": "Click",
        "jupyter": "Jupyter",
        "jupyterlab": "Jupyter",
        "notebook": "Jupyter",
        "ipykernel": "Jupyter",
    }
    IMPORT_TO_PACKAGE = {
        "cv2": "opencv-python",
        "sklearn": "scikit-learn",
        "yaml": "PyYAML",
        "torch": "torch",
        "tensorflow": "tensorflow",
        "xgboost": "xgboost",
        "lightgbm": "lightgbm",
        "pandas": "pandas",
        "numpy": "numpy",
        "openpyxl": "openpyxl",
        "pyarrow": "pyarrow",
        "fastapi": "fastapi",
        "flask": "flask",
        "django": "django",
        "streamlit": "streamlit",
        "gradio": "gradio",
        "typer": "typer",
        "click": "click",
    }
    STDLIB = {
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "collections",
        "csv",
        "datetime",
        "functools",
        "glob",
        "io",
        "itertools",
        "json",
        "logging",
        "math",
        "os",
        "pathlib",
        "random",
        "re",
        "shutil",
        "statistics",
        "string",
        "subprocess",
        "sys",
        "tempfile",
        "time",
        "typing",
        "unittest",
        "uuid",
        "zipfile",
    }
    SEVERITY_WEIGHT = {"LOW": 5, "MEDIUM": 12, "HIGH": 22, "CRITICAL": 35}
    ENTRY_NAMES = {
        "main.py",
        "app.py",
        "train.py",
        "run.py",
        "manage.py",
        "server.py",
        "cli.py",
    }

    def analyze(
        self, repository_path: Path, metadata: RepositoryMetadata
    ) -> RepositoryAIAnalysis:
        root = Path(repository_path)
        if not root.is_dir():
            raise ValueError(f"Repository path is not a directory: {root}")
        issues: list[RepositoryIssue] = []
        source_text = self._source_text(root)
        imports, locations, syntax_errors = self._imports(root)
        declared, config_text = self._declared_dependencies(root)
        names = {Path(item).name for item in metadata.important_files}
        self._metadata_issues(issues, metadata, names, root, config_text)
        for filename, message in syntax_errors:
            self._add(
                issues,
                "BROKEN_IMPORT",
                "Broken Python source",
                "Python AST parsing failed.",
                "HIGH",
                96,
                message,
                "Fix the syntax or import structure.",
                filename,
            )
        self._framework_issues(issues, imports, config_text, metadata)
        self._dependency_issues(issues, declared, imports, locations)
        self._dataset_issues(issues, root, metadata, source_text)
        self._code_issues(issues, root, source_text, imports)
        self._notebook_issues(issues, root)
        risk = min(100, sum(self.SEVERITY_WEIGHT[item.severity] for item in issues))
        critical = sum(item.severity == "CRITICAL" for item in issues)
        execution = max(0, 100 - risk - critical * 20)
        reproducibility = max(0, 100 - risk)
        report = RepositoryAIAnalysis(
            repository_id=metadata.repository_id,
            repository_name=metadata.repository_name,
            issues=issues,
            execution_probability=execution,
            reproducibility_score=reproducibility,
            risk_score=risk,
            summary=self._summary(issues, execution, reproducibility),
        )
        logger.info(
            "AI analysis complete for %s: issues=%d execution=%d reproducibility=%d risk=%d",
            root,
            len(issues),
            execution,
            reproducibility,
            risk,
        )
        return report

    def _metadata_issues(self, issues, metadata, names, root, config_text) -> None:
        if "README.md" not in names:
            self._add(
                issues,
                "MISSING_README",
                "Missing README",
                "README.md is missing.",
                "LOW",
                99,
                "README.md was not detected.",
                "Add Installation, Usage, Dataset, and License sections.",
            )
        else:
            readme_path = next(
                (
                    item
                    for item in metadata.important_files
                    if Path(item).name == "README.md"
                ),
                "README.md",
            )
            readme = self._read_text(root / readme_path)
            for heading in ("installation", "usage", "dataset", "license"):
                if not re.search(
                    rf"^#+\s+.*{heading}", readme, re.IGNORECASE | re.MULTILINE
                ):
                    self._add(
                        issues,
                        "README_SECTION_MISSING",
                        f"README missing {heading.title()} section",
                        f"README.md has no {heading} section.",
                        "LOW",
                        94,
                        "Required reproducibility documentation heading was not found.",
                        f"Document {heading} instructions in README.md.",
                        "README.md",
                    )
        if not {"LICENSE", "LICENSE.txt", "COPYING"}.intersection(names):
            self._add(
                issues,
                "MISSING_LICENSE",
                "Missing license",
                "No recognized license file was found.",
                "LOW",
                99,
                "LICENSE, LICENSE.txt, and COPYING are absent.",
                "Add a project license.",
            )
        if not {
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "environment.yml",
        }.intersection(names):
            self._add(
                issues,
                "MISSING_REQUIREMENTS",
                "Missing requirements",
                "No dependency manifest was found.",
                "HIGH",
                99,
                "No supported dependency file is present.",
                "Add a pinned dependency manifest.",
            )
        if not {"Dockerfile", "docker-compose.yml", "compose.yaml"}.intersection(names):
            self._add(
                issues,
                "MISSING_DOCKER",
                "Missing Docker definition",
                "No Dockerfile or Compose file was found.",
                "LOW",
                99,
                "Container configuration is absent.",
                "Add a Dockerfile or document the runtime environment.",
            )
        if not any(Path(item).name in self.ENTRY_NAMES for item in metadata.tree):
            self._add(
                issues,
                "MISSING_ENTRY_POINT",
                "Missing entry point",
                "No conventional Python entry file was found.",
                "HIGH",
                92,
                "Entry-point filename scan found no supported file.",
                "Add and document a deterministic entry point.",
            )
        if metadata.python_files and not re.search(
            r"(?:python_requires|requires-python|python\s*[:=]|python_version|^3\.\d)",
            config_text,
            re.IGNORECASE | re.MULTILINE,
        ):
            self._add(
                issues,
                "PYTHON_VERSION_UNSPECIFIED",
                "Python version unspecified",
                "The supported Python version is not declared.",
                "MEDIUM",
                88,
                "No version marker was found in Python configuration files.",
                "Declare the supported Python version in pyproject.toml, runtime.txt, .python-version, setup.cfg, or setup.py.",
            )

    def _framework_issues(self, issues, imports, config_text, metadata) -> None:
        detected = {
            self.FRAMEWORKS[key]
            for key in self.FRAMEWORKS
            if key in imports
            or re.search(
                rf"(?<![\w-]){re.escape(key)}(?![\w-])", config_text, re.IGNORECASE
            )
        }
        detected.update(item for item in metadata.detected_frameworks if item)
        if not detected and metadata.python_files:
            self._add(
                issues,
                "FRAMEWORK_UNDETECTED",
                "Framework not detected",
                "Python files exist but no supported framework was identified.",
                "LOW",
                72,
                "Import and dependency scans found no supported framework.",
                "Document the project framework in README.md or configuration.",
            )

    def _dependency_issues(self, issues, declared, imports, locations) -> None:
        declared_norm = {self._normalize_package(item) for item in declared}
        for module in sorted(imports):
            if module in self.STDLIB or module in {"pytest", "setuptools"}:
                continue
            package = self.IMPORT_TO_PACKAGE.get(module, module)
            if self._normalize_package(package) not in declared_norm:
                file = locations.get(module, [""])[0]
                self._add(
                    issues,
                    "MISSING_DEPENDENCY",
                    f"Missing dependency: {package}",
                    f"Import '{module}' has no matching declared dependency.",
                    "HIGH",
                    90,
                    f"AST import scan found {module} in {file}.",
                    f"Declare pinned dependency {package}.",
                    file,
                )
        import_packages = {
            self._normalize_package(self.IMPORT_TO_PACKAGE.get(module, module))
            for module in imports
        }
        for package in sorted(declared_norm - import_packages):
            if package in {self._normalize_package(value) for value in self.FRAMEWORKS}:
                self._add(
                    issues,
                    "UNUSED_DEPENDENCY",
                    f"Possibly unused dependency: {package}",
                    f"{package} is declared but no import was found.",
                    "LOW",
                    68,
                    "Declared dependency did not match a static import.",
                    "Remove it or document indirect/runtime use.",
                )

    def _dataset_issues(self, issues, root, metadata, source_text) -> None:
        calls = re.finditer(
            r"(?P<call>read_csv|read_excel|read_json|read_parquet|np\.load|torch\.load|open)\s*\(\s*['\"](?P<path>[^'\"]+)",
            source_text,
        )
        literal_paths = re.finditer(
            r"(?P<path>[\w./\\-]+\.(?:csv|json|xlsx|parquet))",
            source_text,
            re.IGNORECASE,
        )
        detected = {item.replace("\\", "/").lower() for item in metadata.datasets}
        names = {Path(item).name.lower() for item in metadata.datasets}
        call_found = False
        for match in calls:
            call_found = True
            raw = match.group("path")
            normalized = raw.replace("\\", "/").lstrip("./").lower()
            if normalized not in detected and Path(normalized).name not in names:
                file = self._file_for_text(root, match.group(0))
                self._add(
                    issues,
                    (
                        "MISSING_DATASET"
                        if not metadata.datasets
                        else "INVALID_DATASET_PATH"
                    ),
                    (
                        "Missing dataset"
                        if not metadata.datasets
                        else "Invalid dataset path"
                    ),
                    f"Dataset path '{raw}' does not resolve to a detected file.",
                    "HIGH",
                    94,
                    f"Static call analysis found {match.group('call')}('{raw}').",
                    "Add the dataset or correct the path.",
                    file,
                )
        if not call_found:
            for match in literal_paths:
                raw = match.group("path")
                normalized = raw.replace("\\", "/").lstrip("./").lower()
                if normalized not in detected and Path(normalized).name not in names:
                    self._add(
                        issues,
                        "INVALID_DATASET_PATH",
                        "Invalid dataset path",
                        f"Dataset path '{raw}' does not resolve to a detected file.",
                        "HIGH",
                        86,
                        "A dataset filename was found in source but not in repository metadata.",
                        "Add the dataset or correct the path.",
                        self._file_for_text(root, raw),
                    )

    def _code_issues(self, issues, root, source_text, imports) -> None:
        if re.search(
            r"(?:[A-Za-z]:[\\/]|\\\\[^\\]+\\|/home/|/Users/|/mnt/|/data/)", source_text
        ):
            self._add(
                issues,
                "HARDCODED_PATH",
                "Hardcoded filesystem path",
                "Source contains an environment-specific or network path.",
                "MEDIUM",
                92,
                "Path regex matched Windows, Unix, mounted, or network path syntax.",
                "Use configuration or environment variables.",
            )
        if (
            re.search(r"os\.environ|getenv\(|environ\[|process\.env", source_text)
            and not (root / ".env.example").exists()
        ):
            self._add(
                issues,
                "ENVIRONMENT_VARIABLES",
                "Environment variables required",
                "Code reads environment variables without a template.",
                "MEDIUM",
                86,
                "Environment access was detected without .env.example.",
                "Document required variables in .env.example or README.md.",
            )
        if not any(
            re.search(pattern, source_text)
            for pattern in (
                r"random\.seed",
                r"(?:np|numpy)\.random\.seed",
                r"torch\.manual_seed",
                r"tf\.random\.set_seed",
                r"jax\.random",
            )
        ):
            self._add(
                issues,
                "RANDOM_SEED_MISSING",
                "Random seed is not configured",
                "No supported deterministic seed initialization was detected.",
                "MEDIUM",
                88,
                "Seed pattern scan found no supported seed.",
                "Set and document all relevant random seeds.",
            )
        if {"torch", "tensorflow"}.intersection(imports):
            self._add(
                issues,
                "GPU_DEPENDENCY",
                "GPU-capable dependency detected",
                "PyTorch or TensorFlow may require accelerator support.",
                "MEDIUM",
                80,
                "GPU-capable framework import was detected.",
                "Document CPU fallback and GPU/runtime requirements.",
            )
        if re.search(r"(?:from\s+\.|import\s+\.)", source_text):
            self._add(
                issues,
                "RELATIVE_IMPORT",
                "Relative import detected",
                "Relative imports may fail when an entry file is run directly.",
                "MEDIUM",
                82,
                "Static scan found relative import syntax.",
                "Run the package as a module or correct package layout.",
            )
        if re.search(
            r"(?:\.pth|\.pt|\.ckpt|\.h5|\.safetensors)", source_text, re.IGNORECASE
        ) and not any(
            path.suffix.lower() in {".pth", ".pt", ".ckpt", ".h5", ".safetensors"}
            for path in root.rglob("*")
        ):
            self._add(
                issues,
                "MISSING_MODEL_CHECKPOINT",
                "Model checkpoint may be missing",
                "Source references a model checkpoint but no checkpoint file was detected.",
                "HIGH",
                80,
                "Checkpoint suffix was found in source without a matching file.",
                "Add the checkpoint or document a deterministic download step.",
            )

    def _notebook_issues(self, issues, root) -> None:
        for path in root.rglob("*.ipynb"):
            try:
                notebook = json.loads(self._read_text(path))
            except (json.JSONDecodeError, OSError):
                continue
            cells = notebook.get("cells", [])
            code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
            if any(not cell.get("outputs") for cell in code_cells):
                self._add(
                    issues,
                    "NOTEBOOK_MISSING_OUTPUTS",
                    "Notebook has missing outputs",
                    "One or more code cells have no saved outputs.",
                    "MEDIUM",
                    90,
                    "Notebook code cells contain empty outputs.",
                    "Run the notebook and save deterministic outputs.",
                    path.name,
                )
            if not any(cell.get("cell_type") == "markdown" for cell in cells):
                self._add(
                    issues,
                    "NOTEBOOK_MISSING_MARKDOWN",
                    "Notebook lacks markdown",
                    "No markdown cells explain the workflow.",
                    "LOW",
                    96,
                    "Notebook contains no markdown cells.",
                    "Add narrative markdown and execution guidance.",
                    path.name,
                )
            if len(json.dumps(notebook)) > 5_000_000:
                self._add(
                    issues,
                    "NOTEBOOK_LARGE_OUTPUT",
                    "Notebook has large outputs",
                    "Notebook JSON contains unusually large output data.",
                    "MEDIUM",
                    80,
                    "Serialized notebook exceeds 5 MB.",
                    "Clear bulky outputs or store artifacts separately.",
                    path.name,
                )
            if re.search(
                r"(?:[A-Za-z]:[\\/]|/home/|/Users/|/mnt/)", json.dumps(notebook)
            ):
                self._add(
                    issues,
                    "NOTEBOOK_ABSOLUTE_PATH",
                    "Notebook has absolute paths",
                    "Notebook contains host-specific paths.",
                    "MEDIUM",
                    90,
                    "Absolute path pattern found in notebook JSON.",
                    "Use relative paths or configuration.",
                    path.name,
                )

    def _imports(self, root):
        imports, locations, errors = set(), {}, []
        for path in root.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                errors.append((path.name, str(exc)))
                continue
            except OSError:
                continue
            for node in ast.walk(tree):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else (
                        [node.module]
                        if isinstance(node, ast.ImportFrom) and node.module
                        else []
                    )
                )
                for name in names:
                    module = name.split(".", 1)[0].lower()
                    imports.add(module)
                    locations.setdefault(module, []).append(path.name)
        return imports, locations, errors

    def _declared_dependencies(self, root):
        files = (
            "requirements.txt",
            "environment.yml",
            "pyproject.toml",
            "setup.py",
            "poetry.lock",
            "runtime.txt",
            ".python-version",
            "setup.cfg",
        )
        text = "\n".join(
            self._read_text(root / name) for name in files if (root / name).is_file()
        )
        packages = set()
        for line in text.lower().splitlines():
            match = re.match(
                r"\s*[-\"']?([a-z0-9][a-z0-9_.-]*)\s*(?:[<>=!~].*)?[,\"']?\s*$", line
            )
            if match and match.group(1) not in {
                "name",
                "version",
                "dependencies",
                "python",
            }:
                packages.add(match.group(1))
        return packages, text

    @staticmethod
    def _normalize_package(value: str) -> str:
        return value.lower().replace("_", "-").strip()

    def _source_text(self, root):
        return "\n".join(self._read_text(path) for path in root.rglob("*.py"))

    def _file_for_text(self, root, text):
        for path in root.rglob("*.py"):
            if text in self._read_text(path):
                return path.relative_to(root).as_posix()
        return ""

    @staticmethod
    def _read_text(path):
        try:
            return path.read_bytes()[:1_048_576].decode("utf-8", errors="ignore")
        except OSError:
            return ""

    @staticmethod
    def _add(
        issues,
        issue_type,
        title,
        description,
        severity,
        confidence,
        reason,
        fix,
        affected_file="",
    ):
        issues.append(
            RepositoryAIAnalyzer._issue(
                issue_type,
                title,
                description,
                severity,
                confidence,
                reason,
                fix,
                affected_file,
            )
        )

    @staticmethod
    def _issue(
        issue_type,
        title,
        description,
        severity,
        confidence,
        reason,
        fix,
        affected_file="",
    ):
        return RepositoryIssue(
            issue_type=issue_type,
            title=title,
            description=description,
            severity=severity,
            confidence=confidence,
            reason=reason,
            recommended_fix=fix,
            evidence=[reason],
            affected_file=affected_file,
        )

    @staticmethod
    def _summary(issues, execution_probability, reproducibility_score):
        if not issues:
            return "No static reproducibility issues were detected."
        return f"Detected {len(issues)} static issue(s). Execution probability is {execution_probability}% and reproducibility score is {reproducibility_score}%."
