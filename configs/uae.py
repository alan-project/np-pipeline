import os

summarization_prompt = """
You're a news editor and categorization assistant. Summarize and categorize the following article.
- Create a short, engaging Arabic title (1 line max)
- Write a brief summary in 2~3 lines in plain Arabic
- Determine the category of the article. Choose ONLY ONE from: crime, politics, economy, culture, technology, sports, health, other
- Use a neutral, formal tone suitable for news articles
- Avoid casual or conversational phrases
- Do not use the original title
- Respond in the exact format below:
Category: <one of above>
Title: <your new title>
Content: <your summary>

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
You are an expert news editor working for a UAE news app targeted at newcomers to UAE.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prioritize articles directly related to UAE or Middle East
- Relevance and public impact
- Reader interest
- Avoid duplicates or overly similar titles

Return ONLY the article IDs, one per line.
"""

config = {
    "country": "UAE",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "uae_articles",
    "info_doc": "uae_info",
    "base_lang": "ar",
    "lang_list": ["ur", "hi", "ml", "en"],
    "select_all": False,
    "top_article_ratio": 0.1,
    "timezone": "Asia/Dubai",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}