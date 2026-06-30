"""Static step-definition scanner.

Parses Python source files to extract Behave step definitions decorated with
``@given``, ``@when``, ``@then`` or ``@step``.  No Behave installation is
required — the scanner works purely on source code via :mod:`ast`.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

STEP_DECORATORS = {"given", "when", "then", "step"}


@dataclass(slots=True)
class StepDefinition:
    """A single step definition found in source code."""

    keyword: str  # given | when | then | step
    pattern: str  # the string pattern or regex
    is_regex: bool  # whether the pattern is a compiled regex
    func_name: str  # the Python function name
    file_path: str  # relative file path
    line: int  # line number of the decorator
    end_line: int  # last line of the function
    docstring: str  # function docstring if any
    params: list[str] = field(default_factory=list)  # extracted parameter names
    source: str = ""  # function source code snippet


@dataclass(slots=True)
class StepCatalog:
    """Collection of step definitions with aggregate metrics."""

    steps: list[StepDefinition] = field(default_factory=list)
    base_dir: str = ""

    @property
    def total(self) -> int:
        return len(self.steps)

    @property
    def by_keyword(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self.steps:
            counts[s.keyword] = counts.get(s.keyword, 0) + 1
        return counts

    @property
    def by_file(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self.steps:
            counts[s.file_path] = counts.get(s.file_path, 0) + 1
        return counts

    @property
    def with_params(self) -> int:
        return sum(1 for s in self.steps if s.params)

    @property
    def with_docstring(self) -> int:
        return sum(1 for s in self.steps if s.docstring)

    @property
    def regex_steps(self) -> int:
        return sum(1 for s in self.steps if s.is_regex)


def _extract_pattern(node: ast.expr) -> tuple[str, bool]:
    """Extract the pattern string from a decorator argument.

    Returns (pattern, is_regex).
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, False
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "re" and node.args and isinstance(node.args[0], ast.Constant):
            return node.args[0].value, True
        if isinstance(func, ast.Attribute) and func.attr == "compile" and node.args and isinstance(node.args[0], ast.Constant):
            return node.args[0].value, True
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            elif isinstance(val, ast.FormattedValue) and isinstance(val.value, ast.Name):
                parts.append(f"{{{val.value.id}}}")
        return "".join(parts), False
    return "", False


def _extract_params(pattern: str, func_args: list[ast.arg]) -> list[str]:
    """Extract parameter names from a step pattern and function signature."""
    func_params = [a.arg for a in func_args if a.arg != "context"]
    if not pattern:
        return func_params
    pattern_params = re.findall(r"\{([^}]+)\}", pattern)
    if pattern_params:
        return pattern_params
    return func_params


def _get_source_lines(source: str, start: int, end: int) -> str:
    lines = source.splitlines()
    start_idx = max(0, start - 1)
    end_idx = min(len(lines), end)
    return "\n".join(lines[start_idx:end_idx])


def scan_file(file_path: Path, base_dir: Path | None = None) -> list[StepDefinition]:
    """Scan a single Python file for step definitions.

    Args:
        file_path: Path to the Python file to scan.
        base_dir: Base directory for computing relative paths.

    Returns:
        List of StepDefinition instances found in the file.

    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    rel_path = str(file_path.relative_to(base_dir)) if base_dir else str(file_path)
    definitions: list[StepDefinition] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        for decorator in node.decorator_list:
            keyword = None
            pattern_node = None

            if isinstance(decorator, ast.Name) and decorator.id in STEP_DECORATORS:
                keyword = decorator.id
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr in STEP_DECORATORS:
                    keyword = decorator.attr
            elif isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Name) and func.id in STEP_DECORATORS:
                    keyword = func.id
                    if decorator.args:
                        pattern_node = decorator.args[0]
                elif isinstance(func, ast.Attribute) and func.attr in STEP_DECORATORS:
                    keyword = func.attr
                    if decorator.args:
                        pattern_node = decorator.args[0]

            if keyword is None:
                continue

            pattern, is_regex = _extract_pattern(pattern_node) if pattern_node else ("", False)

            func_args = []
            if node.args and node.args.args:
                func_args = node.args.args

            params = _extract_params(pattern, func_args)

            docstring = ast.get_docstring(node) or ""

            source_snippet = _get_source_lines(source, node.lineno, node.end_lineno or node.lineno)

            definitions.append(StepDefinition(
                keyword=keyword,
                pattern=pattern,
                is_regex=is_regex,
                func_name=node.name,
                file_path=rel_path,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=docstring,
                params=params,
                source=source_snippet,
            ))

    return definitions


def scan_directory(directory: Path) -> StepCatalog:
    """Scan a directory tree for Python files with step definitions.

    Args:
        directory: Root directory to scan (typically ``features/steps``).

    Returns:
        StepCatalog with all definitions found.

    """
    directory = directory.resolve()
    catalog = StepCatalog(base_dir=str(directory))
    py_files = sorted(directory.rglob("*.py"))

    for py_file in py_files:
        if py_file.name.startswith("__"):
            continue
        defs = scan_file(py_file, base_dir=directory)
        catalog.steps.extend(defs)

    return catalog
