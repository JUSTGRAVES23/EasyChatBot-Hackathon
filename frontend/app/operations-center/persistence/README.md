# EasyWorld Persistence Operations Center — Frontend

## Release

**v1.2.0 — EasyWorld-branded frontend refinement**

This route contains the two approved Persistence Operations Center screens:

- `/operations-center/persistence` — decision/control layer.
- `/operations-center/persistence/health` — PostgreSQL health and operations layer.

## Design direction

The visual language follows the supplied EasyWorld Academy reference:

- deep navy / midnight background;
- restrained EasyWorld gold accents;
- serif display typography for major headings;
- compact operational cards and dense information hierarchy;
- gold active navigation and tabs;
- green/amber/red state semantics;
- explicit environment selection;
- responsive desktop/tablet/mobile behaviour.

## Safety

The frontend only calls the existing read-only persistence diagnostics endpoints.
`Apply Approved Migrations` is deliberately disabled because this release does
not expose a migration mutation endpoint. `Generate Repair Plan` is a local,
read-only presentation of the live recommendation returned by the backend.

No database credentials, connection strings or secrets belong in the frontend.
