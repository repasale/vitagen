"""Load YAML CV data from a user project directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from vitagen.paths import data_dir, experience_dir


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_project(project_root: Path) -> dict[str, Any]:
    """Load all CV data files from a user project."""
    root = data_dir(project_root)
    experiences: list[dict[str, Any]] = []
    exp_path = experience_dir(project_root)
    if exp_path.is_dir():
        for file in sorted(exp_path.glob("*.yaml")):
            data = _load_yaml(file)
            if data:
                data["_source"] = str(file)
                experiences.append(data)

    return {
        "personal": _load_yaml(root / "personal.yaml") or {},
        "education": _load_yaml(root / "education.yaml") or [],
        "skills": _load_yaml(root / "skills.yaml") or {},
        "languages": _load_yaml(root / "languages.yaml") or {},
        "certificates": _load_yaml(root / "certificates.yaml") or [],
        "experience": experiences,
    }


def collect_keywords(project_data: dict[str, Any]) -> set[str]:
    """Gather all keywords from experience jobs and achievements."""
    keywords: set[str] = set()
    for job in project_data.get("experience", []):
        keywords.update(_normalize_keywords(job.get("keywords", [])))
        for ach in job.get("achievements", []) or []:
            keywords.update(_normalize_keywords(ach.get("keywords", [])))
    return keywords


def _normalize_keywords(raw: Any) -> set[str]:
    if not raw:
        return set()
    if isinstance(raw, str):
        return {raw.strip().lower()}
    return {str(k).strip().lower() for k in raw if k}


def create_job_template(job_name: str, project_root: Path) -> Path:
    """Create a sample experience YAML file."""
    exp_path = experience_dir(project_root)
    exp_path.mkdir(parents=True, exist_ok=True)
    slug = job_name.lower().replace(" ", "-")
    target = exp_path / f"{slug}.yaml"
    if target.exists():
        raise FileExistsError(f"Job file already exists: {target}")

    sample = {
        "employer": "Company Name",
        "job_title": {
            "en": "Job Title",
            "es": "Título del puesto",
            "fr": "Intitulé du poste",
            "de": "Jobtitel",
            "cz": "Název pozice",
        },
        "location": "City, Country",
        "from": "January 2020",
        "to": "Present",
        "keywords": ["keyword1", "keyword2"],
        "context": {
            "en": [
                "Describe your role and responsibilities.",
                "Add another bullet point.",
            ],
            "cz": [
                "Popište svou roli a odpovědnosti.",
            ],
        },
        "achievements": [
            {
                "text": {
                    "en": "Achievement with its own keywords for filtering.",
                    "cz": "Úspěch s vlastními klíčovými slovy pro filtrování.",
                },
                "keywords": ["keyword1"],
            },
            {
                "text": {
                    "en": "Another achievement.",
                    "cz": "Další úspěch.",
                },
                "keywords": ["keyword2"],
            },
        ],
    }
    with target.open("w", encoding="utf-8") as fh:
        yaml.dump(sample, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return target
