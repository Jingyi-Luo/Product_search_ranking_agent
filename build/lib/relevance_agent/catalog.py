"""Catalog-backed candidate retrieval for product search."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from relevance_agent.runtime_paths import resource_root


DATA_PATH = resource_root() / "data" / "products.csv"
FIELD_WEIGHTS = {
    "name": 8,
    "brand": 5,
    "category": 4,
    "sub_category": 4,
    "attributes": 3,
    "description": 1,
}
# These terms affect ranking preferences but should not prevent candidate retrieval.
RETRIEVAL_MODIFIERS = frozenset({"best", "buy", "cheap", "for", "good", "sale"})


def _tokens(value: str) -> set[str]:
    """Normalize free text and attribute values into comparable search tokens."""
    return set(re.findall(r"[a-z0-9]+", value.lower().replace("_", " ")))


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    brand: str
    category: str
    sub_category: str
    description: str
    attributes: str
    price_usd: float
    inventory_quantity: int
    rating: float
    image_url: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Product":
        return cls(
            product_id=row["product_id"],
            name=row["name"],
            brand=row["brand"],
            category=row["category"],
            sub_category=row["sub_category"],
            description=row["description"],
            attributes=row["attributes"],
            price_usd=float(row["price_usd"]),
            inventory_quantity=int(row["inventory_quantity"]),
            rating=float(row["rating"]),
            image_url=row["image_url"],
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResult:
    """A product candidate and transparent retrieval-match details."""

    product: Product
    retrieval_score: int
    matched_terms: tuple[str, ...]
    match_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "product": self.product.to_dict(),
            "retrieval_score": self.retrieval_score,
            "matched_terms": list(self.matched_terms),
            "match_fields": list(self.match_fields),
        }


@lru_cache(maxsize=1)
def load_products(data_path: Path = DATA_PATH) -> tuple[Product, ...]:
    """Load the product catalog once per process."""
    with data_path.open(newline="", encoding="utf-8") as catalog_file:
        return tuple(Product.from_row(row) for row in csv.DictReader(catalog_file))


def _query_terms(query: str) -> tuple[str, ...]:
    terms = _tokens(query)
    if not terms:
        raise ValueError("query must contain at least one letter or number")
    required_terms = terms - RETRIEVAL_MODIFIERS
    return tuple(sorted(required_terms or terms))


def _match_product(product: Product, query_terms: tuple[str, ...]) -> SearchResult | None:
    fields = {
        field_name: _tokens(getattr(product, field_name))
        for field_name in FIELD_WEIGHTS
    }
    available_terms = set().union(*fields.values())
    if not set(query_terms).issubset(available_terms):
        return None

    matched_fields: list[str] = []
    score = 0
    for field_name, field_terms in fields.items():
        matching = set(query_terms) & field_terms
        if matching:
            matched_fields.append(field_name)
            score += len(matching) * FIELD_WEIGHTS[field_name]

    return SearchResult(
        product=product,
        retrieval_score=score,
        matched_terms=query_terms,
        match_fields=tuple(matched_fields),
    )


def search_products(query: str, *, limit: int = 10) -> list[SearchResult]:
    """Return catalog candidates whose text matches every meaningful query term.

    This is intentionally a retrieval tool, not the final product ranking. It
    returns out-of-stock products too, so the subsequent `check_inventory` tool
    can make an explicit eligibility decision.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    query_terms = _query_terms(query)
    matches = [
        result
        for product in load_products()
        if (result := _match_product(product, query_terms)) is not None
    ]
    return sorted(
        matches,
        key=lambda result: (
            -result.retrieval_score,
            -result.product.rating,
            result.product.price_usd,
            result.product.product_id,
        ),
    )[:limit]
