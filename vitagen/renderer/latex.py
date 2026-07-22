"""LaTeX / PDF renderer using Jinja2 templates."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from vitagen.paths import assets_dir, templates_dir
from vitagen.renderer.base import BaseRenderer

LATEX_SPECIAL = re.compile(r"([#%&$_{}~^\\])")


def latex_escape(text: str) -> str:
    if not text:
        return ""
    return LATEX_SPECIAL.sub(r"\\\1", str(text))


def _find_pdflatex() -> str:
    """Resolve pdflatex binary, including common Windows install paths."""
    env_bin = os.environ.get("PDFLATEX")
    if env_bin and Path(env_bin).exists():
        return env_bin

    found = shutil.which("pdflatex")
    if found:
        return found

    local_app = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        Path(local_app) / "Programs/MiKTeX/miktex/bin/x64/pdflatex.exe",
        Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe"),
        Path(r"C:\texlive\2024\bin\windows\pdflatex.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return "pdflatex"


class LatexRenderer(BaseRenderer):
    format_name = "pdf"

    def render(
        self,
        context: dict[str, Any],
        *,
        template: str,
        output_path: Path,
        assets_path: Path | None = None,
    ) -> Path:
        tpl_dir = templates_dir() / template
        if not tpl_dir.is_dir():
            raise FileNotFoundError(f"Template '{template}' not found in {templates_dir()}")

        template_file = tpl_dir / "template.tex.j2"
        if not template_file.exists():
            raise FileNotFoundError(f"Missing {template_file}")

        env = Environment(
            loader=FileSystemLoader(str(tpl_dir)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["latex_escape"] = latex_escape

        rendered = env.get_template("template.tex.j2").render(
            cv=context,
            assets=str(assets_path or assets_dir()),
        )

        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="vitagen-") as tmp:
            work = Path(tmp)
            tex_file = work / "cv.tex"
            tex_file.write_text(rendered, encoding="utf-8")

            src_assets = assets_path or assets_dir()
            if src_assets.is_dir():
                dest_assets = work / "assets"
                shutil.copytree(src_assets, dest_assets, dirs_exist_ok=True)

            self._compile_latex(work, tex_file.stem)

            pdf_src = work / f"{tex_file.stem}.pdf"
            if not pdf_src.exists():
                raise RuntimeError("LaTeX compilation did not produce a PDF.")

            if output_path.suffix.lower() != ".pdf":
                raise ValueError(f"Output path must be a .pdf file, got: {output_path}")

            shutil.copy2(pdf_src, output_path)

        return output_path

    def _compile_latex(self, work_dir: Path, stem: str) -> None:
        cmd = [
            _find_pdflatex(),
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"{stem}.tex",
        ]
        for _ in range(2):
            try:
                result = subprocess.run(
                    cmd,
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "pdflatex not found. Install a LaTeX distribution "
                    "(MiKTeX, TeX Live) and ensure pdflatex is on PATH."
                ) from exc
            if result.returncode != 0:
                log = work_dir / f"{stem}.log"
                detail = log.read_text(encoding="utf-8", errors="replace") if log.exists() else result.stderr
                raise RuntimeError(f"pdflatex failed:\n{detail[-3000:]}")
