# EasyChatBot — Agentic Cinema Frontend

A responsive, interactive judge-facing frontend for the Agentic Cinema vertical slice.

## Design intent

The UI follows the supplied EasyChatBot visual language:

- dark cinematic navy background
- purple / magenta neon accents
- rounded glass-like panels
- Luminate character identity
- Academy / Memory / Progress concepts
- desktop sidebar
- iPhone-style bottom navigation
- real interactive states rather than static screenshots

## Functional flow

1. Home / Agentic Cinema landing
2. Ask a question
3. Server-side `/api/cinema` boundary
4. Existing cinema/application backend
5. Results with live sources
6. Save to Academy (configurable real backend action)
7. Learning Challenge (configurable real backend evaluation)
8. Profile / personalisation

The browser never receives backend API secrets.

## Connect the real backend

Create `.env.local`:

```env
CINEMA_BACKEND_URL=http://localhost:8000/your-existing-cinema-endpoint
CINEMA_BACKEND_TOKEN=
CINEMA_BACKEND_TIMEOUT_MS=60000
```

The frontend POSTs:

```json
{
  "message": "What are the most important developments in the film industry this week?",
  "user_id": "hackathon-judge",
  "language": "French",
  "learner_level": "B2"
}
```

The backend may return either the existing G5 result shape or a normalised object such as:

```json
{
  "success": true,
  "intelligence": "…",
  "sources": [
    {"title": "Source", "url": "https://example.com", "snippet": "…"}
  ],
  "learning_challenge": {
    "prompt": "Summarise the main development in French.",
    "vocabulary": ["production", "industrie"]
  },
  "personalisation": {
    "applied": true,
    "message": "Adapted to the learner."
  }
}
```

## Run

```powershell
npm install
npm run typecheck
npm run build
npm run dev
```

Open `http://localhost:3000`.

## Integration rule

Do **not** put Gemini, Parallel, database access, Agent Runtime credentials, or API keys into client components.

The intended production boundary is:

`Browser → Next server/API boundary → existing application/Agent Runtime adapter → ADK Cinema Agent → G5 workflow`

## Cloudflare

Place Cloudflare in front of the deployed web application/API after local browser E2E is green.

Use Cloudflare Access to protect the judge surface. Keep backend credentials server-side.


## Important delivery note

This package is a frontend integration layer, not a replacement for the existing EasyChatBot frontend/backend. The main intelligence path is live; persistence and answer-evaluation actions are deliberately endpoint-configurable so they can connect to the existing application contracts without inventing duplicate backend services.


## Release readiness

The package has passed a source-level interaction smoke test (`npm run smoke`).
Before production/hackathon deployment, run:

```powershell
npm install
npm run typecheck
npm run smoke
npm run build
```

Then connect the existing EasyChatBot application endpoint via `CINEMA_BACKEND_URL` and perform browser E2E. The package intentionally does not invent or embed Google/Parallel credentials.
