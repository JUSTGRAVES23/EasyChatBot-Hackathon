# Integration notes

1. Inject the existing `TelegramBotRuntime.bot` into
   `ExistingBotTelegramNotificationSender`. Do not instantiate a second Bot.
2. Resolve the existing bound private Telegram `chat_id` through the existing
   application identity/binding boundary. Do not let an external request supply
   an arbitrary destination.
3. Reuse `EmailProviderManager` / Resend for email delivery and the existing
   registration sender configuration.
4. The approved logo must be supplied through the project's existing inline CID
   email mechanism. The orchestrator does not create a normal attachment.
5. Wire the eligibility check into the existing scheduler/notification
   orchestration only after idempotent delivery persistence is identified.
6. This package does not enable a scheduler or send real messages by itself.
