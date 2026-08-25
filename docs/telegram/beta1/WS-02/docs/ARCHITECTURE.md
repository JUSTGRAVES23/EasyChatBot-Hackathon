# WS-02 Architecture

## Responsibility boundary

WS-02 is an announcement capability, not a Telegram runtime.

### Application layer

Owns:
- announcement type
- title/body validation
- branded composition
- publication enablement policy
- publication audit record

### Infrastructure

Owns:
- Telegram API interaction
- channel message publication
- Telegram message identifier extraction

### Telegram channel

Owns:
- official communications
- historical onboarding messages
- reactions

The channel does not own Beta access or World assignment.

## Controlled publishing

Beta 1 requires an explicit publishing switch:

`TELEGRAM_ANNOUNCEMENT_PUBLISHING_ENABLED=false`

Defaulting to disabled protects against accidental publication during
development and deployment.

## Future Beta 2 evolution

Possible future components can be added without replacing the publisher:
- scheduled publisher
- announcement repository
- approval workflow
- CMS
- analytics
- survey publisher

These are deliberately outside Beta 1.
