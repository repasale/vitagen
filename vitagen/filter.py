"""Keyword-based filtering for jobs and achievements.

Filtering rules (``--include`` / ``--exclude``):

* A job is kept if any keyword on the job **or** on any achievement matches ``--include``.
* When ``--include`` is set, achievements without a matching keyword are dropped.
* ``--exclude`` removes jobs/achievements that match any excluded keyword.
* Job-level keywords apply to the whole position; achievement keywords allow bullet-level filtering.
"""

from __future__ import annotations

from typing import Any


def _normalize_keywords(raw: Any) -> set[str]:
    if not raw:
        return set()
    if isinstance(raw, str):
        return {raw.strip().lower()}
    return {str(k).strip().lower() for k in raw if k}


def _matches_include(keywords: set[str], include: set[str]) -> bool:
    if not include:
        return True
    return bool(keywords & include)


def _matches_exclude(keywords: set[str], exclude: set[str]) -> bool:
    if not exclude:
        return False
    return bool(keywords & exclude)


def filter_experience(
    jobs: list[dict[str, Any]],
    *,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Filter jobs and their achievements by keyword include/exclude rules."""
    include_set = {k.lower() for k in (include or set())}
    exclude_set = {k.lower() for k in (exclude or set())}

    if not include_set and not exclude_set:
        return jobs

    filtered: list[dict[str, Any]] = []
    for job in jobs:
        job_kw = _normalize_keywords(job.get("keywords", []))
        achievements = job.get("achievements", []) or []

        ach_kw: set[str] = set()
        for ach in achievements:
            ach_kw.update(_normalize_keywords(ach.get("keywords", [])))

        all_kw = job_kw | ach_kw

        if _matches_exclude(all_kw, exclude_set):
            continue

        if include_set and not _matches_include(all_kw, include_set):
            continue

        filtered_job = dict(job)
        if include_set and achievements:
            filtered_achievements = []
            for ach in achievements:
                ach_keywords = _normalize_keywords(ach.get("keywords", []))
                combined = job_kw | ach_keywords
                if _matches_exclude(combined, exclude_set):
                    continue
                if _matches_include(combined, include_set):
                    filtered_achievements.append(ach)
            filtered_job["achievements"] = filtered_achievements
            if not filtered_achievements and not _matches_include(job_kw, include_set):
                continue

        filtered.append(filtered_job)

    return filtered
