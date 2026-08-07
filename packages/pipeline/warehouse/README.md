# Warehouse Design

## Grain

One row in the fact table represents:

> One country's vote on one UN resolution.

---

## Star Schema

- fact_votes
- dim_country
- dim_resolution
- dim_date
- dim_council

---

## Design Principles

- Surrogate keys
- Immutable fact table
- Normalized dimensions
- Analytics-first design
- Optimized for aggregation and filtering