# UN Votes Analyzer — Architecture Baseline

## Purpose

This document records the current architecture before the project
is upgraded to the research-grade and industry-grade workflow.

The existing validated analytical work must be preserved.

---

## Current Architecture

```text
External UN Data
       ↓
data/raw/
       ↓
packages/pipeline/
       ├── ingestion/
       ├── profiling/
       ├── transformation/
       └── validation/
       ↓
packages/warehouse/
       ↓
DuckDB
       ↓
packages/analytics/
       ├── alignment
       ├── temporal analysis
       ├── change points
       ├── issue analysis
       ├── coalition analysis
       ├── bridge/swing analysis
       └── resolution analysis
       ↓
Analytical CSV Outputs
       ↓
un_votes_analyzer.py
       ↓
apps/api/

