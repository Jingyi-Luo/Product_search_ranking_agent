"""Locate bundled assets in a source checkout or an installed wheel."""

from __future__ import annotations

import sysconfig
import os
from pathlib import Path


PACKAGE_PATH = Path(__file__).resolve().parent
SOURCE_ROOT = PACKAGE_PATH.parents[1]
INSTALL_ROOT_NAME = "product-ranking-agent"


def resource_root() -> Path:
    """Return the directory containing the server's bundled data and UI files."""
    if (SOURCE_ROOT / "data").is_dir():
        return SOURCE_ROOT

    data_prefix = sysconfig.get_path("data")
    if data_prefix:
        installed_root = Path(data_prefix) / INSTALL_ROOT_NAME
        if (installed_root / "data").is_dir():
            return installed_root

    raise RuntimeError(
        "Bundled Product Search assets are missing. "
        "Reinstall the package with `pip install --force-reinstall "
        "product-ranking-agent`."
    )


def default_logs_path() -> Path:
    """Use repository logs during development and a writable local logs folder when installed."""
    configured_path = Path(path) if (path := os.environ.get("MCP_LOGS_PATH")) else None
    if configured_path is not None:
        return configured_path.expanduser()
    if (resource_root() / "pyproject.toml").is_file():
        return resource_root() / "logs"
    return Path.cwd() / "logs"
