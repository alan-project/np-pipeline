import os
import re
from google import genai

def clean_duplicate_parentheses(text):
    """
    Remove duplicate parentheses patterns from translated text.
    1. ABC(ABC) → ABC (same content in parentheses)
    2. Keep only first occurrence of each unique parenthetical term
    """
    if not text:
        return text

    # Step 1: Remove identical parentheses like ABC(ABC) or AAA BBB CCC(AAA BBB CCC)
    def remove_identical(match):
        before = match.group(1).strip()
        inside = match.group(2).strip()
        # If completely identical, remove parentheses
        if before.lower() == inside.lower():
            return before
        return match.group(0)  # Keep original (e.g., New York(NY))

    # Match text followed by parentheses
    pattern = r'([\w\s\-\.]+)\(([^\)]+)\)'
    text = re.sub(pattern, remove_identical, text)

    # Step 2: Track and remove repeated parenthetical terms
    seen_terms = set()

    def track_duplicates(match):
        term = match.group(1).strip()
        if term in seen_terms:
            return ''  # Remove duplicate parenthetical
        seen_terms.add(term)
        return match.group(0)  # Keep first occurrence

    # Match any parenthetical content
    parenthetical_pattern = r'\(([^\)]+)\)'
    text = re.sub(parenthetical_pattern, track_duplicates, text)

    return text

def translate_ai_summary(ai_title, ai_content, lang, config):
    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"ERROR: GEMINI_API_KEY is missing for translation to {lang}")
        return None
    
    # Set up Gemini client (remove duplicate key to avoid warnings)
    if "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"] != api_key:
        del os.environ["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
    client = genai.Client()
    
    system_prompt = config["translation_prompt"](lang)
    user_prompt = f"Title: {ai_title}\nContent: {ai_content}"
    
    full_prompt = system_prompt + "\n\n" + user_prompt

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=full_prompt
        )
        
        result = response.text.strip()
        print(f"\n[{lang.upper()} translation result] {result}")

        if "Title:" in result and "Content:" in result:
            title = result.split("Title:")[1].split("Content:")[0].strip()
            content = result.split("Content:")[1].strip()

            # Clean duplicate parentheses
            title = clean_duplicate_parentheses(title)
            content = clean_duplicate_parentheses(content)

            return {
                "ai_title": title,
                "ai_content": content
            }
        else:
            print(f"'{lang}' translation result format error")
    except Exception as e:
        print(f"error on translation ({lang}): {e}")
    return None





