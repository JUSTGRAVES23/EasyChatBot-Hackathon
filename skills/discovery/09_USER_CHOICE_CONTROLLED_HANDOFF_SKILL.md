# Skill: User Choice & Controlled Handoff

**Skill ID:** discovery.user_choice_controlled_handoff
**Version:** 1.0
**Status:** Proposed / Beta 1

## Purpose

Keep the learner in control after discovery and recommendation, especially for products or other consequential external actions.

## Core principle

AI recommends → User decides → Controlled service executes

## Activate when

- A learner selects a recommendation.
- A product requires external checkout.
- An external service/action is requested.
- A recommendation needs an explicit next step.

## Workflow

1. Present the recommendation and relevant explanation.
2. Clearly distinguish recommendation from action.
3. Wait for explicit learner choice where required.
4. Validate the selected item/action.
5. Hand off only to an approved controller/service.
6. Never bypass Runtime or policy controls.
7. Return the controlled result.

## Decision rules

- Discovery does not imply permission to act.
- Never purchase automatically.
- Never submit irreversible actions without required confirmation/approval.
- Never expose credentials.
- User choice must remain explicit for consequential actions.

## Product boundary

The Discovery Agent can:

- discover
- compare
- rank
- explain
- provide an approved handoff

The Discovery Agent cannot directly:

- make purchases
- modify payment information
- execute financial transactions
- create uncontrolled external side effects

## Output

A controlled handoff request or a learner-facing next-step response.

## Success metrics

- Correct handoff rate
- Unauthorised-action rate
- User confirmation rate
- Handoff failure rate
