import requests
import os
        



def translate_ai_summary(ai_title, ai_content, lang, config):
    api_url = "https://api.openai.com/v1/chat/completions"
    api_key = config["api_key"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = config["translation_prompt"](lang)
    user_prompt = f"Title: {ai_title}\nContent: {ai_content}"

    data = {
        "model": "gpt-5-mini",
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

            if "Title:" in result and "Content:" in result:
                title = result.split("Title:")[1].split("Content:")[0].strip()
                content = result.split("Content:")[1].strip()
                return {
                    "ai_title": title,
                    "ai_content": content
                }
            else:
                print(f"'{lang}' translation result format error")
        else:
            print(f"translation fail ({lang}): Status {response.status_code}")
    except Exception as e:
        print(f"error on translation ({lang}): {e}")
    return None





