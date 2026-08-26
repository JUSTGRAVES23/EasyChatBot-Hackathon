# Canonical Operations Center Boundaries

## Canonical

| Layer | Canonical location |
|---|---|
| Product frontend | Existing Next.js application |
| Local frontend | `http://localhost:3000` |
| Operations UI | `/operations-center` |
| Backend | Existing FastAPI application |
| Local backend | `http://localhost:8000` |
| Operations API | `/api/operations-center/*` |

## Temporary / non-canonical

The following may continue to exist while migration is performed:

- Vite/hackathon frontend on `5173`
- legacy/static frontend ports
- provider-specific Operations Center implementations
- duplicate dashboard services
- compatibility API routes

They must not become new permanent operational entry points.

## Required separation

### Private Classroom

Monitor:

- Telegram bot status
- PostgreSQL
- LLM provider
- message failures
- rate-limit events
- abuse events
- controlled Telegram user reference
- World
- correlation ID

### Announcement Group

Monitor separately:

- Telegram status
- notification publishing
- delivery
- scheduled notifications
- notification failures
- approval state
- correlation ID

Never merge the two surfaces into one indistinguishable event stream.

## Data protection

The dashboard must never expose:

- learner message content
- prompts
- model responses
- raw Telegram identity when a controlled reference is sufficient
- passwords
- API keys
- bot tokens
- database URLs
- provider credentials
