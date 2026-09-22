from app.api.platform_intelligence_review import create_platform_intelligence_review_router
from app.application.operations_center.platform_intelligence_review_api import (
    PlatformIntelligenceReviewAPI,
)
from app.application.operations_center.platform_intelligence_review_source import (
    UnconfiguredPlatformIntelligenceReviewSource,
)


def test_router_factory_requires_api():
    try:
        create_platform_intelligence_review_router(api=None)
    except ValueError as exc:
        assert str(exc) == "api is required."
    else:
        raise AssertionError("Expected ValueError")


def test_router_exposes_read_only_review_endpoints():
    api = PlatformIntelligenceReviewAPI(
        source=UnconfiguredPlatformIntelligenceReviewSource()
    )
    router = create_platform_intelligence_review_router(api=api)
    paths = {route.path for route in router.routes}

    assert "/api/operations-center/platform-intelligence/reviews" in paths
    assert "/api/operations-center/platform-intelligence/reviews/{review_item_id}" in paths
    assert "/api/operations-center/platform-intelligence/escalations" in paths
