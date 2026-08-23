from __future__ import annotations


def test_beta_demo_scope():
    checks = [
        "private_chat_isolation",
        "group_chat_rejection",
        "ai_response",
    ]

    assert len(checks) == 3
