# Skill: Recommendation Ranking

**Skill ID:** discovery.recommendation_ranking
**Version:** 1.0
**Status:** Proposed / Beta 1

## Purpose

Rank relevant discovery candidates so the learner receives a small, useful set rather than an overwhelming search result list.

## Inputs

- Relevance assessments
- Candidate quality signals
- Learner preferences
- Requested result count
- Diversity requirements

## Ranking factors

1. Hard-constraint satisfaction
2. Relevance
3. Source/content quality
4. Freshness where applicable
5. Preference alignment
6. Learning suitability
7. Novelty/diversity
8. Duplicate avoidance

## Workflow

1. Remove candidates that fail mandatory constraints.
2. Compare remaining relevance assessments.
3. Apply quality and freshness signals.
4. Avoid near-duplicate recommendations.
5. Preserve useful diversity.
6. Select the top candidates.
7. Pass ranked candidates to Recommendation Explanation.

## Decision rules

- Ranking must remain explainable.
- Do not optimise only for popularity.
- Do not hide material conflicts with learner preferences.
- Product ranking must not imply endorsement beyond the available evidence.

## Output

An ordered candidate list with ranking evidence.

## Success metrics

- Recommendation acceptance
- Top-N relevance
- Diversity
- Duplicate rate
- Learner satisfaction
