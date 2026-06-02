# ADR 0002: Classic Text-Based ReAct Loop Parsing

## Status
Proposed

## Context
Modern LLM APIs support native function/tool calling, which returns structured JSON actions. However, we are building a simple Python AI agent *from scratch* to understand how they work. We had to decide between:
1. Standard model-native function calling APIs (e.g., Gemini's tools/declarations, OpenAI's tool calls).
2. Classic text-based parsing using a system prompt that directs the model to output a specific format (e.g., `Thought: ...`, `Action: tool_name: arguments`, `Observation: ...`).

## Decision
We will implement the classic text-based prompting and regex/text parsing for the ReAct loop.

## Consequences
- **Pros**:
  - Highly educational: Decouples the agent logic from specific API capabilities, showing exactly how prompt engineering guides agent reasoning.
  - Universal compatibility: Works on any LLM that can generate text, including lightweight local models (e.g., Llama/Mistral via Ollama) and basic endpoints that don't support native tool calling.
  - Transparent execution log: The entire thought process and tool execution sequence are visible as a single continuous transcript/history.
- **Cons**:
  - Less robust than native function calling: The model might occasionally format the action incorrectly, requiring parsing safeguards or retries. We will design simple, clear formatting rules in the system prompt to minimize this.
