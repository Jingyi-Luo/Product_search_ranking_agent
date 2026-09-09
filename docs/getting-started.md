# Getting started

This guide explains how to run Product Ranking Agent locally and connect an MCP client.

## Requirements

- Python 3.11 or newer
- `pip`
- An MCP client, such as a compatible ChatGPT/Codex workspace, to use MCP tools and visual cards

## Install from this repository

If you use Mamba, create and activate an environment with Python 3.11 or newer before running the same `pip install` commands:

```bash
mamba create -n product-ranking python=3.12
mamba activate product-ranking
```
Install the project and run the mcp server:

```bash
pip install .
python mcp_server.py
```

## Start the HTTP MCP server

Run:

```bash
product-search
```

The default transport is Streamable HTTP. Connect your MCP client to:

```text
http://127.0.0.1:8000/mcp
```

After connecting, start a new chat before testing the tools. This ensures the client loads the current tool descriptions and Product Insight UI.

## Run from the source checkout

The root [mcp_server.py](../mcp_server.py) is a compatibility launcher. Use editable installation while developing:

```bash
python3 -m pip install -e .
MCP_HOST=127.0.0.1 PORT=8000 python3 mcp_server.py
```

## Use stdio instead of HTTP

For a local MCP client that launches the server over standard input/output, run:

```bash
MCP_TRANSPORT=stdio product-search
```

The server uses HTTP unless `MCP_TRANSPORT=stdio` is set.
