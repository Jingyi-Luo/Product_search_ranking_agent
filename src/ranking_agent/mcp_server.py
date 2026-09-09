"""FastMCP server exposing the catalog-backed product search tool.

Streamable HTTP mode (the default, for a remote MCP client)::

    MCP_HOST=0.0.0.0 PORT=8000 python3 mcp_server.py

Local stdio mode (for an MCP desktop client)::

    MCP_TRANSPORT=stdio python3 mcp_server.py

The HTTP MCP endpoint is available at ``/mcp`` by default. FastMCP handles
the MCP protocol, tool schema, JSON-RPC transport, and request validation;
the ranking behavior remains in ``ranking_agent.catalog``.
"""

from __future__ import annotations

import base64
import os
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ranking_agent.runtime_paths import default_logs_path, resource_root

try:
    from fastmcp import FastMCP
    from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
    from fastmcp.tools.base import ToolResult
    from fastmcp.utilities.types import Image
except ImportError as exc:  # pragma: no cover - gives a useful local error
    raise SystemExit(
        "FastMCP is not installed. Install the project dependencies with "
        "`python3 -m pip install -e .`."
    ) from exc


PROJECT_PATH = resource_root()
AD_EVENTS_PATH = PROJECT_PATH / "data" / "ad_events.csv"
LOGS_PATH = default_logs_path()
IMAGES_PATH = PROJECT_PATH / "images"
PRODUCT_RESULTS_UI_URI = "ui://product-search/results-v2.html"
PRODUCT_RESULTS_UI_PATH = PROJECT_PATH / "plugins" / "product-search-chatgpt" / "assets" / "product-results.html"
PRODUCT_UI_META = {
    "ui": {"resourceUri": PRODUCT_RESULTS_UI_URI},
    "openai/outputTemplate": PRODUCT_RESULTS_UI_URI,
}

from ranking_agent import search_products as catalog_search_products
from ranking_agent.catalog import load_products


def _json_default(value: Any) -> Any:
    """Serialize FastMCP and standard-library values for audit logs."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _public_base_url() -> str:
    """Return the externally reachable base URL for image links."""
    configured_url = os.environ.get("MCP_PUBLIC_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL")
    if configured_url:
        return configured_url.rstrip("/")

    host = os.environ.get("MCP_HOST") or os.environ.get("HOST") or "127.0.0.1"
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = os.environ.get("PORT") or "8000"
    return f"http://{host}:{port}"


def _product_response(product: Any) -> dict[str, Any]:
    """Serialize a catalog product with a URL served by this MCP app."""
    response = product.to_dict()
    response["image_url"] = f"{_public_base_url()}/{response['image_url'].lstrip('/')}"
    return response


def _similar_product_results(product: Any, limit: int = 2) -> list[dict[str, Any]]:
    """Build display-ready, in-stock alternatives from the same sub-category."""
    candidates = catalog_search_products(product.sub_category, limit=len(load_products()))
    similar_products: list[dict[str, Any]] = []
    for candidate in candidates:
        similar = candidate.product
        if similar.product_id == product.product_id or similar.inventory_quantity <= 0:
            continue
        similar_products.append({
            "product": _product_response(similar),
            "is_similar": True,
            "retrieval_score": candidate.retrieval_score,
            "matched_terms": list(candidate.matched_terms),
            "match_fields": list(candidate.match_fields),
            "inventory_quantity": similar.inventory_quantity,
        })
        if len(similar_products) == limit:
            break
    return similar_products


def _availability_detail(product: Any) -> dict[str, Any]:
    """Build the display-ready availability detail for one product."""
    quantity = product.inventory_quantity
    return {
        "product_id": product.product_id,
        "inventory_quantity": quantity,
        "in_stock": quantity > 0,
        "eligible": quantity > 0,
        "product": _product_response(product),
    }


def _matching_product_results(
    query: str,
    excluded_product_ids: set[str],
    limit: int = 2,
) -> list[dict[str, Any]]:
    """Build display-ready catalog matches for an inline follow-up section."""
    matches: list[dict[str, Any]] = []
    for result in catalog_search_products(query, limit=len(load_products())):
        if result.product.product_id in excluded_product_ids:
            continue
        matches.append({
            **result.to_dict(),
            "product": _product_response(result.product),
        })
        if len(matches) == limit:
            break
    return matches


def _product_image_data_urls(products: list[dict[str, Any]]) -> dict[str, str]:
    """Return self-contained image URLs for the ChatGPT product-card UI.

    ChatGPT renders an MCP App in an isolated iframe, which cannot fetch a
    product image from this machine's ``localhost`` address.  Tool-result
    metadata is delivered directly to the UI (rather than to the model), so
    data URLs keep the local images available without public hosting.
    """
    image_data_urls: dict[str, str] = {}
    for product in products:
        product_id = product.get("product_id")
        if not product_id:
            continue
        image_path = IMAGES_PATH / "products" / f"{product_id}.png"
        if image_path.is_file():
            encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
            image_data_urls[product_id] = f"data:image/png;base64,{encoded_image}"
    return image_data_urls


def _with_product_images(
    response: dict[str, Any],
    products: list[dict[str, Any]],
    *,
    ui_products: list[dict[str, Any]] | None = None,
    ui_meta: dict[str, Any] | None = None,
) -> ToolResult:
    """Return structured results, native image blocks, and UI-only image data."""
    images = [
        Image(path=IMAGES_PATH / "products" / f"{product['product_id']}.png")
        for product in products
        if product.get("product_id")
    ]
    metadata = {
        "product_image_data_urls": _product_image_data_urls(ui_products or products),
        **(ui_meta or {}),
    }
    return ToolResult(
        content=[response, *images],
        structured_content=response,
        meta=metadata,
    )


def _structured_content(result: ToolResult) -> dict[str, Any]:
    """Get a nested MCP tool call's structured response inside server workflows."""
    if result.structured_content is None:  # pragma: no cover - all product tools supply it
        raise RuntimeError("product tool did not return structured content")
    return result.structured_content


