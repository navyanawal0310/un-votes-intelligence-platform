# UN Votes Analyzer — Architecture Roadmap

## Objective

Transform the UN Votes Analyzer from a research prototype into a
research-grade, reproducible, scalable and production-quality
geopolitical intelligence system.

## Current Validated Modules

- Country-pair voting alignment
- Voting divergence
- Rolling temporal alignment
- Change-point detection
- Ground-truth validation
- Precision, recall and F1 evaluation
- Detection-error analysis
- Event-conditioned detection
- Event-signal diagnostics
- Detection coverage
- Threshold robustness
- Null/random baseline
- Issue-level attribution
- Temporal episode attribution
- Attribution robustness
- Country-pair intelligence scorecards
- User-facing analytical interface

## Target Architecture

```text
External Data
     ↓
Ingestion
     ↓
Bronze / Raw
     ↓
Validation + Normalization
     ↓
Silver / Canonical Data
     ↓
Feature Engineering
     ↓
Analytical Models
     ├── Alignment
     ├── Temporal Models
     ├── Change Points
     ├── Network Science
     ├── Issue / NLP Analysis
     └── Event / Causal Analysis
     ↓
Forecasting
     ↓
Uncertainty + Evaluation
     ↓
Gold Intelligence Layer
     ↓
PostgreSQL
     ↓
FastAPI
     ↓
Next.js Intelligence Dashboard