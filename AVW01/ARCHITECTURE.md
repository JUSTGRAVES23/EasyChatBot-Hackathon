# AVW-01 Architecture

```text
API
 |
 v
AuthenticationService
 |--------------------> Authentication Repository
 |                         |
 |                         +--> user / credential / verification token
 |
 +--------------------> AuthenticationEmailService
                           |
                           v
                    EmailProviderManager
                           |
                           v
                    ResendEmailProvider
```

Registration and resend must use the same verification workflow. Verification remains authoritative through the existing verification endpoint. Login continues to require a verified account.

Do not create a second authentication system, token store, email-provider abstraction, direct Resend calls from application services, database verification bypass, or production development bypass.