class ToolCallLoggingMiddleware(Middleware):
    """Persist the inputs and output of every MCP tool invocation."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext,
    ) -> Any:
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": context.message.name,
            "input": context.message.arguments or {},
        }
        try:
            output = await call_next(context)
        except Exception as exc:
            record["output"] = {
                "error": str(exc),
                "type": type(exc).__name__,
            }
            self._write_record(record)
            raise

        record["output"] = output
        self._write_record(record)
        return output

    @staticmethod
    def _write_record(record: dict[str, Any]) -> None:
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        log_path = LOGS_PATH / f"{timestamp}_{uuid4().hex}.json"
        with log_path.open("w", encoding="utf-8") as log_file:
            json.dump(record, log_file, default=_json_default, indent=2)
            log_file.write("\n")


mcp = FastMCP(
    name="Product Search",
    instructions=(
        "Search the synthetic product catalog for relevant candidates. "
        "Results include transparent relevance details. Inventory eligibility "
        "is intentionally left to a separate workflow step. Product-insight "
        "tools include product image content and an inline product-insight view; "
        "display that view and its images even when the requester does not "
        "explicitly ask for images. After a product-insight tool call, return "
        "no prose, summary, list, or description outside that inline view. "
        "Use suggest_more_products only when the "
        "user asks for more options or additional recommendations."
    ),
)
mcp.add_middleware(ToolCallLoggingMiddleware())


@mcp.resource(
    PRODUCT_RESULTS_UI_URI,
    name="product_results_ui",
    mime_type="text/html;profile=mcp-app",
    meta={
        "ui": {
            "prefersBorder": True,
            "csp": {"resourceDomains": [_public_base_url()]},
        },
    },
)
def product_results_ui() -> str:
    """Serve the ChatGPT component that renders image-first product insights."""
    return PRODUCT_RESULTS_UI_PATH.read_text(encoding="utf-8")


@mcp.tool(name="search_products", meta=PRODUCT_UI_META)
def search_products(
    query: str,
    limit: int = 10,
    excluded_product_ids: list[str] | None = None,
) -> ToolResult:
    """Retrieve catalog candidates for a query; use this before ranking or for unranked search.

    Use ``rank_products`` instead when the user asks for the best, top, or
    recommended products. This tool requires every meaningful query term to
    match, but it does not remove out-of-stock products and does not apply
    rating or advertising-performance ranking.

    Args:
        query: The customer's natural-language product search.
        limit: Maximum number of candidates to return; must be at least 1.
            Defaults to 10.
        excluded_product_ids: Optional product IDs already shown to the user.
            Use this when the user asks for more matching products.

    Returns:
        ``results`` in retrieval-score order without excluded IDs. Each result
        contains ``product``, ``retrieval_score``, ``matched_terms``, and
        ``match_fields``. Every product includes its image URL and MCP image
        content for direct display.
    """
    excluded_ids = set(excluded_product_ids or [])
    all_results = [
        result
        for result in catalog_search_products(query, limit=len(load_products()))
        if result.product.product_id not in excluded_ids
    ]
    results = all_results[:limit]
    more_matching_products = all_results[limit : limit + 2]
    response = {
        "query": query,
        "limit": limit,
        "excluded_product_ids": sorted(excluded_ids),
        "results": [
            {
                **result.to_dict(),
                "product": _product_response(result.product),
            }
            for result in results
        ],
    }
    return _with_product_images(
        response,
        [result["product"] for result in response["results"]],
        ui_products=[
            *[result["product"] for result in response["results"]],
            *[_product_response(result.product) for result in more_matching_products],
        ],
        ui_meta={
            "more_matching_products": [
                {
                    **result.to_dict(),
                    "product": _product_response(result.product),
                }
                for result in more_matching_products
            ]
        },
    )


@mcp.tool(name="health_check")
def health_check() -> dict[str, str]:
    """Check whether the MCP server is reachable and ready to accept tool calls.

    Use only for connection diagnostics, not for product-search requests.

    Returns:
        ``{"status": "ok"}`` when the server is available.
    """
    return {"status": "ok"}


@mcp.tool(name="suggest_more_products", meta=PRODUCT_UI_META)
def suggest_more_products(
    query: str,
    excluded_product_ids: list[str] | None = None,
    limit: int = 3,
) -> ToolResult:
    """Return additional ranked product recommendations after products were already shown.

    Use only when the user asks for more options, more suggestions, or
    alternatives. Pass IDs from the previous result in ``excluded_product_ids``
    so this tool does not repeat products. Use ``rank_products`` for the first
    set of recommendations.

    Args:
        query: The original customer product search.
        excluded_product_ids: Product IDs already displayed to the user.
        limit: Maximum number of additional products to return; must be at
            least 1. Defaults to 3.

    Returns:
        ``results`` in the same ranked, image-first format as ``rank_products``
        but without excluded IDs. Results are marked as ``more_options`` so the
        client displays a compact “More options” section.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    excluded_ids = set(excluded_product_ids or [])
    ranking = rank_products(query, limit=len(load_products())).structured_content
    if ranking is None:  # pragma: no cover - rank_products always supplies it
        raise RuntimeError("rank_products did not return structured content")

    ranked_results = [
        result
        for result in ranking["results"]
        if result["product"]["product_id"] not in excluded_ids
    ]
    additional_results = ranked_results[:limit]
    more_options = ranked_results[limit : limit + 2]
    response = {
        "query": ranking["query"],
        "limit": limit,
        "excluded_product_ids": sorted(excluded_ids),
        "result_set": "more_options",
        "ranking_policy": ranking["ranking_policy"],
        "results": additional_results,
    }
    return _with_product_images(
        response,
        [result["product"] for result in additional_results],
        ui_products=[
            *[result["product"] for result in additional_results],
            *[result["product"] for result in more_options],
        ],
        ui_meta={"more_options": more_options},
    )


