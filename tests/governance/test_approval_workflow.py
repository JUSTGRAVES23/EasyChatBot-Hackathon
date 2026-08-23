from backend.governance.approval.approval_service import ApprovalService


def test_create_and_approve():

    service = ApprovalService()

    request = service.create_request(
        action="PAUSE_PROVIDER",
        component="email_provider",
        reason="Incident",
        requested_by="admin",
    )

    service.approve(request.approval_id)

    assert request.status.value == "APPROVED"
