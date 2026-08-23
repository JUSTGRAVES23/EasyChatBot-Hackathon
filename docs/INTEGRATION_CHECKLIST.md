# Integration Checklist

- [ ] Copy files into repository paths.
- [ ] Verify `users.id` type and `users.telegram_id` type against migration.
- [ ] Verify Alembic current revision is `1c33dbcd7217`.
- [ ] Configure `DATABASE_URL`.
- [ ] Run unit tests.
- [ ] Run `python -m alembic heads`.
- [ ] Review migration SQL.
- [ ] Run `python -m alembic upgrade head`.
- [ ] Verify `beta_connection_tokens`.
- [ ] Wire the existing user repository as `user_gateway`.
- [ ] Wire `BetaTelegramStartHandler` into python-telegram-bot.
- [ ] Wire invitation generation into the existing email workflow.
- [ ] Configure private classroom access.
- [ ] Configure announcement channel separately with administrator-only posting.
- [ ] Run integration/E2E tests.
