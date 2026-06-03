import os
from abc import ABC, abstractmethod
from typing import Optional

class LLMClient(ABC):
    """Abstract Base Class defining the interface for LLM interaction."""
    
    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Sends a prompt to the LLM and returns the generated text response.
        
        Args:
            prompt: The user prompt or conversation history to send to the model.
            system_instruction: The instructions guiding the model's persona/behavior (system prompt).
            
        Returns:
            The text response from the model.
        """
        pass


class GeminiClient(LLMClient):
    """Client for Google Gemini models using the google-genai SDK."""
    
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "The 'google-genai' package is not installed. "
                "Please run: pip install google-genai"
            )
            
        # If API key is not provided, the SDK will look for GEMINI_API_KEY environment variable.
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please set GEMINI_API_KEY in your .env file "
                "or pass it directly to the GeminiClient constructor."
            )
            
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.types = types

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        config = None
        if system_instruction:
            config = self.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,  # Zero temperature is critical for reliable tool calling/parsing
                stop_sequences=["PAUSE", "Observation:"]
            )
        else:
            config = self.types.GenerateContentConfig(
                temperature=0.0,
                stop_sequences=["PAUSE", "Observation:"]
            )
            
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return response.text or ""
        except Exception as e:
            raise RuntimeError(f"Error calling Gemini API: {e}")


class OpenAIClient(LLMClient):
    """Client for OpenAI and OpenAI-compatible APIs (like Ollama, DeepSeek, Groq) using the openai SDK."""
    
    def __init__(
        self, 
        model_name: str = "gpt-4o-mini", 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' package is not installed. "
                "Please run: pip install openai"
            )
            
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        
        # Ollama local setup doesn't strictly require a real API key, but the SDK expects a non-empty string.
        if not self.api_key and not self.base_url:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file "
                "or pass it directly to the OpenAIClient constructor."
            )
            
        self.client = OpenAI(
            api_key=self.api_key or "dummy_key",
            base_url=self.base_url
        )
        self.model_name = model_name

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,  # Zero temperature for deterministic parsing
                stop=["PAUSE", "Observation:"]
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Error calling OpenAI-compatible API: {e}")


class MockClient(LLMClient):
    """A mock LLM client for testing the ReAct loop without API keys."""
    
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        # Check if the prompt contains the observation from get_weather for London and Tokyo (multiple checks)
        if "Observation:" in prompt and "london" in prompt.lower() and "tokyo" in prompt.lower():
            # Extract observations
            obs_lines = [line.replace("Observation:", "").strip() for line in prompt.splitlines() if line.strip().startswith("Observation:")]
            obs_str = " and ".join(obs_lines)
            return f"""Thought: Shiver me timbers! I have the weather glass reports for both ports: {obs_str}. Let's compare these waters.
Answer: Avast! Here is how the seas compare: {obs_str}."""
            
        elif "Observation:" in prompt and "tokyo" in prompt.lower():
            # Extract the last observation line
            obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
            return f"""Thought: Shiver me timbers! The glass reports: {obs}. I shall relay this to the mateys.
Answer: Ahoy! The winds and skies of Tokyo report: {obs}. Trim the sails and ready the anchors!"""
        
        elif "Observation:" in prompt and "london" in prompt.lower():
            # Extract the last observation line
            obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
            return f"""Thought: Shiver me timbers! The glass reports: {obs}. I shall relay this to the mateys.
Answer: Ahoy! The winds and skies of London report: {obs}. Prepare the storm sails!"""


        # Clock tool mock query
        elif "time" in prompt.lower() or "clock" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Shiver me timbers! The clock reports: {obs}.
Answer: Ahoy! The local time in that harbor is: {obs}."""
            else:
                return """Thought: Ahoy! The traveler wants to know the time of day. I must check the ship's clock!
Action: get_system_time: 0
PAUSE"""

        # Wikipedia tool mock query
        elif "wikipedia" in prompt.lower() or "search" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Shiver me timbers! The records state: {obs}.
