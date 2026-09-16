# EasyWorld Persistence Operations Center — Final Phase 1.1 Package

This package is a **read-only diagnostic slice** for the EasyWorld Operations Center.

Primary surfaces:

1. `/operations-center/persistence` — Persistence Overview / decision layer.
2. `/operations-center/persistence/health` — Database Health & Operations / diagnosis layer.

## 4-eyes engineering decision

**STATUS: APPROVED — PHASE 1.1 DIAGNOSTIC RELEASE**

The package passed the final package-level review after remediation of:
- unsafe implicit reuse of one database connection across environments;
- fragile Alembic path resolution;
- false "zero/healthy" values when PostgreSQL statistics are unavailable;
- unredacted query text in slow-query and blocking diagnostics;
- missing migration lineage representation;
- misleading migration-execution wording in the UI;
- missing CSS module class used by the overview page.

This package remains intentionally read-only.

## Live-data contract

Operational facts must come from live PostgreSQL, Alembic and SQLAlchemy metadata.
The UI contains no operational sample values.

Optional capabilities such as `pg_stat_statements`, backup-provider state,
restore verification and application-specific integrity checks are explicitly
reported as unavailable/not configured when their source is not connected.

An environment selector must map to an explicit database engine. A DEV engine
is never silently reused for STAGING or PRODUCTION.

## Architecture

`Frontend → Operations Center API → PersistenceDiagnosticsService → PostgreSQL/Alembic/SQLAlchemy → snapshot`

Environment resolution is an explicit application-composition concern:

```python
from backend.app.application.persistence_operations import (
    PersistenceDiagnosticsService,
)
from backend.app.application.persistence_operations.environment import (
    create_environment_engine_resolver,
)

resolver = create_environment_engine_resolver(
    {
        "dev": dev_engine,
        "staging": staging_engine,
        "production": production_engine,
    }
)

persistence_diagnostics = PersistenceDiagnosticsService(
    engine_resolver=resolver,
    metadata=Base.metadata,
    project_root=PROJECT_ROOT,
)
```

For a local DEV-only installation, the legacy `engine=...` constructor remains
supported, but STAGING/PRODUCTION will report `NOT_CONFIGURED` instead of
silently querying DEV.

## Alembic path contract

Pass the real repository root. The diagnostic service resolves `alembic.ini`
and its configured `script_location` from that root, so the service does not
depend on the process current working directory.

## API

- `GET /api/operations-center/persistence?environment=dev`
- `GET /api/operations-center/persistence/health?environment=dev`

Existing Operations Center authentication/authorisation must be injected through
`operator_dependency`. Do not introduce a second authentication mechanism.

## Environment configuration

Optional per-environment contracts:

```env
APP_VERSION=1.8.2
APP_VERSION_DEV=1.8.2
PERSISTENCE_EXPECTED_SCHEMA_REVISION=20260910_example
PERSISTENCE_EXPECTED_SCHEMA_REVISION_DEV=20260910_example
```

Only values explicitly configured or safely derived from a single repository head
are shown. No expected schema revision is fabricated.

## Safety boundary

This package does **not**:
- run Alembic migrations;
- stamp `alembic_version`;
- modify PostgreSQL;
- execute arbitrary SQL from the browser;
- automatically create/drop indexes;
- perform backups/restores;
- make autonomous production changes.

The future governed workflow remains:

`Detect → Plan → Review → Test → Approve → Apply → Validate → Promote → Verify → Audit`

## Security boundary

Query text from `pg_stat_activity`, blocking diagnostics and
`pg_stat_statements` is redacted by default. Enable
`PERSISTENCE_EXPOSE_QUERY_TEXT=true` only for an explicitly authorised
diagnostic context.

Database/SQL errors returned by diagnostics are sanitised; DSNs, SQL and raw
provider/database error details are not exposed to the browser.

## Testing

From the repository root:

```text
pytest backend/tests/application/persistence_operations/test_persistence_diagnostics_service.py -q
```

The package-level review also performs Python compilation and frontend TSX
syntax parsing. Full Next.js type/lint/build validation must be run in the
target frontend repository because this drop-in package intentionally does not
ship the host application's `package.json`, lockfile or dependency tree.
