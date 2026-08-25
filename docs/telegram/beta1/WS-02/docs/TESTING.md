# Testing

From the WS-02 package root:

```powershell
python -m pytest tests -q
```

The tests do not contact Telegram.

The Telegram client is injected and replaced with a fake implementation.

A production smoke test must only be performed after:
1. channel configuration is verified;
2. publishing is explicitly enabled;
3. administrator approval is confirmed;
4. a harmless test/update message is prepared;
5. the publication result is checked.

Never put a real Telegram token in the repository.
