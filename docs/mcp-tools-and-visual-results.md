# MCP tools and visual results

The seven product-insight tools return structured product data, product-image content, and metadata for the shared Product Insight UI. In an MCP App-compatible client, results appear as image-first cards. The component adds context-specific **Explore more** controls after every result type. `suggest_more_products` returns compact additional-product cards, while `health_check` returns plain text.

## Tool reference

| Tool | When to use it | Inputs | Result |
| --- | --- | --- | --- |
| `search_products` | Find unranked catalog candidates. | `query`, optional `limit` (default `10`), optional `excluded_product_ids` | Candidate cards with images, matched terms, and matched fields. It preloads up to two more non-duplicated matches for the component. Out-of-stock products may appear. |
| `rank_products` | Answer “best,” “top,” or recommendation requests. | `query`, optional `limit` (default `3`) | Ranked, in-stock product cards with images, score details, and campaign signals. It preloads up to two additional ranked cards for the component. |
| `calculate_relevance` | Inspect how one known product matches a query. | `query`, `product_id` | One relevance card with an image, match status, and retrieval details. It preloads the product’s availability detail. |
| `check_inventory` | Check availability for one known product. | `product_id` | One inventory card with an image, quantity, and eligibility. It preloads up to two in-stock products from the same subcategory. |
| `get_campaign_metrics` | Inspect historical advertising performance. | `product_id` | One metrics card with an image, CTR, conversion, revenue, and totals. It preloads up to two in-stock products from the same subcategory. |
| `explain_ranking` | Explain why one product ranked, was excluded, or was not retrieved. | `query`, `product_id` | One explanation card with an image, decision, reasons, and score details. It preloads campaign metrics and up to two other matching products. |
| `suggest_more_products` | Return additional recommendations after products were already shown. | `query`, optional `excluded_product_ids`, optional `limit` (default `3`) | Additional ranked, in-stock products in compact image-first cards. It preloads up to two remaining non-duplicated exact matches. |
| `health_check` | Check whether the server is available. | None | Plain `{ "status": "ok" }` text. |

## Explore more controls

| Result type | Controls shown |
| --- | --- |
| Search candidates | Show more matching products — reveals up to two more matches directly. |
| Ranked products or more-options results | More Options — reveals up to two remaining non-duplicated products directly, when available. |
| Relevance check | Check availability — reveals a framed availability section directly · Explain ranking · View campaign metrics |
| Inventory check | View campaign metrics · Find similar products — reveals a framed similar-product section directly. |
| Campaign metrics | Check availability · Find similar products — reveals a framed similar-product section directly. |
| Ranking explanation | View campaign metrics — reveals a framed metrics section directly · Show matching products — reveals up to two framed matching-product cards directly. |

## Ranking formula

`rank_products` retrieves matching catalog products, removes products with zero or negative inventory, and ranks the rest with the following weights:

| Signal | Weight |
| --- | ---: |
| Retrieval relevance | 60% |
| Product rating | 15% |
| Historical click-through rate | 10% |
| Historical purchase conversion rate | 10% |
| Historical revenue | 5% |

Campaign values are product-level historical aggregates, not values filtered to the current query.

## Product images

Image references are stored in [products.csv](../data/products.csv), and the PNG files are in [images/products](../images/products/). For every product-related tool call, the server returns:

1. Structured product data, including `image_url`.
2. Native MCP image-content blocks.
3. Base64 image data in UI-only metadata, allowing local images to appear in the Product Insight component without a public image host.

If a component does not appear after a server or UI update, restart the server and begin a new chat. Final inline rendering is controlled by the MCP client, which must support MCP Apps/components.

## Test prompts

Use these prompts after connecting the MCP server.

### Health check

```text
Call the health_check MCP tool. Show only its returned status text.
```

### Search cards

```text
Call search_products with query "cordless power drills" and limit 3.
```

### Ranked recommendation cards

```text
Call rank_products with query "cordless power drills" and limit 3.
```

### Relevance, inventory, and metrics cards

```text
For product ID P020 and query "cordless power drills", call calculate_relevance, check_inventory, and get_campaign_metrics.
```

### Ranking explanation card

```text
Call explain_ranking with query "cordless power drills" and product ID P020.
```

### More product suggestions

```text
Call suggest_more_products with query "cordless power drills", excluded product IDs P020, P018, and P014, and limit 3.
```
