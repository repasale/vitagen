# Vitagen

Extensible LaTeX CV generator with multi-language support and keyword-based filtering.

Vitagen separates **data** (YAML in your project) from **presentation** (LaTeX templates shipped with the tool). The renderer layer is pluggable, so additional export formats can be added without changing the YAML schema.

## Quick start

```bash
git clone git@github.com:repasale/vitagen.git
cd vitagen
pip install -e .

# Generate a CV from the included sample data
python -m vitagen

# Spanish CV with the modern template
python -m vitagen --lang=spanish --template=modern

# Tailored CV by keyword
python -m vitagen --include=pentesting,cybersecurity
```

**Requirements:** Python 3.10+ and a LaTeX distribution with `pdflatex` on PATH.

## Project layout

```
vitagen/
├── vitagen/              # Python package
│   ├── cli.py            # Command-line interface
│   ├── loader.py         # YAML loading
│   ├── i18n.py           # Language resolution
│   ├── languages.yaml    # Built-in language definitions
│   ├── model.py          # Data → render context
│   ├── filter.py         # Keyword filtering
│   └── renderer/         # Output backends (LaTeX/PDF)
├── templates/            # LaTeX Jinja2 templates (classic, modern)
├── assets/               # Static files (photos, icons)
└── output/               # Default PDF output (git-ignored)

user-cv/                  # Sample CV data (copy and customize)
└── data/
    ├── personal.yaml
    ├── education.yaml
    ├── skills.yaml
    ├── languages.yaml
    ├── certificates.yaml
    ├── locale.yaml.example
    └── experience/*.yaml
```

Set `VITAGEN_HOME` to override where templates, assets, and default output are loaded from.

## CLI reference

| Switch | Description |
|--------|-------------|
| *(none)* | Generate a CV from the current directory |
| `--input=DIR` | CV data project directory |
| `--output=PATH` | Output directory or explicit `.pdf` file |
| `--lang=LANG` | Language code or alias (default: `english`) |
| `--list-languages` | List supported output languages |
| `--include=KW,KW` | Include jobs/achievements matching keywords |
| `--exclude=KW,KW` | Exclude jobs/achievements matching keywords |
| `--template=NAME` | Template from `templates/` (default: `classic`) |
| `--new-job=NAME` | Scaffold a new `experience/NAME.yaml` file |
| `--list-keywords` | List keywords defined in the project |
| `--validate` | Validate YAML data without generating a PDF |
| `--preview` | Print usage examples |
| `--help` | Show help |

Generated PDFs are named `Firstname_Surname_LANG.pdf` (e.g. `John_Shepard_EN.pdf`).

## Languages

Built-in languages: **English**, **Spanish**, **French**, **German**, **Chinese**, and **Czech**.

```bash
python -m vitagen --list-languages
python -m vitagen --lang=fr --template=modern
```

Localized fields use language keys in YAML:

```yaml
job_title:
  en: "Security Analyst"
  es: "Analista de Seguridad"
  fr: "Analyste Sécurité"
  de: "Sicherheitsanalyst"
  cz: "Bezpečnostní analytik"
```

English is the fallback when a translation for the requested language is missing.

### Adding a language

Copy `user-cv/data/locale.yaml.example` to `locale.yaml` and define your language:

```yaml
languages:
  pt:
    name: Portuguese
    aliases: [portuguese, pt]
    babel: portuguese
    filename_code: PT
    show_title_in_name: false
    labels:
      experience: Experiência
      education: Educação
      skills: Competências
      languages: Idiomas
      certificates: Certificações
      present: Presente
```

If the language requires a new babel package, add it to the `\usepackage[...]{babel}` line in your template.

## Keyword filtering

Keywords can be set on a job and on individual achievements:

```yaml
keywords: [cybersecurity, pentesting]
achievements:
  - text:
      en: "Built automation tooling"
    keywords: [automation]
```

Use `--include` to produce a tailored CV and `--exclude` to omit specific topics.

## Architecture

```
YAML  →  loader  →  i18n + filter  →  model  →  renderer  →  PDF
```

Implement a new renderer in `vitagen/renderer/` to support additional export formats.

## License

MIT — see [LICENSE](LICENSE).
