from demo.operations_center_demo_service import (
    OperationsCenterDemoService,
)


def test_operations_center_demo_view():

    service = OperationsCenterDemoService()

    result = service.build_view(
        {
            "event": "PROVIDER_PAUSED",
            "component": "AI_PROVIDER",
            "severity": "CRITICAL",
            "reason": "Incident",
            "email": {
                "subject": "Demo",
                "status": "prepared",
            },
            "yeti_message": "Evidence available",
        }
    )

    assert result["timeline"]["event"] == "PROVIDER_PAUSED"
    assert result["evidence"]["available"] is True
    assert result["email_preview"]["status"] == "prepared"
    assert result["yeti"] == "Evidence available"

