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
        "max_completion_tokens": 1024
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            message = response_data.get("choices", [])[0].get("message", {})
            
            # Check for refusal first
            refusal = message.get("refusal")
            if refusal:
                print(f"\n[{lang.upper()} translation refused] {refusal}")
                return None
            
            result = message.get("content", "")
            print(f"\n[{lang.upper()} translation result] {result}")
            print(f"[{lang.upper()} result length] {len(result)}")
            print(f"[{lang.upper()} result type] {type(result)}")
            
            # Check if result is empty
            if not result or not result.strip():
                print(f"[{lang.upper()} translation] Empty response from API")
                return None

            if "Title:" in result and "Content:" in result:
                title = result.split("Title:")[1].split("Content:")[0].strip()
                content = result.split("Content:")[1].strip()
                return {
                    "ai_title": title,
                    "ai_content": content
                }
            else:
                print(f"'{lang}' translation result format error - missing Title: or Content:")
                print(f"'{lang}' raw result: '{result[:200]}...'")
        else:
            print(f"translation fail ({lang}): Status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"error on translation ({lang}): {e}")
    return None





