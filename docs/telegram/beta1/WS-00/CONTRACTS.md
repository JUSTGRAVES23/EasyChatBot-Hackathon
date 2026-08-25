# Application Contracts — Beta 1

These are conceptual contracts to be aligned with existing repository abstractions before code is written.

## TelegramAdapter

Responsibilities:
- translate Telegram updates into application calls;
- render application results;
- handle Telegram-specific errors.

Must not:
- query repositories directly;
- implement World business rules.

## BetaAccessService

Conceptual operations:
- resolve/start onboarding for Telegram identity;
- determine whether approved Beta access exists;
- return safe classroom access state.

## WorldService

Conceptual operations:
- list Worlds assigned to the authenticated application user;
- return World onboarding dates;
- return World status.

It must not expose World administration through Telegram.

## BetaStatusService

Conceptual operation:
- return a compact Beta account snapshot.

Expected data:
- Academy status;
- Academy onboarding date;
- assigned Worlds;
- World onboarding dates;
- classroom state;
- support/open-issue summary.

## IssueManagementService

Conceptual operations:
- create issue;
- retrieve user's issues;
- return reference number;
- provide operational status.

## LinkService / configuration

Centralise:
- Academy URL;
- issue-report URL;
- voice/report URLs;
- bot deep link;
- announcement channel invitation URL.

Avoid scattered hard-coded URLs.
