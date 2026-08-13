from src.ai_runtime.memory.models import MemoryEntry, MemoryType
from src.ai_runtime.podcast.agent import PodcastDiscoveryAgent
from src.ai_runtime.podcast.models import LearningContext


def context() -> LearningContext:
    return LearningContext(
        world_id="French World",
        target_language="fr",
        learner_level="B2",
        learning_goal="Learn French through current affairs.",
    )


def test_agent_is_provider_agnostic_and_uses_preferences() -> None:
    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Prefers technology podcasts.",
        metadata={
            "topics": "artificial intelligence, European regulation",
        },
    )

    intent = PodcastDiscoveryAgent().build_search_intent(
        user_id="user-001",
        learning_context=context(),
        memories=[memory],
    )

    assert intent.learning_context.target_language == "fr"
    assert intent.learning_context.world_id == "French World"
    assert "artificial intelligence" in intent.topics
    assert "European regulation" in intent.topics
    assert intent.language_required is True


def test_agent_ignores_non_preference_memory() -> None:
    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.DISCOVERY_CONTEXT,
        content="Discussed artificial intelligence.",
    )

    intent = PodcastDiscoveryAgent().build_search_intent(
        user_id="user-001",
        learning_context=context(),
        memories=[memory],
    )

    assert intent.topics == ("French World",)
