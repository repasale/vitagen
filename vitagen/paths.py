"""Resolve vitagen install paths and user CV project paths.

Two directory trees coexist:

* **Vitagen home** — where the tool is installed (``templates/``, ``assets/``, ``output/``).
* **User CV project** — where your YAML data lives (``user-cv/data/`` or ``data/``).

Override the install location with the ``VITAGEN_HOME`` environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path


def vitagen_home() -> Path:
    """Directory where vitagen is installed (contains templates/, assets/, output/)."""
    env = os.environ.get("VITAGEN_HOME")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def resolve_input_dir(input_arg: str | None) -> Path:
    """Return the user CV project root (contains data/ or user-cv/data/).

    Resolution order:
    1. Explicit ``--input`` directory
    2. Current working directory
    3. Vitagen install directory (repo root when installed editable)
    """
    candidates: list[Path] = []

    if input_arg:
        candidates.append(Path(input_arg).resolve())
    else:
        candidates.append(Path.cwd().resolve())
        home = vitagen_home()
        if home not in candidates:
            candidates.append(home)

    checked: list[Path] = []
    for base in candidates:
        if base in checked:
            continue
        checked.append(base)
        if (base / "user-cv" / "data").is_dir():
            return base / "user-cv"
        if (base / "data").is_dir():
            return base

    searched = ", ".join(str(p) for p in checked)
    raise FileNotFoundError(
        f"No CV data found. Looked in: {searched}. "
        "Expected a 'data/' or 'user-cv/data/' directory. "
        "Use --input=DIR to point at your CV project, or run --help / --preview."
    )


def data_dir(project_root: Path) -> Path:
    return project_root / "data"


def experience_dir(project_root: Path) -> Path:
    return data_dir(project_root) / "experience"


def default_output_dir() -> Path:
    out = vitagen_home() / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def templates_dir() -> Path:
    return vitagen_home() / "templates"


def assets_dir() -> Path:
    return vitagen_home() / "assets"
