# Integration checklist

1. Keep existing registration and email-verification flow.
2. Approve Beta explicitly after verification.
3. Only then generate the one-time Telegram token.
4. Send the "Enter My Classroom" email containing the Telegram deep link.
5. Wire `BetaTelegramStartHandler` into the active Telegram listener.
6. Process `/start TOKEN` before ordinary lesson handling.
7. Gate normal private-chat messages with `authorize_private_chat()`.
8. Do not invoke lesson/AI/memory workflows for unauthorized Telegram users.
9. ACTIVE requires:
   - verified email;
   - Beta approval;
   - Telegram binding;
   - selected Learning World.
10. Reuse the existing TelegramConnectionService/EventService rather than
    creating a second identity implementation.
11. Persist tokens durably. Store a token hash at rest.
12. Do not log raw tokens.

The uploaded repository inspection confirms the existing token, deep-link,
Telegram connection, event, Learning World and Telegram listener boundaries.
The exact active runtime bootstrap should be verified before wiring the handler.
