# AVW-01 Configuration

Reuse existing:
- `RESEND_API_KEY`
- `EASYCHATBOT_REGISTRATION_EMAIL`
- existing authentication email frontend/base URL configuration.

Do not introduce another Resend key/configuration.

## Test/local delivery
Use dependency injection:
```text
AuthenticationEmailService
  -> AuthenticationEmailSender
       -> production: EmailProviderManager -> Resend
       -> tests/local: in-memory capture sender
```
The capture sender must be selected explicitly in test/development composition and must never silently replace production delivery.
