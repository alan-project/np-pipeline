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
        
def generate_ai_summary(content, api_key):
    api_url = os.getenv("AI_URL")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    categories = [
        "crime",
        "politics",
        "economy",
        "culture",
        "technology",
        "sports",
        "health",
        "other"
    ]

    prompt = (
        "You're a news editor and categorization assistant. Summarize and categorize the following article.\n"
        "- Create a short, engaging Arabic title (1 line max)\n"
        "- Write a brief summary in 2~3 lines in plain Arabic\n"
        "- Determine the category of the article. Choose ONLY ONE from: "
        f"{', '.join(categories)}\n"
        "- Use a neutral, formal tone suitable for news articles\n"
        "- Avoid casual or conversational phrases\n"
        "- Do not use the original title\n"
        "- Respond in the exact format below:\n"
        "Category: <one of above>\n"
        "Title: <your new title>\n"
        "Content: <your summary>\n\n"
        "If the content is not suitable for summarization (e.g., too short, incomplete, or lacks meaning), just return: SKIP\n\n"
        f"Article:\n{content}"
    )

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

            # Parse results
            category, title, summary = None, None, None
            if "Category:" in text and "Title:" in text and "Content:" in text:
                category = text.split("Category:")[1].split("Title:")[0].strip()
                title = text.split("Title:")[1].split("Content:")[0].strip()
                summary = text.split("Content:")[1].strip()

            if not (category and title and summary):
                print("summary/category parsing fail")
                return None

            return {
                "category_ai": category,
                "ai_title": title,
                "ai_content": summary
            }
        else:
            print(f"GPT API resp fail: ({response.status_code})")
    except Exception as e:
        print(f"generate_ai_summary error: {e}")
    return None



# translate_ai_summary function moved to translate.py with config support


def process_article(article, api_key):
    content = article.get("content")

    if not content:
        print(f"no content: article ID {article['article_id']} ")
        return None
    
    # Generate English summary using AI
    ai_summary = generate_ai_summary(content, api_key)
    if not ai_summary:
        print(f"article ID {article['article_id']} Arabic summary fail")
        return None

    article["category_ai"] = ai_summary["category_ai"]
    article["ai_title"] = ai_summary["ai_title"]
    article["ai_content"] = ai_summary["ai_content"]

    # Translate to each language
    translations = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            lang: executor.submit(translate_ai_summary, ai_summary["ai_title"], ai_summary["ai_content"], lang, api_key)
            for lang in ["ur", "hi", "bn", "en"]
        }
        for lang, future in futures.items():
            result = future.result()
            if not result:
                print(f"article ID {article['article_id']} -> {lang} translation fail -> exclude whole article")
                return None
            translations[lang] = result

    translations["ar"] = {
        "ai_title": ai_summary["ai_title"],
        "ai_content": ai_summary["ai_content"]
    }

    article["translations"] = translations
    
    
    article["clicked_cnt"] = 0

    print(f"article ID {article['article_id']} translation is done and stored")
    return article

def select_top_articles(articles, top_article_count, config):
    api_url = os.getenv("AI_URL")
    api_key = config["api_key"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    print(f"\n**Available articles for selection:**")
    for article in articles:
        print(f"  - ID: {article['article_id']}, Title: {article.get('title', 'No title')}")
    
    prompt = config["top_prompt"](top_article_count) + "\n\nHere are the articles:\n\n" + \
        "\n".join([
            f"Article ID: {article['article_id']}\n"
            f"Title: {article['title']}\n"
            "---"
            for article in articles
        ]) + "\n\nReturn ONLY the article IDs of the selected articles, one per line."
    
    data = {
        "model": "gpt-4.1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.3
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            ai_response = response.json().get("choices", [])[0].get("message", {}).get("content", "").strip()
            print(f"\n**AI Response for article selection:**\n{ai_response}")
            content = ai_response.split("\n")
            selected_articles = [article_id.strip() for article_id in content if article_id.strip()][:top_article_count]
            
            print("\n**AI selected TOP article list (removed duplicates):**")
            for idx, article_id in enumerate(selected_articles):
                print(f"  {idx+1}. {article_id}")

            return selected_articles
        else:
            print(f"GPT API resp fail ({response.status_code})")
            print(response.text)
            return []
    except Exception as e:
        print(f"Error in selecting top articles: {e}")
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
