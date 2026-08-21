from app.infrastructure.persistence.beta_access_models import (
    BetaConnectionTokenRecord,
    BetaUserRecord,
    TelegramBindingRecord,
)
from app.infrastructure.persistence.database import Base


def test_beta_persistence_tables_are_declared():
    assert BetaUserRecord.__tablename__ == "beta_users"
    assert BetaConnectionTokenRecord.__tablename__ == "beta_connection_tokens"
    assert TelegramBindingRecord.__tablename__ == "telegram_bindings"

    tables = Base.metadata.tables
    assert "beta_users" in tables
    assert "beta_connection_tokens" in tables
    assert "telegram_bindings" in tables
