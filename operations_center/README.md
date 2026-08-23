# EasyChatBot AI Operations Center — Signed-Off Demo Package

## Head Service Provider Review

**Status: APPROVED — Beta Demo UI Slice**

Review scope:
- provider-management dashboard presentation;
- read-only Operations Center boundary;
- live backend data consumption;
- provider health presentation;
- escalation visibility;
- operational-event visibility;
- no autonomous provider action.

This package is approved for the EasyChatBot Beta/demo Operations Center UI slice.

It is **not** a production provider-management control plane and does not claim
production readiness for provider routing, remediation, SLA enforcement or
financial reconciliation.

## Intended provider set

- OpenAI
- Google Gemini
- Parallel AI
- Ollama (Local)

Perplexity is intentionally not part of this demo.

## Sign-off conditions

The UI is deliberately contract-driven. It does not invent provider health,
latency, error rates, execution counts, costs or quality scores.

The backend is the source of truth.

Fields currently supported when supplied by the backend include:
- provider
- model/models
- health/status
- active
- latency_ms / average_latency_ms / avg_latency_ms
- error_rate / error_rate_percent
- last_checked_at / checked_at / observed_at
- dashboard confidence
- monitoring status
- escalation counters
- operational events

If a metric is not supplied, the UI shows `—` rather than fabricated data.

## Architecture decision

The Operations Center is intentionally separate from the learner frontend.

It does not depend on:
- character themes;
- learner context;
- character artwork;
- learner presentation logic.

Flow:

Backend API
  -> Operations Center HTTP boundary
  -> Operations Center dashboard API
  -> this read-only dashboard

The dashboard never accesses repositories directly and never performs provider
routing or autonomous remediation.

## Run

From the EasyChatBot-Hackathon repository root:

```powershell
python -m uvicorn backend.api.main:app --reload --port 8000
```

Second terminal:

```powershell
python -m http.server 5501 --directory operations_center
```

Open:

```text
http://127.0.0.1:5501/
```

## Backend endpoints

```text
GET /api/operations-center/dashboard
GET /api/operations-center/operational-events
```

## QA performed on this package

- HTML/JS/CSS package structure checked.
- Provider rendering is defensive against missing optional metrics.
- No provider health values are fabricated.
- No write/POST operation exists in the dashboard.
- API consumption uses GET-only Operations Center endpoints.
- Automatic refresh is 30 seconds.
- Manual refresh is available.
- Responsive layout retained for desktop and mobile demo viewing.

## Remaining implementation gate

Before calling the full provider-management capability DONE, the repository
must pass the existing backend test suite plus an end-to-end smoke test proving:

1. OpenAI appears from backend provider data.
2. Gemini appears from backend provider data.
3. Parallel AI appears from backend provider data.
4. Ollama appears with its actual observed health state.
5. An operational event appears in the dashboard after backend ingestion.
6. Escalation counters reflect backend state.
7. No dashboard action changes provider routing.

Those are backend/runtime acceptance criteria, not responsibilities of this
frontend package.
