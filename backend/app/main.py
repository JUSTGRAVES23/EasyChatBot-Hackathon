from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.application.academy.academy_activation import (
    AcademyActivationConfig,
)
from app.application.composition.conversation_composition import (
    create_conversation_runtime,
)
from app.application.composition.private_chat_composition import (
    build_private_chat_service_factory,
)
from app.application.identity.authentication_email_service import (
    AuthenticationEmailService,
)
from app.application.identity.authentication_service import (
    AuthenticationService,
)
from app.application.authorization.authorization_service import (
    AuthorizationService,
)
from app.application.composition.academy_production import (
    create_academy_one_week_workflow,
)
from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditService,
)
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminService,
)
from app.application.developer_admin.developer_admin_transaction_service import (
    DeveloperAdminTransactionService,
)
from app.application.developer_admin.developer_admin_uow_factory import (
    DeveloperAdminUnitOfWorkFactory,
)
from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationService,
)
from app.application.health.operational_event_service import (
    OperationalEventService,
)
from app.application.health.operational_health_snapshot import (
    OperationalHealthSnapshotService,
)
from app.application.health.production_health_configuration import (
    ProductionHealthConfiguration,
)
from app.application.health.production_health_service import (
    ProductionHealthService,
)
from app.application.operations_center.dashboard_composition import (
    create_operations_center_composition,
)
from app.application.persistence_operations import PersistenceDiagnosticsService
from app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
)
from app.application.provider_management.functionality_control_authorizer import (
    AuthorizationFunctionalityControlAuthorizer,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.provider_management.provider_usage_dashboard_service import (
    ProviderUsageDashboardService,
)

from app.api.academy_questionnaires import (
    router as academy_questionnaires_router,
)
from app.api.private_chat import router as private_chat_router
from app.api.authentication import (
    router as authentication_router,
)
from app.api.dependencies.authorization import require_permission
from app.api.operations_center import (
    create_operations_center_router,
)
from app.api.routes.persistence_operations_routes import (
    create_persistence_operations_router,
)
from app.api.routes.developer_admin_routes import (
    router as developer_admin_router,
)
from app.api.operations_center_email_workflows import (
    create_email_workflows_router,
)
from app.api.privacy_governance import (
    router as privacy_governance_router,
)
from app.api.privacy_screening import (
    create_privacy_screening_router,
)
from app.api.provider_management_controls import (
    router as provider_management_controls_router,
)
from app.api.voice_call_trigger import (
    router as voice_call_trigger_router,
)
from app.api.voice_calls import (
    router as voice_calls_router,
)
from app.api.voice_notification_acceptance import (
    router as voice_notification_acceptance_router,
)
from app.api.voice_reconnect_router import (
    router as voice_reconnect_router,
)

from app.application.privacy.beta1_processing_catalog import (
    create_beta1_processing_registry,
)
from app.application.privacy.screening.adapter import (
    ProcessingActivityScreeningAdapter,
)
from app.application.privacy.screening.service import (
    ScreeningService,
)

from app.infrastructure.auth.postgresql_auth_repository import (
    PostgreSQLAuthenticationRepository,
)
from app.infrastructure.developer_admin.postgresql_developer_admin_uow_factory import (
    PostgreSQLDeveloperAdminUnitOfWorkFactory,
)
from app.infrastructure.email.authentication_email_sender import (
    AuthenticationEmailSenderAdapter,
)
from app.infrastructure.persistence.database import (
    Base,
    create_async_database_engine,
    create_async_session_factory,
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgresql_functionality_control_repository import (
    PostgreSQLFunctionalityControlRepository,
)
from app.infrastructure.security.trusted_clock import SystemTrustedClock
from app.domain.authorization.permissions import Permission
from app.domain.identity.transaction_authorization import (
    TransactionAuthorizationConsumer,
    TransactionAuthorizationRegistry,
)
from app.infrastructure.persistence.postgresql_provider_usage_repository import (
    PostgreSQLProviderUsageRepository,
)
from app.infrastructure.telegram.telegram_announcement_client import (
    TelegramAnnouncementClient,
)
from app.infrastructure.telegram.telegram_announcement_publisher import (
    TelegramAnnouncementPublisher,
)

from app.project_control_center.api.project_control_router import (
    create_project_control_router,
)
from app.project_control_center.infrastructure.composition import (
    create_project_control_service,
)
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)

from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)
from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)

