from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from planning import Material, load_materials, recommend


class RecommendationTests(unittest.TestCase):
    def test_order_now_restores_the_target_level(self) -> None:
        material = Material(
            item_id="MAT-1",
            description="Synthetic material",
            avg_daily_demand=10,
            lead_time_days=5,
            safety_stock=20,
            on_hand=30,
            on_order=0,
        )

        result = recommend([material], review_period_days=14)[0]

        self.assertEqual(result.material.inventory_position, 30)
        self.assertEqual(result.material.reorder_point, 70)
        self.assertEqual(result.target_level, 210)
        self.assertEqual(result.status, "ORDER NOW")
        self.assertEqual(result.recommended_order_quantity, 180)

    def test_watch_and_covered_items_do_not_get_an_order_recommendation(self) -> None:
        watch = Material("WATCH", "Watch item", 5, 10, 20, 100, 0)
        covered = Material("COVERED", "Covered item", 5, 10, 20, 250, 0)

        results = {item.material.item_id: item for item in recommend([watch, covered], 14)}

        self.assertEqual(results["WATCH"].status, "WATCH")
        self.assertEqual(results["WATCH"].recommended_order_quantity, 0)
        self.assertEqual(results["COVERED"].status, "COVERED")
        self.assertEqual(results["COVERED"].recommended_order_quantity, 0)


class InputValidationTests(unittest.TestCase):
    def test_rejects_duplicate_item_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "materials.csv"
            with path.open("w", newline="", encoding="utf-8") as destination:
                writer = csv.DictWriter(destination, fieldnames=[
                    "item_id", "description", "avg_daily_demand", "lead_time_days",
                    "safety_stock", "on_hand", "on_order",
                ])
                writer.writeheader()
                for description in ("One", "Two"):
                    writer.writerow({
                        "item_id": "DUP", "description": description, "avg_daily_demand": 1,
                        "lead_time_days": 1, "safety_stock": 0, "on_hand": 0, "on_order": 0,
                    })

            with self.assertRaisesRegex(ValueError, "duplicate item_id"):
                load_materials(path)

    def test_rejects_missing_required_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "materials.csv"
            path.write_text("item_id,description\nMAT-1,Example\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required fields"):
                load_materials(path)


if __name__ == "__main__":
    unittest.main()
