# EasyChatBot Telegram Beta 1 — WS-01 Telegram Foundation

## Purpose

This workstream repairs and hardens the existing Telegram Beta 1 foundation
before implementing the announcement channel or additional classroom commands.

## Scope

- Telegram runtime delegates classroom messages through `BetaTelegramAdapter`.
- Private-chat authorization is centralized in `BetaPrivateChatGate`.
- `BetaAccessService` remains the authority for Telegram identity binding.
- `/start <token>` uses the Telegram message's reply boundary correctly.
- `/start` does not select, change, or imply a Telegram-controlled World.
- Group/channel messages cannot enter the classroom application boundary.
- Telegram transport does not call an LLM/provider directly.
- Tests cover the repaired boundaries.

## Explicitly out of scope

- Announcement channel implementation (WS-02)
- `/help`, `/world`, `/status` (WS-03/WS-04)
- Beta Issue Management (WS-05)
- Surveys/reminders
- CMS
- Multi-World domain migration

## Important integration note

The existing Beta Access / World model may still expose a single
`active_world_id`. This ZIP deliberately does not redesign that domain model.
That work belongs to the World-authority workstream and must be completed
before `/world` is implemented.

## Verification

Run from the repository root:

```powershell
pytest .\tests\interfaces\telegram\ -q
pytest .\tests\infrastructure\telegram\ -q
pytest .\tests\application\ -q
```

Then run the repository's normal formatting, lint, type-check, security and
smoke-test commands.

Do not merge this workstream until the intended repository environment passes.
