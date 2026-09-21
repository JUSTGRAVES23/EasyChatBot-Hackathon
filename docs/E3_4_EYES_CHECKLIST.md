# M1.4-E.3 4-Eyes Checklist

Reviewer 1:
- [ ] IDs verified against existing implementation
- [ ] schedules verified
- [ ] event-driven classification verified
- [ ] no existing records overwritten
- [ ] no secrets/email content persisted

Reviewer 2:
- [ ] focused tests pass
- [ ] PostgreSQL bootstrap verified
- [ ] second bootstrap is idempotent
- [ ] scheduler remains unchanged
- [ ] API returns Registry records

Release:
- [ ] both reviewers sign off
- [ ] targeted tests green
- [ ] live PostgreSQL verification green
- [ ] no unrelated changes
