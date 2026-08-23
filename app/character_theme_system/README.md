# EasyChatBot Character Theme System

## Purpose

The Character Theme System controls the visual experience associated with
EasyChatBot characters.

It is deliberately isolated from:

- database models
- SQLAlchemy
- Alembic
- learner persistence
- authentication
- LLM services
- Telegram
- existing character specification loading

## Responsibility split

### Existing character specification

`docs/specifications/characters/profiles/*.yaml`

Answers:

> Who is this character?

### Character Theme System

`app/configuration/character_themes/themes/*.yaml`

Answers:

> How should this character's experience look?

### Runtime resolver

`app/character_theme_system/application/theme_resolver.py`

Answers:

> Given character + world + language context, what theme should the dashboard use?

## Database safety

This framework is read-only and file-based.

It does not:

- create tables
- modify tables
- run migrations
- access SQLAlchemy
- access PostgreSQL
- persist learner state

The existing database remains the source of truth for learner state.

## Runtime architecture

Database / existing application
        |
        | learner state
        v
Dashboard integration boundary
        |
        v
CharacterThemeResolver
        |
        +--> character theme YAML
        |
        +--> world override
        |
        +--> language context
        |
        v
DashboardThemeContext
        |
        v
DashboardThemeAdapter
        |
        v
Existing dashboard

## First integration rule

Do not modify the existing dashboard or database until this package's tests pass.

## Test

From the repository root:

    pytest app/character_theme_system/tests -q
