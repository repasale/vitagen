"""Vitagen CLI — argparse entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vitagen import __version__
from vitagen.i18n import list_languages, load_locale_config, normalize_lang
from vitagen.loader import collect_keywords, create_job_template, load_project
from vitagen.model import build_cv_context
from vitagen.naming import build_pdf_filename
from vitagen.paths import default_output_dir, resolve_input_dir, templates_dir
from vitagen.renderer import get_renderer
from vitagen.validator import format_report, validate_project


PREVIEW_COMMANDS = """
Vitagen — usage examples
========================

  vitagen
  vitagen --lang=spanish --template=modern
  vitagen --input=/path/to/user-cv
  vitagen --output=/path/to/output/
  vitagen --include=cybersecurity --exclude=developer
  vitagen --new-job acme-corp
  vitagen --list-languages
  vitagen --list-keywords
  vitagen --validate
"""


def _parse_keywords(value: str | None) -> set[str]:
    if not value:
        return set()
    return {k.strip().lower() for k in value.split(",") if k.strip()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vitagen",
        description="Extensible LaTeX CV generator with multi-language support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Data lives in user-cv/data/ (or data/ inside --input). "
        "Templates live in vitagen/templates/.",
    )
    parser.add_argument(
        "--input",
        metavar="DIR",
        help="CV data project directory (default: current working directory)",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Output PDF file or directory (default: vitagen home/output/)",
    )
    parser.add_argument(
        "--lang",
        default="english",
        help="Output language code or alias (default: english). Use --list-languages to see all.",
    )
    parser.add_argument(
        "--include",
        metavar="KW,KW",
        help="Include only jobs/achievements matching at least one keyword",
    )
    parser.add_argument(
        "--exclude",
        metavar="KW,KW",
        help="Exclude jobs/achievements matching any keyword",
    )
    parser.add_argument(
        "--template",
        default="classic",
        help="Template name from vitagen/templates/ (default: classic)",
    )
    parser.add_argument(
        "--new-job",
        metavar="JOBNAME",
        help="Create sample experience/JOBNAME.yaml and exit",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all supported output languages and exit",
    )
    parser.add_argument(
        "--list-keywords",
        action="store_true",
        help="List all keywords in the project and exit",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate YAML data structure and required fields; exit without PDF",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print usage examples and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"vitagen {__version__}",
    )
    return parser


def _resolve_output_path(
    output_arg: str | None,
    *,
    personal: dict,
    lang: str,
) -> Path:
    """Resolve --output to a full PDF path using firstname_surname_LANG.pdf."""
    filename = build_pdf_filename(personal, lang)

    if output_arg:
        output_path = Path(output_arg)
        if output_path.suffix.lower() == ".pdf":
            return output_path
        if output_path.exists() and output_path.is_dir():
            return output_path / filename
        if output_path.suffix:
            return output_path
        return output_path / filename

    return default_output_dir() / filename


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.preview:
        print(PREVIEW_COMMANDS)
        return 0

    try:
        project_root = resolve_input_dir(args.input)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Merge project-specific language overrides from data/locale.yaml (if present).
    load_locale_config(project_root)

    if args.new_job:
        try:
            path = create_job_template(args.new_job, project_root)
            print(f"Created sample job: {path}")
            return 0
        except FileExistsError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if args.list_languages:
        print("Supported languages:")
        for code, name in list_languages():
            print(f"  {code:4}  {name}")
        print("\nCustom languages can be added in user-cv/data/locale.yaml.")
        return 0

    if args.list_keywords:
        data = load_project(project_root)
        keywords = sorted(collect_keywords(data))
        if keywords:
            print("Available keywords:")
            for kw in keywords:
                print(f"  - {kw}")
        else:
            print("No keywords found in experience files.")
        return 0

    lang = normalize_lang(args.lang, project_root=project_root)

    if args.validate:
        report = validate_project(project_root, lang=lang, template=args.template)
        print(format_report(report))
        return 0 if report.ok else 1

    report = validate_project(project_root, lang=lang, template=args.template)
    if not report.ok:
        print(format_report(report), file=sys.stderr)
        return 1

    data = load_project(project_root)
    context = build_cv_context(
        data,
        lang=lang,
        include=_parse_keywords(args.include),
        exclude=_parse_keywords(args.exclude),
    )

    output_path = _resolve_output_path(args.output, personal=data["personal"], lang=lang)

    renderer = get_renderer("latex")
    try:
        result = renderer.render(
            context,
            template=args.template.lower(),
            output_path=output_path,
            assets_path=None,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(
            "\nHint: ensure a LaTeX distribution (pdflatex) is installed and on PATH.",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        available = [p.name for p in templates_dir().iterdir() if p.is_dir()] if templates_dir().is_dir() else []
        if available:
            print(f"Available templates: {', '.join(sorted(available))}", file=sys.stderr)
        return 1

    print(f"Generated: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
