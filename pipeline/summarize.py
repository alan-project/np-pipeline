import requests
import os

# Config-driven approach - no hardcoded values
        
def generate_ai_summary(content, config):
    api_url = os.getenv("AI_URL")
    api_key = config["api_key"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = config["summarization_prompt"].format(content=content)

    data = {
        "model": "gpt-5-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.5
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            text = response.json().get("choices", [])[0].get("message", {}).get("content", "").strip()

            # Handle SKIP response
            if text.upper() == "SKIP":
                print("GPT resp: SKIP -> failed to summarize article")
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
        else:
            print(f"GPT API resp fail: ({response.status_code})")
    except Exception as e:
        print(f"generate_ai_summary error: {e}")
    return None