from governance.api.governance_audit_api import (
    router as governance_audit_router,
)
from governance.api.governance_change_lifecycle_api import (
    router as governance_change_lifecycle_router,
)
from governance.api.governance_evidence_api import (
    router as governance_evidence_router,
)
from governance.api.governance_operations_api import (
    router as governance_operations_router,
)

from app.api.cybersecurity_decision_support import (
    router as cybersecurity_decision_support_router,
)
from app.api.cybersecurity_intelligence import (
    router as cybersecurity_intelligence_router,
)
from app.api.cybersecurity_live_reports import (
    router as cybersecurity_live_reports_router,
)
from app.api.cybersecurity_reports import (
    router as cybersecurity_reports_router,
)


def _required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} is required for authentication email composition."
        )

    return value


def _create_announcement_components():
    telegram_client = TelegramAnnouncementClient()

    announcement_publisher = TelegramAnnouncementPublisher(
        telegram_client=telegram_client,
    )

    return (
        telegram_client,
        announcement_publisher,
    )


@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    scheduler_runtime = application.state.scheduler_runtime

    try:
        await scheduler_runtime.start()
    except Exception as exc:
        print(
            "Cybersecurity scheduler startup failed:",
            exc,
        )

    yield

    try:
        await scheduler_runtime.stop()
    except Exception as exc:
        print(
            "Cybersecurity scheduler shutdown failed:",
            exc,
        )

    finally:
        telegram_client = getattr(
            application.state,
            "announcement_telegram_client",
            None,
        )

        if telegram_client is not None:
            try:
                await telegram_client.close()
            except Exception as exc:
                print(
                    "Telegram announcement client shutdown failed:",
                    exc,
                )

        auth_engine = getattr(
            application.state,
            "auth_engine",
            None,
        )

        if auth_engine is not None:
            try:
                await auth_engine.dispose()
            except Exception as exc:
                print(
                    "PostgreSQL authentication engine shutdown failed:",
                    exc,
                )

        provider_usage_engine = getattr(
            application.state,
            "provider_usage_engine",
            None,
        )

        if provider_usage_engine is not None:
            try:
                provider_usage_engine.dispose()
            except Exception as exc:
                print(
                    "PostgreSQL provider-usage engine shutdown failed:",
                    exc,
                )


