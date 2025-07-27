import os

summarization_prompt = """
You're a news summarization assistant. Summarize the following article.
- Write a brief summary in 2~3 lines in plain Arabic
- Use a neutral, formal tone suitable for news articles
- Avoid casual or conversational phrases
- Respond with ONLY the summary content

If the content is not suitable for summarization (e.g., too short, incomplete, or lacks meaning), just return: SKIP

Article:
{content}
"""

def translation_prompt(lang):
    return f"""
You are a professional news translator. Translate the following Arabic news title and summary into {lang}.
- Translate proper nouns unless globally recognized in Arabic
- Title must be short and natural in {lang}
- Use neutral and formal tone
- Respond ONLY in the following format:
Title: <translated title>
Content: <translated summary>
"""

def top_prompt(top_n):
    return f"""
You are an expert news editor working for a Saudi news app targeted at newcomers to Saudi.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prioritize articles directly related to Saudi or Middle East
- Relevance and public impact
- Reader interest
- Avoid duplicates or overly similar titles

Return ONLY the article IDs, one per line.
"""

config = {
    "country": "Saudi",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "saudi_articles",
    "info_doc": "saudi_info",
    "base_lang": "ar",
    "lang_list": ["ur", "hi", "bn", "en"],
    "select_all": False,
    "top_article_ratio": 0.2,
    "timezone": "Asia/Riyadh",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}