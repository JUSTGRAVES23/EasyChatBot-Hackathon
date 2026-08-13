"""
EasyChatBot Hackathon — personalised podcast recommendation service.

This is the application-level selection boundary.

Language is a HARD filter because EasyChatBot is a language-learning
platform. Preference/topic relevance is evaluated only after a candidate
is language-eligible.
"""

from __future__ import annotations

import re
from uuid import uuid4

from src.ai_runtime.podcast.models import (
    PodcastRecommendation,
    PodcastSearchIntent,
    PodcastSearchResult,
    normalise_language,
)
from src.ai_runtime.podcast.providers import PodcastProvider


class PodcastRecommendationService:
    """Search providers and select a personalised candidate."""

    def __init__(self, providers: list[PodcastProvider]) -> None:
        if not providers:
            raise ValueError(
                "PodcastRecommendationService requires at least one provider."
            )
        self._providers = list(providers)

    def recommend(
        self,
        *,
        intent: PodcastSearchIntent,
        character_id: str,
        character_name: str,
        character_message: str,
    ) -> PodcastRecommendation:
        candidates: list[PodcastSearchResult] = []

        for provider in self._providers:
            candidates.extend(provider.search(intent))

        ranked = self.rank_candidates(
            candidates=candidates,
            intent=intent,
        )

        if not ranked:
            raise LookupError(
                "No podcast matched the learner's language and preferences."
            )

        result, score, reason = ranked[0]

        return PodcastRecommendation(
            recommendation_id=str(uuid4()),
            user_id=intent.user_id,
            character_id=character_id,
            character_name=character_name,
            character_message=character_message,
            result=result,
            relevance_reason=reason,
            match_score=score,
        )

    @classmethod
    def rank_candidates(
        cls,
        *,
        candidates: list[PodcastSearchResult],
        intent: PodcastSearchIntent,
    ) -> list[tuple[PodcastSearchResult, float, str]]:
        ranked: list[tuple[PodcastSearchResult, float, str]] = []

        target_language = normalise_language(
            intent.learning_context.target_language
        )

        preference_terms = [
            term.lower()
            for term in list(intent.topics) + list(intent.keywords)
            if term.strip()
        ]

        for candidate in candidates:
            candidate_languages = {
                normalise_language(language)
                for language in candidate.languages
            }

            # Critical learning-platform rule:
            # unknown/wrong-language content is not eligible.
            if (
                intent.language_required
                and target_language not in candidate_languages
            ):
                continue

            haystack = " ".join(
                [
                    candidate.title,
                    candidate.description,
                    candidate.publisher,
                ]
            ).lower()

            matched_terms = [
                term
                for term in preference_terms
                if cls._term_matches(term, haystack)
            ]

            score = 50.0

            if matched_terms:
                score += min(30.0, len(matched_terms) * 10.0)

            if intent.learning_context.world_id.lower() in haystack:
                score += 10.0

            level = intent.learning_context.learner_level.lower()
            if level and level in haystack:
                score += 10.0

            reason = cls._build_reason(
                language=intent.learning_context.target_language,
                matched_terms=matched_terms,
                world_id=intent.learning_context.world_id,
            )

            ranked.append(
                (candidate, min(score, 100.0), reason)
            )

        ranked.sort(
            key=lambda item: (
                item[1],
                item[0].published_at or "",
            ),
            reverse=True,
        )

        return ranked[: intent.max_results]

    @staticmethod
    def _term_matches(term: str, haystack: str) -> bool:
        term = term.strip().lower()
        if not term:
            return False
        if term in haystack:
            return True

        words = [
            word
            for word in re.findall(r"[a-z0-9À-ÿ'-]+", term)
            if len(word) > 2
        ]
        return bool(words) and any(
            word in haystack
            for word in words
        )

    @staticmethod
    def _build_reason(
        *,
        language: str,
        matched_terms: list[str],
        world_id: str,
    ) -> str:
        reasons = [f"It is available in {language}."]

        if matched_terms:
            reasons.append(
                "It matches your interests in "
                + ", ".join(matched_terms[:3])
                + "."
            )

        reasons.append(
            f"It fits your {world_id} learning world."
        )

        return " ".join(reasons)
