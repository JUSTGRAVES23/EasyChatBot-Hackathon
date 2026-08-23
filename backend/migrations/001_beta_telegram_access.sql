-- Beta Telegram Access persistence.
-- Apply through the project's PostgreSQL deployment mechanism.

CREATE TABLE IF NOT EXISTS beta_users (
    id VARCHAR(128) PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    active_world_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_beta_users_active_world_id
    ON beta_users(active_world_id);

CREATE TABLE IF NOT EXISTS beta_connection_tokens (
    id VARCHAR(128) PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(128) NOT NULL REFERENCES beta_users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_beta_connection_tokens_user_id
    ON beta_connection_tokens(user_id);

CREATE TABLE IF NOT EXISTS telegram_bindings (
    id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL REFERENCES beta_users(id) ON DELETE CASCADE,
    telegram_user_id VARCHAR(128) NOT NULL UNIQUE,
    chat_id VARCHAR(128) NOT NULL,
    connected_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_telegram_binding_beta_user UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS ix_telegram_bindings_user_id
    ON telegram_bindings(user_id);
