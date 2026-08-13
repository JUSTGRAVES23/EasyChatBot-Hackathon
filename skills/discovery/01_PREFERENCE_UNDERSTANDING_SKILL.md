# Skill: Preference Understanding

**Skill ID:** discovery.preference_understanding
**Version:** 1.0
**Status:** Proposed / Beta 1

## Purpose

Transform explicit learner preferences and approved contextual signals into a structured discovery profile that can be used by the Discovery Agent.

The skill determines what the learner is interested in, how they prefer to consume content, and which constraints should influence discovery.

## Activate when

- A discovery request is received.
- The learner provides or changes a preference.
- Existing approved preferences are relevant to discovery.
- A recommendation needs personalisation.

## Do not use when

- No discovery or personalisation is required.
- The information is not authorised for discovery use.
- The signal is too ambiguous to justify a persistent preference.

## Inputs

- Current learner request
- Approved learner preferences
- Relevant MemoryContext
- Current learning context, where available
- Requested content/product type
- Explicit constraints

## Outputs

A structured DiscoveryProfile containing only relevant and permitted signals.

Example:

```yaml
topics:
  - artificial intelligence
  - European regulation

content_types:
  - podcasts
  - news

languages:
  - French

learning_level:
  - B2

explicit_constraints: []
```

## Workflow

1. Read the current request.
2. Identify explicit preferences.
3. Retrieve relevant approved contextual preferences.
4. Distinguish explicit preferences from inferred signals.
5. Resolve conflicts in favour of the most recent explicit learner instruction.
6. Produce a bounded DiscoveryProfile.
7. Pass the profile to Discovery Query Generation.

## Decision rules

- Explicit learner preferences take priority over inferred preferences.
- Do not invent preferences.
- Do not convert a one-off request into a permanent preference without an approved memory workflow.
- Do not use unrelated memory.
- Keep sensitive or restricted information outside the profile unless explicitly authorised by policy.

## Common failure modes

- Treating every interaction as a permanent preference.
- Using irrelevant memory.
- Over-personalising.
- Confusing content preference with topic interest.

## Security

The skill only consumes approved learner context. It does not directly read arbitrary data stores.

## Success metrics

- Preference extraction accuracy
- Explicit-vs-inferred classification accuracy
- Recommendation relevance improvement
- Incorrect personalisation rate
