# Phase B.4.1 Runbook

## Provision Beta users

Run:

python backend/scripts/create_beta_demo_users.py

Expected:

Provisioned Beta user: david
Provisioned Beta user: brother


## Validation

Check database:

- beta_users contains David
- beta_users contains Brother

Next:

Generate Telegram invitations.
