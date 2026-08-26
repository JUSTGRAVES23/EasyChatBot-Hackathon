# Operations Center Implementation Inventory

Complete this inventory before modifying or deleting duplicate implementations.

## Frontend

| Location | Framework | Route | Status | Action |
|---|---|---|---|---|
| Existing Next.js frontend | Next.js | `/operations-center` | Canonical candidate | Retain |
| Hackathon frontend | Vite/React | `/operations-center/...` | Temporary | Assess/migrate |
| Legacy/static UI | TBD | TBD | Legacy | Assess |

## Backend

| Location | Component | API | Status | Action |
|---|---|---|---|---|
| `backend/app/application/operations_center/` | Application services | Operations Center | Canonical candidate | Assess |
| Existing Operations Center router | FastAPI | `/api/operations-center/*` | Canonical API | Retain |
| Provider-management Operations Center | Provider dashboard | Operations Center | Duplicate/capability source | Assess |
| Legacy API modules | TBD | TBD | Legacy | Assess |

## Health / Operations

| Capability | Source | Canonical target |
|---|---|---|
| Production readiness | WS-21.5 | Operations Center |
| Real dependency probes | WS-21.6 | Operations Center |
| Operational health integration | WS-21.7 | Operations Center |
| Operational snapshot | WS-21.8 | Operations Center |
| Events/incidents | WS-21.9 | Operations Center |
| Dashboard contract | WS-21.10 | Operations Center |
| Visual dashboard | WS-21.11 | Existing `/operations-center` |

## Inventory rule

Do not mark an item as removable until:

1. imports/usages are searched
2. routes are searched
3. tests are searched
4. runtime references are searched
5. migration impact is documented
