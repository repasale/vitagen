"""Allow running as python -m vitagen."""

from vitagen.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
