# Telegram Beta 1 Architecture

## Target flow

User
  -> Telegram
  -> Telegram Adapter
  -> Application Service
  -> Domain / Runtime
  -> Persistence / approved provider
  -> Application Result
  -> Telegram Adapter
  -> User

Telegram code MUST NOT:
- access PostgreSQL directly;
- implement World assignment rules;
- make governance decisions;
- modify production data outside application services;
- expose administrative World commands.

## Surfaces

### Private classroom bot
Purpose:
- character interaction;
- learning/practice;
- voice/report access;
- World/status information;
- support and issue reporting.

### Announcement channel
Purpose:
- official Beta 1 information;
- maintenance;
- known issues;
- incidents;
- planned downtime;
- important instructions;
- Beta testing requests;
- privacy/policy notices;
- Beta updates.

Permissions:
- administrator publishes;
- Beta users read/react;
- bot is NOT a channel administrator;
- discussion/comments disabled.

## Authoritative systems

Application state is authoritative for:
- Beta approval;
- user identity;
- assigned Worlds;
- World onboarding dates;
- issue state.

Telegram is a presentation/integration surface, not the source of truth.
