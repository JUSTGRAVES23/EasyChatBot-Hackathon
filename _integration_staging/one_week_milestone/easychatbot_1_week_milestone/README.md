# EasyChatBot — 1 Week Milestone Notification

Implements the approved `1_WEEK_MILESTONE` vertical slice:
User registration → eligibility → notification orchestrator → Email + Telegram → portal CTA.

This package is deliberately provider-independent and does not create a second Telegram Bot or scheduler.

Configuration:
- `EASYCHATBOT_PORTAL_URL=http://localhost:3000/dashboard`
- Registration sender: `registrationeasychatbot@resend.dev`

The Telegram adapter receives the existing `TelegramBotRuntime.bot` instance.
The caller must resolve the existing bound private `chat_id` through the application's existing identity/binding boundary.
