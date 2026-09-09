"""Package the MCP server's runtime data, UI asset, and Codex skill."""

from __future__ import annotations

from pathlib import Path

from setuptools import setup


ROOT = Path(__file__).resolve().parent
ASSET_DIRECTORIES = (
    "data",
    "images",
    "plugins/product-search-chatgpt/assets",
    ".codex/skills/product-search-results",
)

data_files: list[tuple[str, list[str]]] = []
for relative_directory in ASSET_DIRECTORIES:
    directory = ROOT / relative_directory
    for asset_path in sorted(path for path in directory.rglob("*") if path.is_file()):
        destination = Path("product-ranking-agent") / asset_path.parent.relative_to(ROOT)
        data_files.append((str(destination), [str(asset_path.relative_to(ROOT))]))


setup(data_files=data_files)
