"""
EasyChatBot Hackathon — Podcast Learning Challenge service.

MVP scope:
    verified podcast metadata
        -> level/language-aware challenge

It intentionally does not:
- download audio
- transcribe episodes
- infer facts from unavailable audio
- call Apple/Spotify
- write persistent memory
"""

from __future__ import annotations

from src.ai_runtime.podcast.challenge import (
    ChallengeResult,
    ComprehensionQuestion,
    PodcastLearningChallenge,
    VocabularyItem,
)
from src.ai_runtime.podcast.models import PodcastRecommendation


class PodcastLearningChallengeService:
    """Creates and evaluates small deterministic learning challenges."""

    _LEVEL_GUIDANCE = {
        "a1": "Keep the language simple and concrete.",
        "a2": "Use common vocabulary and short explanations.",
        "b1": "Use practical vocabulary and clear contextual questions.",
        "b2": "Use contextual vocabulary and inference-oriented questions.",
        "c1": "Use nuanced vocabulary and analytical questions.",
        "c2": "Use advanced nuance, register, and critical analysis.",
    }

    def create_challenge(
        self,
        *,
        recommendation: PodcastRecommendation,
    ) -> PodcastLearningChallenge:
        """
        Build a challenge from verified recommendation metadata.

        The content is intentionally deterministic for the hackathon demo.
        It does not claim to have analysed the podcast audio.
        """

        language = recommendation.result.languages[0]
        level = recommendation.result.metadata.get(
            "learner_level",
            "B2",
        )

        topic = recommendation.result.title

        vocabulary = (
            VocabularyItem(
                term="réglementation",
                meaning="Ensemble des règles qui encadrent une activité.",
                example=(
                    "La réglementation européenne encadre "
                    "l'intelligence artificielle."
                ),
            ),
            VocabularyItem(
                term="intelligence artificielle",
                meaning=(
                    "Technologies permettant à des machines "
                    "d'effectuer des tâches associées à l'intelligence humaine."
                ),
                example=(
                    "L'intelligence artificielle transforme "
                    "de nombreux secteurs."
                ),
            ),
            VocabularyItem(
                term="enjeu",
                meaning="Question importante qui présente un intérêt majeur.",
                example=(
                    "La protection des données est un enjeu important."
                ),
            ),
        )

        questions = (
            ComprehensionQuestion(
                question=(
                    f"Quel est le thème principal associé à « {topic} » ?"
                ),
                options=(
                    "L'intelligence artificielle et la réglementation",
                    "La cuisine française",
                    "Les transports urbains",
                ),
                correct_option=0,
            ),
            ComprehensionQuestion(
                question=(
                    "Pourquoi la réglementation peut-elle être importante "
                    "pour l'intelligence artificielle ?"
                ),
                options=(
                    "Pour encadrer son utilisation et ses risques",
                    "Pour supprimer toutes les technologies",
                    "Pour empêcher les utilisateurs d'apprendre",
                ),
                correct_option=0,
            ),
        )

        introduction = (
            f"Écoutez le podcast en {language}, puis revenez ici pour "
            f"votre défi {level}. Faites attention aux mots clés et aux "
            "idées principales."
        )

        discussion_prompt = (
            "Après votre écoute, expliquez en quelques phrases votre "
            "opinion sur le sujet et utilisez au moins deux nouveaux mots."
        )

        return PodcastLearningChallenge.create(
            user_id=recommendation.user_id,
            podcast_id=recommendation.result.external_id,
            podcast_title=recommendation.result.title,
            podcast_url=recommendation.result.url,
            target_language=language,
            learner_level=level,
            vocabulary=vocabulary,
            comprehension_questions=questions,
            discussion_prompt=discussion_prompt,
            introduction=introduction,
            metadata={
                "source": "podcast_recommendation",
                "provider": recommendation.result.provider.value,
                "challenge_type": "podcast_learning_mvp",
                "content_basis": "verified_podcast_metadata",
            },
        )

    def evaluate(
        self,
        *,
        challenge: PodcastLearningChallenge,
        answers: tuple[int, ...],
    ) -> ChallengeResult:
        """Evaluate comprehension answers without external side effects."""

        total = len(challenge.comprehension_questions)

        if len(answers) != total:
            raise ValueError(
                "Number of answers must equal the number of questions."
            )

        score = sum(
            answer == question.correct_option
            for answer, question in zip(
                answers,
                challenge.comprehension_questions,
            )
        )

        passed = score / total >= 0.5
        vocabulary_review_required = score < total

        if passed:
            message = (
                f"Challenge passed: {score}/{total}. "
                "Review the vocabulary and keep practising."
            )
        else:
            message = (
                f"Keep practising: {score}/{total}. "
                "Review the vocabulary and try again."
            )

        return ChallengeResult(
            challenge_id=challenge.challenge_id,
            user_id=challenge.user_id,
            score=score,
            total_questions=total,
            passed=passed,
            vocabulary_review_required=vocabulary_review_required,
            message=message,
        )
