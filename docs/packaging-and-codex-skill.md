# Packaging and Codex skill

The Python distribution is named `product-ranking-agent`. Its wheel bundles the MCP server, catalog data, images, Product Insight UI, and `product-search-results` Codex skill.

## Install a wheel

The current wheel is in [dist](../dist/):

```bash
python3 -m pip install --upgrade ../dist/product_ranking_agent-0.1.23-py3-none-any.whl
```

Run this command from the `docs/` directory. From the repository root, omit `../`.

## Share the package without publishing to PyPI

1. Send the `.whl` file from `dist/` to the other person.
2. They download it and run this command from the folder containing the file:

   ```bash
   python3 -m pip install product_ranking_agent-0.1.23-py3-none-any.whl
   ```

3. They start the server with:

   ```bash
   product-search
   ```

## Build a new wheel

Run this from the repository root after making changes:

```bash
python3 -m pip wheel . --no-deps --wheel-dir dist
```

When shipped behavior changes, increase `version` in [pyproject.toml](../pyproject.toml) before rebuilding. This lets users upgrade without needing `--force-reinstall`.

## Install the bundled Codex skill

The `product-search-results` skill selects the appropriate direct MCP tool and asks the client to show the returned Product Insight component without duplicating product details in Markdown.

Install it into the current project:

```bash
product-search-install-skill
```

This creates:

```text
./.codex/skills/product-search-results/
```

Install it into a different project:

```bash
product-search-install-skill --project /path/to/another-project
```

Replace an existing copy:

```bash
product-search-install-skill --project /path/to/another-project --force
```

The source skill is [SKILL.md](../.codex/skills/product-search-results/SKILL.md). Start a new Codex session, or reload skills if the client supports it, after installing or updating the skill.
