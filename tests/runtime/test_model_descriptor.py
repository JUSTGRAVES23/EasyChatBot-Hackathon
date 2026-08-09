from backend.runtime.models.model_id import ModelId
from backend.runtime.models.model_capabilities import ModelCapabilities
from backend.runtime.models.model_descriptor import ModelDescriptor


def test_model_id():

    model = ModelId(
        provider="google",
        name="gemini-2.5-flash",
    )

    assert model.full_name() == (
        "google:gemini-2.5-flash"
    )


def test_model_descriptor():

    descriptor = ModelDescriptor(
        model_id=ModelId(
            provider="google",
            name="gemini-2.5-flash",
        ),
        capabilities=ModelCapabilities(
            reasoning=True,
            tool_usage=True,
        ),
        description="Fast reasoning model",
    )

    assert descriptor.model_id.provider == "google"

    assert descriptor.capabilities.reasoning is True

    assert descriptor.capabilities.tool_usage is True