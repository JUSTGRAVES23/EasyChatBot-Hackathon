# WS-21.6 — Real Dependency Health Probes

## Delivered

Application layer:

- `backend/app/application/health/health_result.py`
- `backend/app/application/health/dependency_checks.py`
- `backend/app/application/health/production_readiness_service.py`

Infrastructure adapters:

- `backend/app/infrastructure/health/postgresql_health_check.py`
- `backend/app/infrastructure/health/llm_provider_health_check.py`
- `backend/app/infrastructure/health/telegram_health_check.py`

Tests:

- `backend/tests/health/test_ws21_6_real_dependency_health.py`

## Design

The application layer owns the health/readiness contract and aggregation.

Infrastructure owns the concrete checks:

PostgreSQL
- reuses the existing `create_database_engine()`
- performs only `SELECT 1`

LLM
- Ollama: checks `/api/tags`
- OpenAI: checks the models endpoint
- does not generate learner content

Telegram
- checks `TELEGRAM_BOT_TOKEN`
- calls Telegram `getMe`
- never sends a classroom/group message

## Security

Health results contain only sanitized status/details.

Credentials, raw exception messages, Telegram IDs, learner content and API
keys are not returned by the probes.

## Future dashboard

The structured `ProductionReadinessResult.as_dict()` contract is suitable
for a later AI Operations Center dashboard covering:

- private classroom health
- Telegram bot health
- PostgreSQL health
- LLM provider health
- main announcement-group health
- notification delivery health

The notification planning/publishing workflow remains outside WS-21.6.
