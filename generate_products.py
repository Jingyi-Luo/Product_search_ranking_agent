"""Generate data/products.csv for the product ranking sample."""

import csv
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "products.csv"
HEADER = [
    "product_id", "name", "brand", "category", "sub_category", "description",
    "attributes", "price_usd", "inventory_quantity", "rating",
]
ROWS = [
    ["P001", "20V MAX Cordless Drill Driver Kit", "DEWALT", "Tools", "Power Drills", "Compact cordless drill driver with two batteries and charger", "voltage=20V;power_source=cordless;tool_type=drill_driver;chuck=1/2 in;includes=batteries charger", "99.00", 34, "4.8"],
    ["P002", "M18 18V Cordless Drill Driver Kit", "Milwaukee", "Tools", "Power Drills", "Brushless cordless drill driver kit with battery and case", "voltage=18V;power_source=cordless;tool_type=drill_driver;chuck=1/2 in;motor=brushless", "129.00", 21, "4.7"],
    ["P003", "20V Cordless Impact Driver Kit", "DEWALT", "Tools", "Impact Drivers", "High torque cordless impact driver for fasteners", "voltage=20V;power_source=cordless;tool_type=impact_driver;chuck=1/4 in", "109.00", 18, "4.8"],
    ["P004", "18V Cordless Drill Driver Bare Tool", "Ryobi", "Tools", "Power Drills", "Affordable cordless drill driver without battery", "voltage=18V;power_source=cordless;tool_type=drill_driver;includes=bare_tool", "49.00", 0, "4.4"],
    ["P005", "7.5 Amp Corded Drill", "BLACK+DECKER", "Tools", "Power Drills", "Variable speed corded drill for household repairs", "power_source=corded;tool_type=drill;chuck=3/8 in", "39.00", 57, "4.3"],
    ["P006", "12V Compact Cordless Drill Kit", "Bosch", "Tools", "Power Drills", "Lightweight compact cordless drill for tight spaces", "voltage=12V;power_source=cordless;tool_type=drill_driver;chuck=3/8 in", "79.00", 26, "4.6"],
    ["P007", "5 Piece Titanium Drill Bit Set", "Milwaukee", "Tools", "Drill Accessories", "Durable titanium coated drill bits for wood and metal", "tool_type=drill_bits;material=titanium;pieces=5", "18.00", 83, "4.6"],
    ["P008", "18V Cordless Circular Saw Kit", "Ryobi", "Tools", "Power Saws", "Cordless circular saw with battery and charger", "voltage=18V;power_source=cordless;tool_type=circular_saw;blade=6-1/2 in", "119.00", 16, "4.5"],
    ["P009", "100 ft Garden Hose", "Flexzilla", "Garden", "Watering", "Flexible lightweight drinking-water-safe garden hose", "length=100 ft;product_type=garden_hose;material=hybrid_polymer", "74.00", 42, "4.7"],
    ["P010", "50 ft Expandable Garden Hose", "Flexi Hose", "Garden", "Watering", "Expandable hose with spray nozzle for small yards", "length=50 ft;product_type=garden_hose;expandable=true", "38.00", 29, "4.2"],
    ["P011", "15 in Cordless String Trimmer Kit", "EGO", "Garden", "Outdoor Power Equipment", "Battery powered string trimmer with 56V battery", "voltage=56V;power_source=cordless;tool_type=string_trimmer;cutting_width=15 in", "249.00", 12, "4.7"],
    ["P012", "10 in Adjustable Wrench", "Crescent", "Tools", "Hand Tools", "Adjustable steel wrench for plumbing and mechanical tasks", "tool_type=adjustable_wrench;length=10 in;material=steel", "22.00", 68, "4.8"],
    ["P013", "3 Piece Screwdriver Set", "Milwaukee", "Tools", "Hand Tools", "Phillips and slotted screwdriver set", "tool_type=screwdriver;pieces=3", "14.00", 95, "4.5"],
    ["P014", "1 Gallon Interior Paint and Primer", "BEHR", "Paint", "Interior Paint", "Low odor eggshell white interior wall paint", "volume=1 gal;finish=eggshell;color=white;product_type=interior_paint", "42.00", 37, "4.6"],
    ["P015", "5 Gallon Exterior Paint", "BEHR", "Paint", "Exterior Paint", "Weather resistant flat white exterior paint", "volume=5 gal;finish=flat;color=white;product_type=exterior_paint", "189.00", 14, "4.5"],
    ["P016", "Smart Wi-Fi Thermostat", "Google", "Electrical", "Smart Home", "Programmable energy saving smart thermostat", "product_type=smart_thermostat;connectivity=wi-fi;compatible=HVAC", "249.00", 19, "4.4"],
    ["P017", "LED Soft White Light Bulbs 8-Pack", "Philips", "Electrical", "Lighting", "Energy efficient A19 LED replacement bulbs", "product_type=led_light_bulb;color_temperature=soft_white;pack_size=8", "21.00", 74, "4.7"],
    ["P018", "4 ft Step Ladder", "Werner", "Ladders", "Step Ladders", "Fiberglass step ladder rated for household and jobsite use", "height=4 ft;material=fiberglass;product_type=step_ladder", "89.00", 23, "4.8"],
    ["P019", "12 ft Aluminum Extension Ladder", "Werner", "Ladders", "Extension Ladders", "Lightweight aluminum extension ladder", "height=12 ft;material=aluminum;product_type=extension_ladder", "159.00", 11, "4.6"],
    ["P020", "20V Cordless Drill and Impact Driver Combo Kit", "DEWALT", "Tools", "Power Drills", "Two tool cordless combo kit with drill driver and impact driver", "voltage=20V;power_source=cordless;tool_type=combo_kit;includes=drill_driver impact_driver batteries", "179.00", 9, "4.9"],
]


def main() -> None:
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} products to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
