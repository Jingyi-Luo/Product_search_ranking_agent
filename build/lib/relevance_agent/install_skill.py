"""Install the bundled Product Search Results skill into a project."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from relevance_agent.runtime_paths import resource_root


def main() -> None:
    """Copy the bundled skill into ``<project>/.codex/skills``."""
    parser = argparse.ArgumentParser(
        description="Install the Product Search Results skill into a Codex project."
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Project directory that receives .codex/skills (default: current directory).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing product-search-results skill in that project.",
    )
    args = parser.parse_args()

    source = resource_root() / ".codex" / "skills" / "product-search-results"
    destination = args.project.resolve() / ".codex" / "skills" / source.name
    if destination.exists():
        if not args.force:
            raise SystemExit(
                f"{destination} already exists. Use --force to replace that skill."
            )
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    print(f"Installed {source.name} to {destination}")


if __name__ == "__main__":
    main()
