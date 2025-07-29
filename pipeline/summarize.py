import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import firebase_admin
import os
import re
from firebase_admin import credentials, firestore
from enum import Enum
from datetime import datetime

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
        "model": "gpt-4.1-mini",
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



def translate_ai_summary(ai_title, ai_content, lang, config):
    api_url = "https://api.openai.com/v1/chat/completions"
    api_key = config["api_key"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = config["translation_prompt"](lang)

    user_prompt = (
        f"Title: {ai_title}\n"
        f"Content: {ai_content}"
    )

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


def process_article(article, config, api_key):
    content = article.get("content")
    title = article.get("title")
    server_ai_summary = article.get("ai_summary")

    if not title:
        print(f"no title: article ID {article['article_id']} ")
        return None
    
    # Check if server already has ai_summary
    if server_ai_summary:
        print(f"article ID {article['article_id']} using existing ai_summary from server")
        ai_content = server_ai_summary
        # Use original title from server
        # Note: When using server ai_summary, we don't have AI-generated category
        # so we keep the original server category
    else:
        # Generate summary using AI if not available from server
        if not content:
            print(f"no content: article ID {article['article_id']} ")
            return None
        
        print(f"article ID {article['article_id']} generating new ai_summary")
        ai_summary = generate_ai_summary(content, {**config, "api_key": api_key})
        if not ai_summary:
            print(f"article ID {article['article_id']} summary fail")
            return None
        ai_content = ai_summary["ai_content"]
        ai_category = ai_summary["category_ai"]

    # Translate to each language using original title
    translations = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            lang: executor.submit(translate_ai_summary, title, ai_content, lang, config)
            for lang in config["lang_list"]
        }
        for lang, future in futures.items():
            result = future.result()
            if not result:
                print(f"article ID {article['article_id']} -> {lang} translation fail -> exclude whole article")
                return None
            translations[lang] = result

    translations[config["base_lang"]] = {
        "ai_title": title,
        "ai_content": ai_content
    }

    article["translations"] = translations
    article["clicked_cnt"] = 0
    
    # Add AI category to article (overriding server category)
    if 'ai_category' in locals():
        article["category"] = ai_category
        article["category_ai"] = ai_category

    print(f"article ID {article['article_id']} translation is done and stored")
    return article

