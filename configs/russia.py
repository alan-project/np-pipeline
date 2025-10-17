import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('Russian')

def translation_prompt(lang):
    # Check if source and target languages are the same
    source_lang = 'ru'  # Russia's base language

    # Simple logic: only skip parentheses if source and target are the same
    if lang == source_lang:
        return f"""
You are a professional news translator. Translate the following Russian news title and summary into {lang}.

IMPORTANT: Since the source language (Russian) and target language ({lang}) are the same, DO NOT add parentheses with original text for proper nouns.

- For the title, translate naturally in {lang} but keep it short and concise.
- Maintain a neutral, objective tone suitable for news articles.
- Use formal language and avoid conversational tone.
- Do not add any extra comments or labels.

Return your response in this format:
Title: <translated title>
Content: <translated summary>
"""

    # Language-specific examples
    examples = {
        "en": """- Person names: Russian President Vladimir Putin(Владимир Путин), Sergey Lavrov(Сергей Лавров)
- Company/Organization names: Gazprom(Газпром), Sberbank(Сбербанк), Russian Railways(РЖД)
- City/Country names: Moscow(Москва), Saint Petersburg(Санкт-Петербург), Novosibirsk(Новосибирск)""",

        "uk": """- Person names: Президент Росії Володимир Путін(Владимир Путин), Сергій Лавров(Сергей Лавров)
- Company/Organization names: Газпром(Газпром), Сбербанк(Сбербанк), Російські залізниці(РЖД)
- City/Country names: Москва(Москва), Санкт-Петербург(Санкт-Петербург), Новосибірськ(Новосибирск)""",

        "tg": """- Person names: Президенти Русия Владимир Путин(Владимир Путин), Сергей Лавров(Сергей Лавров)
- Company/Organization names: Газпром(Газпром), Сбербанк(Сбербанк), Роҳи оҳани Русия(РЖД)
- City/Country names: Москва(Москва), Санкт-Петербург(Санкт-Петербург), Новосибирск(Новосибирск)""",

        "uz": """- Person names: Rossiya prezidenti Vladimir Putin(Владимир Путин), Sergey Lavrov(Сергей Лавров)
- Company/Organization names: Gazprom(Газпром), Sberbank(Сбербанк), Rossiya temir yoʻllari(РЖД)
- City/Country names: Moskva(Москва), Sankt-Peterburg(Санкт-Петербург), Novosibirsk(Новосибирск)"""
    }

    lang_examples = examples.get(lang, examples["en"])  # Default to English if lang not found

    return f"""
You are a professional news translator. Translate the following Russian news title and summary into {lang}.

STRICT REQUIREMENTS:
1. ONLY these proper nouns need parentheses with original Russian text:
   - Person names (politicians, celebrities, public figures)
   - Geographic locations (countries, cities, regions)
   - Organizations and companies
   - Brand names
2. Format: Translation(Original)
3. DO NOT add parentheses for:
   - Common nouns (war, prisoner, video, shock, death, etc.)
   - Verbs or adjectives
   - General concepts or abstract nouns
4. This rule is MANDATORY - be precise about what qualifies as a proper noun

DETAILED EXAMPLES for {lang}:
{lang_examples}

IMPORTANT NOTES:
- For the title, translate naturally in {lang} but keep it short and concise. Avoid using parentheses in the title.
- Maintain a neutral, objective tone suitable for news articles.
- Use formal language and avoid conversational tone.
- Do not add any extra comments or labels.
- CRITICAL: Use ONLY {lang} script/characters in your translation. Do NOT mix characters from other languages.

Return your response in this format:
Title: <translated title>
Content: <translated summary with ALL proper nouns followed by (Original Russian)>
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