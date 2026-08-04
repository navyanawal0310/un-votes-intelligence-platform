# Data Source
THE DATA SOURCE:
Source Owner: United Nations
Source Type: Official public dataset
Update Frequency: As new General Assembly voting sessions are published
Primary Key Strategy: To be derived from official identifiers (e.g., session + resolution + country)
Expected Record Count: Decades of voting history (hundreds of thousands of country-vote records)

# Data Architecture
Official UN Source
        │
        ▼
Extract
        │
        ▼
Raw Layer (Immutable)
        │
        ▼
Validation Layer
        │
        ▼
Transformation Layer
        │
        ▼
Warehouse Layer
        │
        ▼
Analytics Layer

# Data Engineering Workflow
Source Data
      ↓
Data Profiling
      ↓
Business Understanding
      ↓
Conceptual Model
      ↓
Logical Model
      ↓
Physical Schema
      ↓
ETL Implementation