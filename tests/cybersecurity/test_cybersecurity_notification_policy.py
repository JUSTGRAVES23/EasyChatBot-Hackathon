"""
Tests for cybersecurity notification policy.
"""

from cybersecurity.notifications.policy import (
    CybersecurityNotificationPolicy,
)



def test_notification_policy_default_configuration():

    policy = (
        CybersecurityNotificationPolicy()
    )


    assert (
        policy.should_send_daily_report()
        is True
    )


    assert (
        policy.should_send_weekly_report()
        is True
    )


    assert (
        policy.should_send_critical_alert(
            {
                "critical_count": 1
            }
        )
        is True
    )



def test_notification_policy_blocks_critical_alert_when_disabled():

    policy = (
        CybersecurityNotificationPolicy(
            critical_alerts_enabled=False
        )
    )


    assert (
        policy.should_send_critical_alert(
            {
                "critical_count": 1
            }
        )
        is False
    )


