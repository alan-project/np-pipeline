import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('English')

def translation_prompt(lang):
    return f"""
You are a professional news translator. Translate the following English news title and summary into {lang}.
- Keep proper nouns (like names, locations, or organizations) in English within parentheses in the summary.
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
You are an expert news editor working for a Canadian news app targeted at newcomers to Canada.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prefer articles related to Canada or North America when available
- If no Canada/North America articles are available, select the most globally important news
- Overall importance and public impact
- Reader engagement potential
- Avoid selecting multiple articles with very similar or identical titles

CRITICAL: You must copy EXACTLY the Article ID as shown below. Do NOT modify, shorten, or change any characters.
- Copy the entire ID string character by character
- Double-check each ID before including it in your response
- Return ONLY the article IDs, one per line, no additional text
- You MUST select exactly {top_n} articles

Example format:
eaf5dbb6c306b8ab5f539ed210b18958
a153b83d4640740c93766d23dbafcd67
"""

config = {
    "country": "Canada",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "canada_articles",
    "info_doc": "canada_info",
    "base_lang": "en",
    "lang_list": ["ko", "hi", "zh", "ar"],
    "select_all": False,
    "top_article_ratio": 0.12,
    "timezone": "America/Toronto",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}
