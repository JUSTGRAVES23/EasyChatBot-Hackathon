"""
Shared Governance Runtime Composition.

Provides the shared governance dependencies used by:

- Provider Management controls
- Cybersecurity delivery controls
- Governance Audit API
- Governance Operations Center
- Governance Evidence API

This module is a composition boundary only.

It does not:
- execute AI agents;
- make governance decisions;
- perform remediation;
- send email.

The purpose is to ensure governance state and audit
evidence are observed through the same runtime instances.
"""

from __future__ import annotations

from governance.governance_audit_service import (
    GovernanceAuditService,
)

from provider_management.control.provider_delivery_control import (
    ProviderDeliveryControl,
)


# ------------------------------------------------------------------
# Shared governance audit service
# ------------------------------------------------------------------

governance_audit_service = GovernanceAuditService()


# ------------------------------------------------------------------
# Shared Provider Management control
# ------------------------------------------------------------------

provider_delivery_control = ProviderDeliveryControl(
    audit_service=governance_audit_service,
)


# ------------------------------------------------------------------
# Governance Operations Center read model
# ------------------------------------------------------------------

from governance.operations_center.governance_dashboard_service import (
    GovernanceDashboardService,
)

from governance.operations_center.governance_evidence_service import (
    GovernanceEvidenceService,
)


governance_dashboard_service = GovernanceDashboardService(
    audit_service=governance_audit_service,
    provider_control=provider_delivery_control,
)


governance_evidence_service = GovernanceEvidenceService(
    audit_service=governance_audit_service,
)


__all__ = [
    "governance_audit_service",
    "provider_delivery_control",
    "governance_dashboard_service",
    "governance_evidence_service",
]
