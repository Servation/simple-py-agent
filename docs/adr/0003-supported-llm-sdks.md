# ADR 0003: Supported LLM SDKs and Compatibility

## Status
Proposed

## Context
We want our ReAct agent to run on models from multiple providers (e.g. Gemini, OpenAI, Anthropic, Ollama, DeepSeek). Installing individual SDKs for every single provider would bloat dependencies and complicate configuration. We need to decide which client adapters to include.

## Decision
We will ship with two concrete LLM clients:
1. `GeminiClient` utilizing the `google-genai` SDK.
2. `OpenAIClient` utilizing the `openai` SDK.

The `OpenAIClient` will be designed with configurable parameters (`api_key` and `base_url`).

## Consequences
- **Pros**:
  - Broad coverage: The OpenAI client can act as a generic adapter for any OpenAI-compatible API endpoint (such as local Ollama, Groq, DeepSeek, OpenRouter, and local Llama.cpp servers).
  - Minimal dependency footprint: We only need `google-genai` and `openai` libraries in our `requirements.txt`.
  - Simple client switching: Users can switch models by passing a different client class or setting a few environment variables.
- **Cons**:
  - Anthropic (Claude) is not natively supported out-of-the-box via its own SDK, but can be accessed if the user routes it through an OpenAI-compatible proxy (like OpenRouter) or writes a small Anthropic client adapter.
