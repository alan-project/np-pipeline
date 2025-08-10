import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import firebase_admin
import os
import re
from firebase_admin import credentials, firestore
from enum import Enum
from datetime import datetime
import importlib

# Config-driven approach - no hardcoded values
        



# translate_ai_summary function moved to translate.py with config support



def select_top_articles(articles, top_article_count, config):
    print(f"\n**=== DEBUG: Starting article selection ===**")
    print(f"**Total articles to choose from:** {len(articles)}")
    print(f"**Target selection count:** {top_article_count}")
    
    # Check environment variables
    api_url = os.getenv("AI_URL")
    print(f"**AI_URL from env:** {api_url}")
    
    if not api_url:
        print("**ERROR: AI_URL environment variable is not set!**")
        return []
    
    api_key = config.get("api_key")
    print(f"**API key exists:** {bool(api_key)}")
    print(f"**API key length:** {len(api_key) if api_key else 0}")
    
    if not api_key:
        print("**ERROR: API key is missing from config!**")
        return []
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    print(f"\n**Available articles for selection:**")
    for article in articles:
        print(f"  - ID: {article['article_id']}, Title: {article.get('title', 'No title')}")
    
    # Check if top_prompt function exists
    if "top_prompt" not in config:
        print("**ERROR: top_prompt function not found in config!**")
        return []
    
    try:
        base_prompt = config["top_prompt"](top_article_count)
        print(f"**Base prompt generated successfully, length:** {len(base_prompt)}")
    except Exception as e:
        print(f"**ERROR: Failed to generate base prompt: {e}**")
        return []
    
    prompt = base_prompt + "\n\nHere are the articles:\n\n" + \
        "\n".join([
            f"Article ID: {article['article_id']}\n"
            f"Title: {article['title']}\n"
            "---"
            for article in articles
        ]) + "\n\nReturn ONLY the article IDs of the selected articles, one per line."
    
    print(f"**Final prompt length:** {len(prompt)}")
    print(f"**Final prompt preview (first 500 chars):**\n{prompt[:500]}...")
    
    data = {
        "model": "gpt-5",
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 400
    }

    try:
        print(f"\n**Making API request to:** {api_url}")
        print(f"**Request payload:** {data}")
        response = requests.post(api_url, headers=headers, json=data)
        print(f"**API Response Status:** {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                print(f"**API Response JSON keys:** {list(response_json.keys())}")
                
                choices = response_json.get("choices", [])
                print(f"**Choices array length:** {len(choices)}")
                
                if not choices:
                    print("**ERROR: No choices in API response**")
                    return []
                
                message = choices[0].get("message", {})
                print(f"**Message keys:** {list(message.keys())}")
                
                ai_response = message.get("content", "").strip()
                print(f"**Raw AI Response:** '{ai_response}'")
                print(f"**AI Response length:** {len(ai_response)}")
                print(f"**AI Response type:** {type(ai_response)}")
                
                if not ai_response:
                    print("**ERROR: AI returned empty response**")
                    return []
                
                if ai_response.lower() == "none":
                    print("**ERROR: AI explicitly returned 'none'**")
                    return []
                
                print(f"\n**AI Response for article selection:**\n{ai_response}")
                
                # Parse response
                content_lines = ai_response.split("\n")
                print(f"**Split into {len(content_lines)} lines:**")
                for i, line in enumerate(content_lines):
                    print(f"  Line {i+1}: '{line.strip()}'")
                
                selected_articles = [article_id.strip() for article_id in content_lines if article_id.strip()][:top_article_count]
                
                print(f"**After filtering, {len(selected_articles)} articles selected:**")
                for i, article_id in enumerate(selected_articles):
                    print(f"  {i+1}. '{article_id}'")
                
                # Validate selected articles exist in original list
                valid_ids = [article['article_id'] for article in articles]
                print(f"**Valid article IDs:** {valid_ids}")
                
                validated_articles = []
                for article_id in selected_articles:
                    if article_id in valid_ids:
                        validated_articles.append(article_id)
                        print(f"  ✓ '{article_id}' is valid")
                    else:
                        print(f"  ✗ '{article_id}' is NOT in original list")
                
                print("\n**AI selected TOP article list (validated):**")
                for idx, article_id in enumerate(validated_articles):
                    print(f"  {idx+1}. {article_id}")

                return validated_articles
                
            except Exception as json_error:
                print(f"**ERROR: Failed to parse JSON response: {json_error}**")
                print(f"**Raw response text:** {response.text}")
                return []
        else:
            print(f"GPT API resp fail ({response.status_code})")
            print(f"**Response text:** {response.text}")
            return []
    except Exception as e:
        print(f"Error in selecting top articles: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_page_articles(url):
    """fetching single page"""
    response = requests.get(url)
    data = response.json()
    if data["status"] == "success":
        return data.get("results", []), data.get("nextPage")
    return [], None

def fetch_articles(api_url, api_key, config):
    all_articles = []
    next_page = None
    page_count = 0
    
    # Get first page
    first_page_articles, next_page = get_page_articles(api_url)
    all_articles.extend(first_page_articles)
    page_count += 1
    print(f"\n**Page {page_count} article number:**", len(first_page_articles))
    
    # Get remaining pages if nextPage exists
    while next_page:
        page_url = f"{api_url}&page={next_page}"
        page_articles, next_page = get_page_articles(page_url)
        all_articles.extend(page_articles)
        page_count += 1
        print(f"**Page {page_count} article number:**", len(page_articles))
    
    print(f"\n**Total pages fetched:** {page_count}")
    print("**AI target article numbers (description included):**", len(all_articles))
    
    if config["select_all"]:
        selected_articles = all_articles
        print("\n**ALL articles selected for translation.**")
    else:
        top_article_count = max(1, round(len(all_articles) * config["top_article_ratio"]))
        selected_article_ids = select_top_articles(all_articles, top_article_count, {**config, "api_key": api_key})
        selected_articles = [article for article in all_articles if article["article_id"] in selected_article_ids]
        print("\n**Selected articles for translation:**")
        for article in selected_articles:
            print(f"  - {article['title']} (ID: {article['article_id']})")

    print("\n**Translating and storing to Firebase...**")
    # Force reload the news_pipeline module to get latest changes
    from . import news_pipeline
    importlib.reload(news_pipeline)
    from .news_pipeline import process_article
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_article, article, config, api_key) for article in selected_articles]
        processed_articles = [future.result() for future in as_completed(futures)]
        processed_articles = [article for article in processed_articles if article is not None]

    return processed_articles, len(all_articles)

def save_to_firestore(data):
    collection_name = "saudi_articles"
    for article in data:
        if not article:
            continue
        article_id = article["article_id"]
        db.collection(collection_name).document(article_id).set(article)
        print(f"update success: {article_id}")
    
    try:
        db.collection("saudi_info").document("meta").set({
            "lastUpdatedAt": datetime.utcnow()
        }, merge=True)
        print("meta data updated")
    except Exception as e:
        print(f"metadata update fail: {e}")


if __name__ == "__main__":
    print(f"START TIME: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC / {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    final_result = fetch_articles(api_url, api_key)
    save_to_firestore(final_result)
