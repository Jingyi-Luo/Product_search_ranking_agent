"""Run the search_products tool locally.

Example:
    PYTHONPATH=src python3 search_products.py "cordless drill"
"""

from __future__ import annotations

import argparse
import json

from ranking_agent import search_products


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the synthetic product catalog.")
    parser.add_argument("query", help="Customer search query")
    parser.add_argument("--limit", type=int, default=10, help="Maximum candidates to return")
    args = parser.parse_args()

    results = search_products(args.query, limit=args.limit)
    print(json.dumps([result.to_dict() for result in results], indent=2))


if __name__ == "__main__":
    main()
