# AVW-01 4-Eyes Review Checklist

## Architecture
- [ ] Existing authentication/provider boundaries preserved.
- [ ] No duplicate authentication implementation.
- [ ] No duplicate token store.
- [ ] API remains thin.
- [ ] Dependency injection is testable.
- [ ] No unrelated refactoring.

## Cybersecurity
- [ ] Enumeration review complete.
- [ ] Resend abuse controls complete.
- [ ] Token confidentiality reviewed.
- [ ] Expiry/replay reviewed.
- [ ] Provider failure reviewed.
- [ ] Logs reviewed.
- [ ] Production/test separation reviewed.

## QA
- [ ] Happy path.
- [ ] Provider failure.
- [ ] Unknown account.
- [ ] Verified account.
- [ ] Rate limiting.
- [ ] Expired token.
- [ ] Used token.
- [ ] Regression.
- [ ] E2E.

Architecture: __________________  Date: __________
Cybersecurity: _________________  Date: __________
QA: ___________________________  Date: __________
Project owner: _________________  Date: __________
