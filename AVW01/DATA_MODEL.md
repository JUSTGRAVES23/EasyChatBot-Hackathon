# AVW-01 Data Model

Reuse the existing verification-token persistence.

Required properties:
- cryptographically secure token generation;
- digest/hash persisted rather than raw token;
- expiration;
- consumed/used state;
- transactional verification.

If the current repository contract needs to expose the freshly generated token to the application workflow, use a narrowly scoped internal result such as:

```python
@dataclass(frozen=True, slots=True)
class EmailVerificationToken:
    token: str
    expires_at: datetime
```

This value must never become an API response or database field.

Before implementing latest-token invalidation, confirm the actual schema/constraints.
