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
    """Return the user CV project root (contains data/ or user-cv/data/)."""
    base = Path(input_arg or os.getcwd()).resolve()
    if (base / "user-cv" / "data").is_dir():
        return base / "user-cv"
    if (base / "data").is_dir():
        return base
    raise FileNotFoundError(
        f"No CV data found in {base}. Expected 'data/' or 'user-cv/data/'."
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
