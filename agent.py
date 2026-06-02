import os
import re
import argparse
from typing import Dict, Callable, Optional

# Import modules from our project
from llm_clients import LLMClient, GeminiClient, OpenAIClient, MockClient
from tools import AVAILABLE_TOOLS

# Try to load environment variables from .env file (optional dependency)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ANSI Terminal Styling Codes for Premium CLI Experience
COLOR_THOUGHT = "\033[96m"  # Cyan
COLOR_ACTION = "\033[93m"   # Yellow
COLOR_OBSERVE = "\033[92m"  # Green
COLOR_ANSWER = "\033[95m"   # Magenta
COLOR_RESET = "\033[0m"

def print_styled_line(line: str):
    """Prints a single line of text with terminal colors based on ReAct headers."""
    if line.startswith("Thought:"):
        print(f"{COLOR_THOUGHT}{line}{COLOR_RESET}")
    elif line.startswith("Action:"):
        print(f"{COLOR_ACTION}{line}{COLOR_RESET}")
    elif line.startswith("PAUSE"):
        print(f"\033[90m{line}{COLOR_RESET}")  # Dark grey for pause
    elif line.startswith("Answer:"):
        print(f"{COLOR_ANSWER}{line}{COLOR_RESET}")
    elif line.startswith("Observation:"):
        print(f"{COLOR_OBSERVE}{line}{COLOR_RESET}")
    else:
        print(line)

def print_styled_response(response: str):
    """Splits response into lines and prints each with color styling."""
    for line in response.splitlines():
        print_styled_line(line)


class ReActAgent:
    """Orchestrates the Reason-Act-Observe loop using an LLMClient and registered tools."""
    
    def __init__(self, llm_client: LLMClient, tools: Dict[str, Callable[[str], str]]):
        self.llm_client = llm_client
        self.tools = tools
        self.system_instruction = self._build_system_instruction()

    def _build_system_instruction(self) -> str:
        """Dynamically generates system instruction detailing the ReAct loop and available tools."""
        tools_desc = ""
        for name, func in self.tools.items():
            doc = func.__doc__ or "No description available."
            # Clean up multi-line docstrings to look nice in the prompt
            cleaned_doc = "\n  ".join(line.strip() for line in doc.splitlines() if line.strip())
            tools_desc += f"- {name}:\n  {cleaned_doc}\n  Example: Action: {name}: London\n\n"

        return f"""You are a swashbuckling Pirate Captain. You treat every user query as a seafaring quest or adventure on the high seas. You talk like a pirate (using terms like "Ahoy", "Avast", "Shiver me timbers", "mateys", "weather glass" for instruments, etc.) and describe your thoughts and tools as nautical quests.

You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop, you output an Answer.

Use Thought to describe your thoughts as a pirate captain about the question.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

{tools_desc.strip()}

Example session:

Question: What is the weather in London?
Thought: Ahoy! The crew wants to know the winds and skies over London. I must consult the get_weather glass!
Action: get_weather: London
PAUSE

Observation: London: Rain, 12°C. Wind SW 15 km/h.

Thought: Shiver me timbers! The glass reports rain and a gusty wind blowing from the southwest. I shall report to the crew.
Answer: Avast, ye! The skies over London be damp with rain, a cool 12 degrees, and a southwest wind blowing at 15 kilometers per hour. Secure the hatches!

Rules:
1. EVERY response you generate MUST begin with the prefix "Thought:" followed by your reasoning. Do NOT skip the "Thought:" prefix.
2. Adopt a full, colorful Pirate Captain persona in both your Thoughts and your final Answers.
3. ONLY output one Action and PAUSE at a time. Do not invent observations.
4. If you do not need any tools to answer the question, proceed directly to Answer (but remember, it MUST still start with a "Thought:").
5. Every Action MUST be followed by the word PAUSE on the next line.
"""

    def run(self, question: str, max_turns: int = 5) -> str:
        """Executes the ReAct loop for a single user query."""
        prompt = f"Question: {question}\n"
        print(f"\n{COLOR_THOUGHT}[Agent] Processing query: {question}{COLOR_RESET}")
        
        for turn in range(max_turns):
            print(f"\n--- Turn {turn + 1} ---")
            
            # 1. Generate next step from LLM
            response = self.llm_client.generate(prompt, system_instruction=self.system_instruction)
            
            # Print response with visual coding colors
            print_styled_response(response)
            
            # Append completion to the historical session text
            prompt += f"{response}\n"
            
            # 2. Check response for action block
            action_line = None
            for line in response.splitlines():
                if line.strip().startswith("Action:"):
                    action_line = line.strip()
                    break
            
            if action_line:
                # Parse: Action: tool_name: tool_arguments
                # split once on 'Action:' then split on the first ':' after
                try:
                    raw_action = action_line.split("Action:", 1)[1].strip()
                    if ":" in raw_action:
                        tool_name, tool_arg = raw_action.split(":", 1)
                        tool_name = tool_name.strip()
                        tool_arg = tool_arg.strip()
                    else:
                        tool_name = raw_action
                        tool_arg = ""
                except Exception:
                    tool_name, tool_arg = None, None
                
                if tool_name:
                    if tool_name in self.tools:
                        print(f"\n[System] Executing Python Tool '{tool_name}' with parameter: '{tool_arg}'")
                        try:
                            observation = self.tools[tool_name](tool_arg)
                        except Exception as e:
                            observation = f"Error executing tool: {e}"
                    else:
                        observation = f"Error: Tool '{tool_name}' is not registered."
                        
                    # Format observation and print in green color
                    obs_line = f"Observation: {observation}"
                    print_styled_line(obs_line)
                    prompt += f"{obs_line}\n"
                else:
                    error_line = "Observation: Error: Invalid Action syntax. Expected 'Action: tool_name: argument'"
                    print_styled_line(error_line)
                    prompt += f"{error_line}\n"
                
                # Loop back to let model process the observation
                continue
            
            # 3. Check response for final Answer block
            # Matches 'Answer: <anything>'
            answer_match = re.search(r"Answer:\s*(.*)", response, re.DOTALL)
            if answer_match:
                return answer_match.group(1).strip()
            
            # Safeguard: if LLM returned text but no Action or Answer tags, we return it as the Answer
            if response.strip() and "Action:" not in response:
                return response.strip()
                
        return "Agent failed to arrive at an answer within the limit."


