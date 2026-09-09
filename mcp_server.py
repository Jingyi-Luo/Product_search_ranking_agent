"""Compatibility launcher for the installable Product Search MCP server."""

from __future__ import annotations

import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ranking_agent.mcp_server import *  # noqa: F401,F403,E402
from ranking_agent.mcp_server import main  # noqa: E402


if __name__ == "__main__":
    main()
