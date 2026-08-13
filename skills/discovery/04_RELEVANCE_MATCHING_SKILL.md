# Skill: Relevance Matching

**Skill ID:** discovery.relevance_matching
**Version:** 1.0
**Status:** Proposed / Beta 1

## Purpose

Determine how well each discovered candidate matches the learner's current interests, constraints and learning context.

## Core question

**Why is this candidate relevant to this learner?**

## Inputs

- DiscoveryProfile
- DiscoveryQuery
- Candidate collection
- Current learner request
- Relevant learning context

## Matching dimensions

- Topic match
- Explicit preference match
- Language match
- Learning-level match
- Content/product type match
- Recency
- Quality signals
- Duplicate/novelty signals

## Workflow

1. Evaluate each candidate against the DiscoveryProfile.
2. Separate hard constraints from preference signals.
3. Identify positive matches.
4. Identify mismatches.
5. Produce structured relevance evidence.
6. Return a relevance assessment to Recommendation Ranking.

## Output

Example:

```yaml
candidate_id: item-123
match_score: 0.93
matched_preferences:
  - artificial intelligence
  - French
  - B2
reasons:
  - matches current AI interest
  - suitable language
  - suitable learning level
mismatches: []
```

## Decision rules

- Relevance is not the same as popularity.
- A high score must be explainable.
- Hard constraints should not be silently ignored.
- Do not fabricate reasons for a match.

## Success metrics

- Human-rated relevance
- Recommendation acceptance rate
- False-positive recommendation rate
- Explanation accuracy
