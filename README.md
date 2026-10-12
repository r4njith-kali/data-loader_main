# Industrial IoT Data Integration & ETL Platform

**Production manufacturing data engineering case study | Hyundai internship project**

[![Industrial IoT ETL CI](https://github.com/r4njith-kali/data-loader_main/actions/workflows/ci.yml/badge.svg)](https://github.com/r4njith-kali/data-loader_main/actions/workflows/ci.yml)

**Stack:** Python 3.11 · PTC ThingWorx REST APIs · PostgreSQL · SQLAlchemy · pandas · Docker Compose · pytest · GitHub Actions

## Overview

This repository documents a manufacturing data integration system developed during a Hyundai internship and subsequently modernized for maintainability, reproducibility, and testing. The original system was deployed to transfer industrial equipment telemetry into databases supporting operational monitoring, reporting, analytics, and predictive-maintenance workflows.

The original implementation integrates PTC ThingWorx equipment discovery and historical property queries with equipment/facility mappings, production-date filtering, quality checks, and relational database loading. The modernization adds improved HTTP handling, configuration overrides, PostgreSQL conflict-aware loading, a reproducible local environment, and automated tests.

> **Deployment context:** The original deployment is recalled as supporting approximately **200–1,000 manufacturing assets** and **millions of telemetry records per day** in a near-real-time operational environment. These are retrospective estimates, **not measured performance results of the version in this repository**. The original Python jobs also include scheduled historical/batch extraction; this repository does not claim that the Python ETL itself was a continuous streaming service.

## Architecture

```mermaid
flowchart TD
  A[Manufacturing equipment: motors, inverters, HVAC] --> B[PTC ThingWorx]
  B --> C[Thing discovery and property history extraction]
  D[Equipment metadata / facility mapping] --> E[SDM pipeline]
  C --> E
  F[Production date filters and equipment property maps] --> E
  E --> G[Validation, timestamp processing, data quality]
  G --> H[PostgreSQL ingestion and conflict-aware bulk loading]
  H --> I[Operational monitoring, reporting, analytics, maintenance workflows]
  J[Mock ThingWorx responses / synthetic readings] --> K[Local reproducible test path]
  K --> H
```

The diagram combines original production responsibilities with later modernization. Mocked inputs are for local verification, not a replacement for the original ThingWorx integration.

## Engineering capabilities

| Capability | Implementation |
| --- | --- |
| Equipment discovery | `GetThings` supports template-based ThingWorx discovery, including multiple templates. |
| Historical telemetry | Property-history retrieval by equipment, property, date window and record limit. |
| Manufacturing mappings | Template-specific mappings for SEW inverter, Siemens motor and air-conditioning readings. |
| Operational data quality | Equipment connectivity, liveness and property quality-check routines. |
| Manufacturing context | Facility identifiers and production-date filtering within the SDM pipeline. |
| Incremental database writes | Modernized PostgreSQL bulk loader uses transactional batches and conflict handling where matching unique constraints exist. |
| Verification | Unit tests, PostgreSQL integration tests, a mocked upstream ingestion test and GitHub Actions CI. |

## Run locally

Requires **Docker Desktop** with Docker Compose. The default container command runs a deterministic synthetic sensor pipeline against local PostgreSQL; it does **not** contact Hyundai or ThingWorx infrastructure.

```bash
cd data_loader-main
docker compose -f compose.demo.yaml build etl
docker compose -f compose.demo.yaml run --rm etl
```

Expected initial output includes `extracted=120`, `valid=120`, and `total=120`. A second run should insert `0` duplicates if the local database volume is unchanged.

Run the automated suite with a disposable local PostgreSQL instance:

```bash
docker compose -f compose.demo.yaml run --rm \
  -e TEST_DATABASE_URL=postgresql+psycopg2://etl_user:local_demo_only@postgres:5432/industrial_iot \
  etl python -m pytest tests/ -v
```

The fixed credentials above are **only for the isolated local demonstration**. Do not reuse them for deployed systems. Stop the local services with `docker compose -f compose.demo.yaml down` (omit `-v` unless you intentionally want to erase the local database volume).

## Repository map

```text
.github/workflows/ci.yml          GitHub Actions tests with PostgreSQL service
README.md                         Project overview and reproduction guide
docs/                             Architecture and engineering case study
data_loader-main/
  src/utils/api_client.py         ThingWorx REST client
  src/utils/read_thing.py         Equipment discovery and property histories
  src/utils/sdm_client.py         Original PostgreSQL connection interfaces
  src/sdm/sdm_pipeline.py         Manufacturing extraction / transformation orchestration
  src/sdm/sdm_tbl.py              Equipment-specific relational table definitions
  src/sdm/bulk_loader.py          Transactional PostgreSQL bulk upserts
  src/demo/                      Reproducible synthetic and mocked-ingestion path
  tests/                         Unit and PostgreSQL integration tests
  Dockerfile.demo                 Reproducible Python container
  compose.demo.yaml               Local ETL + PostgreSQL services
  config/                         Sanitized example settings
```

## Production work vs. subsequent modernization

**Original internship implementation:** ThingWorx integration, equipment/property discovery, historical data retrieval, SDM database operations, facility mappings, quality checks, scheduled ingestion logic and operational deployment scripts.

**Later modernization:** HTTP timeouts and error handling, configuration environment overrides, improved multi-template discovery, normalized historical measurement adapters, PostgreSQL conflict-aware loaders, Docker-based reproduction, automated tests and GitHub Actions.

The local synthetic pipeline and mocked API responses are **test fixtures**, not a claim that production manufacturing data is included in this repository. The test suite verifies defined behaviors but does not establish original deployment throughput, availability, or live integration.

## Technical notes and limitations

- Historical jobs may use bounded result limits; full pagination/backfill behavior should be verified for each ThingWorx service before production reuse.
- Original SDM table definitions do not uniformly declare unique constraints. Conflict-aware writes require a matching primary key or unique index.
- Some original SQL queries and resource lifecycle paths remain legacy code and should be reviewed before reuse against a real deployment.
- The current demo runs a deterministic local pipeline; the ThingWorx-to-PostgreSQL path is exercised through mocked API responses in tests.
- Do not point this repository at a live manufacturing environment without a separate security, configuration and operational review.

For deeper context, see [Architecture](docs/architecture.md) and [Engineering case study](docs/engineering-case-study.md).

## Attribution

This repository contains internship-era code with existing source-file author headers. Preserve original authorship and any applicable employer permissions when describing individual contributions. The deployment context and subsequent modernization are documented separately to avoid attributing every historical file or later change to the same development period.
