import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('German')

def translation_prompt(lang):
    return f"""
You are a professional news translator. Translate the following German news title and summary into {lang}.
- Keep proper nouns (like names, locations, or organizations) in German within parentheses in the summary.
- For the title, translate naturally in {lang} but keep it short and concise. Avoid using parentheses in the title.
- Maintain a neutral, objective tone suitable for news articles.
- Use formal language and avoid conversational tone.
- Do not add any extra comments or labels.

Return your response in this format:
Title: <translated title>
Content: <translated summary>
"""

def top_prompt(top_n):
    return f"""
You are an expert news editor working for a German news app targeted at newcomers to Germany.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prefer articles related to Germany or Europe when available
- If no Germany/Europe articles are available, select the most globally important news
- Overall importance and public impact
- Reader engagement potential
- Avoid selecting multiple articles with very similar or identical titles

IMPORTANT: You must respond with EXACTLY the Article ID as shown in the list below.
Return ONLY the article IDs of the selected articles, one per line, nothing else.
You MUST select {top_n} articles even if none are specifically about Germany/Europe.
"""

config = {
    "country": "Germany",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "germany_articles",
    "info_doc": "germany_info",
    "base_lang": "de",
    "lang_list": ["en", "ar", "tr", "ru"],
    "select_all": False,
    "top_article_ratio": 0.15,
    "timezone": "Europe/Berlin",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}