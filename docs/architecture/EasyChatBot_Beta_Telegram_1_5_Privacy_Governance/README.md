# Beta Telegram 1.5 Privacy Governance

Flow:

Telegram ID
 -> Authorization
 -> PrivacyIdentifierService
 -> telegram_user_hash
 -> conversation_events
 -> Future Memory Engine

Direct identifiers are not stored in conversation events.

Environment:

PRIVACY_HASH_SECRET=<long-random-secret>