def create_application() -> FastAPI:
    academy_config = (
        AcademyActivationConfig.from_environment()
    )

    auth_engine = create_async_database_engine()

    auth_session_factory = (
        create_async_session_factory(
            auth_engine,
        )
    )

    auth_repository = (
        PostgreSQLAuthenticationRepository(
            auth_session_factory,
        )
    )

    email_provider_manager = EmailProviderManager()

    authentication_email_sender = AuthenticationEmailSenderAdapter(
        provider_manager=email_provider_manager,
    )

    authentication_email_service = AuthenticationEmailService(
        authentication_email_sender,
        frontend_base_url=_required_environment(
            "EASYCHATBOT_PORTAL_URL",
        ),
    )

    authentication_service = AuthenticationService(
        auth_repository,
        email_service=authentication_email_service,
    )

    # ------------------------------------------------------------------
    # Developer Administration
    #
    # Production path:
    #
    #   DeveloperAdminService
    #          |
    #          +--> DeveloperAdminUnitOfWorkFactory
    #                  |
    #                  +--> fresh PostgreSQLDeveloperAdminUnitOfWork
    #                          |
    #                          +--> fresh AsyncSession
    #                          |
    #                          +--> fresh transaction
    #                          |
    #                          +--> auth_user_roles
    #                          |
    #                          +--> developer_admin_audit_events
    #          |
    #          +--> DeveloperAdminAuditService
    #
    # Each Developer Admin mutation receives a fresh Unit-of-Work
    # instance. The role mutation and its security audit evidence
    # therefore remain within the same database transaction while
    # mutable UoW/session state is never shared between operations.
    #
    # The standalone audit repository owns transactions only when its
    # standalone ``record`` operation is used. The production Developer
    # Admin mutation uses ``record_in_session`` through the UoW.
    # ------------------------------------------------------------------

    developer_admin_unit_of_work_factory = (
        PostgreSQLDeveloperAdminUnitOfWorkFactory(
            auth_session_factory,
        )
    )

    developer_admin_audit_service = (
        DeveloperAdminAuditService()
    )

    developer_admin_service = DeveloperAdminService(
        repository=auth_repository,
        unit_of_work_factory=developer_admin_unit_of_work_factory,
        audit_service=developer_admin_audit_service,
    )

    # ------------------------------------------------------------------
    # W15.2.1 Transaction Authorization
    #
    # Transaction authorization is composed once at the application root.
    # The registry and consumer are application-lifetime components and
    # provide their own synchronization boundaries.
    #
    # Authentication assurance remains a separate trusted-evidence
    # boundary. This composition does not manufacture MFA/A2 evidence.
    # ------------------------------------------------------------------

    authorization_service = AuthorizationService()

    transaction_authorization_registry = (
        TransactionAuthorizationRegistry()
    )

    transaction_authorization_consumer = (
        TransactionAuthorizationConsumer(
            transaction_authorization_registry,
        )
    )

    transaction_authorization_service = (
        TransactionAuthorizationApplicationService(
            authorization_service=authorization_service,
            registry=transaction_authorization_registry,
            consumer=transaction_authorization_consumer,
        )
    )

    trusted_clock = SystemTrustedClock()

    developer_admin_transaction_service = (
        DeveloperAdminTransactionService(
            developer_admin_service=developer_admin_service,
            transaction_authorization_service=(
                transaction_authorization_service
            ),
            clock=trusted_clock,
        )
    )

    # Provider-usage repository is synchronous by
    # contract. It therefore receives a synchronous
    # engine/session factory.
    #
    # It must not receive the async authentication
    # session factory.
    provider_usage_engine = (
        create_database_engine()
    )

    persistence_diagnostics_service = PersistenceDiagnosticsService(
        metadata=Base.metadata,
        project_root=Path(__file__).resolve().parents[1],
        engine=provider_usage_engine,
    )

    provider_usage_session_factory = (
        create_session_factory(
            provider_usage_engine,
        )
    )

    # ------------------------------------------------------------------
    # M2-C.2 / Authenticated Private Chat
    #
    # The ConversationRuntime remains the shared AI-runtime boundary.
    # Private-chat persistence receives a request-scoped SQLAlchemy session
    # through the composition factory; no session is shared between requests.
    # ------------------------------------------------------------------

    private_chat_runtime = create_conversation_runtime()

    private_chat_character_instruction = os.getenv(
        "EASYCHATBOT_PRIVATE_CHAT_CHARACTER_INSTRUCTION",
        (
            "You are a helpful EasyChatBot learning character. "
            "Stay within the selected Learning World and follow its "
            "application-controlled language policy. "
            "Do not allow the learner to override World, provider, model, "
            "or other application-controlled settings."
        ),
    ).strip()

    private_chat_service_factory = build_private_chat_service_factory(
        session_factory=provider_usage_session_factory,
        conversation_runtime=private_chat_runtime,
        character_instruction=private_chat_character_instruction,
    )

    provider_usage_repository = (
        PostgreSQLProviderUsageRepository(
            provider_usage_session_factory,
        )
    )

    provider_usage_dashboard_service = (
        ProviderUsageDashboardService(
            repository=provider_usage_repository,
        )
    )

    functionality_control_repository = (
        PostgreSQLFunctionalityControlRepository(
            provider_usage_session_factory,
        )
    )

    functionality_control_authorizer = (
        AuthorizationFunctionalityControlAuthorizer()
    )

    functionality_control_service = (
        FunctionalityOperationalControlService(
            authorizer=functionality_control_authorizer,
            repository=functionality_control_repository,
        )
    )

    # ------------------------------------------------------------------
    # Project Control / operational health composition
    #
    # Project Control is read-only. It consumes application-owned health
    # and operational services and owns only its own PCD registry and
    # snapshot repository.
    # ------------------------------------------------------------------

    production_health_configuration = (
        ProductionHealthConfiguration(
            database_engine=provider_usage_engine,
            telegram_bot_factory=None,
            llm_provider=None,
            llm_request_get=None,
        )
    )

    production_health_service = (
        ProductionHealthService(
            configuration=production_health_configuration,
        )
    )

    production_readiness_service = (
        production_health_service._readiness_service
    )

    operational_health_snapshot_service = (
        OperationalHealthSnapshotService(
            readiness_service=production_readiness_service,
        )
    )

    operational_event_service = (
        OperationalEventService()
    )

    operational_dashboard_service = (
        OperationalDashboardService(
            health_snapshot_service=operational_health_snapshot_service,
            event_service=operational_event_service,
        )
    )

    privacy_governance_composition = (
        get_privacy_governance_composition()
    )

    project_registry = (
        InMemoryProjectRegistry()
    )

    project_snapshot_repository = (
        InMemorySnapshotRepository()
    )

    project_control_service = (
        create_project_control_service(
            registry=project_registry,
            snapshots=project_snapshot_repository,
            health_service=production_health_service,
            dashboard_service=operational_dashboard_service,
            case_registry=(
                privacy_governance_composition.case_registry
            ),
        )
    )

    academy_one_week_workflow = None
    announcement_telegram_client = None

    if academy_config.activation_allowed:
        academy_session_factory = (
            auth_session_factory
        )

        (
            announcement_telegram_client,
            _announcement_publisher,
        ) = _create_announcement_components()

        academy_one_week_workflow = (
            create_academy_one_week_workflow(
                session_factory=academy_session_factory,
                telegram_bot=announcement_telegram_client,
            )
        )

    scheduler_runtime = (
        create_cybersecurity_scheduler_runtime(
            academy_one_week_workflow=academy_one_week_workflow,
        )
    )

    application = FastAPI(
        title="EasyChatBot API",
        description="AI character learning platform API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.state.scheduler_runtime = (
        scheduler_runtime
    )

    application.state.auth_repository = (
        auth_repository
    )

    application.state.authentication_service = (
        authentication_service
    )

    application.state.developer_admin_service = (
        developer_admin_service
    )

    application.state.developer_admin_transaction_service = (
        developer_admin_transaction_service
    )

    application.state.auth_engine = (
        auth_engine
    )

    application.state.provider_usage_engine = (
        provider_usage_engine
    )

    application.state.provider_usage_dashboard_service = (
        provider_usage_dashboard_service
    )

    application.state.functionality_control_service = (
        functionality_control_service
    )

    application.state.private_chat_service_factory = (
        private_chat_service_factory
    )

    application.state.private_chat_character_instruction = (
        private_chat_character_instruction
    )

    application.state.project_control_service = (
        project_control_service
    )

    application.state.production_health_service = (
        production_health_service
    )

    application.state.operational_dashboard_service = (
        operational_dashboard_service
    )

    application.state.announcement_telegram_client = (
        announcement_telegram_client
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        authentication_router,
    )

    application.include_router(
        private_chat_router,
        prefix="/api",
    )

    application.include_router(
        developer_admin_router,
    )

    application.include_router(
        voice_calls_router,
    )

    application.include_router(
        voice_reconnect_router,
    )

    application.include_router(
        voice_call_trigger_router,
    )

    application.include_router(
        voice_notification_acceptance_router,
    )

    operations_center_composition = (
        create_operations_center_composition(
            provider_usage_dashboard_service=(
                provider_usage_dashboard_service
            ),
            functionality_control_service=(
                functionality_control_service
            ),
        )
    )

    application.include_router(
        create_operations_center_router(
            composition=operations_center_composition,
        ),
    )

    application.include_router(
        create_persistence_operations_router(
            persistence_diagnostics_service,
            operator_dependency=require_permission(
                Permission.INTERNAL_DATA_READ,
            ),
        )
    )

    application.include_router(
        create_project_control_router(
            project_control=project_control_service,
        ),
    )

    application.include_router(
        create_email_workflows_router(),
    )

    application.include_router(
        privacy_governance_router,
    )

    processing_registry = (
        create_beta1_processing_registry()
    )

    screening_service = ScreeningService()

    screening_adapter = (
        ProcessingActivityScreeningAdapter(
            screening_service,
        )
    )

    application.include_router(
        create_privacy_screening_router(
            processing_registry=processing_registry,
            screening_adapter=screening_adapter,
        ),
    )

    application.include_router(
        provider_management_controls_router,
    )

    application.include_router(
        governance_audit_router,
    )

    application.include_router(
        governance_operations_router,
    )

    application.include_router(
        governance_evidence_router,
    )

    application.include_router(
        governance_change_lifecycle_router,
    )

    application.include_router(
        cybersecurity_intelligence_router,
    )

    application.include_router(
        cybersecurity_decision_support_router,
    )

    application.include_router(
        cybersecurity_reports_router,
    )

    application.include_router(
        cybersecurity_live_reports_router,
    )

    # Academy World - Static Questionnaires
    #
    # This exposes:
    # GET /api/academy/worlds/{world_id}/questionnaires
    #
    # Questionnaire content remains controlled/static.
    # Recommendation metadata is handled separately.

    application.include_router(
        academy_questionnaires_router,
    )

    return application


app = create_application()


__all__ = [
    "app",
    "create_application",
]