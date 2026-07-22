"""Validate CV YAML data without generating output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vitagen.i18n import resolve_list, resolve_text
from vitagen.loader import load_project
from vitagen.paths import data_dir, experience_dir, templates_dir


@dataclass
class ValidationIssue:
    level: str  # error | warning
    message: str
    source: str = ""


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def add(self, level: str, message: str, source: str = "") -> None:
        self.issues.append(ValidationIssue(level, message, source))


def validate_project(
    project_root: Path,
    *,
    lang: str = "en",
    template: str | None = None,
) -> ValidationReport:
    """Check data completeness, structure, and render prerequisites."""
    report = ValidationReport()
    root = data_dir(project_root)

    required_files = [
        "personal.yaml",
        "education.yaml",
        "skills.yaml",
        "languages.yaml",
    ]
    for name in required_files:
        path = root / name
        if not path.exists():
            report.add("error", f"Missing required file: {path}", str(path))

    if not experience_dir(project_root).is_dir():
        report.add("warning", "No experience/ directory found.", str(experience_dir(project_root)))

    try:
        data = load_project(project_root)
    except Exception as exc:
        report.add("error", f"Failed to load project: {exc}")
        return report

    personal = data.get("personal", {})
    for field_name in ("name", "surname", "email"):
        if not resolve_text(personal.get(field_name, ""), lang):
            report.add("warning", f"Personal field '{field_name}' is empty.", "personal.yaml")

    for job in data.get("experience", []):
        source = job.get("_source", "experience")
        if not job.get("employer"):
            report.add("error", "Job missing 'employer'.", source)
        if not resolve_text(job.get("job_title", ""), lang):
            report.add("error", "Job missing 'job_title'.", source)
        if not job.get("from"):
            report.add("warning", "Job missing 'from' date.", source)
        if not resolve_list(job.get("context", []), lang) and not (job.get("achievements") or []):
            report.add("warning", "Job has no context bullets or achievements.", source)

    if template:
        tpl = templates_dir() / template
        if not tpl.is_dir():
            report.add("error", f"Template '{template}' not found in {templates_dir()}.")
        elif not (tpl / "template.tex.j2").exists():
            report.add("error", f"Template missing template.tex.j2.", str(tpl))

    return report


def format_report(report: ValidationReport) -> str:
    if not report.issues:
        return "Validation passed — no issues found."
    lines = []
    for issue in report.issues:
        prefix = issue.level.upper()
        loc = f" [{issue.source}]" if issue.source else ""
        lines.append(f"{prefix}{loc}: {issue.message}")
    status = "FAILED" if not report.ok else "PASSED WITH WARNINGS"
    return f"Validation {status}\n" + "\n".join(lines)
