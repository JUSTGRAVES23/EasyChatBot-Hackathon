# Configuration Contract

Do not commit secrets.

Expected environment-driven configuration should be mapped to the existing repository configuration system.

Likely settings include:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_BOT_USERNAME
- TELEGRAM_ANNOUNCEMENT_CHANNEL_ID
- TELEGRAM_ANNOUNCEMENT_INVITE_URL
- EASYCHATBOT_APP_BASE_URL
- EASYCHATBOT_ISSUE_REPORT_URL

Important:
Use the repository's existing settings/configuration abstraction if one exists. Do not create a second configuration system without review.

No real credentials belong in this package.
