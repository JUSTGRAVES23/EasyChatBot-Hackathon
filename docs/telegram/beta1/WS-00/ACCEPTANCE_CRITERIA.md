# WS-00 Acceptance Criteria

AC-01:
Architecture clearly separates Telegram Adapter, Application Services, Domain/Runtime, and persistence/provider layers.

AC-02:
Telegram has no direct database/business-logic responsibility.

AC-03:
Beta 1 uses one private classroom bot and one private announcement channel.

AC-04:
The bot is not an administrator of the announcement channel.

AC-05:
World onboarding is explicitly application-owned.

AC-06:
The allowed command contract is /start, /help, /world, /status.

AC-07:
World administration commands are explicitly excluded.

AC-08:
Approved Beta access is required for the private classroom.

AC-09:
Issue reporting routes to the EasyChatBot web application.

AC-10:
Survey/feedback implementation is explicitly deferred.

AC-11:
Security boundaries and ownership are documented.

AC-12:
Implementation workstreams can consume these contracts without inventing competing abstractions.
