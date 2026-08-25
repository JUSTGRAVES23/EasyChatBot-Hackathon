# ADR-003 — World Assignment Remains Application-Owned

## Decision
Users onboard Worlds through the EasyChatBot web application only.

Telegram may display assigned Worlds but cannot add, remove, switch, or join Worlds.

## Required Telegram command set
/start
/help
/world
/status

## Forbidden World administration commands
/change_world
/select_world
/join_world
/switch_world
/add_world

## Rationale
Prevents Telegram from becoming an authorization bypass and keeps World lifecycle rules centralized.