@mcp.tool(name="calculate_relevance", meta=PRODUCT_UI_META)
def calculate_relevance(query: str, product_id: str) -> ToolResult:
    """Diagnose how one known product matches a query; do not use for product discovery.

    Use ``search_products`` to find candidates or ``rank_products`` to return
    recommendations. This tool evaluates one exact ``product_id`` against the
    same all-meaningful-terms matching rule used by search.

    Args:
        query: The customer's natural-language product search.
        product_id: Stable catalog identifier such as ``P001``.

    Returns:
        ``is_match``, ``retrieval_score``, ``matched_terms``, ``match_fields``,
        and product details. A non-match has a score of zero because one or
        more meaningful query terms did not match. The returned product is
        displayed through an image-first Product Insight component.
    """
    products = load_products()
    product = next((candidate for candidate in products if candidate.product_id == product_id), None)
    if product is None:
        raise ValueError(f"unknown product_id: {product_id}")

    # Use the same scoring implementation as the search tool. A full catalog
    # limit ensures the requested product is considered when it matches.
    result = next(
        (
            candidate
            for candidate in catalog_search_products(query, limit=len(products))
            if candidate.product.product_id == product_id
        ),
        None,
    )
    if result is None:
        response = {
            "query": query,
            "product_id": product_id,
            "is_match": False,
            "retrieval_score": 0,
            "matched_terms": [],
            "match_fields": [],
            "product": _product_response(product),
        }
        availability_detail = _availability_detail(product)
        return _with_product_images(
            response,
            [response["product"]],
            ui_meta={
                "availability_detail": availability_detail,
                "availability_intro": f"Current availability for {product.name}.",
            },
        )

    response = {
        "query": query,
        "product_id": product_id,
        "is_match": True,
        "retrieval_score": result.retrieval_score,
        "matched_terms": list(result.matched_terms),
        "match_fields": list(result.match_fields),
        "product": _product_response(product),
    }
    availability_detail = _availability_detail(product)
    return _with_product_images(
        response,
        [response["product"]],
        ui_meta={
            "availability_detail": availability_detail,
            "availability_intro": f"Current availability for {product.name}.",
        },
    )


