import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('German')

def translation_prompt(lang):
    # Check if source and target languages are the same
    source_lang = 'de'  # Germany's base language

    # Simple logic: only skip parentheses if source and target are the same
    if lang == source_lang:
        return f"""
You are a professional news translator. Translate the following German news title and summary into {lang}.

IMPORTANT: Since the source language (German) and target language ({lang}) are the same, DO NOT add parentheses with original text for proper nouns.

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
        "ro": """- Person names: Cancelarul german Olaf Scholz(Olaf Scholz), Angela Merkel(Angela Merkel)
- Company/Organization names: Volkswagen(Volkswagen), BMW(BMW), Banca Federală Germană(Deutsche Bundesbank)
- City/Country names: Berlin(Berlin), München(München), Frankfurt(Frankfurt), Hamburg(Hamburg)""",

        "ar": """- Person names: المستشار الألماني أولاف شولتس(Olaf Scholz), أنغيلا ميركل(Angela Merkel)
- Company/Organization names: فولكس فاغن(Volkswagen), بي إم دبليو(BMW), البنك الفيدرالي الألماني(Deutsche Bundesbank)
- City/Country names: برلين(Berlin), ميونخ(München), فرانكفورت(Frankfurt), هامبورغ(Hamburg)""",

        "tr": """- Person names: Almanya Şansölyesi Olaf Scholz(Olaf Scholz), Angela Merkel(Angela Merkel)
- Company/Organization names: Volkswagen(Volkswagen), BMW(BMW), Alman Federal Bankası(Deutsche Bundesbank)
- City/Country names: Berlin(Berlin), Münih(München), Frankfurt(Frankfurt), Hamburg(Hamburg)""",

        "ru": """- Person names: Канцлер Германии Олаф Шольц(Olaf Scholz), Ангела Меркель(Angela Merkel)
- Company/Organization names: Фольксваген(Volkswagen), БМВ(BMW), Немецкий федеральный банк(Deutsche Bundesbank)
- City/Country names: Берлин(Berlin), Мюнхен(München), Франкфурт(Frankfurt), Гамбург(Hamburg)""",

        "en": """- Person names: German Chancellor Olaf Scholz(Olaf Scholz), Angela Merkel(Angela Merkel)
- Company/Organization names: Volkswagen(Volkswagen), BMW(BMW), German Federal Bank(Deutsche Bundesbank)
- City/Country names: Berlin(Berlin), Munich(München), Frankfurt(Frankfurt), Hamburg(Hamburg)"""
    }

    lang_examples = examples.get(lang, examples["en"])  # Default to English if lang not found

    return f"""
You are a professional news translator. Translate the following German news title and summary into {lang}.

STRICT REQUIREMENTS:
1. ALL proper nouns (names, locations, organizations, brands) MUST include the original German text in parentheses
2. Format: Translation(Original)
3. This rule is MANDATORY - apply to every proper noun in the content

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
Content: <translated summary with ALL proper nouns followed by (Original German)>
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
    "lang_list": ["ro", "ar", "tr", "ru"],
    "select_all": False,
    "top_article_ratio": 0.08,
    "timezone": "Europe/Berlin",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}