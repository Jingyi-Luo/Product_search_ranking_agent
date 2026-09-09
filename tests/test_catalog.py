import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ranking_agent.catalog import load_products, search_products


class SearchProductsTests(unittest.TestCase):
    def test_catalog_contains_expected_product_count(self) -> None:
        self.assertEqual(len(load_products()), 20)

    def test_products_include_existing_image_assets(self) -> None:
        for product in load_products():
            self.assertTrue(product.image_url)
            self.assertTrue((Path(__file__).parents[1] / product.image_url).is_file())

    def test_cordless_drill_returns_relevant_candidates(self) -> None:
        results = search_products("cordless drill")
        product_ids = {result.product.product_id for result in results}

        self.assertTrue({"P001", "P002", "P004", "P006", "P020"}.issubset(product_ids))
        self.assertNotIn("P009", product_ids)

    def test_out_of_stock_product_is_returned_for_inventory_check(self) -> None:
        results = search_products("cordless drill")
        out_of_stock = next(result.product for result in results if result.product.product_id == "P004")

        self.assertEqual(out_of_stock.inventory_quantity, 0)

    def test_search_is_case_and_whitespace_insensitive(self) -> None:
        result_ids = [result.product.product_id for result in search_products("  DeWaLt   Cordless Drill ")]

        self.assertIn("P001", result_ids)
        self.assertIn("P020", result_ids)

    def test_invalid_query_and_limit_raise_clear_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "query"):
            search_products("   ")
        with self.assertRaisesRegex(ValueError, "limit"):
            search_products("cordless drill", limit=0)
