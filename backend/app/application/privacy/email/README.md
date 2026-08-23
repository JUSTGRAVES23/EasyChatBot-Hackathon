# Privacy Governance Reminder Email

This template is specifically for **follow-up reminders**.

It is intentionally more concise than the initial "Approval Required" escalation.

The reminder:
- identifies the pending case;
- shows only the key case details;
- provides one primary action: **REVIEW THIS CASE →**;
- links to the controlled Governance Center;
- states that the email is not an approval/rejection;
- includes the EasyChatBot logo.

The current development URL is generated from `APP_BASE_URL`:

`http://127.0.0.1:5173/privacy-governance/{case_id}`

For production, configure the approved application base URL instead.

The logo is embedded as an inline CID asset so the email does not depend on
the recipient having access to the development machine's local filesystem.
