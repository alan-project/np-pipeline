import requests
import os
        



def translate_ai_summary(title, ai_summary, lang, config):
    api_url = "https://api.openai.com/v1/chat/completions"
    api_key = config["api_key"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = config["translation_prompt"](lang)
    user_prompt = f"Title: {title}\nSummary: {ai_summary}"

    data = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.3
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json().get("choices", [])[0].get("message", {}).get("content", "")
            print(f"\n[{lang.upper()} translation result] {result}")

            if "Title:" in result and "Summary:" in result:
                translated_title = result.split("Title:")[1].split("Summary:")[0].strip()
                translated_summary = result.split("Summary:")[1].strip()
                return {
                    "ai_title": translated_title,
                    "ai_content": translated_summary
                }
            else:
                print(f"'{lang}' translation result format error")
                return None
        else:
            print(f"translation fail ({lang}): Status {response.status_code}")
    except Exception as e:
        print(f"error on translation ({lang}): {e}")
    return None


