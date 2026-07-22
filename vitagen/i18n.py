"""Language resolution with configurable, extensible multi-language support.

Vitagen loads built-in language definitions from ``vitagen/languages.yaml``.
Users can extend or override them by placing ``data/locale.yaml`` in their CV project.

Resolution order for any localized field (``{en: ..., es: ..., cz: ...}``):
  1. Requested language code
  2. Configured fallback language (default: ``en``)
  3. First non-empty translation found in the dict
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_BUILTIN_CONFIG = Path(__file__).resolve().parent / "languages.yaml"

# Populated at import time from languages.yaml; extended at runtime via load_locale_config().
_LANG_REGISTRY: dict[str, dict[str, Any]] = {}
_ALIAS_MAP: dict[str, str] = {}
_DEFAULT_LANG = "en"
_FALLBACK_LANG = "en"


def _register_language(code: str, config: dict[str, Any]) -> None:
    """Register one language code and all of its CLI aliases."""
    code = code.strip().lower()
    _LANG_REGISTRY[code] = config
    _ALIAS_MAP[code] = code
    for alias in config.get("aliases", []):
        _ALIAS_MAP[str(alias).strip().lower()] = code


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _apply_config(config: dict[str, Any]) -> None:
    """Merge a languages config dict into the in-memory registry."""
    global _DEFAULT_LANG, _FALLBACK_LANG

    _DEFAULT_LANG = str(config.get("default", _DEFAULT_LANG)).lower()
    _FALLBACK_LANG = str(config.get("fallback", _FALLBACK_LANG)).lower()

    for code, lang_cfg in config.get("languages", {}).items():
        if isinstance(lang_cfg, dict):
            _register_language(code, lang_cfg)


def _reset_registry() -> None:
    """Clear registry (used before reloading config in tests or project load)."""
    _LANG_REGISTRY.clear()
    _ALIAS_MAP.clear()


@lru_cache(maxsize=1)
def _load_builtin_config() -> None:
    _reset_registry()
    _apply_config(_load_yaml(_BUILTIN_CONFIG))


def load_locale_config(project_root: Path | None = None) -> None:
    """Load built-in languages and optional project ``data/locale.yaml`` overrides."""
    _load_builtin_config.cache_clear()
    _reset_registry()
    _apply_config(_load_yaml(_BUILTIN_CONFIG))

    if project_root is not None:
        locale_file = project_root / "data" / "locale.yaml"
        if locale_file.exists():
            _apply_config(_load_yaml(locale_file))


def normalize_lang(lang: str, *, project_root: Path | None = None) -> str:
    """Map a ``--lang`` value to a canonical two-letter (or custom) language code."""
    if project_root is not None:
        load_locale_config(project_root)
    else:
        _load_builtin_config()

    key = lang.strip().lower()
    if key in _ALIAS_MAP:
        return _ALIAS_MAP[key]

    # Accept direct codes (e.g. user-defined ``pt`` in locale.yaml).
    if key in _LANG_REGISTRY:
        return key

    supported = ", ".join(sorted(_ALIAS_MAP.keys()))
    raise ValueError(
        f"Unsupported language '{lang}'. "
        f"Known aliases: {supported}. "
        f"Add custom languages in data/locale.yaml."
    )


def list_languages() -> list[tuple[str, str]]:
    """Return (code, display_name) pairs for all registered languages."""
    _load_builtin_config()
    return sorted(
        (code, str(cfg.get("name", code)))
        for code, cfg in _LANG_REGISTRY.items()
    )


def get_fallback_lang() -> str:
    _load_builtin_config()
    return _FALLBACK_LANG


def get_babel_language(lang: str) -> str:
    """LaTeX babel package language name for PDF rendering."""
    _load_builtin_config()
    cfg = _LANG_REGISTRY.get(lang, {})
    return str(cfg.get("babel", "english"))


def get_all_babel_languages() -> list[str]:
    """Unique babel language names to load in LaTeX preamble."""
    _load_builtin_config()
    names = {str(cfg.get("babel", "english")) for cfg in _LANG_REGISTRY.values()}
    return sorted(names)


def get_filename_code(lang: str) -> str:
    _load_builtin_config()
    cfg = _LANG_REGISTRY.get(lang, {})
    return str(cfg.get("filename_code", lang.upper()))


def default_show_title_in_name(lang: str) -> bool:
    _load_builtin_config()
    cfg = _LANG_REGISTRY.get(lang, {})
    return bool(cfg.get("show_title_in_name", False))


def resolve_text(value: Any, lang: str, *, fallback: str | None = None) -> str:
    """Resolve a plain string or ``{en: ..., es: ...}`` dict to one string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        fb = fallback if fallback is not None else get_fallback_lang()
        if lang in value and value[lang]:
            return str(value[lang])
        if fb in value and value[fb]:
            return str(value[fb])
        for v in value.values():
            if v:
                return str(v)
        return ""
    return str(value)


def resolve_list(value: Any, lang: str, *, fallback: str | None = None) -> list[str]:
    """Resolve bullet lists that may be plain lists or per-language dicts."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, dict):
        fb = fallback if fallback is not None else get_fallback_lang()
        if lang in value and value[lang]:
            items = value[lang]
            if isinstance(items, list):
                return [str(i) for i in items if i]
        if fb in value and value[fb]:
            items = value[fb]
            if isinstance(items, list):
                return [str(i) for i in items if i]
        for items in value.values():
            if isinstance(items, list) and items:
                return [str(i) for i in items if i]
    return []


def format_display_name(personal: dict, lang: str) -> str:
    """Build full display name, optionally prefixing localized degree title."""
    title = resolve_text(personal.get("title", ""), lang)
    name = resolve_text(personal.get("name", ""), lang)
    middle = resolve_text(personal.get("middle_name", ""), lang)
    surname = resolve_text(personal.get("surname", ""), lang)

    show_title = personal.get("show_title_in_name")
    if show_title is None:
        include_title = default_show_title_in_name(lang) and bool(title)
    elif isinstance(show_title, bool):
        include_title = show_title
    elif isinstance(show_title, dict):
        fb = get_fallback_lang()
        include_title = bool(show_title.get(lang, show_title.get(fb, False)))
    else:
        include_title = bool(show_title)

    parts = []
    if include_title and title:
        parts.append(title)
    parts.extend(p for p in (name, middle, surname) if p)
    return " ".join(parts)


def section_label(key: str, lang: str) -> str:
    """Return a localized section heading (Experience, Education, …)."""
    _load_builtin_config()
    cfg = _LANG_REGISTRY.get(lang, {})
    labels = cfg.get("labels", {})
    if key in labels:
        return str(labels[key])
    fb = get_fallback_lang()
    fb_labels = _LANG_REGISTRY.get(fb, {}).get("labels", {})
    return str(fb_labels.get(key, key))