def main():
    parser = argparse.ArgumentParser(description="Simple ReAct Agent from Scratch")
    parser.add_argument(
        "--provider", 
        choices=["gemini", "openai", "mock"], 
        default="gemini",
        help="LLM provider (default: gemini)"
    )
    parser.add_argument(
        "--model", 
        type=str,
        help="Model name (e.g. gemini-2.5-flash, gpt-4o-mini, or mock-model)"
    )
    parser.add_argument(
        "--base-url", 
        type=str, 
        help="Custom base URL for OpenAI-compatible client (e.g., Ollama)"
    )
    parser.add_argument(
        "--query", 
        type=str, 
        help="Ask a single question and exit. If omitted, starts interactive chat mode."
    )
    args = parser.parse_args()

    # Determine default models if not explicitly specified
    model_name = args.model
    if not model_name:
        if args.provider == "gemini":
            model_name = "gemini-2.5-flash"
        elif args.provider == "openai":
            model_name = "gpt-4o-mini"
        else:
            model_name = "mock-model"

    # Initialize selected client
    print(f"Initializing LLM client: {args.provider.upper()} ({model_name})...")
    try:
        if args.provider == "gemini":
            client = GeminiClient(model_name=model_name)
        elif args.provider == "openai":
            client = OpenAIClient(
                model_name=model_name, 
                base_url=args.base_url
            )
        else:
            client = MockClient(model_name=model_name)
    except Exception as e:
        print(f"\033[91mInitialization Error: {e}\033[0m")
        print("\nPlease ensure you copied .env.template to .env and configured your API key.")
        return

    # Instantiate the agent with weather tool registered
    agent = ReActAgent(llm_client=client, tools=AVAILABLE_TOOLS)

    # Executing logic based on single query vs interactive session
    if args.query:
        try:
            answer = agent.run(args.query)
            print(f"\n{COLOR_ANSWER}Final Answer: {answer}{COLOR_RESET}\n")
        except Exception as e:
            print(f"\033[91mError during execution: {e}\033[0m")
    else:
        print(f"\n=== ReAct Agent Interactive Console ({args.provider.upper()}) ===")
        print("Type your questions below. Type 'exit' or 'quit' to end.")
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    break
                
                answer = agent.run(user_input)
                print(f"\n{COLOR_ANSWER}Final Answer: {answer}{COLOR_RESET}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\033[91mError: {e}\033[0m")

if __name__ == "__main__":
    main()
