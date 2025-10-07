import os
import re
from google import genai

def clean_duplicate_parentheses(text, article_id=None):
    """
    Remove duplicate parentheses patterns from translated text.
    1. ABC(ABC) → ABC (same content in parentheses)
    2. (ABC(ABC)) → (ABC) (nested duplicates)
    3. Keep only first occurrence of each unique parenthetical term
    """
    if not text:
        return text

    # Log input
    print(f"\n[{article_id}] [clean_duplicate_parentheses] Input: {text}")
    original_text = text

    # Step 1: Remove nested duplicate parentheses like (SPD(SPD)) → (SPD)
    # First, handle the pattern where the same text appears nested: (TEXT(TEXT))
    nested_pattern = r'\((\w+)\(\1\)\)'
    text = re.sub(nested_pattern, r'(\1)', text)
    print(f"[{article_id}] [clean_duplicate_parentheses] After nested removal: {text}")

    # Step 2: Remove identical parentheses like "Iris Stalzer(Iris Stalzer)" → "Iris Stalzer"
    # Look for cases where the same words appear just before and inside parentheses
    # Match one or more words followed by parentheses containing the same text
    def remove_identical_simple(text):
        """Remove cases where text is immediately followed by itself in parentheses"""
        # Pattern to match any text (excluding parentheses) followed by identical text in parentheses
        # This handles names with special chars like "Elsässer", "Putin'in", etc.
        pattern = r'([^\s()]+(?:\s+[^\s()]+)*)\s*\(\1\)'

        def replace_match(match):
            word = match.group(1)
            print(f"[{article_id}] [clean_duplicate_parentheses] Found duplicate: {word}({word}) → {word}")
            return word

        return re.sub(pattern, replace_match, text)

    text = remove_identical_simple(text)
    print(f"[{article_id}] [clean_duplicate_parentheses] After identical removal: {text}")

    # Step 3: Track and remove repeated parenthetical terms
    seen_terms = set()

    def track_duplicates(match):
        term = match.group(1).strip().lower()
        if term in seen_terms:
            print(f"[{article_id}] [clean_duplicate_parentheses] Removing duplicate parenthetical: ({match.group(1)})")
            return ''  # Remove duplicate parenthetical
        seen_terms.add(term)
        return match.group(0)  # Keep first occurrence

    # Match any parenthetical content
    parenthetical_pattern = r'\(([^\)]+)\)'
    text = re.sub(parenthetical_pattern, track_duplicates, text)

    # Log output
    print(f"[{article_id}] [clean_duplicate_parentheses] Output: {text}")
    if original_text != text:
        print(f"[{article_id}] [clean_duplicate_parentheses] Changed: {original_text} → {text}")

    return text

def translate_ai_summary(ai_title, ai_content, lang, config, article_id=None):
    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"[{article_id}] ERROR: GEMINI_API_KEY is missing for translation to {lang}")
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
        print(f"\n[{article_id}] [{lang.upper()} translation result] {result}")

        if "Title:" in result and "Content:" in result:
            title = result.split("Title:")[1].split("Content:")[0].strip()
            content = result.split("Content:")[1].strip()

            # Clean duplicate parentheses
            title = clean_duplicate_parentheses(title, article_id)
            content = clean_duplicate_parentheses(content, article_id)

            return {
                "ai_title": title,
                "ai_content": content
            }
        else:
            print(f"[{article_id}] '{lang}' translation result format error")
    except Exception as e:
        print(f"[{article_id}] error on translation ({lang}): {e}")
    return None





