# EasyChatBot Hackathon Architecture Alignment

Version: 1.0

Status: Architecture Baseline

Date: 2026

---

# 1. Purpose

This document defines the relationship between the EasyChatBot core platform and the EasyChatBot Hackathon implementation.

The Hackathon repository is not a separate product.

It is a public vertical slice demonstrating the core EasyChatBot architecture:

> EasyChatBot is an AI platform where governed AI agents create personalised AI companions and learning experiences.

The objective is to demonstrate a complete working experience while preserving architectural compatibility with the main EasyChatBot ecosystem.

---

# 2. Architecture Relationship

The relationship is:


EasyChatBot Core Platform
|
|
+-------------------------
|
v
EasyChatBot Hackathon

Public Demonstration Layer


The Hackathon implementation:

- follows the same architectural principles
- uses simplified implementations
- avoids private enterprise components
- demonstrates production-oriented design

---

# 3. Core Architecture Principles

The following principles are preserved:

## Separation of Responsibilities

Applications do not execute AI directly.

Preferred flow:


User

|

Application

|

AI Runtime

|

AI Agent

|

Provider Layer

|

Memory / Knowledge

|

Response


---

# 4. Component Mapping

| Hackathon Component | EasyChatBot Core Equivalent | Purpose |
|---|---|---|
| runtime | AI Runtime | Orchestration and lifecycle |
| agents | ai_agents framework | AI execution capabilities |
| characters | Character Studio | AI companion identity |
| providers | Provider Layer | External AI services |
| memory | Memory Services | Personalisation |
| evaluation | AI Quality Framework | Output assessment |
| frontend | Applications | User experience |

---

# 5. AI Runtime Alignment

The Runtime is the central orchestration layer.

Responsibilities:

- Receive requests
- Create execution context
- Select agents
- Apply policies
- Manage execution lifecycle
- Return structured results

Agents must never bypass the Runtime.

---

# 6. Agent Architecture Alignment

Agents follow the EasyChatBot principles:

Agents are:

- stateless where possible
- explicitly configured
- independently testable
- governed by policies

Agents do not:

- directly modify production systems
- directly access infrastructure
- create uncontrolled side effects

---

# 7. Agent Categories

The platform contains two main agent categories.

## User Experience Agents

Purpose:

Create personalised AI experiences.

Examples:

- Tutor Agent
- Conversation Agent
- Research Agent


## Internal Quality Agents

Purpose:

Improve platform reliability and governance.

Examples:

- Evaluation Agent
- Quality Review Agent
- Safety Agent

These two categories share the same agent framework but have different responsibilities.

---

# 8. Character Architecture

Characters represent AI companion identities.

A character contains:

- Identity
- Personality
- Behaviour
- Communication style
- Guardrails

Characters are configuration-driven.

The Hackathon implementation will reuse the same philosophy as the EasyChatBot Character System.

---

# 9. Provider Architecture

Providers are separated from agents.

Architecture:


Agent

|

Runtime

|

Provider Interface

|

External Provider


Examples:

- Gemini
- Parallel Search
- Future LLM providers
- Voice providers

The objective is provider independence.

---

# 10. Memory Architecture

Memory is divided into two concepts.

## Runtime Memory

Temporary execution information:

- current request
- workflow state
- execution context


## User Memory

Long-term personalisation:

- preferences
- interests
- learning progress
- previous interactions

---

# 11. Quality Framework Alignment

Quality evaluation is separated from execution.

Flow:


AI Response

|

Quality Framework

|

Evaluation Agents

|

Metrics

|

Improvement


The purpose is:

- measure quality
- detect issues
- improve user experience

---

# 12. Hackathon Scope

The Hackathon implementation focuses on:

- AI Runtime demonstration
- Agent execution
- Character interaction
- Gemini integration
- Parallel Search integration
- Memory demonstration
- Quality evaluation

---

# 13. Out of Scope

The following remain part of the main EasyChatBot platform:

- Enterprise administration
- Full governance repository
- Production operations centre
- Large-scale infrastructure
- Advanced autonomous workflows

---

# 14. Future Integration

After the Hackathon, successful components may be integrated into the main EasyChatBot platform.

Integration principles:

- Preserve interfaces
- Avoid duplication
- Maintain provider independence
- Keep security boundaries

The Hackathon repository demonstrates the architecture.

The main EasyChatBot platform remains the source of truth.

---

# Final Principle

The Hackathon project is not a prototype disconnected from the product.

It is the first public demonstration of the EasyChatBot ecosystem:

AI agents + AI runtime + knowledge + memory + characters + quality.