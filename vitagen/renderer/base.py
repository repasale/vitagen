"""Abstract renderer interface for extensibility (LaTeX, HTML, DOCX)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseRenderer(ABC):
    """Render a resolved CV context to an output file."""

    @abstractmethod
    def render(
        self,
        context: dict[str, Any],
        *,
        template: str,
        output_path: Path,
        assets_path: Path,
    ) -> Path:
        """Produce output file and return its path."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Short format identifier, e.g. 'pdf', 'html', 'docx'."""
