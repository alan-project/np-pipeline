import os
from google import genai

def generate_ai_summary(content, config, article_id=None):
    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"[{article_id}] ERROR: GEMINI_API_KEY is missing for summarization")
        return None
    
    # Set up Gemini client (remove duplicate key to avoid warnings)
    if "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"] != api_key:
        del os.environ["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
    client = genai.Client()

    prompt = config["summarization_prompt"].format(content=content)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        
        text = response.text.strip()

        # Handle SKIP response
        if text.upper() == "SKIP":
            print(f"[{article_id}] Gemini resp: SKIP -> failed to summarize article")
            return None

        print(f"\n[{article_id}] AI summary result:\n", text[:500])

        # Parse results for category and content
        category, summary = None, None
        if "Category:" in text and "Content:" in text:
            category = text.split("Category:")[1].split("Content:")[0].strip()
            summary = text.split("Content:")[1].strip()

        if not (category and summary):
            print(f"[{article_id}] summary/category parsing fail")
            return None

        return {
            "category_ai": category,
            "ai_content": summary
        }
    except Exception as e:
        print(f"[{article_id}] generate_ai_summary error: {e}")
    return None




