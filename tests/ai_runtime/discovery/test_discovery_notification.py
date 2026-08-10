"""
Tests for DiscoveryNotification.
"""

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_flash_deal_card,
)

from src.ai_runtime.discovery.notification import (
    DiscoveryNotification,
)


def test_notification_is_created_from_flash_deal():

    deal = build_demo_flash_deal_card()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="notification-001",
            user_id="demo-user",
            deal=deal,
        )
    )

    assert notification.notification_id == (
        "notification-001"
    )

    assert notification.user_id == "demo-user"

    assert notification.character_id == "yeti"

    assert notification.character_name == "Yeti"

    assert notification.product_name == (
        deal.product_name
    )


def test_notification_preserves_flash_deal_identity():

    deal = build_demo_flash_deal_card()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="notification-002",
            user_id="demo-user",
            deal=deal,
        )
    )

    assert notification.deal is deal

    assert notification.get_deal_url == (
        deal.get_deal_url
    )

    assert notification.more_information_url == (
        deal.more_information_url
    )


def test_notification_contains_personalisation():

    deal = build_demo_flash_deal_card()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="notification-003",
            user_id="demo-user",
            deal=deal,
        )
    )

    assert notification.relevance_reason == (
        deal.relevance_reason
    )


def test_notification_renders_compact_message():

    deal = build_demo_flash_deal_card()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="notification-004",
            user_id="demo-user",
            deal=deal,
        )
    )

    output = notification.render()

    assert "Yeti" in output

    assert "iPhone 17 Pro" in output

    assert "Why this may interest you:" in output

    assert deal.relevance_reason in output


def test_notification_rejects_empty_notification_id():

    deal = build_demo_flash_deal_card()

    try:
        DiscoveryNotification.from_flash_deal(
            notification_id="",
            user_id="demo-user",
            deal=deal,
        )
    except ValueError as exc:
        assert "notification_id cannot be empty" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_notification_rejects_empty_user_id():

    deal = build_demo_flash_deal_card()

    try:
        DiscoveryNotification.from_flash_deal(
            notification_id="notification-005",
            user_id="",
            deal=deal,
        )
    except ValueError as exc:
        assert "user_id cannot be empty" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )