#!/usr/bin/env python3
"""Линтер качества автотестов: исполняемая версия чек-листа из SKILL.md.

Без зависимостей (stdlib): работает и до установки venv проекта.
Понимает python-ветки (ast) и java-ветки (регулярки).

    python <директория-скилла>/scripts/review_tests.py .            # весь проект
    python <директория-скилла>/scripts/review_tests.py . --json     # для CI/агента
    python <директория-скилла>/scripts/review_tests.py . --fail-on medium

Коды возврата: 0 — находок ниже порога нет, 1 — есть, 2 — нечего проверять.

Назначение: шаг 5 «Самопроверка качества» и режим «Ревью» не должны держаться
на памяти — здесь они проверяются детерминированно. Линтер намеренно
консервативен: лучше не найти спорное, чем завалить отчёт шумом. Он не заменяет
чтение кода, а снимает механическую часть.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

SEVERITIES = ["critical", "high", "medium", "low"]

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "allure-results", "allure-report",
    "target", "build", "__pycache__", ".pytest_cache", ".idea", ".gradle",
}

# Достаточно «секретоподобные» литералы: JWT, длинные hex/base64-ключи, пароли.
SECRET_PATTERNS = [
    (re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\."), "JWT-токен в коде"),
    (re.compile(r"(?i)\b(password|passwd|secret|api_?key|token)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"),
     "пароль/токен захардкожен в коде"),
]
URL_PATTERN = re.compile(r"[\"']https?://(?!localhost|127\.0\.0\.1)[^\"'\s]+[\"']")
UUID_PATTERN = re.compile(r"[\"'][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[\"']")


@dataclass
class Finding:
    severity: str
    rule: str
    file: str
    line: int
    message: str
    fix: str


def is_test_path(path: Path) -> bool:
    """Файл относится к тестам, а не к слою клиентов/страниц/конфига.

    Для java `src/test/java` содержит весь тестовый проект целиком, поэтому
    тестом считается только файл с именем *Test/*Tests/*IT — иначе правила
    вроде «URL захардкожен» ругались бы на TestConfig, где дефолт уместен.
    """
    if path.suffix == ".java":
        return path.name.endswith(("Test.java", "Tests.java", "IT.java"))
    parts = {p.lower() for p in path.parts}
    return "tests" in parts or "test" in parts or path.name.startswith("test_")


def iter_files(root: Path, suffix: str):
    for path in sorted(root.rglob(f"*{suffix}")):
        if SKIP_DIRS & set(path.parts):
            continue
        yield path


# --------------------------------------------------------------------------- python

def _decorator_names(node: ast.AST) -> list[str]:
    names = []
    for dec in getattr(node, "decorator_list", []):
        names.append(ast.unparse(dec))
    return names


def _has_assertion(fn: ast.FunctionDef) -> bool:
    """Есть ли в теле хоть одна проверка: assert, assert_*/expect/should, pytest.raises."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            call = ast.unparse(node.func)
            if re.search(r"(^|\.)(assert\w*|expect|should\w*|raises|check)$", call):
                return True
        if isinstance(node, ast.With):
            for item in node.items:
                if "raises" in ast.unparse(item.context_expr):
                    return True
    return False


def _only_status_assertions(fn: ast.FunctionDef) -> bool:
    """Все проверки теста — только про код ответа (тело ответа не проверяется)."""
    checks = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            checks.append(ast.unparse(node.test))
        elif isinstance(node, ast.Call):
            call = ast.unparse(node.func)
            if re.search(r"(^|\.)assert\w*$", call):
                checks.append(ast.unparse(node))
    if not checks:
        return False
    status_only = re.compile(r"status_code|assert_status\(|status\s*==")
    contract = re.compile(r"assert_contract|model_validate|json\(\)|\.text|assert_error")
    return all(status_only.search(c) for c in checks) and not any(contract.search(c) for c in checks)


