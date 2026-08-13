# Skill: Recommendation Explanation

**Skill ID:** discovery.recommendation_explanation
**Version:** 1.0
**Status:** Proposed / Beta 1

## Purpose

Explain why a discovered item was selected for a particular learner.

The core product questions are:

- Why this?
- Why now?
- Why for me?

## Inputs

- Ranked candidates
- Relevance evidence
- DiscoveryProfile
- Current learner request
- Freshness/source evidence

## Workflow

1. Read the candidate's actual evidence.
2. Select the strongest valid reasons.
3. Connect those reasons to explicit learner needs/preferences.
4. State freshness when relevant.
5. Avoid unsupported claims.
6. Produce a concise learner-facing explanation.

## Example

> I chose this podcast because you have been exploring AI regulation, it is available in French, and it is suitable for your current learning level.

## Decision rules

- Every stated reason must be supported by available evidence.
- Do not claim the learner likes something unless supported.
- Do not claim quality solely from popularity.
- Do not disguise advertising as neutral recommendation.
- Keep explanations concise.

## Success metrics

- Explanation factual accuracy
- Learner trust
- Recommendation acceptance
- Explanation usefulness
