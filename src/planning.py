"""Synthetic inventory-planning example with explicit validation and calculations."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_FIELDS = (
    "item_id",
    "description",
    "avg_daily_demand",
    "lead_time_days",
    "safety_stock",
    "on_hand",
    "on_order",
)


@dataclass(frozen=True)
class Material:
    """Validated synthetic material-planning input."""

    item_id: str
    description: str
    avg_daily_demand: float
    lead_time_days: float
    safety_stock: float
    on_hand: float
    on_order: float

    @property
    def inventory_position(self) -> float:
        return self.on_hand + self.on_order

    @property
    def reorder_point(self) -> float:
        return (self.avg_daily_demand * self.lead_time_days) + self.safety_stock


@dataclass(frozen=True)
class Recommendation:
    """A calculated replenishment recommendation for one material."""

    material: Material
    review_period_days: float

    @property
    def target_level(self) -> float:
        return self.material.reorder_point + (
            self.material.avg_daily_demand * self.review_period_days
        )

    @property
    def status(self) -> str:
        if self.material.inventory_position <= self.material.reorder_point:
            return "ORDER NOW"
        if self.material.inventory_position <= self.target_level:
            return "WATCH"
        return "COVERED"

    @property
    def recommended_order_quantity(self) -> int:
        if self.status != "ORDER NOW":
            return 0
        return max(0, math.ceil(self.target_level - self.material.inventory_position))


def _number(row: dict[str, str], field: str, row_number: int, *, allow_zero: bool) -> float:
    raw_value = row.get(field, "")
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Row {row_number}: {field} must be numeric.") from error

    if value < 0 or (value == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "greater than zero"
        raise ValueError(f"Row {row_number}: {field} must be {qualifier}.")
    return value


def load_materials(path: Path) -> list[Material]:
    """Load and validate material records from a CSV file."""

    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        actual_fields = tuple(reader.fieldnames or ())
        missing_fields = [field for field in REQUIRED_FIELDS if field not in actual_fields]
        if missing_fields:
            raise ValueError(
                "Input file is missing required fields: " + ", ".join(missing_fields)
            )

        materials: list[Material] = []
        seen_item_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            item_id = row["item_id"].strip()
            description = row["description"].strip()
            if not item_id or not description:
                raise ValueError(
                    f"Row {row_number}: item_id and description are required."
                )
            if item_id in seen_item_ids:
                raise ValueError(f"Row {row_number}: duplicate item_id {item_id!r}.")

            seen_item_ids.add(item_id)
            materials.append(
                Material(
                    item_id=item_id,
                    description=description,
                    avg_daily_demand=_number(
                        row, "avg_daily_demand", row_number, allow_zero=False
                    ),
                    lead_time_days=_number(
                        row, "lead_time_days", row_number, allow_zero=False
                    ),
                    safety_stock=_number(
                        row, "safety_stock", row_number, allow_zero=True
                    ),
                    on_hand=_number(row, "on_hand", row_number, allow_zero=True),
                    on_order=_number(row, "on_order", row_number, allow_zero=True),
                )
            )
    return materials


def recommend(materials: Iterable[Material], review_period_days: float) -> list[Recommendation]:
    """Calculate recommendations ordered by status and highest required quantity."""

    if review_period_days <= 0:
        raise ValueError("review_period_days must be greater than zero.")

    recommendations = [
        Recommendation(material=material, review_period_days=review_period_days)
        for material in materials
    ]
    priority = {"ORDER NOW": 0, "WATCH": 1, "COVERED": 2}
    return sorted(
        recommendations,
        key=lambda item: (priority[item.status], -item.recommended_order_quantity, item.material.item_id),
    )


def format_report(recommendations: Iterable[Recommendation]) -> str:
    """Return a compact, terminal-readable planning report."""

    rows = list(recommendations)
    header = (
        f"{'Item':<10} {'Status':<10} {'Position':>10} {'Reorder':>10} "
        f"{'Target':>10} {'Order Qty':>10}  Description"
    )
    divider = "-" * len(header)
    body = [header, divider]
    for item in rows:
        material = item.material
        body.append(
            f"{material.item_id:<10} {item.status:<10} {material.inventory_position:>10.1f} "
            f"{material.reorder_point:>10.1f} {item.target_level:>10.1f} "
            f"{item.recommended_order_quantity:>10}  {material.description}"
        )
    body.append(divider)
    body.append(f"Materials reviewed: {len(rows)}")
    body.append(f"Order-now exceptions: {sum(item.status == 'ORDER NOW' for item in rows)}")
    return "\n".join(body)


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=project_root / "data" / "synthetic_materials.csv",
        help="CSV file containing synthetic material inputs.",
    )
    parser.add_argument(
        "--review-period-days",
        type=float,
        default=14,
        help="Days of demand to carry above the reorder point (default: 14).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    materials = load_materials(args.input)
    print(format_report(recommend(materials, args.review_period_days)))


if __name__ == "__main__":
    main()
