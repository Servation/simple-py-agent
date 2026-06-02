# Simple ReAct Agent from Scratch

A simple, educational, and modular Python AI agent built from scratch to demonstrate the **ReAct (Reason, Act, Observe)** loop pattern. 

This agent is model-agnostic, supporting Google Gemini, OpenAI, and local/compatible endpoints (like Ollama, DeepSeek, or Groq) using a custom client adapter layer, and includes a live weather tool that fetches real-time data.

---

## Features

- **Model Agnostic**: Choose between Gemini, OpenAI, or local models using a unified client abstraction.
- **Offline Mock Mode**: Verify the ReAct loop, tool call parsing, and terminal coloring without any API keys or network connection.
- **Live Weather API**: Fetches real-time weather data dynamically from the free `wttr.in` service using standard library `urllib` (no keys required!).
- **Safe Rendering**: Emojis and direction arrows are stripped automatically to prevent Windows console Unicode crashes.
- **Stop Sequences Guardrail**: Uses API stop sequences (`PAUSE` and `Observation:`) to force local models to stop generating and prevent runaway hallucinations.
- **Premium Terminal Styling**: Prints the agent's thought processes using ANSI color-coding (Thoughts in Cyan, Actions in Yellow, Observations in Green, Answers in Magenta).
- **Pirate Persona**: Built-in swashbuckling Pirate Captain character rules.

---

## Project Structure

```text
d:\simple-agent\
├── agent.py            # Core ReAct loop parser & interactive CLI
├── llm_clients.py      # Abstract LLMClient base and provider adapters
├── tools.py            # Live weather fetching tool using wttr.in
├── requirements.txt    # Python dependencies
├── .env.template       # Environment variables template
├── .gitignore          # Ignores .venv, .env, and compiled files
├── CONTEXT.md          # Domain glossary terms
└── docs/
    └── adr/            # Architectural Decision Records (ADRs 0001 - 0003)
```

---

## Installation & Setup

1. **Verify Python**: Ensure you have Python 3.10+ installed.
2. **Install Dependencies**: Choose one of the following:
   - **System-level User Install (Recommended on Windows)**:
     ```powershell
     pip install -r requirements.txt --user
     ```
   - **Virtual Environment Install**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\pip install -r requirements.txt
     ```
3. **Configure Keys**: Copy `.env.template` to a new file named `.env`:
   ```powershell
   copy .env.template .env
   ```
   Open `.env` and fill in your `GEMINI_API_KEY` (from Google AI Studio) or your `OPENAI_API_KEY` if using commercial models.

---

## How to Run

You can run the agent in single-query mode using `--query` or in interactive console mode.

### 1. Offline Mock Mode (No API keys required)
Test the entire ReAct loop, tool extraction, and console colors completely offline:
```powershell
python agent.py --provider mock --query "What is the weather in Tokyo?"
```

### 2. Live Gemini Mode
Query the live Google Gemini model:
```powershell
python agent.py --provider gemini --query "What is the weather in Visalia?"
```

### 3. Local LLM Mode (Ollama)
Connect to a local model (like Gemma 2 2B or Llama 3) running on Ollama:
```powershell
# 1. Pull the model first
ollama pull gemma2:2b

# 2. Run the agent pointing to Ollama's local port
python agent.py --provider openai --model gemma2:2b --base-url http://localhost:11434/v1
```

### ⚠️ Notes on Smaller / Local Models

Smaller local models (such as `gemma2:2b` or `llama3:8b`) can struggle with strict formatting in agent loops:
- **Missing PAUSE / Runaway Generation**: They often forget to stop generating output after declaring an action. Instead of halting for Python to run, they keep talking, hallucinate their own tool observations, and eventually time out.
- **How we fixed it (Stop Sequences)**: We configured `stop=["PAUSE", "Observation:"]` in `llm_clients.py`. This instructs the LLM server (like Ollama) to physically terminate the text generation the millisecond the model finishes declaring an `Action`, forcing it to hand control back to our Python tools.
- **Model Recommendations**: While 2B models are fast for testing, **7B to 9B instruct models** (like `gemma2:9b` or `llama3:8b`) offer significantly more stable instruction-following and reasoning behavior.

---

## Extending the Agent

### Adding a New Tool
1. Define a standard Python function in `tools.py`.
2. Give it a clear docstring explaining what it does (the agent's system prompt compiles this dynamically to teach the LLM).
3. Add it to the `AVAILABLE_TOOLS` dictionary at the bottom of the file:
   ```python
   def reverse_string(text: str) -> str:
       """Reverses a given text string.
       
       Args:
           text: The text to reverse (e.g. hello).
       """
       return text.strip()[::-1]

   AVAILABLE_TOOLS = {
       "get_weather": get_weather,
       "calculate": calculate,
       "reverse_string": reverse_string
   }
   ```

### Changing the Persona
Open `agent.py` and modify the system instructions generated in the `_build_system_instruction` method of the `ReActAgent` class to define a different character (e.g., Cyberpunk Hacker, Steampunk Inventor, or helpful assistant).
