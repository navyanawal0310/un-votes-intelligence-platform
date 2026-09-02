# UN Votes Intelligence

> From voting records to relationship intelligence.

UN Votes Intelligence is an evidence-oriented analytical platform that transforms United Nations General Assembly voting records into measurable, temporal and explainable intelligence about relationships between countries.

The system moves beyond vote-by-vote dashboards. It constructs country-pair alignment measures, historical trajectories, temporal change points, higher-level change episodes, validation evidence and relationship scorecards, then exposes those analytical outputs through a FastAPI service and an interactive React interface.

---

## Table of Contents

- [Overview](#overview)
- [Why This Project](#why-this-project)
- [Key Capabilities](#key-capabilities)
- [System Architecture](#system-architecture)
- [Analytical Pipeline](#analytical-pipeline)
- [Architecture Layers](#architecture-layers)
- [Data Flow](#data-flow)
- [Analytical Methodology](#analytical-methodology)
- [Validation](#validation)
- [API](#api)
- [Web Application](#web-application)
- [Docker](#docker)
- [Repository Structure](#repository-structure)
- [Reproducibility](#reproducibility)
- [Limitations](#limitations)
- [Future Scope](#future-scope)
- [Project Status](#project-status)
- [Author](#author)

---

## Overview

Traditional UN voting analysis answers questions such as:

- Did a country vote Yes, No or Abstain?
- Which countries voted similarly on a resolution?
- How often did two countries agree?

UN Votes Intelligence asks a broader analytical question:

> **How does observed voting behaviour reveal alignment, divergence and change between countries over time?**

The platform therefore treats the country pair—not the individual vote—as a central analytical object.

A typical analytical path is:

```text
UN General Assembly Voting Records
              │
              ▼
       Canonical Evidence
              │
              ▼
      Analytical Pipeline
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
 Alignment  Temporal  Validation
      │       │        │
      └───────┼────────┘
              ▼
   Relationship Intelligence
              │
              ▼
          FastAPI API
              │
              ▼
      Interactive Dossier
```

---

# Why This Project

A large historical voting record contains thousands of individual observations, but raw observations do not directly communicate the evolution of a bilateral relationship.

This project introduces an analytical layer between the voting record and the user interface.

Instead of only displaying:

```text
Country A → YES
Country B → NO
```

the system can construct:

```text
Country Pair
    ↓
Voting Alignment
    ↓
Historical Trajectory
    ↓
Change Detection
    ↓
Temporal Episodes
    ↓
Evidence / Validation
    ↓
Relationship Intelligence
```

This makes the underlying record more suitable for longitudinal analysis and structured interrogation.

---

# Key Capabilities

| Capability | Purpose |
|---|---|
| Country-pair alignment | Measures similarity in observed voting behaviour |
| Historical trajectory | Represents how alignment evolves through time |
| Change-point detection | Identifies years with material changes in alignment |
| Temporal episodes | Groups nearby change points into higher-level periods |
| Effect-size analysis | Quantifies the magnitude of detected changes |
| Ground-truth validation | Tests detected episodes against reference events |
| Robustness analysis | Examines whether detected signals persist under analytical variations |
| Null baseline | Provides a baseline for interpreting detection performance |
| Issue-level evidence | Connects relationships with substantive voting categories where available |
| Relationship scorecards | Bundles major analytical indicators into a country-pair assessment |
| Provenance | Identifies the source and analytical origin of outputs |
| Natural-language interrogation | Allows users to ask analytical questions about the record |
| Interactive dossiers | Presents the evidence as a structured analytical interface |

---

# System Architecture

The platform follows a modular architecture in which data preparation, analytical computation, relationship intelligence, API delivery and presentation are separated.

## Architecture at a glance

| Layer | Responsibility | Representative Components |
|---|---|---|
| **Source** | Provide authoritative voting evidence | UN General Assembly voting records |
| **Data** | Store raw, validated and processed evidence | `data/` |
| **Pipeline** | Convert source data into canonical analytical artifacts | `analytical_pipeline.py`, `pipeline.py` |
| **Analytics** | Calculate alignment, temporal changes and validation measures | `packages/analytics/` |
| **Intelligence** | Construct country-pair relationship representations | Relationship intelligence / scorecard modules |
| **API** | Expose analytical results as services | FastAPI, `packages/api/` |
| **Interface** | Present analytical results to users | React / Vite frontend |
| **Deployment** | Package and run the application | Docker Compose, Dockerfiles, nginx |

## Architectural principle

The **canonical analytical pipeline is the integration boundary**.

Downstream components should consume validated analytical artifacts rather than independently reinterpreting raw source files.

This provides:

- reproducibility
- modularity
- provenance
- consistent analytical definitions
- easier testing
- cleaner future integration

---

# Analytical Pipeline

The current analytical workflow can be represented as:

```text
                 ┌─────────────────────┐
                 │ UN Voting Evidence  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Data Validation     │
                 │ & Canonicalisation  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Country-Pair        │
                 │ Alignment           │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Temporal Alignment  │
                 │ & Trajectories      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Change-Point        │
                 │ Detection           │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Temporal Episodes   │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
        Validation      Robustness     Attribution
              │             │              │
              └─────────────┼──────────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Relationship        │
                 │ Intelligence        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ API + Interactive   │
                 │ Dossier             │
                 └─────────────────────┘
```

---

# Architecture Layers

## 1. Data Foundation

The data layer separates source evidence from derived analytical artifacts.

| Data Layer | Role |
|---|---|
| `data/raw/` | Source-level UN voting extracts |
| `data/bronze/` | Initial structured ingestion |
| `data/silver/` | Cleaned / transformed data |
| `data/gold/` | Canonical analytical outputs |
| `reports/analytical_outputs/` | Generated analytical and validation result files |

The repository intentionally separates analytical results from application source code.

---

## 2. Analytical Layer

The analytical layer contains the core statistical and temporal transformations.

Major concepts include:

| Analytical Object | Description |
|---|---|
| Country pair | Normalised pair of countries used as the primary relationship unit |
| Alignment | Similarity in observed voting behaviour |
| Temporal alignment | Time-indexed representation of pair alignment |
| Change point | Detected material change in a relationship trajectory |
| Episode | Cluster of temporally close change-point detections |
| Ground truth | Reference events used to evaluate temporal detection |
| Attribution | Evidence connecting detected changes to substantive issues/events |
| Robustness | Tests of analytical stability |
| Null baseline | Baseline for evaluating whether detections exceed expected signal |

---

## 3. Relationship Intelligence

Relationship intelligence converts analytical measurements into a country-pair representation.

A relationship profile can include:

- relationship direction
- relationship score
- voting alignment
- observed divergence
- latest assessment year
- evidence observation count
- historical trajectory
- change points
- temporal episodes
- validation and evidence indicators

The interface deliberately distinguishes **observed analytical evidence** from broader political interpretation.

---

## 4. API Layer

The backend is implemented with FastAPI.

Current API namespace:

```text
/api/v1
```

| Endpoint | Method | Purpose |
|---|---:|---|
| `/countries` | GET | Return available countries |
| `/relationship/{country_a}/{country_b}` | GET | Return relationship profile |
| `/relationship/{country_a}/{country_b}/history` | GET | Return historical relationship data |
| `/relationship/{country_a}/{country_b}/changes` | GET | Return detected relationship changes |
| `/query` | POST | Execute a natural-language analytical query |

The API also normalises analytical objects into JSON-safe values before transport.

---

## 5. Presentation Layer

The frontend is a React/Vite application designed around an analytical dossier rather than a conventional dashboard.

Major interface concepts include:

- country-pair selection
- relationship overview
- alignment trajectory
- turning points
- temporal episodes
- evidence and methodology
- natural-language interrogation
- project architecture / methodology information

The About page documents the system architecture and its future extensibility.

---

# Data Flow

A simplified request-to-result path is:

```text
User
 │
 ▼
React Interface
 │
 ▼
FastAPI Endpoint
 │
 ▼
Relationship / Query Service
 │
 ▼
Canonical Analytical Artifacts
 │
 ▼
Country-Pair Intelligence
 │
 ▼
JSON-safe API Response
 │
 ▼
Interactive Dossier
```

For analytical generation:

```text
Source Data
   ↓
Validation
   ↓
Canonicalisation
   ↓
Pair Alignment
   ↓
Temporal Analysis
   ↓
Change Detection
   ↓
Episode Construction
   ↓
Validation / Robustness
   ↓
Relationship Scorecard
```

---

# Analytical Methodology

## Country-pair alignment

The system evaluates how similarly two countries vote across the available record.

This produces a quantitative representation of observed voting alignment rather than a qualitative diplomatic label.

## Historical trajectory

Alignment is retained through time so that the system can distinguish:

- persistent alignment
- persistent divergence
- gradual movement
- abrupt change
- periods of instability

## Change-point detection

The temporal analysis identifies years where the observed relationship changes materially.

Each change record can contain fields such as:

```text
country_a
country_b
change_year
change_magnitude
effect_size
confirmed
confidence
```

## Temporal episodes

Individual change points can be close together.

The episode layer groups nearby detections into higher-level periods, making the output more interpretable than a long list of isolated years.

For example:

```text
1987
    ↓
Episode

2008
    ↓
Episode

2022 ── 2023 ── 2024
    ↓
Single temporal episode
```

## Evidence and provenance

Analytical outputs retain source and provenance information wherever available.

This allows the interface to distinguish:

```text
Observed evidence
       ≠
Analytical inference
       ≠
Political explanation
```

That distinction is fundamental to the project's design.

---

# Validation

Validation is treated as a first-class analytical layer rather than an afterthought.

The repository includes outputs covering:

- ground-truth validation
- quantitative evaluation
- temporal error analysis
- event-conditioned detection
- event-signal diagnostics
- detection coverage
- robustness analysis
- null-baseline analysis
- attribution robustness

## Current validation result

The current recorded ground-truth experiment contains **9 reference events**.

For the evaluated detection set, the recorded aggregate metrics are:

| Metric | Result |
|---|---:|
| Precision | 0.500 |
| Recall | 0.111 |
| F1 | 0.182 |
| Mean temporal overlap | 0.250 |
| Mean temporal lead/lag | -2.0 years |
| Directional agreement | 1.000 |

These results indicate that the current detector should **not** be interpreted as a comprehensive geopolitical-event detector.

The validation result is therefore presented as both:

1. evidence about what the current analytical method can detect, and
2. a documented limitation of the present system.

---

# Example: India–China Relationship

The interactive dossier has been tested using the `IND–CHN` country pair.

The current analytical record reports approximately:

| Indicator | Value |
|---|---:|
| Latest assessment year | 2025 |
| Relationship score | 0.893 |
| Voting alignment | 0.927 |
| Observed divergence | 0.146 |
| Evidence observations | 192 |

The turning-point analysis currently identifies:

| Episode | Period | Peak |
|---|---|---|
| 1 | 1987 | 1987 |
| 2 | 2008 | 2008 |
| 3 | 2022–2024 | 2023 |

These values are **pair-specific analytical outputs** and should not be generalized to other country pairs without running the corresponding analysis.

---

# Web Application

The interface is intentionally designed as an analytical dossier.

## Core exhibits

| Exhibit | Function |
|---|---|
| Relationship profile | Current country-pair assessment |
| Historical trajectory | Longitudinal relationship behaviour |
| Turning points | Detected change points and temporal episodes |
| Interrogate the record | Natural-language analytical queries |
| Evidence & method | Source, provenance and methodological context |
| About | Project architecture, innovation and future direction |

---

# Docker

The application is containerised using Docker Compose.

The deployment consists of:

```text
                    Docker Compose
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      Frontend Container       Backend Container
             │                       │
          nginx                  FastAPI
             │                       │
             └───────────┬───────────┘
                         ▼
                    Application
```

## Frontend container

Responsibilities:

- install frontend dependencies
- build the Vite application
- serve the production bundle through nginx

## Backend container

Responsibilities:

- install Python dependencies
- expose FastAPI
- serve analytical/API functionality

## Build

From the repository root:

```bash
docker compose build
```

## Start

```bash
docker compose up
```

## Stop

```bash
docker compose down
```

## Health check

The backend exposes:

```text
/health
```

A successful local deployment has returned:

```text
HTTP 200 OK
```

---

# Repository Structure

The repository is organised around application code, analytical packages, data and reproducibility artifacts.

```text
un-votes-intelligence-platform/
│
├── apps/
│   ├── api/
│   │   ├── Dockerfile
│   │   └── ...
│   │
│   └── frontend/
│       ├── Dockerfile
│       ├── nginx.conf
│       └── ...
│
├── packages/
│   ├── analytics/
│   ├── api/
│   └── ...
│
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── reports/
│   └── analytical_outputs/
│
├── tests/
│
├── docs/
│
├── analytical_pipeline.py
├── pipeline.py
├── load_warehouse.py
├── country_pair_intelligence.py
├── country_pair_scorecard.py
├── change_point_explanation.py
├── un_votes_analyzer.py
│
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

Generated analytical outputs are kept under `reports/analytical_outputs/` rather than cluttering the repository root.

---

# Reproducibility

The project is designed around explicit analytical artifacts and reproducible processing stages.

Recommended workflow:

```text
1. Acquire source data
2. Validate source structure
3. Run canonical pipeline
4. Generate analytical artifacts
5. Run validation / robustness analyses
6. Build relationship intelligence
7. Start API
8. Start frontend
9. Inspect analytical dossier
```

Important reproducibility principles:

- preserve source provenance
- avoid silently changing analytical definitions
- keep generated outputs identifiable
- separate source data from derived results
- maintain tests for analytical components
- use Docker for environment-level reproducibility

---

# Limitations

UN voting behaviour is an **indirect proxy** for broader international relationships.

The platform therefore does not claim that:

- voting alignment equals diplomatic friendship
- voting divergence proves political conflict
- a detected change proves a geopolitical cause
- temporal correlation establishes causality
- a detected episode represents a complete explanation of a country's foreign policy

The current validation results also demonstrate that the temporal detector has limited recall against the available ground-truth set.

Where attribution evidence is unavailable, the interface should explicitly indicate that limitation rather than fabricate an explanation.

---

# Future Scope

The architecture is deliberately source-agnostic.

The current analytical foundation is based on UN voting evidence, but future evidence sources can be integrated through the same temporal, provenance and entity-alignment concepts.

Potential future sources include:

```text
UN Voting
    +
Resolution Text
    +
Statements / Speeches
    +
Current Affairs
    +
Geopolitical Events
    +
Other Structured Evidence
    ↓
Richer Relationship Intelligence
```

Future integration should preserve:

- country/entity identifiers
- issue identifiers
- event identifiers
- temporal alignment
- provenance
- source-specific evidence
- confidence
- analytical lineage

The future evidence layer is an architectural direction; it is **not currently implemented as a live current-affairs or geopolitical data source**.

---

# Project Status

| Area | Status |
|---|---|
| UN voting data foundation | Complete |
| Canonical analytical pipeline | Implemented |
| Country-pair alignment | Implemented |
| Temporal alignment | Implemented |
| Change-point detection | Implemented |
| Temporal episode construction | Implemented |
| Validation framework | Implemented |
| Relationship intelligence | Implemented |
| FastAPI backend | Implemented |
| Interactive React interface | Implemented |
| Natural-language query layer | Implemented |
| About / architecture page | Implemented |
| Docker Compose | Working locally |
| Repository cleanup | Initial cleanup complete |
| Production deployment | Next stage |
| Current-affairs / geopolitical evidence | Future scope |

---

# Author

**Navya Nawal**  
Undergraduate Student

- Email: navyanawal4396@gmail.com
- GitHub: `navyanawal0310`
- LinkedIn: `Navya Nawal`

---

## Closing Note

UN Votes Intelligence is designed as an analytical system rather than a static visualisation.

Its central objective is to make long-running patterns in international voting behaviour **measurable, temporal, inspectable and evidence-aware**.

The system therefore treats the analytical pipeline, validation framework and provenance model as first-class components of the product—not merely implementation details behind the interface.
