import os
from google import genai

def generate_ai_summary(content, config):
    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is missing for summarization")
        return None
    
    # Set up Gemini client
    os.environ["GOOGLE_API_KEY"] = api_key
    client = genai.Client()

    prompt = config["summarization_prompt"].format(content=content)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.5
            )
        )
        
        text = response.text.strip()

        # Handle SKIP response
        if text.upper() == "SKIP":
            print("Gemini resp: SKIP -> failed to summarize article")
            return None

        print("\nAI summary result:\n", text[:500])

        # Parse results for category and content
        category, summary = None, None
        if "Category:" in text and "Content:" in text:
            category = text.split("Category:")[1].split("Content:")[0].strip()
            summary = text.split("Content:")[1].strip()

        if not (category and summary):
            print("summary/category parsing fail")
            return None

        return {
            "category_ai": category,
            "ai_content": summary
        }
    except Exception as e:
        print(f"generate_ai_summary error: {e}")
    return None