@mcp.tool(name="check_inventory", meta=PRODUCT_UI_META)
def check_inventory(product_id: str) -> ToolResult:
    """Check inventory and ranking eligibility for one known product.

    Use this for a single-product availability check. ``rank_products`` already
    excludes out-of-stock products, so do not call this separately for normal
    ranked recommendations.

    Args:
        product_id: Stable catalog identifier such as ``P001``.

    Returns:
        ``inventory_quantity``, ``in_stock``, and ``eligible``. Only quantities
        greater than zero are eligible for product ranking. The returned
        product is displayed through an image-first Product Insight component.
    """
    product = next(
        (candidate for candidate in load_products() if candidate.product_id == product_id),
        None,
    )
    if product is None:
        raise ValueError(f"unknown product_id: {product_id}")

    quantity = product.inventory_quantity
    response = {
        "product_id": product_id,
        "inventory_quantity": quantity,
        "in_stock": quantity > 0,
        "eligible": quantity > 0,
        "product": _product_response(product),
    }
    similar_products = _similar_product_results(product)
    availability_detail = _availability_detail(product)
    return _with_product_images(
        response,
        [response["product"]],
        ui_products=[response["product"], *[item["product"] for item in similar_products]],
        ui_meta={
            "similar_products": similar_products,
            "similar_products_intro": (
                f"These in-stock products are in the same {product.sub_category} category."
            ),
            "availability_detail": availability_detail,
            "availability_intro": f"Current availability for {product.name}.",
        },
    )


@mcp.tool(name="get_campaign_metrics", meta=PRODUCT_UI_META)
def get_campaign_metrics(product_id: str) -> ToolResult:
    """Return historical advertising metrics for one known product.

    Use this to inspect a product's aggregate campaign performance. The metrics
    cover all recorded ad events for the product, not only the current query;
    use ``rank_products`` when you need an actual query-specific ranking.

    Args:
        product_id: Stable catalog identifier such as ``P001``.

    Returns:
        Aggregate ``impressions``, ``clicks``, ``click_through_rate``,
        ``add_to_carts``, ``purchases``, ``purchase_conversion_rate``,
        ``revenue_usd``, and ``average_order_value_usd``. The returned product
        is displayed through an image-first Product Insight component.
    """
    product = next(
        (candidate for candidate in load_products() if candidate.product_id == product_id),
        None,
    )
    if product is None:
        raise ValueError(f"unknown product_id: {product_id}")

    totals = {
        "events": 0,
        "impressions": 0,
        "clicks": 0,
        "add_to_carts": 0,
        "purchases": 0,
        "revenue_usd": 0.0,
    }
    with AD_EVENTS_PATH.open(newline="", encoding="utf-8") as events_file:
        for row in csv.DictReader(events_file):
            if row["product_id"] != product_id:
                continue
            totals["events"] += 1
            totals["impressions"] += int(row["impressions"])
            totals["clicks"] += int(row["clicks"])
            totals["add_to_carts"] += int(row["add_to_carts"])
            totals["purchases"] += int(row["purchases"])
            totals["revenue_usd"] += float(row["revenue_usd"])

    impressions = totals["impressions"]
    clicks = totals["clicks"]
    purchases = totals["purchases"]
    response = {
        "product_id": product_id,
        "events": totals["events"],
        "impressions": impressions,
        "clicks": clicks,
        "click_through_rate": clicks / impressions if impressions else 0.0,
        "add_to_carts": totals["add_to_carts"],
        "purchases": purchases,
        "purchase_conversion_rate": purchases / clicks if clicks else 0.0,
        "revenue_usd": round(totals["revenue_usd"], 2),
        "average_order_value_usd": round(totals["revenue_usd"] / purchases, 2) if purchases else 0.0,
        "product": _product_response(product),
    }
    similar_products = _similar_product_results(product)
    availability_detail = _availability_detail(product)
    return _with_product_images(
        response,
        [response["product"]],
        ui_products=[response["product"], *[item["product"] for item in similar_products]],
        ui_meta={
            "similar_products": similar_products,
            "similar_products_intro": (
                f"These in-stock products are in the same {product.sub_category} category."
            ),
            "availability_detail": availability_detail,
            "availability_intro": f"Current availability for {product.name}.",
        },
    )


