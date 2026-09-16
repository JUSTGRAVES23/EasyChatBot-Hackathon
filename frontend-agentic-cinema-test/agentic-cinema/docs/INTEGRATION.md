# Agentic Cinema integration plan

## Existing backend contract

This frontend deliberately does not replace the existing EasyChatBot Runtime or G5 workflow.

Connect `CINEMA_BACKEND_URL` to the existing application-level endpoint/adapter that invokes the deployed Google ADK Cinema Agent.

Preferred flow:

Browser
→ Next server route
→ Application/API adapter
→ Google Agent Runtime
→ `easychatbot_cinema_agent`
→ `run_g5_cinema_workflow`
→ Parallel + Gemini + memory/personalisation

## Why the proxy exists

The browser must not hold:

- Parallel API key
- Gemini credentials
- Google service-account credentials
- Agent Runtime authentication material

The Next server route keeps those concerns server-side.

## If the existing application already has an API

Do not add a second backend. Point `CINEMA_BACKEND_URL` at the existing business endpoint and map its response into the UI contract.

## If the Agent Runtime endpoint is the only available entry point

Create a small server-side adapter in the existing backend/application layer. Keep Agent Runtime invocation out of React components.

## Cloudflare Access

Recommended judge deployment:

Judge
→ Cloudflare Access
→ HTTPS frontend
→ server-side API boundary
→ existing backend / Agent Runtime

Do not expose the Parallel or Gemini credentials through Cloudflare/browser configuration.


## Interactive actions

The main intelligence request is a real server-side fetch through `/api/cinema`.

Optional action endpoints are exposed through `/api/cinema/action`:

- `CINEMA_SAVE_URL` — persistence for Save to Memory / Academy.
- `CINEMA_CHALLENGE_URL` — answer evaluation.

If these are not configured, the UI does not invent backend success; it tells the user that the endpoint is not configured. Wire these to existing application/domain endpoints rather than creating a second persistence system.

`PDF / Print` uses the browser print dialog, which can produce a PDF without adding a new backend service. `Share` uses Web Share where supported and clipboard fallback elsewhere.
