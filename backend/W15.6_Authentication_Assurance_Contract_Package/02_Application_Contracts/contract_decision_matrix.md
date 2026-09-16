# W15.6 Contract Decision Matrix

| Decision | W15.6 |
|---|---|
| Central assurance service | REQUIRED |
| Business-service MFA logic | FORBIDDEN |
| Provider-specific logic in business services | FORBIDDEN |
| Provider-specific logic in Identity Adapter | ALLOWED |
| Authorization inside IAM provider | NOT THE PRIMARY APPLICATION AUTHORIZATION |
| Transaction authorization in IAM provider | NO |
| EasyChatBot transaction authorization | REQUIRED |
| Assurance downgrade | FORBIDDEN |
| Replay of assurance evidence | FORBIDDEN |
| Raw secrets in assurance context | FORBIDDEN |
| Audit correlation | REQUIRED |
