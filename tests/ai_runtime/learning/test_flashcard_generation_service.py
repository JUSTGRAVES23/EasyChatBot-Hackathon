from src.ai_runtime.learning.flashcard_generation_service import (
    FlashcardGenerationService,
)


def test_flashcard_service_generates_set():

    service = FlashcardGenerationService()

    result = service.create_flashcards(
        topic="AI regulation",
        learner_context="B2 French learner",
    )

    assert result.topic == "AI regulation"

    assert result.count == 3


def test_flashcard_service_rejects_empty_topic():

    service = FlashcardGenerationService()

    try:
        service.create_flashcards(
            topic="",
        )

        assert False

    except ValueError:
        assert True