@mcp.tool(
    name="rank_products",
    meta=PRODUCT_UI_META,
)
def rank_products(query: str, limit: int = 3) -> ToolResult:
    """Return the best in-stock product recommendations for a customer query.

    Use this as the default tool for requests such as “top products”, “best
    options”, or product recommendations. It retrieves matching products,
    excludes out-of-stock items, ranks the remainder, and returns display-ready
    product data and images. Use ``search_products`` only when unranked catalog
    matches are specifically needed.

    Products are first retrieved using catalog relevance. Out-of-stock
    products are excluded, then the remaining candidates are scored with this
    transparent weighted formula:

    - 60% retrieval relevance
    - 15% product rating
    - 10% historical click-through rate
    - 10% historical purchase conversion rate
    - 5% historical revenue

    Campaign metrics are aggregated historical product metrics, not query-only
    metrics. The returned breakdown makes each ranking decision inspectable.

    Args:
        query: The customer's natural-language product search.
        limit: Exact maximum number of ranked products to return; must be at
            least 1. Defaults to 3. Pass the user's requested result count.

    Returns:
        ``results`` ordered best to worst, with the product, ``ranking_score``,
        query match details, inventory, historical campaign metrics, and a
        score breakdown. Every product has an image URL and a returned MCP
        image-content block; display the images even if the user did not ask.
        The UI also receives up to two further recommendations as private component
        data so its More Options button can reveal them without another prompt.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    products = load_products()
    candidates = catalog_search_products(query, limit=len(products))
    max_relevance = max((candidate.retrieval_score for candidate in candidates), default=1)

    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        product = candidate.product
        inventory = _structured_content(check_inventory(product.product_id))
        if not inventory["eligible"]:
            continue

        metrics = _structured_content(get_campaign_metrics(product.product_id))
        relevance_component = candidate.retrieval_score / max_relevance * 0.60
        rating_component = product.rating / 5 * 0.15
        ctr_component = min(metrics["click_through_rate"] / 0.15, 1.0) * 0.10
        conversion_component = min(metrics["purchase_conversion_rate"] / 0.25, 1.0) * 0.10
        revenue_component = min(metrics["revenue_usd"] / 5000, 1.0) * 0.05
        ranking_score = 100 * (
            relevance_component
            + rating_component
            + ctr_component
            + conversion_component
            + revenue_component
        )

        ranked.append({
            "product": _product_response(product),
            "ranking_score": round(ranking_score, 4),
            "retrieval_score": candidate.retrieval_score,
            "matched_terms": list(candidate.matched_terms),
            "match_fields": list(candidate.match_fields),
            "inventory_quantity": inventory["inventory_quantity"],
            "campaign_metrics": metrics,
            "score_breakdown": {
                "relevance": round(relevance_component * 100, 4),
                "rating": round(rating_component * 100, 4),
                "click_through_rate": round(ctr_component * 100, 4),
                "purchase_conversion_rate": round(conversion_component * 100, 4),
                "revenue": round(revenue_component * 100, 4),
            },
        })

    ranked.sort(key=lambda item: (-item["ranking_score"], -item["product"]["rating"], item["product"]["price_usd"], item["product"]["product_id"]))
    results = ranked[:limit]
    more_options = ranked[limit : limit + 2]
    response = {
        "query": query,
        "limit": limit,
        "ranking_policy": {
            "relevance_weight": 0.60,
            "rating_weight": 0.15,
            "click_through_rate_weight": 0.10,
            "purchase_conversion_rate_weight": 0.10,
            "revenue_weight": 0.05,
            "out_of_stock_products_excluded": True,
        },
        "results": results,
    }
    return _with_product_images(
        response,
        [result["product"] for result in results],
        ui_products=[result["product"] for result in [*results, *more_options]],
        ui_meta={"more_options": more_options},
    )


@mcp.tool(name="explain_ranking", meta=PRODUCT_UI_META)
def explain_ranking(query: str, product_id: str) -> ToolResult:
    """Explain why one known product ranked, was excluded, or was not retrieved.

    Use after ``rank_products`` when the user asks why a specific product did
    or did not appear. Do not use it to discover products; it requires an exact
    ``product_id``.

    The explanation uses the same retrieval, inventory, rating, and campaign
    signals as :func:`rank_products`. It distinguishes a product that was
    ranked, excluded for being out of stock, or not retrieved because it did
    not match every meaningful query term.

    Args:
        query: The customer's natural-language product search.
        product_id: Stable catalog identifier such as ``P001``.

    Returns:
        ``decision`` (``ranked``, ``excluded_out_of_stock``, or
        ``not_retrieved``), human-readable ``reasons``, relevance, inventory,
        campaign metrics, rank position, and score breakdown where applicable.
        The returned product is displayed through an image-first Product Insight
        component.
    """
    relevance = _structured_content(calculate_relevance(query, product_id))
    inventory = _structured_content(check_inventory(product_id))
    metrics = _structured_content(get_campaign_metrics(product_id))
    ranking = rank_products(query, limit=len(load_products())).structured_content
    if ranking is None:  # pragma: no cover - rank_products always supplies it
        raise RuntimeError("rank_products did not return structured content")
    ranked_result = next(
        (result for result in ranking["results"] if result["product"]["product_id"] == product_id),
        None,
    )

    reasons: list[str] = []
    if not relevance["is_match"]:
        decision = "not_retrieved"
        reasons.append("The product does not contain every meaningful query term.")
    elif not inventory["eligible"]:
        decision = "excluded_out_of_stock"
        reasons.append("The product has zero inventory and is ineligible for product ranking.")
    else:
        decision = "ranked"
        rank_position = next(
            (index for index, result in enumerate(ranking["results"], start=1) if result["product"]["product_id"] == product_id),
            None,
        )
        reasons.append(f"The product is eligible and ranked at position {rank_position}.")
        reasons.append(
            "The final score combines 60% relevance, 15% rating, 10% CTR, "
            "10% purchase conversion, and 5% revenue."
        )

    response = {
        "query": query,
        "product_id": product_id,
        "product": relevance["product"],
        "decision": decision,
        "reasons": reasons,
        "relevance": relevance,
        "inventory": inventory,
        "campaign_metrics": metrics,
        "rank_position": next(
            (index for index, result in enumerate(ranking["results"], start=1) if result["product"]["product_id"] == product_id),
            None,
        ),
        "ranking_score": ranked_result["ranking_score"] if ranked_result else None,
        "score_breakdown": ranked_result["score_breakdown"] if ranked_result else None,
    }
    matching_products = _matching_product_results(query, {product_id})
    return _with_product_images(
        response,
        [response["product"]],
        ui_products=[response["product"], *[item["product"] for item in matching_products]],
        ui_meta={
            "campaign_metrics_detail": metrics,
            "campaign_metrics_intro": f"Campaign performance for {response['product']['name']}.",
            "matching_products": matching_products,
            "matching_products_intro": f"Other catalog products matching “{query}”.",
        },
    )


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "http").lower()
    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    host = os.environ.get("MCP_HOST") or os.environ.get("HOST") or "127.0.0.1"
    port = int(os.environ.get("PORT") or "8000")
    path = os.environ.get("MCP_PATH") or "/mcp"
    if transport in {"http", "streamable-http"}:
        from starlette.staticfiles import StaticFiles
        import uvicorn

        app = mcp.http_app(path=path)
        app.mount("/images", StaticFiles(directory=IMAGES_PATH), name="images")
        uvicorn.run(app, host=host, port=port)
    elif transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    else:
        raise SystemExit("MCP_TRANSPORT must be stdio, http, streamable-http, or sse")


if __name__ == "__main__":
    main()
