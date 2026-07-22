"""Default PDF output filenames."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from vitagen.i18n import get_filename_code, resolve_text


def _name_part(value: str) -> str:
    """Convert a name to an ASCII filename segment (e.g. Aleš -> Ales)."""
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", ascii_text)
    if not cleaned:
        return "Unknown"
    return cleaned[0].upper() + cleaned[1:]


def build_pdf_filename(personal: dict[str, Any], lang: str) -> str:
    """Return firstname_surname_LANG.pdf (e.g. John_Shepard_EN.pdf)."""
    first = _name_part(resolve_text(personal.get("name", ""), lang))
    last = _name_part(resolve_text(personal.get("surname", ""), lang))
    lang_code = get_filename_code(lang)
    return f"{first}_{last}_{lang_code}.pdf"
