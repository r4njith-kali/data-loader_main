# Architecture and Data Flow

## Original manufacturing integration

The original implementation uses `GetThings` and `ApiClient` to query ThingWorx entities and historical property values. `SDM_PIPELINE` coordinates production-date selection, facility metadata lookup, equipment-specific property mappings and relational storage. SQLAlchemy and psycopg2 are used in database utility modules.

Equipment mappings in `sdm_tbl.py` include SEW inverter, Siemens servo motor and air-conditioning tables. Other definitions cover equipment metadata, quality summaries and maintenance/breakdown events.

## Modernized ingestion components

- `src/demo/thingworx_adapter.py`: normalizes timestamped numeric property responses into long-format measurements with stable IDs.
- `src/demo/thingworx_pipeline.py`: fetches configured properties via a client interface and sends normalized records to PostgreSQL.
- `src/demo/measurement_loader.py`: writes long-format measurements with primary-key conflict handling.
- `src/sdm/bulk_loader.py`: transactional batched insert/upsert for existing tables with matching unique constraints.
- `src/sdm/sdm_pipeline.py`: the legacy telemetry loading branch was adapted to call the bulk loader, with an integration test using a representative local table.

## Data identity and time

The legacy wide-format path builds IDs from facility and timestamp. This is appropriate only where that pair uniquely identifies a row. The normalized long-format path identifies device, property and UTC timestamp. Corrected historical measurements require an explicit update/versioning policy.

## Deployment boundaries

The local Docker Compose setup is a reproducible verification environment. It is not the original production deployment. The GitHub Actions job provisions an ephemeral PostgreSQL service and executes the test suite. No live ThingWorx connection is required for the tests.
