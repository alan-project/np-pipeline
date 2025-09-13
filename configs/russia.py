import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('Russian')

def translation_prompt(lang):
    return f"""
You are a professional news translator. Translate the following Russian news title and summary into {lang}.
- For proper nouns (names, locations, organizations), first provide the translation or description in {lang}, then add the original Russian in parentheses.
  Example: If translating to English: Russian President Vladimir Putin(Владимир Путин)
  Example: If translating to Ukrainian: Президент Росії Володимир Путін(Владимир Путин)
  Example: If translating to Tajik: Президенти Русия Владимир Путин(Владимир Путин)
  Example: If translating to Uzbek: Rossiya prezidenti Vladimir Putin(Владимир Путин)
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
You are an expert news editor working for a Russian news app targeted at newcomers to Russia.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prefer articles related to Russia or Eastern Europe when available
- If no Russia/Eastern Europe articles are available, select the most globally important news
- Overall importance and public impact
- Reader engagement potential
- Avoid selecting multiple articles with very similar or identical titles

IMPORTANT: You must respond with EXACTLY the Article ID as shown in the list below.
Return ONLY the article IDs of the selected articles, one per line, nothing else.
You MUST select {top_n} articles even if none are specifically about Russia/Eastern Europe.
"""

config = {
    "country": "Russia",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "russia_articles",
    "info_doc": "russia_info",
    "base_lang": "ru",
    "lang_list": ["en", "uk", "tg", "uz"],
    "select_all": False,
    "top_article_ratio": 0.05,
    "timezone": "Europe/Moscow",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}