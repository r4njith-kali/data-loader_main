# Engineering Case Study: Manufacturing IoT ETL

## Business context

During a Hyundai internship, the original system was deployed to move manufacturing equipment telemetry into relational databases supporting operational monitoring, dashboards/reporting, analytics and predictive-maintenance workflows.

The reported deployment involved approximately 200–1,000 industrial assets and millions of telemetry records daily. These are recollected estimates; original operational metrics have not been independently reproduced in this public repository.

## Engineering problem

Manufacturing telemetry arrives from different equipment families with different property names and measurement characteristics. Historical data must be associated with facility metadata and production periods, transformed into stable schemas, and made available to downstream systems without unintentionally dropping new measurements or duplicating previous records.

## Original solution

The source includes ThingWorx template/device discovery, numeric property-history queries, facility mapping, production-date filtering, equipment-specific column mappings, data quality checks and SQL database loading. Historical extraction is configured using date windows and bounded query sizes.

## Modernization decisions

1. Preserve the original integration modules rather than replacing the project with a synthetic-only tutorial.
2. Make local execution independent of proprietary infrastructure through mocked ThingWorx responses and deterministic sample readings.
3. Improve the HTTP client with timeouts, error propagation and environment-based authentication overrides.
4. Add database-enforced conflict handling and transactional batches for appropriately constrained tables.
5. Verify key behaviors through unit tests, PostgreSQL integration tests, Docker and GitHub Actions.

## Validation evidence

At the time of the release review, 35 local tests had passed, including a representative SDM ingestion integration test. An earlier Dockerized run passed 25 tests; the containerized suite must be rerun after the later changes. These results establish correctness for tested scenarios, not throughput at the reported historical production scale.

## Known engineering trade-offs

- The original code includes SQL string interpolation and legacy connection handling outside the newly tested paths.
- Some telemetry tables lack declared unique constraints; these must be established before enabling conflict-aware writes on them.
- Backfills, retries and API pagination require service-specific validation for production use.
- Original operating metrics and availability figures are not part of this repository; do not infer benchmarks from the local demo.

## Portfolio interpretation

This repository demonstrates experience with an actual deployed industrial integration system and a separate, documented modernization effort. The source and tests show implementation details; production scale and downstream use are based on the developer's retrospective account.
