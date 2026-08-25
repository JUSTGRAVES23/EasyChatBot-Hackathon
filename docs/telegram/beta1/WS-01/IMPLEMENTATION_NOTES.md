# WS-01 Implementation Notes

## Changes

### Runtime boundary

Before:

TelegramBotRuntime -> BetaTelegramConversationBoundary

After:

TelegramBotRuntime -> BetaTelegramAdapter -> BetaPrivateChatGate ->
BetaTelegramConversationBoundary

The runtime retains its optional `conversation_boundary` constructor parameter
for compatibility but does not use it to execute messages.

### Private-chat gate

`BetaPrivateChatGate` is the authoritative new interface.

`BetaTelegramPrivateChatGate` remains as a compatibility alias so existing
imports do not immediately break.

### Start handler

The previous contract passed a Telegram message object where the start handler
expected a callable. WS-01 fixes this by creating a small reply closure in the
adapter:

`message.reply_text` -> application-facing `reply(text)`.

### World handling

`/start` no longer reads `active_world_id` to tell the user which World is
selected. Telegram does not onboard or switch Worlds.

### Logging

Message content is no longer logged by the Telegram runtime. Telegram user
IDs remain operational identifiers at the transport boundary and should not be
persisted as conversation content.
