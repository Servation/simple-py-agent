import urllib.request
import urllib.parse

def get_weather(city: str) -> str:
    """Gets the live weather for a given city.
    
    Args:
        city: The name of the city.
    """
    try:
        # URL encode the city name to handle spaces, e.g. "New York"
        encoded_city = urllib.parse.quote(city.strip())
        
        # Use wttr.in plain text format string:
        # %l = location, %C = weather condition, %t = temperature, %w = wind speed/direction
        url = f"https://wttr.in/{encoded_city}?format=%l:+%C,+%t.+Wind+%w"
        
        # A curl User-Agent instructs wttr.in to return raw plain text instead of HTML
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.88.1'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_data = response.read().decode('utf-8').strip()
            
            # Strip non-ASCII characters (e.g. unicode arrows and emojis)
            # to guarantee safe rendering on standard Windows consoles.
            ascii_data = raw_data.encode('ascii', 'ignore').decode('ascii')
            
            # Clean double spaces or double periods if any
            clean_data = ' '.join(ascii_data.split())
            return clean_data
            
    except Exception as e:
        return f"Error fetching live weather for '{city}': {e}"


def calculate(expression: str) -> str:
    """Evaluates a basic mathematical expression.
    
    Args:
        expression: A mathematical expression containing numbers and basic operators (e.g. 12 + 45, 3 * 2).
    """
    try:
        # Sanitize expression: allow only numbers, basic operators, brackets, and dots
        import re
        sanitized = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        result = eval(sanitized, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


# Dictionary mapping tool names to python functions for dynamic lookup
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "calculate": calculate
}
