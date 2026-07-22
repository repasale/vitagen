"""Renderer registry for Vitagen output backends."""

from vitagen.renderer.base import BaseRenderer
from vitagen.renderer.latex import LatexRenderer

RENDERERS: dict[str, type[BaseRenderer]] = {
    "latex": LatexRenderer,
    "pdf": LatexRenderer,
}


def get_renderer(format_name: str = "latex") -> BaseRenderer:
    """Return a renderer instance for the requested output format."""
    key = format_name.lower()
    if key not in RENDERERS:
        supported = ", ".join(sorted(RENDERERS))
        raise ValueError(f"Unknown renderer '{format_name}'. Supported: {supported}")
    return RENDERERS[key]()
