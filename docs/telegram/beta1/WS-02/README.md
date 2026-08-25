# EasyChatBot Telegram Beta 1 — WS-02 Announcement Channel

## Objective

Implement the Beta 1 Announcement Channel as a controlled, read-only Telegram
surface for official EasyChatBot Academy communications.

Beta 1 uses exactly two Telegram surfaces:

1. Private classroom bot — individual learner interaction.
2. Announcement channel — official, administrator-controlled information.

The EasyChatBot classroom bot is NOT an administrator of the announcement
channel.

## Beta 1 scope

Included:
- structured announcement types
- branded message formatting
- policy validation
- controlled/manual publishing
- Telegram publisher adapter
- pinned onboarding-message definitions
- channel configuration
- publication audit records
- tests
- security/operational documentation

Explicitly excluded from Beta 1:
- CMS
- autonomous AI publishing
- automatic publishing from incidents/monitoring
- complex scheduling UI
- multi-channel management
- user-generated announcements
- Telegram channel membership verification
- survey implementation

## Branding

Channel identity: EasyChatBot Academy

Suggested handle: @EasyChatBotAcademyBot

Motto: EasyWorld — Growing with You 🌱

## Channel behaviour

- English only.
- Read-only for Beta users.
- Only the administrator publishes.
- Emoji reactions are allowed.
- Users do not select or onboard Worlds from the channel.
- The channel contains useful information and an application link.
- New users should be able to read the historical onboarding messages.

## Issue escalation

The channel should expose the fixed EasyChatBot Beta issue-reporting
application link in its description and onboarding messages.

The actual issue form/service is a separate capability and is not implemented
inside WS-02.

## Architecture

Application/service code prepares and validates an announcement. The Telegram
publisher is an infrastructure adapter.

    Admin/Application
          |
          v
    AnnouncementComposer
          |
          v
    AnnouncementPolicy
          |
          v
    AnnouncementFormatter
          |
          v
    TelegramAnnouncementPublisher
          |
          v
    Telegram Bot API / Channel

The publisher never decides whether an announcement is appropriate. Policy
validation happens before publication.

## Long-term Beta 2 compatibility

The channel remains a stable Telegram surface across Beta 1 and Beta 2.

Future changes should be introduced behind configuration and the publisher
interface. If a migration is ever required, place the channel into maintenance,
announce the change, migrate, verify, and communicate completion.
