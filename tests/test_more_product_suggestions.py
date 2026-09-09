"""Tests for the MCP additional-product suggestion tool."""

from __future__ import annotations

import unittest

from ranking_agent.mcp_server import (
    calculate_relevance,
    check_inventory,
    explain_ranking,
    get_campaign_metrics,
    rank_products,
    search_products,
    suggest_more_products,
)


class MoreProductSuggestionsTests(unittest.TestCase):
    """Verify that additional recommendations are ranked and non-duplicated."""

    def test_suggestions_exclude_previous_product_ids(self) -> None:
        initial = rank_products("cordless power drills", limit=3).structured_content
        self.assertIsNotNone(initial)
        assert initial is not None
        excluded_ids = [result["product"]["product_id"] for result in initial["results"]]

        additional = suggest_more_products(
            "cordless power drills",
            excluded_product_ids=excluded_ids,
            limit=3,
        ).structured_content

        self.assertIsNotNone(additional)
        assert additional is not None
        self.assertEqual(additional["result_set"], "more_options")
        self.assertEqual(additional["excluded_product_ids"], sorted(excluded_ids))
        self.assertTrue(additional["results"])
        self.assertLessEqual(len(additional["results"]), 3)
        self.assertTrue(
            all(result["product"]["product_id"] not in excluded_ids for result in additional["results"])
        )

    def test_suggestions_preload_only_remaining_exact_options_for_the_component(self) -> None:
        result = suggest_more_products(
            "cordless power drills",
            excluded_product_ids=["P020", "P018", "P014"],
            limit=3,
        )
        content = result.structured_content
        self.assertIsNotNone(content)
        assert content is not None
        more_options = result.meta.get("more_options", [])

        self.assertLessEqual(len(more_options), 2)
        shown_ids = {item["product"]["product_id"] for item in content["results"]}
        more_ids = {item["product"]["product_id"] for item in more_options}
        self.assertFalse(shown_ids & more_ids)
        self.assertFalse({"P020", "P018", "P014"} & more_ids)
        self.assertFalse(more_options)

    def test_invalid_limit_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "limit must be at least 1"):
            suggest_more_products("cordless power drills", limit=0)

    def test_ranking_preloads_two_more_options_for_the_component(self) -> None:
        ranking = rank_products("cordless power drills", limit=3)
        content = ranking.structured_content
        self.assertIsNotNone(content)
        assert content is not None
        more_options = ranking.meta.get("more_options", [])

        self.assertLessEqual(len(more_options), 2)
        self.assertTrue(more_options)
        shown_ids = {result["product"]["product_id"] for result in content["results"]}
        more_ids = {result["product"]["product_id"] for result in more_options}
        self.assertFalse(shown_ids & more_ids)

    def test_search_can_exclude_already_displayed_candidates(self) -> None:
        initial = search_products("cordless power drills", limit=2).structured_content
        self.assertIsNotNone(initial)
        assert initial is not None
        excluded_ids = [result["product"]["product_id"] for result in initial["results"]]

        more = search_products(
            "cordless power drills",
            limit=3,
            excluded_product_ids=excluded_ids,
        ).structured_content

        self.assertIsNotNone(more)
        assert more is not None
        self.assertEqual(more["excluded_product_ids"], sorted(excluded_ids))
        self.assertTrue(more["results"])
        self.assertTrue(
            all(result["product"]["product_id"] not in excluded_ids for result in more["results"])
        )

    def test_search_preloads_up_to_two_more_matching_products_for_the_component(self) -> None:
        search = search_products("cordless power drills", limit=2)
        content = search.structured_content
        self.assertIsNotNone(content)
        assert content is not None
        more_matches = search.meta.get("more_matching_products", [])

        self.assertLessEqual(len(more_matches), 2)
        self.assertTrue(more_matches)
        shown_ids = {result["product"]["product_id"] for result in content["results"]}
        more_ids = {result["product"]["product_id"] for result in more_matches}
        self.assertFalse(shown_ids & more_ids)

    def test_inventory_and_metrics_preload_similar_products_for_the_component(self) -> None:
        for tool in (check_inventory, get_campaign_metrics):
            result = tool("P020")
            similar_products = result.meta.get("similar_products", [])

            self.assertTrue(similar_products)
            self.assertLessEqual(len(similar_products), 2)
            self.assertTrue(all(item["is_similar"] for item in similar_products))
            self.assertNotIn("P020", {item["product"]["product_id"] for item in similar_products})
            self.assertTrue(result.meta.get("similar_products_intro"))
            self.assertTrue(result.meta.get("availability_detail"))

    def test_relevance_preloads_availability_for_the_component(self) -> None:
        result = calculate_relevance("cordless power drills", "P020")
        availability = result.meta.get("availability_detail")

        self.assertIsNotNone(availability)
        assert availability is not None
        self.assertEqual(availability["product_id"], "P020")
        self.assertIn("in_stock", availability)
        self.assertTrue(result.meta.get("availability_intro"))

    def test_ranking_explanation_preloads_metrics_and_matching_products(self) -> None:
        result = explain_ranking("cordless power drills", "P020")
        matching_products = result.meta.get("matching_products", [])

        self.assertTrue(result.meta.get("campaign_metrics_detail"))
        self.assertTrue(result.meta.get("campaign_metrics_intro"))
        self.assertLessEqual(len(matching_products), 2)
        self.assertTrue(matching_products)
        self.assertNotIn("P020", {item["product"]["product_id"] for item in matching_products})
