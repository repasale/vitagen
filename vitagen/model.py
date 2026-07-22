"""Build a language-resolved, filter-ready CV context for renderers."""

from __future__ import annotations

from typing import Any

from vitagen.dates import sort_by_from_desc
from vitagen.filter import filter_experience
from vitagen.i18n import (
    format_display_name,
    get_all_babel_languages,
    get_babel_language,
    resolve_list,
    resolve_text,
    section_label,
)


def build_cv_context(
    project_data: dict[str, Any],
    *,
    lang: str,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """Transform raw YAML data into a flat, localized context dict for templates."""
    personal = project_data.get("personal", {})
    filtered_jobs = filter_experience(
        project_data.get("experience", []),
        include=include,
        exclude=exclude,
    )
    education_entries = sort_by_from_desc(_as_list(project_data.get("education")))
    job_entries = sort_by_from_desc(filtered_jobs)
    certificates = [
        c for c in (_build_certificate(cert, lang) for cert in _as_list(project_data.get("certificates")))
        if c.get("name")
    ]

    return {
        "lang": lang,
        "babel_language": get_babel_language(lang),
        "babel_languages": get_all_babel_languages(),
        "labels": {
            "experience": section_label("experience", lang),
            "education": section_label("education", lang),
            "skills": section_label("skills", lang),
            "languages": section_label("languages", lang),
            "certificates": section_label("certificates", lang),
            "present": section_label("present", lang),
        },
        "personal": _build_personal(personal, lang),
        "education": [_build_education(entry, lang) for entry in education_entries],
        "skills": _build_skills(project_data.get("skills", {}), lang),
        "languages": _build_languages(project_data.get("languages", {}), lang),
        "certificates": certificates,
        "experience": [_build_job(job, lang) for job in job_entries],
    }


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _build_personal(personal: dict, lang: str) -> dict[str, str]:
    return {
        "display_name": format_display_name(personal, lang),
        "title": resolve_text(personal.get("title", ""), lang),
        "name": resolve_text(personal.get("name", ""), lang),
        "middle_name": resolve_text(personal.get("middle_name", ""), lang),
        "surname": resolve_text(personal.get("surname", ""), lang),
        "city": resolve_text(personal.get("city", ""), lang),
        "email": resolve_text(personal.get("email", ""), lang),
        "telephone": resolve_text(personal.get("telephone", ""), lang),
        "linkedin": resolve_text(personal.get("linkedin", personal.get("LinkedIn", "")), lang),
        "github": resolve_text(personal.get("github", personal.get("Github", "")), lang),
        "web": resolve_text(personal.get("web", ""), lang),
        "photo": resolve_text(personal.get("photo", ""), lang),
    }


def _build_education(entry: dict, lang: str) -> dict[str, str]:
    return {
        "school": resolve_text(entry.get("school", ""), lang),
        "faculty": resolve_text(entry.get("faculty", ""), lang),
        "program": resolve_text(entry.get("program", ""), lang),
        "specialization": resolve_text(entry.get("specialization", ""), lang),
        "degree": resolve_text(entry.get("degree", ""), lang),
        "from": resolve_text(entry.get("from", ""), lang),
        "to": resolve_text(entry.get("to", ""), lang),
    }


def _build_skills(skills: Any, lang: str) -> list[dict[str, Any]]:
    if isinstance(skills, dict):
        result = []
        for category, items in skills.items():
            cat_name = resolve_text(category, lang) if isinstance(category, str) else str(category)
            if isinstance(items, list):
                result.append({"category": cat_name, "items": [resolve_text(i, lang) for i in items]})
            elif isinstance(items, dict):
                result.append({
                    "category": cat_name,
                    "items": [resolve_text(i, lang) for i in items.get(lang, items.get("en", []))],
                })
        return result
    if isinstance(skills, list):
        return [{"category": "", "items": [resolve_text(i, lang) for i in skills]}]
    return []


def _build_languages(languages: Any, lang: str) -> list[dict[str, str]]:
    if isinstance(languages, dict):
        return [
            {
                "name": resolve_text(name, lang),
                "level": resolve_text(level, lang),
            }
            for name, level in languages.items()
        ]
    if isinstance(languages, list):
        return [
            {
                "name": resolve_text(entry.get("name", ""), lang),
                "level": resolve_text(entry.get("level", ""), lang),
            }
            for entry in languages
        ]
    return []


def _build_certificate(cert: dict, lang: str) -> dict[str, str]:
    return {
        "name": resolve_text(cert.get("name", ""), lang),
        "issuer": resolve_text(cert.get("issuer", ""), lang),
        "year": resolve_text(cert.get("year", cert.get("date", "")), lang),
        "id": resolve_text(cert.get("id", ""), lang),
    }


def _build_job(job: dict, lang: str) -> dict[str, Any]:
    to_val = resolve_text(job.get("to", ""), lang)
    present = section_label("present", lang)
    if to_val.lower() in ("present", "současnost", "current"):
        to_val = present

    achievements = []
    for ach in job.get("achievements", []) or []:
        text = resolve_text(ach.get("text", ach), lang)
        if text:
            achievements.append(text)

    return {
        "employer": resolve_text(job.get("employer", ""), lang),
        "job_title": resolve_text(job.get("job_title", ""), lang),
        "location": resolve_text(job.get("location", ""), lang),
        "from": resolve_text(job.get("from", ""), lang),
        "to": to_val,
        "context": resolve_list(job.get("context", []), lang),
        "achievements": achievements,
    }
