#!/usr/bin/env python3

from pathlib import Path
import shutil


def main():
    repo_root = Path(__file__).resolve().parent.parent
    source = repo_root / "ai_bias_codex.svg"
    destination = repo_root / "docs" / "ai_bias_codex.svg"

    if not source.exists():
        raise SystemExit(f"Missing source SVG: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"Copied {source.name} -> {destination}")


if __name__ == "__main__":
    main()
