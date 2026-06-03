import urllib.request
import urllib.parse
import datetime
import os
import re
import json

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


def write_ships_log(entry: str, llm_client = None) -> str:
    """Writes an entry into the ship's log file with a timestamp. Handles auto-compaction at 30 entries.
    
    Args:
        entry: The log entry description to write (e.g. Spotted a storm).
        llm_client: Injected LLM client for performing log compaction summaries (automatically managed).
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        active_file = "ships_log.txt"
        archive_file = "ships_log_archive.txt"
        
        # Write the entry to active log
        with open(active_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {entry.strip()}\n")
            
        # Check active log line count
        with open(active_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Threshold for log compaction. We use 30 as defined in ADR 0004.
        # Developers can change this to 3 for testing.
        COMPACTION_THRESHOLD = 30
        
        compacted_msg = ""
        if len(lines) >= COMPACTION_THRESHOLD and llm_client is not None:
            # 1. Read entire active log content
            full_content = "".join(lines)
            
            # 2. Append to raw archive log
            with open(archive_file, "a", encoding="utf-8") as f_arch:
                archive_header = f"\n--- ARCHIVE SESSION COMPACTION: {timestamp} ---\n"
                f_arch.write(archive_header + full_content)
                
            # 3. Request LLM Client to summarize the log entries
            prompt = f"""You are the First Mate compiling the Captain's ship log history.
Summarize the following raw chronological log entries into a concise summary of EXACTLY 5 bullet points.
Retain key dates, coordinates/cities, and major milestones. Discard repetitive entries.

Raw Log Entries:
{full_content}

Summarized Ship Log (exactly 5 bullet points, start each bullet with '-'):"""
            
            try:
                summary = llm_client.generate(prompt)
                
                # 4. Overwrite active log with the summary
                with open(active_file, "w", encoding="utf-8") as f_active:
                    f_active.write(summary.strip() + "\n")
                compacted_msg = " (Notice: Log compacted and archived because it reached 30 entries!)"
            except Exception as summary_err:
                compacted_msg = f" (Warning: Compaction failed during LLM summary: {summary_err})"
                
        return f"Successfully recorded in the ship's log: '{entry.strip()}'{compacted_msg}"
    except Exception as e:
        return f"Error writing to ship's log: {e}"


def read_ships_log(dummy: str = "") -> str:
    """Reads the entire contents of the ship's log file.
    
    Args:
        dummy: Optional dummy parameter (can be left blank).
    """
    try:
        if not os.path.exists("ships_log.txt"):
            return "The ship's log is empty. No entries have been recorded yet."
        with open("ships_log.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content if content else "The ship's log is empty."
    except Exception as e:
        return f"Error reading ship's log: {e}"


def get_system_time(timezone_offset: str = "0") -> str:
    """Gets the current system date and time, adjusted by an hourly offset.
    
    Args:
        timezone_offset: Hour offset from UTC (e.g. +9 for JST/Tokyo, -5 for EST/New York, or 0 for UTC/London).
    """
    try:
        # Parse timezone offset (default to 0 if invalid or empty)
        try:
            offset = float(timezone_offset.strip())
        except ValueError:
            offset = 0.0
            
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        target_time = utc_now + datetime.timedelta(hours=offset)
        formatted_time = target_time.strftime("%A, %Y-%m-%d %H:%M:%S")
        offset_str = f"UTC{'+' if offset >= 0 else ''}{offset}"
        return f"Time ({offset_str}): {formatted_time}"
    except Exception as e:
        return f"Error retrieving system time: {e}"


def search_wikipedia(query: str) -> str:
    """Searches Wikipedia and returns a short summary of the page.
    
    Args:
        query: The topic or term to look up (e.g. Blackbeard).
    """
    try:
        # Standardize and URL encode query
        formatted_query = urllib.parse.quote(query.strip().replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_query}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.88.1'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Extract summary text
            summary = data.get("extract", "")
            if not summary:
                return f"No Wikipedia summary found for '{query}'."
                
            # Strip non-ASCII characters to keep terminal output safe on Windows
            clean_summary = summary.encode('ascii', 'ignore').decode('ascii')
            return clean_summary
            
    except Exception as e:
        return f"Could not find Wikipedia entry for '{query}'. Error: {e}"


def translate_to_pirate(text: str) -> str:
    """Translates standard English text into pirate slang phrases.
    
    Args:
        text: The English sentence or word to translate.
    """
    pirate_dict = {
        "hello": "ahoy",
        "hi": "ahoy",
        "friend": "matey",
        "friends": "mateys",
        "yes": "aye",
        "no": "nay",
        "my": "me",
        "of": "o'",
        "you": "ye",
        "your": "yer",
        "are": "be",
        "is": "be",
        "was": "were",
        "money": "doubloons",
        "gold": "booty",
        "treasure": "loot",
        "look": "avast",
        "where": "whither",
        "stop": "avast",
    }
    
    words = text.split()
    translated_words = []
    
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word).lower()
        punctuation = re.sub(r'[\w]', '', word)
        
        if clean_word in pirate_dict:
            t_word = pirate_dict[clean_word]
            if word.isupper():
                t_word = t_word.upper()
            elif word[0].isupper():
                t_word = t_word.capitalize()
            translated_words.append(t_word + punctuation)
        else:
            translated_words.append(word)
            
    return " ".join(translated_words)


def read_file(filename: str) -> str:
    """Reads the contents of a local file in the workspace.
    
    Args:
        filename: The name/path of the file to read (e.g. command.txt).
    """
    try:
        clean_name = filename.strip()
        # Protect against path traversal (only allow files within the workspace)
        if ".." in clean_name or clean_name.startswith("/") or clean_name.startswith("\\"):
            return "Error: Access denied. Paths outside the workspace are prohibited."
            
        if not os.path.exists(clean_name):
            return f"Error: File '{clean_name}' does not exist."
            
        with open(clean_name, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(arguments: str) -> str:
    """Creates or overwrites a local file with the specified content.
    
    Args:
        arguments: Format must be 'filename | content' (e.g. 'command.txt | Lower sails!').
    """
    try:
        if "|" not in arguments:
            return "Error: Arguments must be in the format 'filename | content'."
            
        parts = arguments.split("|", 1)
        filename = parts[0].strip()
        content = parts[1].strip()
        
        # Protect against path traversal
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            return "Error: Access denied. Paths outside the workspace are prohibited."
            
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to file '{filename}'"
    except Exception as e:
        return f"Error writing file: {e}"


def list_directory(dummy: str = "") -> str:
    """Lists all files and directories in the current working directory.
    
    Args:
        dummy: Optional dummy parameter (can be left blank).
    """
    try:
        files = os.listdir(".")
        if not files:
            return "The current directory is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error listing directory: {e}"


# Dictionary mapping tool names to python functions for dynamic lookup
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "write_ships_log": write_ships_log,
    "read_ships_log": read_ships_log,
    "get_system_time": get_system_time,
    "search_wikipedia": search_wikipedia,
    "translate_to_pirate": translate_to_pirate,
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory
}
