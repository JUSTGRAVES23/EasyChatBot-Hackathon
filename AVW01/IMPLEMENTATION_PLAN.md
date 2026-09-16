# AVW-01 Implementation Plan

1. Confirm repository token schema/constraints.
2. Confirm application composition and introduce only the minimum DI change.
3. Complete registration -> AuthenticationEmailService -> EmailProviderManager -> provider.
4. Define controlled provider-failure behavior: account remains unverified.
5. Add `POST /auth/resend-verification` using the same workflow.
6. Add enumeration-safe response and resend abuse controls.
7. Add injectable local/test email capture.
8. Run focused tests.
9. Run authentication/security regression.
10. Run build and smoke tests.
11. Run register -> verify -> login -> protected application E2E.
12. Architecture + Cybersecurity + QA 4-eyes sign-off.
