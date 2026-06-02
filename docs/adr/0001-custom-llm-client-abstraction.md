# ADR 0001: Custom LLM Client Abstraction Layer

## Status
Proposed

## Context
We want to support multiple LLM providers (e.g., Gemini, OpenAI, Anthropic) so the user can use models from any other company.
We have multiple options:
1. Use a unified third-party library like `litellm`.
2. Direct API integration inside the Agent logic with conditional checks.
3. Build a custom, lightweight `LLMClient` interface and adapter classes from scratch.

## Decision
We will build a custom, lightweight `LLMClient` interface and provider-specific adapter classes (`GeminiClient`, `OpenAIClient`, etc.) from scratch in Python.

## Consequences
- **Pros**:
  - Educational clarity: Stays true to the "from scratch" philosophy, making it easy to see exactly how requests, payloads, system prompts, and responses are formatted for each LLM provider.
  - Zero heavy third-party agent/LLM-wrapper dependencies (like langchain or litellm).
  - Simple, easily readable codebase.
- **Cons**:
  - Adding a brand-new model provider requires writing a new adapter class mapping to their specific SDK (though this is simple and follows a clear interface).
