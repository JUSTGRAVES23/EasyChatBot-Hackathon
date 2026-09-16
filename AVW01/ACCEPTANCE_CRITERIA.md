# AVW-01 Acceptance Criteria

## Functional
- [ ] Registration requires no prior authentication.
- [ ] New account is unverified.
- [ ] Token is securely issued and persisted.
- [ ] Verification email is attempted through existing email abstractions.
- [ ] Provider failure leaves account unverified.
- [ ] Resend exists and uses the same workflow.
- [ ] Verification is single-use and time-limited.
- [ ] Verified user can log in.
- [ ] Unverified user cannot log in.

## Security
- [ ] Resend does not disclose account existence.
- [ ] Resend is rate-limited.
- [ ] Raw token never appears in responses/logs.
- [ ] No direct database verification bypass.
- [ ] No production test bypass.
- [ ] Project Control authorization unchanged.

## Quality
- [ ] Unit tests pass.
- [ ] API/security tests pass.
- [ ] Authentication regression passes.
- [ ] Frontend auth regression passes.
- [ ] Build passes.
- [ ] Smoke test passes.
- [ ] E2E passes.

## Governance
- [ ] Architecture review.
- [ ] Cybersecurity review.
- [ ] QA review.
- [ ] Configuration review.
- [ ] 4-eyes sign-off.
