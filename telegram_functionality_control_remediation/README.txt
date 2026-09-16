TELEGRAM FUNCTIONALITY CONTROL REMEDIATION

Objective:
Enforce Operations Center functionality stop/resume controls at the
Beta Telegram application boundary.

Architecture:
Telegram transport
 -> BetaTelegramAdapter
 -> BetaTelegramConversationBoundary
 -> TelegramConversationService
 -> ConversationRuntime

Control enforcement:
BetaTelegramConversationBoundary checks the existing
FunctionalityOperationalControlService for:
  functionality_id = "telegram"
  environment = resolve_environment(None) = adults

A disabled Telegram functionality must stop before:
- rate limiting
- abuse protection
- conversation persistence
- AI runtime execution
- provider usage

No Telegram transport/runtime or provider changes are permitted.
