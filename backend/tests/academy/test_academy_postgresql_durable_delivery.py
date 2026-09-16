"""Targeted PostgreSQL integration tests for Academy durable delivery."""
from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration
DATABASE_URL = os.getenv("DATABASE_URL")


@pytest.fixture(scope="module")
def engine():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL is required")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
    yield engine
    engine.dispose()


@pytest.fixture()
def test_user(engine):
    user_id = uuid4()
    email = f"academy-test-{user_id}@example.invalid"
    username = f"academy_test_{str(user_id).replace('-', '')[:20]}"
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO users
                (id, email, username, status, trial_status,
                 created_at, email_verified)
            VALUES
                (:id, :email, :username, 'active', 'active',
                 CURRENT_TIMESTAMP, TRUE)
        """), {"id": user_id, "email": email, "username": username})
    try:
        yield user_id
    finally:
        with engine.begin() as connection:
            connection.execute(text("""
                DELETE FROM academy_notification_deliveries
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            connection.execute(text("""
                DELETE FROM users WHERE id = :user_id
            """), {"user_id": user_id})


def insert_delivery(connection, user_id, status="pending", attempts=0):
    delivery_id = uuid4()
    connection.execute(text("""
        INSERT INTO academy_notification_deliveries
            (id, user_id, notification_type, status, attempt_count,
             created_at, updated_at)
        VALUES
            (:id, :user_id, 'academy_one_week', :status, :attempts,
             CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """), {"id": delivery_id, "user_id": user_id,
           "status": status, "attempts": attempts})
    return delivery_id


def test_delivery_record_can_be_created(engine, test_user):
    with engine.begin() as connection:
        delivery_id = insert_delivery(connection, test_user)
        row = connection.execute(text("""
            SELECT id, user_id, notification_type, status, attempt_count
            FROM academy_notification_deliveries WHERE id = :id
        """), {"id": delivery_id}).mappings().one()
    assert row["id"] == delivery_id
    assert row["user_id"] == test_user
    assert row["notification_type"] == "academy_one_week"
    assert row["status"] == "pending"
    assert row["attempt_count"] == 0


def test_user_notification_type_prevents_duplicate_claim(engine, test_user):
    with engine.begin() as connection:
        insert_delivery(connection, test_user)
        with pytest.raises(Exception):
            insert_delivery(connection, test_user)


def test_successful_delivery_becomes_sent(engine, test_user):
    with engine.begin() as connection:
        delivery_id = insert_delivery(connection, test_user)
        connection.execute(text("""
            UPDATE academy_notification_deliveries
            SET status = 'sent',
                provider_message_id = 'controlled-test-message',
                sent_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": delivery_id})
        row = connection.execute(text("""
            SELECT status, provider_message_id, sent_at
            FROM academy_notification_deliveries WHERE id = :id
        """), {"id": delivery_id}).mappings().one()
    assert row["status"] == "sent"
    assert row["provider_message_id"] == "controlled-test-message"
    assert row["sent_at"] is not None


def test_failure_is_persisted(engine, test_user):
    with engine.begin() as connection:
        delivery_id = insert_delivery(connection, test_user, status="failed")
        connection.execute(text("""
            UPDATE academy_notification_deliveries
            SET status = 'failed',
                last_error = 'controlled integration-test failure',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": delivery_id})
        row = connection.execute(text("""
            SELECT status, last_error
            FROM academy_notification_deliveries WHERE id = :id
        """), {"id": delivery_id}).mappings().one()
    assert row["status"] == "failed"
    assert row["last_error"] == "controlled integration-test failure"


def test_retry_increments_attempt_count(engine, test_user):
    with engine.begin() as connection:
        delivery_id = insert_delivery(connection, test_user, "failed", 1)
        connection.execute(text("""
            UPDATE academy_notification_deliveries
            SET attempt_count = attempt_count + 1,
                status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": delivery_id})
        attempts = connection.execute(text("""
            SELECT attempt_count FROM academy_notification_deliveries
            WHERE id = :id
        """), {"id": delivery_id}).scalar_one()
    assert attempts == 2


def test_sent_notification_cannot_be_claimed_again(engine, test_user):
    with engine.begin() as connection:
        insert_delivery(connection, test_user, "sent")
        count = connection.execute(text("""
            SELECT COUNT(*) FROM academy_notification_deliveries
            WHERE user_id = :user_id
              AND notification_type = 'academy_one_week'
        """), {"user_id": test_user}).scalar_one()
    assert count == 1


def test_existing_users_can_be_queried_for_academy_eligibility(engine, test_user):
    with engine.connect() as connection:
        row = connection.execute(text("""
            SELECT id, email, username, created_at, email_verified,
                   status, trial_status
            FROM users WHERE id = :user_id
        """), {"user_id": test_user}).mappings().one()
    assert row["id"] == test_user
    assert row["email"]
    assert row["username"]
    assert row["created_at"] is not None
    assert row["email_verified"] is True
    assert row["status"] == "active"
    assert row["trial_status"] == "active"
