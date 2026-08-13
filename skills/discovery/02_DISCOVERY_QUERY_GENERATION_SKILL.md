# Skill: Discovery Query Generation

**Skill ID:** discovery.query_generation
**Version:** 1.0
**Status:** Proposed / Beta 1

## Purpose

Convert the learner's request and DiscoveryProfile into structured search criteria suitable for approved discovery tools.

## Activate when

A discovery operation requires external or indexed content/product retrieval.

## Inputs

- Learner request
- DiscoveryProfile
- Requested content/product type
- Language
- Learning level, where relevant
- Recency requirements
- Geographic or commercial constraints, where relevant

## Outputs

A structured DiscoveryQuery.

Example:

```yaml
content_type: podcast
topics:
  - artificial intelligence
  - European regulation
language: French
level: B2
recency: recent
```

## Workflow

1. Identify the discovery objective.
2. Convert preferences into searchable concepts.
3. Separate mandatory constraints from ranking preferences.
4. Add appropriate content-type constraints.
5. Add language and learning-level constraints where relevant.
6. Apply recency only when useful or requested.
7. Produce the structured query.
8. Pass it to Content/Product Discovery.

## Decision rules

- Preserve explicit constraints.
- Do not over-constrain searches unnecessarily.
- Do not add unsupported preferences.
- Search criteria must remain provider-independent.
- Provider-specific query syntax belongs in the Tool/Provider layer.

## Common failure modes

- Producing vague queries.
- Embedding provider-specific implementation logic.
- Treating ranking preferences as hard filters.
- Losing the learner's original intent.

## Success metrics

- Search precision
- Search recall
- Constraint preservation
- Useful candidate rate
