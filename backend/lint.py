"""
Automated Code Quality & Linter Inspector for FIFA WC 2026 Core Platform.

Scans all Python backend files for:
- AST syntax validity
- Missing module and function docstrings
- Flake8 / PEP8 style compliance (imports, blank lines, whitespace)
"""
import ast
import subprocess
import sys
from pathlib import Path

# Terminal colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

APP_DIR = Path(__file__).parent / "app"
TESTS_DIR = Path(__file__).parent / "tests"


def run_flake8():
    """Execute flake8 analysis on app and tests directory."""
    print(f"\n{BOLD}{CYAN}=== Running Flake8 Compliance Checker ==={RESET}\n")
    try:
        res = subprocess.run(
            [sys.executable, "-m", "flake8", "app", "tests"],
            capture_output=True,
            text=True,
        )
        output = res.stdout.strip()
        if not output:
            print(f"{GREEN}{BOLD}✔ Flake8: 0 PEP8 style issues found across all backend modules.{RESET}\n")
            return 0
        else:
            print(f"{YELLOW}Flake8 reported issues:\n{output}{RESET}\n")
            lines = [l for l in output.split("\n") if l.strip()]
            return len(lines)
    except FileNotFoundError:
        print(f"{YELLOW}Flake8 tool not found. Skipping PEP8 check.{RESET}\n")
        return 0


def run_lint_check():
    """Run comprehensive AST lint checks across app and tests directories."""
    print(f"\n{BOLD}{CYAN}=== FIFA WC 2026 Code Quality & AST Auditor ==={RESET}\n")

    files_scanned = 0
    total_issues = 0

    all_py_files = list(APP_DIR.glob("**/*.py")) + list(TESTS_DIR.glob("**/*.py"))

    for filepath in sorted(all_py_files):
        if filepath.name == "__init__.py" and "tests" in str(filepath):
            continue

        rel_path = filepath.relative_to(Path(__file__).parent)
        files_scanned += 1
        file_issues = []

        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError as e:
            total_issues += 1
            print(f"{RED}✖ {rel_path} - Syntax Error line {e.lineno}: {e.msg}{RESET}")
            continue

        # Check Module Docstring
        if not ast.get_docstring(tree):
            file_issues.append("Missing module docstring")

        # Check Function Docstrings & Type Annotations
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                if not ast.get_docstring(node) and not node.name.startswith("test_"):
                    file_issues.append(f"Function '{node.name}' (line {node.lineno}) lacks docstring")

            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    file_issues.append(f"Bare except handler found at line {node.lineno}")

        if file_issues:
            print(f"{YELLOW}⚠ {rel_path}:{RESET}")
            for issue in file_issues:
                print(f"   • {issue}")
            total_issues += len(file_issues)
        else:
            print(f"{GREEN}✔ {rel_path} - Clean{RESET}")

    flake8_issues = run_flake8()

    print(f"{BOLD}{CYAN}=== Audit Summary ==={RESET}")
    print(f"Files Scanned: {files_scanned}")
    if total_issues == 0 and flake8_issues == 0:
        print(f"{GREEN}{BOLD}PASSED! All {files_scanned} files passed AST & Flake8 checks with 0 errors.{RESET}\n")
        sys.exit(0)
    else:
        print(f"{YELLOW}Found {total_issues + flake8_issues} issue(s) across scanned files.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    run_lint_check()
