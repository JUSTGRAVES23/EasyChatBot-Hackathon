# Hackathon Vertical Slice

## Objective

Demonstrate an AI French tutor capable of
using current information to create personalised
learning content.

---

## User Story

As a French learner,

I want to ask:
"Teach me French using today's AI news"

So that:

I receive:
- explanation
- vocabulary
- exercise
- feedback

---

## Demo Capability

live_intelligence_learning

---

## API Entry Point

POST /chat

or

POST /runtime/execute

---

## Runtime Capability

live_intelligence

---

## Provider

Gemini / approved search provider

---

## Acceptance Criteria

Given a user request

When the system receives:

"Teach me French using today's AI news"

Then:

1. Runtime receives request
2. Capability executes
3. Provider returns information
4. AI generates lesson
5. Response returned