def check_python(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    test_dirs_seen: set[Path] = set()

    for path in iter_files(root, ".py"):
        rel = str(path.relative_to(root))
        source = path.read_text(encoding="utf-8", errors="replace")
        lines = source.splitlines()
        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            findings.append(Finding("critical", "syntax", rel, error.lineno or 1,
                                    f"файл не парсится: {error.msg}", "почините синтаксис"))
            continue

        in_tests = is_test_path(path)
        if in_tests and path.parent != root:
            test_dirs_seen.add(path.parent)

        # --- построчные правила
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if in_tests and re.search(r"\btime\.sleep\(|\bsleep\(\d|wait_for_timeout\(", line):
                findings.append(Finding(
                    "high", "sleep", rel, number,
                    "sleep/wait_for_timeout в тесте — слепое ожидание",
                    "wait_until из utils/waiters.py или expect(...).to_be_visible()"))
            # conftest исключён: там фикстуры законно конструируют HTTP-клиент
            if in_tests and path.name != "conftest.py" and re.search(
                    r"\brequests\.(get|post|put|delete|patch)\(|httpx\.(get|post|Client\()", line):
                findings.append(Finding(
                    "medium", "http-in-test", rel, number,
                    "HTTP-вызов прямо из теста в обход клиентского слоя",
                    "перенесите вызов в clients/<resource>.py"))
            if in_tests and "networkidle" in line:
                findings.append(Finding(
                    "medium", "networkidle", rel, number,
                    "ожидание networkidle нестабильно на живых страницах",
                    "ждите конкретный элемент/ответ, а не тишину сети"))
            if in_tests and re.search(r"By\.XPATH|xpath=|\.xpath\(", line) and re.search(r"\[\d+\]|/div|/span", line):
                findings.append(Finding(
                    "high", "fragile-xpath", rel, number,
                    "хрупкий xpath (индексы/путь по вёрстке)",
                    "стабильный id/data-testid → роль → css"))
            for pattern, message in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding("critical", "secret", rel, number, message,
                                            "вынесите в env-переменную/Settings"))
            if in_tests and URL_PATTERN.search(line) and "example.com" not in line:
                findings.append(Finding(
                    "medium", "hardcoded-url", rel, number,
                    "URL захардкожен в тесте — сломается на другом стенде",
                    "берите base_url из config.Settings"))
            if in_tests and UUID_PATTERN.search(line) and "0000-0000" not in line:
                findings.append(Finding(
                    "medium", "hardcoded-id", rel, number,
                    "id опорных данных захардкожен",
                    "создавайте данные фикстурой или получайте запросом"))
            if re.search(r"extra\s*=\s*[\"']ignore[\"']", line) and "config.py" not in rel:
                findings.append(Finding(
                    "medium", "weak-contract", rel, number,
                    "модель с extra='ignore' не ловит недокументированные поля",
                    "extra='forbid'; ослабление — точечно и с комментарием"))
            if "xfail" in line and "strict" not in line and "pytest.ini" not in rel:
                findings.append(Finding(
                    "medium", "xfail-not-strict", rel, number,
                    "xfail без strict=True: починенный баг не просигналит",
                    "xfail(reason='Баг API: ...', strict=True)"))

        # --- правила по тестовым функциям
        if not in_tests:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test"):
                continue
            decorators = " ".join(_decorator_names(node))
            if not _has_assertion(node):
                findings.append(Finding(
                    "critical", "no-assert", rel, node.lineno,
                    f"тест {node.name} не содержит ни одной проверки — он не может упасть",
                    "добавьте assert_status/assert_contract и проверку значений"))
            elif _only_status_assertions(node):
                findings.append(Finding(
                    "medium", "weak-assert", rel, node.lineno,
                    f"тест {node.name} проверяет только статус-код",
                    "assert_contract(...) + проверка значений полей"))
            if "allure.severity" not in decorators:
                findings.append(Finding(
                    "low", "no-severity", rel, node.lineno,
                    f"у теста {node.name} нет @allure.severity",
                    "blocker/critical/normal/minor по таксономии SKILL.md"))
            if "flaky" in decorators:
                # Долг карантина документируется комментарием: либо в конце строки
                # с маркером, либо в строках прямо над ним.
                marker_line = next(
                    (index for index in range(max(0, node.lineno - 6), node.lineno)
                     if "flaky" in lines[index]), node.lineno - 1)
                documented = "#" in lines[marker_line].split("flaky")[-1] or any(
                    lines[index].strip().startswith("#")
                    for index in range(max(0, marker_line - 3), marker_line))
                if not documented:
                    findings.append(Finding(
                        "low", "quarantine-without-debt", rel, node.lineno,
                        f"тест {node.name} в карантине flaky без комментария о причине",
                        "симптом + гипотеза + срок возврата рядом с маркером"))
            for inner in ast.walk(node):
                if isinstance(inner, ast.Global):
                    findings.append(Finding(
                        "high", "shared-state", rel, inner.lineno,
                        f"тест {node.name} пишет в глобальную переменную — зависимость от порядка",
                        "состояние в фикстуры, каждый тест готовит свои данные"))

    for directory in sorted(test_dirs_seen):
        if not (directory / "__init__.py").exists():
            findings.append(Finding(
                "medium", "missing-init", str(directory.relative_to(root)), 1,
                "нет __init__.py — одинаковые имена файлов уронят коллекцию pytest",
                "положите пустой __init__.py в tests/ и каждую поддиректорию"))
    return findings


