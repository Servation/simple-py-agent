# Domain Context

This project is a simple, educational Python AI agent built from scratch to demonstrate the **ReAct (Reason, Act, Observe)** pattern. It is designed to be model-agnostic, supporting multiple LLM providers (e.g., Google, OpenAI, Anthropic, or local models via Ollama) through a custom lightweight abstraction layer.

## Glossary

### LLM Client
An abstraction wrapper that standardizes calls to different LLM providers. It translates the conversation history and prompt into the specific API payload required by the selected provider and returns a unified text completion.

### ReAct Loop
The orchestrating loop executed by the Agent. It consists of the following phases:
1. **Thought**: The model reasons about the prompt and decides how to proceed.
2. **Action**: The model triggers a registered tool using a structured format.
3. **Observe**: The system runs the tool and returns the result (the Observation).
4. **Answer**: The model provides the final response once it has gathered sufficient information.

### Agent
The core software entity that holds the system instructions, maintains the conversation history (memory), invokes the LLM Client, parses the LLM output for Actions, runs the appropriate Tool, and appends the Observation back into memory.

### Tool
A Python function registered with the Agent that executes specific logic (e.g., fetching weather, looking up database records) and returns a string representation of its result as an Observation.
