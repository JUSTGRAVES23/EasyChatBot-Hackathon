# Architecture Boundary

This repository is a standalone demonstration.

The LLMService exists here as an application execution
boundary because the production AI Runtime repository is
not included.

In the production EasyChatBot platform, this responsibility
will be provided by the AI Runtime execution layer.

The hackathon implementation intentionally preserves:

- provider independence
- dependency injection
- agent/provider separation
- testability

while remaining independently executable.