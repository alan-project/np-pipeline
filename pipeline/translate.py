import os
from google import genai

def translate_ai_summary(ai_title, ai_content, lang, config):
    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"ERROR: GEMINI_API_KEY is missing for translation to {lang}")
        return None
    
    # Set up Gemini client
    os.environ["GOOGLE_API_KEY"] = api_key
    client = genai.Client()
    
    system_prompt = config["translation_prompt"](lang)
    user_prompt = f"Title: {ai_title}\nContent: {ai_content}"
    
    full_prompt = system_prompt + "\n\n" + user_prompt

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        
        result = response.text.strip()
        print(f"\n[{lang.upper()} translation result] {result}")

        if "Title:" in result and "Content:" in result:
            title = result.split("Title:")[1].split("Content:")[0].strip()
            content = result.split("Content:")[1].strip()
            return {
                "ai_title": title,
                "ai_content": content
            }
        else:
            print(f"'{lang}' translation result format error")
    except Exception as e:
        print(f"error on translation ({lang}): {e}")
    return None





