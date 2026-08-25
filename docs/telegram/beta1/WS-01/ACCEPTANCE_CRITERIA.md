# WS-01 Acceptance Criteria

- [ ] Telegram runtime routes normal classroom messages through
      `BetaTelegramAdapter`.
- [ ] Runtime does not directly invoke `BetaTelegramConversationBoundary`.
- [ ] Private chat is required.
- [ ] Beta authorization is required.
- [ ] Unauthorized users do not reach conversation execution.
- [ ] Group/channel messages do not reach conversation execution.
- [ ] `/start` uses the real Telegram reply boundary.
- [ ] `/start` performs token binding through `BetaAccessService`.
- [ ] `/start` does not select/change a World.
- [ ] No Telegram business logic calls an LLM/provider.
- [ ] Telegram-specific unit tests pass.
- [ ] Application regression tests pass.
- [ ] Lint/type/security checks pass.
- [ ] Intended Beta environment smoke test passes.
