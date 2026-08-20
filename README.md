# Supply-Chain Planning Demo

> A synthetic, illustrative portfolio project. It uses no employer, client, ERP, or production data.

A small Python example that turns demand, lead-time, safety-stock, on-hand, and on-order inputs into a clear reorder recommendation. The emphasis is on traceable calculations, data validation, and an exception-oriented planning output.

## What it demonstrates

- Reorder-point planning based on average daily demand, lead time, and safety stock
- Inventory-position logic that accounts for both on-hand and on-order stock
- Input validation at the data boundary
- A readable report that separates **order now**, **watch**, and **covered** items
- Automated unit coverage for core calculations and invalid inputs

## Planning logic

```text
reorder point = (average daily demand × lead time) + safety stock
inventory position = on hand + on order
target level = reorder point + (average daily demand × review period)
```

When inventory position is at or below the reorder point, the demo recommends an order quantity that restores the item to its target level. The default review period is 14 days and can be changed from the command line.

## Run it

```bash
python3 -m unittest discover -s tests
python3 src/planning.py
```

Use a different input file or review period when needed:

```bash
python3 src/planning.py --input data/synthetic_materials.csv --review-period-days 21
```

## Input data

The included CSV is deliberately synthetic. Its fields are:

| Field | Meaning |
| --- | --- |
| `item_id` | Unique material identifier |
| `description` | Plain-language item description |
| `avg_daily_demand` | Average demand per day |
| `lead_time_days` | Replenishment lead time |
| `safety_stock` | Buffer stock quantity |
| `on_hand` | Current available quantity |
| `on_order` | Confirmed replenishment quantity |

## Boundary

This is a portfolio demonstration of planning concepts, not a claim of a production planning system or a substitute for approved ERP, procurement, or inventory controls.
