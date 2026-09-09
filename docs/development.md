# Development guide

## Synthetic data

The project includes these synthetic datasets:

| File | Purpose |
| --- | --- |
| [products.csv](../data/products.csv) | 20 products with IDs, descriptions, prices, ratings, inventory, and image references. |
| [search-queries.csv](../data/search-queries.csv) | Sample customer search queries. |
| [ad_events.csv](../data/ad_events.csv) | Historical advertising events used to calculate campaign metrics. |

Product images live in [images/products](../images/products/). The `generate_products.py`, `generate_search_queries.py`, and `generate_ad_events.py` scripts can regenerate the sample data.

## Run a local catalog search

Test catalog retrieval without starting an MCP server:

```bash
PYTHONPATH=src python3 search_products.py "cordless drill" --limit 5
```

The command prints candidate data as JSON. Use `rank_products` through MCP when you need final ranked recommendations and Product Insight cards.

## Run tests

Run the test suite from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Project layout

```text
.
├── data/                         # Catalog, sample queries, and campaign events
├── docs/                         # Detailed documentation
├── images/products/              # Product PNG images
├── src/ranking_agent/            # MCP server, ranking logic, and package helpers
├── plugins/product-search-chatgpt/assets/
│   └── product-results.html      # Shared Product Insight component
├── .codex/skills/product-search-results/
│   └── SKILL.md                  # Bundled Codex routing/presentation skill
├── logs/                         # JSON audit records created during development
├── dist/                         # Installable wheel files
├── mcp_server.py                 # Source-checkout launcher
├── pyproject.toml                # Package metadata and command entry points
└── setup.py                      # Includes data, images, UI, and skill in the wheel
```
