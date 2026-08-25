# Implementation Gate

Before WS-01/WS-02 production code is generated:

1. Inspect the current repository.
2. Locate existing Telegram integrations, if any.
3. Locate configuration/settings abstractions.
4. Locate user/account identity services.
5. Locate WorldService or equivalent.
6. Locate issue-management capabilities, if any.
7. Locate existing application/API link builders.
8. Reuse existing abstractions where appropriate.
9. Identify conflicts/duplicates.
10. Only then create implementation files.

If an existing abstraction is correct:
USE IT.

If it is incomplete:
EXTEND IT.

If it is architecturally wrong:
DOCUMENT -> REVIEW -> REPLACE carefully.

Do not duplicate functionality merely to make the ZIP self-contained.
