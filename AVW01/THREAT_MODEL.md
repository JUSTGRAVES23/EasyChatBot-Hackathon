# AVW-01 Threat Model

| Threat | Control |
|---|---|
| Account enumeration | Generic resend response |
| Email flooding | Per-email/account and IP throttling |
| Token replay | Single-use token |
| Expired token | Expiration validation |
| Token leakage | No response/log exposure |
| Provider outage | Account remains unverified |
| Credential leakage | Existing provider configuration |
| Authentication bypass | Existing verified-email login gate |
| Unauthorized Project Control | Existing permission gate |
| Test bypass in production | Explicit test/dev composition only |
