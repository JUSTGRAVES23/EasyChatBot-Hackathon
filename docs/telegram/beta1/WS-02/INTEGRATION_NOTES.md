# WS-02 Integration v1

## Production paths

Application:
`backend/app/application/announcement/`

Infrastructure:
`backend/app/infrastructure/telegram/telegram_announcement_publisher.py`

Tests:
`backend/tests/announcement/`

## Boundary

The application owns announcement policy, composition and controlled
publication.

The infrastructure adapter only talks to the Telegram client.

The existing private classroom runtime remains unchanged.

## Explicitly not integrated

WS-02 v1 does not:
- modify `telegram_bot_runtime.py`;
- modify the private classroom gate;
- add autonomous publishing;
- add scheduling;
- add survey logic;
- add CMS functionality;
- add database persistence for publication history.

These are deliberate Beta 1 scope controls.

## Future composition

A later controlled admin/application composition can inject:

1. `AnnouncementComposer`
2. `TelegramAnnouncementPublisher`
3. `ControlledAnnouncementPublisher`

The Telegram client must be supplied by the existing Telegram infrastructure
or an explicitly configured publishing client.

Publishing must remain disabled until the administrator enables the approved
deployment configuration.

## Verification

From repository root:

`python -m pytest .\backend\tests\announcement\ -q`

Then run the existing Telegram regression suite before integration is
considered complete.