# ----------------------------------------------------------------------------- java

def check_java(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root, ".java"):
        rel = str(path.relative_to(root))
        source = path.read_text(encoding="utf-8", errors="replace")
        lines = source.splitlines()
        in_tests = is_test_path(path)

        if in_tests and "@Test" in source and not re.search(
                r"\bassert\w*\(|Assertions\.|\.should[A-Za-z]*\(|assertThat\(|\.statusCode\(", source):
            findings.append(Finding(
                "critical", "no-assert", rel, 1,
                "в файле есть @Test, но нет ни одной проверки",
                "добавьте Assertions/should/statusCode"))

        for number, line in enumerate(lines, start=1):
            if line.strip().startswith("//"):
                continue
            if in_tests and "Thread.sleep(" in line:
                findings.append(Finding(
                    "high", "sleep", rel, number, "Thread.sleep в тесте — слепое ожидание",
                    "Awaitility / should(visible, Duration)"))
            if in_tests and re.search(r"By\.xpath|\$x\(", line) and re.search(r"\[\d+\]|/div|/span", line):
                findings.append(Finding(
                    "high", "fragile-xpath", rel, number, "хрупкий xpath (индексы/путь по вёрстке)",
                    "стабильный id/data-testid → роль → css"))
            for pattern, message in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding("critical", "secret", rel, number, message,
                                            "System.getenv / TestConfig"))
            if in_tests and URL_PATTERN.search(line) and "example.com" not in line:
                findings.append(Finding(
                    "medium", "hardcoded-url", rel, number,
                    "URL захардкожен в тесте — сломается на другом стенде",
                    "берите базовый URL из TestConfig (env-переменные)"))
            if "@Test" in line.strip() and number < len(lines):
                # Аннотации метода идут блоком: от @Test вперёд до сигнатуры
                # (строка с `void`) — @Severity может стоять в любой строке блока.
                window = lines[max(0, number - 4):number - 1]
                for ahead in lines[number - 1:number + 11]:
                    window.append(ahead)
                    if re.search(r"\bvoid\b|\)\s*\{", ahead):
                        break
                if "@Severity" not in "\n".join(window):
                    findings.append(Finding(
                        "low", "no-severity", rel, number, "у теста нет @Severity",
                        "BLOCKER/CRITICAL/NORMAL/MINOR по таксономии SKILL.md"))
    return findings


# ---------------------------------------------------------------------------- отчёт

def render(findings: list[Finding], threshold: str) -> str:
    if not findings:
        return "Находок нет — чек-лист качества пройден.\n"
    lines = []
    for severity in SEVERITIES:
        bucket = [f for f in findings if f.severity == severity]
        if not bucket:
            continue
        lines.append(f"\n=== {severity.upper()} ({len(bucket)})")
        for finding in bucket:
            lines.append(f"  {finding.file}:{finding.line}  [{finding.rule}] {finding.message}")
            lines.append(f"      → {finding.fix}")
    counts = ", ".join(
        f"{severity}: {sum(1 for f in findings if f.severity == severity)}"
        for severity in SEVERITIES if any(f.severity == severity for f in findings)
    )
    lines.append(f"\nИтого: {len(findings)} ({counts}); порог падения — {threshold}.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Линтер качества автотестов (чек-лист does-it-work)")
    parser.add_argument("path", nargs="?", default=".", help="Корень тестового проекта")
    parser.add_argument("--json", action="store_true", help="Вывод в JSON (для CI/агента)")
    parser.add_argument("--fail-on", default="high", choices=SEVERITIES + ["none"],
                        help="Минимальная severity, при которой код возврата 1 (default: high)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Не директория: {root}", file=sys.stderr)
        return 2

    findings = check_python(root) + check_java(root)
    findings.sort(key=lambda f: (SEVERITIES.index(f.severity), f.file, f.line))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        print(render(findings, args.fail_on))

    if args.fail_on == "none":
        return 0
    limit = SEVERITIES.index(args.fail_on)
    return 1 if any(SEVERITIES.index(f.severity) <= limit for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
