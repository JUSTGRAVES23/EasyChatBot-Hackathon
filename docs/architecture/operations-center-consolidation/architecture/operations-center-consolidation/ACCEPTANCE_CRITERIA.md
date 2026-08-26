# Acceptance Criteria

## Architecture

- [ ] One canonical Operations Center route: `/operations-center`
- [ ] One canonical product frontend
- [ ] One canonical Operations Center API namespace
- [ ] No new competing dashboard route created
- [ ] No direct browser access to infrastructure dependencies

## Functional

- [ ] Overall health visible
- [ ] Telegram health visible
- [ ] PostgreSQL health visible
- [ ] LLM health visible
- [ ] Private Classroom monitoring visible
- [ ] Announcement Group monitoring visible
- [ ] Operational incidents visible
- [ ] Correlation ID available
- [ ] Controlled user reference available
- [ ] World association available
- [ ] Message failures visible
- [ ] Rate-limit events visible
- [ ] Abuse events visible

## UX

- [ ] Desktop verified
- [ ] Tablet verified
- [ ] Mobile verified
- [ ] One persistent navigation shell
- [ ] One visual identity
- [ ] No duplicate operational dashboards exposed to operators

## Security / Governance

- [ ] No learner message content in dashboard data
- [ ] No raw credentials in dashboard data
- [ ] User identity access is controlled
- [ ] Private and announcement surfaces remain separated
- [ ] Read-only monitoring remains read-only
- [ ] Notification publishing is separately authorized

## Quality

- [ ] Existing health tests pass
- [ ] Existing operations tests pass
- [ ] Existing frontend tests pass
- [ ] Frontend build passes
- [ ] Backend tests pass
- [ ] Security checks pass
- [ ] Smoke test passes
- [ ] Migration is documented
- [ ] Retired components have no remaining runtime references
