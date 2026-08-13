"""
EasyChatBot Hackathon — Podcast Learning Challenge presentation.
"""

from __future__ import annotations

from src.ai_runtime.podcast.challenge import (
    ChallengeResult,
    PodcastLearningChallenge,
)


class PodcastLearningChallengePresenter:
    """Render the learner-facing challenge for the hackathon demo."""

    def render(
        self,
        challenge: PodcastLearningChallenge,
    ) -> str:
        lines = [
            "",
            "=" * 72,
            "[PODCAST] PODCAST LEARNING CHALLENGE",
            "=" * 72,
            "",
            challenge.introduction,
            "",
            f"Podcast: {challenge.podcast_title}",
            f"Language: {challenge.target_language}",
            f"Level: {challenge.learner_level}",
            "",
            "[ LISTEN ]",
            f"  {challenge.podcast_url}",
            "",
            "VOCABULARY",
            "-" * 72,
        ]

        for index, item in enumerate(
            challenge.vocabulary,
            start=1,
        ):
            lines.extend(
                [
                    f"{index}. {item.term}",
                    f"   {item.meaning}",
                    f"   Example: {item.example}",
                    "",
                ]
            )

        lines.extend(
            [
                "COMPREHENSION",
                "-" * 72,
            ]
        )

        for index, question in enumerate(
            challenge.comprehension_questions,
            start=1,
        ):
            lines.append(f"{index}. {question.question}")
            for option_index, option in enumerate(
                question.options,
                start=1,
            ):
                lines.append(f"   {option_index}. {option}")
            lines.append("")

        lines.extend(
            [
                "DISCUSSION",
                "-" * 72,
                challenge.discussion_prompt,
                "",
            ]
        )

        return "\n".join(lines)

    def render_result(
        self,
        result: ChallengeResult,
    ) -> str:
        return "\n".join(
            [
                "",
                "CHALLENGE RESULT",
                "-" * 72,
                f"Score: {result.score}/{result.total_questions}",
                f"Status: {'PASS' if result.passed else 'REVIEW'}",
                result.message,
                (
                    "Vocabulary review: YES"
                    if result.vocabulary_review_required
                    else "Vocabulary review: NOT REQUIRED"
                ),
            ]
        )
