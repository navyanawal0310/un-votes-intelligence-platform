# ETL Design Document

## Project

UN Votes Intelligence Platform

---

# Purpose

The ETL pipeline transforms raw United Nations voting records into an analytics-ready warehouse while preserving data integrity, traceability, and reproducibility.

The pipeline follows a layered architecture inspired by the Medallion architecture.

---

# Data Flow

```
Raw CSV
    │
    ▼
Schema Validation
    │
    ▼
Column Classification
    │
    ▼
Vote Mapping
    │
    ▼
Country Standardization
    │
    ▼
Wide → Long Transformation
    │
    ▼
Silver Dataset
    │
    ▼
Warehouse Load
    │
    ▼
Analytics Layer
```

---

# Bronze Layer

Purpose:

Store the downloaded dataset exactly as received.

Characteristics

- Immutable
- No cleaning
- No transformation
- Versioned

Input

Official UN CSV

Output

```
data/raw/downloads/
```

---

# Validation Layer

Responsibilities

- Required metadata columns
- Duplicate columns
- Empty column names
- Country column detection
- Vote column detection

Failure Behaviour

Pipeline terminates immediately.

---

# Vote Mapping

Input

```
Y
N
A
X
```

Output

```
YES
NO
ABSTAIN
ABSENT
```

---

# Country Standardization

Responsibilities

Normalize country names.

Examples

```
Burma → Myanmar

USSR → USSR

Russian Federation → Russia

Czech Republic → Czechia
```

Historical names are preserved unless explicitly mapped.

---

# Transformation

Input

Wide table

```
Resolution
India
USA
China
```

Output

Long table

```
Resolution
Country
Vote
```

One record represents

One country voting on one resolution.

---

# Silver Layer

Contains

- Clean
- Validated
- Normalized
- Long format

Recommended Storage

Parquet

---

# Warehouse Layer

Target

PostgreSQL

Schema

Star Schema

Fact Table

fact_votes

Dimensions

dim_country

dim_resolution

dim_date

dim_council

---

# Logging

Every pipeline stage records

- Start time
- End time
- Duration
- Records processed
- Records rejected
- Errors

---

# Error Handling

Invalid schema

Stop pipeline

Invalid vote

Reject record

Unknown country

Log warning

Unexpected exception

Fail pipeline

---

# Future Improvements

Incremental loading

Pipeline orchestration

Data versioning

Historical snapshots

Data lineage

Monitoring dashboard