Answer: Avast! Here is what Wikipedia knows about that topic: {obs}."""
            else:
                topic = "Blackbeard" if "blackbeard" in prompt.lower() else "Piracy"
                return f"""Thought: Ahoy! The crew wants to look up records on '{topic}'. I must search the Wikipedia archives!
Action: search_wikipedia: {topic}
PAUSE"""

        # Log write tool mock query
        elif "log entry:" in prompt.lower() or "write to ship's log" in prompt.lower() or "log We spotted" in prompt:
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Ahoy! The entry has been saved in the log: {obs}.
Answer: I have written your entry in the ship's log book, Captain!"""
            else:
                return """Thought: The Captain wishes to write an entry in the log. I will deploy the writing quill!
Action: write_ships_log: We spotted a merchant ship
PAUSE"""

        # Log read tool mock query
        elif "read the ship's log" in prompt.lower() or "read log" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Shiver me timbers! Here is the historical log contents: {obs}.
Answer: Ahoy, Captain! Here is the ship's log book entries: \n{obs}"""
            else:
                return """Thought: The Captain wants to read the ship's log. I must fetch the log book!
Action: read_ships_log: 
PAUSE"""

        # Translator tool mock query
        elif "translate:" in prompt.lower() or "pirate slang" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Shiver me timbers! The translation is complete: {obs}.
Answer: Avast! The translated phrase reads: "{obs}"."""
            else:
                return """Thought: The traveler wants to translate words into the pirate tongue. I must consult the dialect dictionary!
Action: translate_to_pirate: Hello friend, yes indeed
PAUSE"""

        # List files mock query
        elif "list files" in prompt.lower() or "list directory" in prompt.lower() or "folder" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Shiver me timbers! The list of items in our harbor is: {obs}.
Answer: Ahoy, Captain! Here be the files in our harbor: \n{obs}"""
            else:
                return """Thought: The Captain wishes to see what cargo is in the folder. I must inspect the directory!
Action: list_directory: 
PAUSE"""

        # Write file mock query
        elif "write '" in prompt.lower() or "write file" in prompt.lower() or "to command.txt" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Ahoy! The writing is completed: {obs}.
Answer: I have written 'Lower sails!' into command.txt as commanded, Captain!"""
            else:
                return """Thought: The Captain wishes to write a new document 'command.txt'. I must quill the words!
Action: write_file: command.txt | Lower sails!
PAUSE"""

        # Read file mock query
        elif "read the contents of command.txt" in prompt.lower() or "read command.txt" in prompt.lower():
            if "Observation:" in prompt:
                obs = [line for line in prompt.splitlines() if line.strip().startswith("Observation:")][-1].replace("Observation:", "").strip()
                return f"""Thought: Shiver me timbers! The document reads: {obs}.
Answer: Ahoy! The message inside command.txt is: "{obs}"."""
            else:
                return """Thought: The Captain wishes to inspect command.txt. I must retrieve it from the desk!
Action: read_file: command.txt
PAUSE"""

        # First turn for Tokyo
        elif "Tokyo" in prompt or "tokyo" in prompt:
            return """Thought: Ahoy! The crew wants to see if we can set sail for Tokyo. I must cast my weather glass to check their skies!
Action: get_weather: Tokyo
PAUSE"""

        # First turn for London
        elif "London" in prompt or "london" in prompt:
            return """Thought: Ahoy! The crew wants to see if we can set sail for London. I must cast my weather glass to check their skies!
Action: get_weather: London
PAUSE"""
            
        # Non-tool query
        else:
            return """Thought: No weather glass is needed for this query. I shall speak to the user directly as their Captain.
Answer: Ahoy, matey! I am the Pirate Captain ReAct agent. Tell me which port you'd like to navigate, or ask your questions!"""

