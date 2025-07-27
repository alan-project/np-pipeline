import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Config-driven approach - no hardcoded values
        



# translate_ai_summary function moved to translate.py with config support



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

