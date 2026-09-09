"""Generate data/search-queries.csv for the product ranking sample."""

import csv
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "search-queries.csv"
HEADER = ["query_id", "query", "primary_category", "intended_product_type", "notes"]
ROWS = [
    ["Q001", "cordless drill", "Tools", "drill_driver", "Core relevance test with exact and near matches"],
    ["Q002", "dewalt cordless drill", "Tools", "drill_driver", "Brand-sensitive drill query"],
    ["Q003", "cheap drill", "Tools", "drill_driver", "Price-sensitive drill query"],
    ["Q004", "drill bits", "Tools", "drill_bits", "Accessory query"],
    ["Q005", "impact driver", "Tools", "impact_driver", "Related but distinct power tool"],
    ["Q006", "corded drill", "Tools", "drill", "Power-source constraint test"],
    ["Q007", "garden hose", "Garden", "garden_hose", "Outdoor watering query"],
    ["Q008", "expandable hose", "Garden", "garden_hose", "Attribute-sensitive hose query"],
    ["Q009", "cordless trimmer", "Garden", "string_trimmer", "Outdoor power equipment query"],
    ["Q010", "white interior paint", "Paint", "interior_paint", "Color and use-case constraint test"],
    ["Q011", "smart thermostat", "Electrical", "smart_thermostat", "Exact smart-home query"],
    ["Q012", "led light bulbs", "Electrical", "led_light_bulb", "Lighting query"],
    ["Q013", "step ladder", "Ladders", "step_ladder", "Ladder type constraint test"],
    ["Q014", "adjustable wrench", "Tools", "adjustable_wrench", "Exact hand-tool query"],
]


def main() -> None:
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} search queries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
