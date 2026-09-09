---
name: product-search-results
description: Route product-search, ranking, product-check, and additional-recommendation requests to Product Search MCP tools. Use for catalog questions that need image-first cards or more matching products.
---

# Product Search Results

Use the connected Product Search MCP server directly. Do not write or run Python scripts as a substitute for an MCP tool call. If its tools are unavailable in the current session, say that the MCP server must be connected at its `/mcp` endpoint before continuing.

## Route the request

| User intent | MCP tool | Notes |
| --- | --- | --- |
| Find matching products | `search_products(query, limit, excluded_product_ids=[])` | Use for retrieval, filters, or a short candidate list. Exclude prior IDs when the user asks for more matches. |
| Best, top, recommended products | `rank_products(query, limit)` | Use for any ordering or recommendation request. Pass the requested number of products as `limit`; it defaults to three. |
| Why a product ranked or was excluded | `explain_ranking(query, product_id)` | Use after identifying the product ID. |
| Check stock or eligibility | `check_inventory(product_id)` | Use alone for a known product, or after search for an ambiguous name. |
| Relevance of one product | `calculate_relevance(query, product_id)` | Use when the question is about match quality rather than final rank. |
| Advertising performance | `get_campaign_metrics(product_id)` | Use for CTR, conversion, revenue, or campaign comparisons. |
| More product suggestions | `suggest_more_products(query, excluded_product_ids=[], limit=3)` | Use only when the user asks for more options, alternatives, or additional recommendations. Exclude products already shown. |
| Server availability | `health_check()` | Use only when asked to verify the service. |

Use `rank_products` rather than trying to recompute scores. When a request specifies a count, pass that count as `limit` so the inline card UI receives exactly that many products. Use `search_products` before a product-specific call when the user has not supplied an unambiguous product ID. For a comparison, call the minimum number of tools needed to answer it. Do not call `suggest_more_products` until the user asks for more products.

## Present results

For every product-related tool—`search_products`, `rank_products`, `calculate_relevance`, `check_inventory`, `get_campaign_metrics`, `explain_ranking`, and `suggest_more_products`—use the returned Product Insight inline component. It shows a real product image first and adapts the labeled facts to the tool. The `search_products` and `rank_products` controls reveal up to two preloaded products directly; they do not need a follow-up prompt or tool call. For `suggest_more_products`, show the compact “More options” cards. Render every returned image even when the user does not explicitly ask for images.

After a product tool call, return no assistant prose before or after the inline component: the component is the complete product response. Do not repeat, summarize, list, or describe its contents. Do not emit a Markdown table, Markdown product cards, literal HTML image markup, or a separate image list. If a component is unavailable, state that it could not be displayed rather than presenting an alternate product list. For `health_check`, return its short text result without a component or image.

When the request asks for a specific count, show exactly that many inline cards unless fewer valid products exist. State clearly when no product matches or when a product is excluded because it is out of stock.
