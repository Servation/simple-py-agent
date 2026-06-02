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

