-- P1.6.2B rollback
-- Academy-owned database migration handoff.
--
-- Execute ONLY if the corresponding migration has been approved
-- for rollback by the migration owner.

DROP INDEX IF EXISTS ix_provider_usage_events_created_at;
DROP INDEX IF EXISTS ix_provider_usage_events_provider_request_id;
DROP INDEX IF EXISTS ix_provider_usage_events_success;
DROP INDEX IF EXISTS ix_provider_usage_events_agent;
DROP INDEX IF EXISTS ix_provider_usage_events_functionality;
DROP INDEX IF EXISTS ix_provider_usage_events_capability;
DROP INDEX IF EXISTS ix_provider_usage_events_model;
DROP INDEX IF EXISTS ix_provider_usage_events_provider;

DROP TABLE IF EXISTS provider_usage_events;
